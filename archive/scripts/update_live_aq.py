import os
import json
import requests
from datetime import datetime

# =========================
# CONFIG
# =========================

API_KEY = "B422C1EB-F856-430D-81AB-C0834D831F39"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "live_air_quality.json")
HISTORY_FILE = os.path.join(DATA_DIR, "live_air_quality_history.json")

os.makedirs(DATA_DIR, exist_ok=True)

AIRNOW_URL = "https://www.airnowapi.org/aq/observation/latLong/current/"
CHPC_UT_URL = "https://utahaq.chpc.utah.edu/jsondata/FixedSiteMapData.json"
NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"

NWS_HEADERS = {
    "User-Agent": "StewardBasin/1.0 ruthjanegibson@gmail.com",
    "Accept": "application/geo+json",
}

MONITOR_POINTS = [
    {"name": "Fruitland", "lat": 40.2144, "lng": -110.8413, "distance": 35},
    {"name": "Duchesne", "lat": 40.1633, "lng": -110.4029, "distance": 35},
    {"name": "Roosevelt", "lat": 40.2994, "lng": -109.9887, "distance": 35},
    {"name": "Fort Duchesne", "lat": 40.2889, "lng": -109.8618, "distance": 35},
    {"name": "Vernal", "lat": 40.4555, "lng": -109.5287, "distance": 35},
    {"name": "Horsepool", "lat": 40.143, "lng": -109.468, "distance": 35},
    {"name": "South Ouray", "lat": 40.0894, "lng": -109.6812, "distance": 35},
]


# =========================
# HELPERS
# =========================


def fetch_airnow_for_point(point):
    params = {
        "format": "application/json",
        "latitude": point["lat"],
        "longitude": point["lng"],
        "distance": point["distance"],
        "API_KEY": API_KEY,
    }

    response = requests.get(AIRNOW_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def find_pollutant(records, pollutant_name):
    for record in records:
        if record.get("ParameterName", "").lower() == pollutant_name.lower():
            return record
    return None


def get_highest_aqi(records):
    values = [
        record.get("AQI") for record in records if isinstance(record.get("AQI"), int)
    ]

    return max(values) if values else "--"


def simplify_airnow_records(point, records):
    ozone = find_pollutant(records, "O3")
    pm25 = find_pollutant(records, "PM2.5")
    pm10 = find_pollutant(records, "PM10")

    return {
        "name": point["name"],
        "lat": point["lat"],
        "lng": point["lng"],
        "aqi": get_highest_aqi(records),
        "ozone": ozone.get("AQI") if ozone else "--",
        "pm25": pm25.get("AQI") if pm25 else "--",
        "pm10": pm10.get("AQI") if pm10 else "--",
        "raw_airnow_records": records,
    }


def fetch_nws_fire_risk(point):
    params = {"point": f'{point["lat"]},{point["lng"]}'}

    try:
        response = requests.get(
            NWS_ALERTS_URL,
            params=params,
            headers=NWS_HEADERS,
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        alerts = data.get("features", [])
        fire_alerts = []

        for alert in alerts:
            properties = alert.get("properties", {})

            event = properties.get("event", "")
            headline = properties.get("headline", "")
            severity = properties.get("severity", "")
            description = properties.get("description", "")

            text = f"{event} {headline} {description}".lower()

            if (
                "red flag" in text
                or "fire weather" in text
                or "critical fire" in text
                or "extreme fire" in text
            ):
                fire_alerts.append(
                    {
                        "location": point["name"],
                        "event": event,
                        "headline": headline,
                        "severity": severity,
                    }
                )

        return fire_alerts

    except Exception as e:
        print(f"NWS unavailable for {point['name']}: {e}")
        return []


def append_history_snapshot(output):

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            try:
                history = json.load(file)
            except json.JSONDecodeError:
                history = []
    else:
        history = []

    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "updated": output.get("updated"),
        "aqi": output.get("aqi"),
        "ozone": output.get("ozone"),
        "pm25": output.get("pm25"),
        "pm10": output.get("pm10"),
        "fireRisk": output.get("fireRisk"),
        "stations": output.get("stations", []),
    }

    history.append(snapshot)

    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=2)


# =========================
# MAIN
# =========================


def main():
    stations = []
    all_fire_alerts = []

    for point in MONITOR_POINTS:
        print(f"\nFetching AirNow for {point['name']}...")

        try:
            records = fetch_airnow_for_point(point)
            station_data = simplify_airnow_records(point, records)
            stations.append(station_data)

        except Exception as e:
            print(f"AirNow unavailable for {point['name']}: {e}")

            stations.append(
                {
                    "name": point["name"],
                    "lat": point["lat"],
                    "lng": point["lng"],
                    "aqi": "--",
                    "ozone": "--",
                    "pm25": "--",
                    "pm10": "--",
                    "raw_airnow_records": [],
                }
            )

        fire_alerts = fetch_nws_fire_risk(point)
        all_fire_alerts.extend(fire_alerts)

    valid_aqi_values = [
        station["aqi"] for station in stations if isinstance(station.get("aqi"), int)
    ]

    highest_station = None

    if valid_aqi_values:
        highest_aqi = max(valid_aqi_values)

        for station in stations:
            if station["aqi"] == highest_aqi:
                highest_station = station
                break
    else:
        highest_aqi = "--"
        highest_station = stations[0] if stations else {}

    if all_fire_alerts:
        fire_risk = all_fire_alerts[0]["event"] or "Fire Weather Alert"
    else:
        fire_risk = "No active NWS fire weather alert"

    output = {
        "aqi": highest_aqi,
        "ozone": highest_station.get("ozone", "--") if highest_station else "--",
        "pm25": highest_station.get("pm25", "--") if highest_station else "--",
        "pm10": highest_station.get("pm10", "--") if highest_station else "--",
        "fireRisk": fire_risk,
        "fireAlerts": all_fire_alerts,
        "updated": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "source": "AirNow API + NWS API",
        "location": "Eastern Utah / Uinta Basin monitor points",
        "stations": stations,
        "note": "AirNow values are live AQI observations near selected Eastern Utah points. NWS fire weather alerts are active alerts by point.",
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)

        append_history_snapshot(output)

    print("\n====================")
    print("LIVE AQ UPDATED")
    print("====================")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
