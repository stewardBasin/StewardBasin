import os
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# CONFIG
# =========================

API_KEY = os.getenv("AIRNOW_API_KEY", "B422C1EB-F856-430D-81AB-C0834D831F39")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

LIVE_AQ_FILE = os.path.join(DATA_DIR, "live_air_quality.json")
HISTORY_FILE = os.path.join(DATA_DIR, "live_air_quality_history.json")
CHPC_FILE = os.path.join(DATA_DIR, "chpc_live_air_quality.json")

os.makedirs(DATA_DIR, exist_ok=True)

AIRNOW_URL = "https://www.airnowapi.org/aq/observation/latLong/current/"
CHPC_UT_URL = "https://utahaq.chpc.utah.edu/jsondata/FixedSiteMapData.json"
NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"

NWS_HEADERS = {
    "User-Agent": "StewardBasin/1.0 ruthjanegibson@gmail.com",
    "Accept": "application/geo+json",
}
UTAH_TZ = ZoneInfo("America/Denver")


def utah_now():
    return datetime.now(UTAH_TZ)


MONITOR_POINTS = [
    {"name": "Fruitland", "lat": 40.2144, "lng": -110.8413, "distance": 35},
    {"name": "Duchesne", "lat": 40.1633, "lng": -110.4029, "distance": 35},
    {"name": "Roosevelt", "lat": 40.2994, "lng": -109.9887, "distance": 35},
    {"name": "Fort Duchesne", "lat": 40.2889, "lng": -109.8618, "distance": 35},
    {"name": "Vernal", "lat": 40.4555, "lng": -109.5287, "distance": 35},
    {"name": "Horsepool", "lat": 40.143, "lng": -109.468, "distance": 35},
    {"name": "South Ouray", "lat": 40.0894, "lng": -109.6812, "distance": 35},
]

CHPC_STATIONS = [
    {
        "station_code": "QRS",
        "name": "Roosevelt",
        "display_name": "Roosevelt AQ Monitor",
        "station_key": "Roosevelt",
        "region": "Duchesne County",
        "confidence": "verified_coordinate_match",
        "notes": "Coordinates match Roosevelt AQ monitor area.",
    },
    {
        "station_code": "QV4",
        "name": "Vernal",
        "display_name": "Vernal #4 AQ Monitor",
        "station_key": "Vernal",
        "region": "Uintah County",
        "confidence": "verified_coordinate_match",
        "notes": "Coordinates match Vernal #4 monitor area.",
    },
    {
        "station_code": "A1388",
        "name": "Duchesne / Myton / Fruitland",
        "display_name": "Duchesne / Myton / Fruitland Area Ozone Monitor",
        "station_key": "Duchesne",
        "region": "Duchesne County",
        "confidence": "likely_coordinate_match",
        "notes": "Coordinates place this monitor in the Duchesne/Myton corridor.",
    },
    {
        "station_code": "A1622",
        "name": "South Ouray",
        "display_name": "South Ouray / Ouray Wildlife Refuge Ozone Monitor",
        "station_key": "South Ouray",
        "region": "Uintah County",
        "confidence": "verified_coordinate_match",
        "notes": "Coordinates place this monitor near South Ouray / Ouray National Wildlife Refuge.",
    },
    {
        "station_code": "A1386",
        "name": "North Uintah Basin / Whiterocks",
        "display_name": "North Uintah Basin / Whiterocks Area Ozone Monitor",
        "station_key": "North Uintah Basin",
        "region": "Uintah County",
        "confidence": "likely_coordinate_match",
        "notes": "Coordinates place this monitor north of Fort Duchesne / Whiterocks area.",
    },
    {
        "station_code": "A1633",
        "name": "Uintah Basin East / Horsepool Candidate",
        "display_name": "Uintah Basin East Research Candidate",
        "station_key": "Uintah Basin East",
        "region": "Uintah County",
        "confidence": "needs_verification",
        "notes": "Possible eastern Uintah Basin research site related to Horsepool / Red Wash area.",
    },
]

LAST_VALID_CHPC_FALLBACKS = {
    "A1622": {
        "value": "45.00",
        "unit": "ppbv",
        "timeLocal": "2026-05-30 13:00:00 MDT",
        "timeUTC": "2026-05-30 19:00:00 UTC",
        "lat": "40.05485",
        "lng": "-109.68737",
        "color": "#006600",
        "source_pollutant_key": "OZNE",
    },
    "A1633": {
        "value": "55.00",
        "unit": "ppbv",
        "timeLocal": "2026-05-30 13:00:00 MDT",
        "timeUTC": "2026-05-30 19:00:00 UTC",
        "lat": "40.20443",
        "lng": "-109.35321",
        "color": "#FFFF00",
        "source_pollutant_key": "OZNE",
    },
}

# =========================
# AIRNOW + NWS
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
    try:
        response = requests.get(
            NWS_ALERTS_URL,
            params={"point": f'{point["lat"]},{point["lng"]}'},
            headers=NWS_HEADERS,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        fire_alerts = []

        for alert in data.get("features", []):
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


# =========================
# CHPC
# =========================


def fetch_chpc_data():
    response = requests.get(CHPC_UT_URL, timeout=30)
    response.raise_for_status()
    return response.json()


def simplify_chpc_pollutant(raw_chpc, pollutant_key, station_code):
    pollutant_group = raw_chpc.get(pollutant_key, {})
    record = pollutant_group.get(station_code)

    if not record:
        return None

    return {
        "value": record.get("Value"),
        "unit": pollutant_group.get("VarUnit", ""),
        "timeLocal": record.get("TimeLocal"),
        "timeUTC": record.get("TimeUTC"),
        "lat": record.get("Latitude"),
        "lng": record.get("Longitude"),
        "color": record.get("ValueColor"),
        "source_pollutant_key": pollutant_key,
    }


def build_chpc_station(raw_chpc, station_meta, updated):
    code = station_meta["station_code"]

    pm25 = simplify_chpc_pollutant(raw_chpc, "PM25", code)
    pm10 = simplify_chpc_pollutant(raw_chpc, "PM10", code)
    ozone = simplify_chpc_pollutant(raw_chpc, "OZNE", code)

    best_location = ozone or pm25 or pm10

    return {
        **station_meta,
        "source": "Utah CHPC FixedSiteMapData",
        "source_url": CHPC_UT_URL,
        "updated": updated,
        "pm25": pm25,
        "pm10": pm10,
        "ozone": ozone,
        "lat": best_location.get("lat") if best_location else None,
        "lng": best_location.get("lng") if best_location else None,
    }


def load_previous_chpc():
    if not os.path.exists(CHPC_FILE):
        return {}

    try:
        with open(CHPC_FILE, "r", encoding="utf-8") as file:
            previous_data = json.load(file)

        return {
            station["station_code"]: station
            for station in previous_data.get("stations", [])
            if station.get("station_code")
        }

    except Exception:
        return {}


def apply_chpc_fallbacks(station, previous_station):
    code = station["station_code"]

    if station.get("ozone") is not None:
        station["data_status"] = "current"
        return station

    if previous_station.get("ozone"):
        station["ozone"] = previous_station["ozone"]
        station["lat"] = previous_station.get("lat")
        station["lng"] = previous_station.get("lng")
        station["data_status"] = "using_last_available_chpc_reading"
        return station

    if code in LAST_VALID_CHPC_FALLBACKS:
        fallback = LAST_VALID_CHPC_FALLBACKS[code]
        station["ozone"] = fallback
        station["lat"] = fallback.get("lat")
        station["lng"] = fallback.get("lng")
        station["data_status"] = "using_verified_fallback_chpc_reading"
        return station

    station["data_status"] = "no_current_chpc_reading"
    return station


def update_chpc_live_file():
    try:
        raw_chpc = fetch_chpc_data()

        updated = (
            raw_chpc.get("OZNE", {}).get("LastUpdateLocal")
            or raw_chpc.get("PM25", {}).get("LastUpdateLocal")
            or utah_now().strftime("%Y-%m-%d %I:%M %p MDT")
        )

        previous_chpc = load_previous_chpc()
        stations = []

        for station_meta in CHPC_STATIONS:
            station = build_chpc_station(raw_chpc, station_meta, updated)
            previous_station = previous_chpc.get(station["station_code"], {})
            station = apply_chpc_fallbacks(station, previous_station)
            stations.append(station)

        output = {
            "updated": updated,
            "source": CHPC_UT_URL,
            "stations": stations,
            "note": "CHPC values are pollutant concentrations, not AirNow AQI values. Station labels are based on coordinate matching and should retain confidence notes.",
        }

        with open(CHPC_FILE, "w", encoding="utf-8") as file:
            json.dump(output, file, indent=2)

        print("\n====================")
        print("CHPC LIVE AQ UPDATED")
        print("====================")
        print(f"Saved: {CHPC_FILE}")

        return output

    except Exception as e:
        print(f"CHPC unavailable: {e}")
        return None


# =========================
# HISTORY
# =========================


def append_history_snapshot(output):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            try:
                history = json.load(file)
            except json.JSONDecodeError:
                history = []
    else:
        history = []

    history.append(
        {
            "timestamp": utah_now().isoformat(),
            "updated": output.get("updated"),
            "aqi": output.get("aqi"),
            "ozone": output.get("ozone"),
            "pm25": output.get("pm25"),
            "pm10": output.get("pm10"),
            "fireRisk": output.get("fireRisk"),
            "stations": output.get("stations", []),
        }
    )

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
            stations.append(simplify_airnow_records(point, records))

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

        all_fire_alerts.extend(fetch_nws_fire_risk(point))

    valid_aqi_values = [
        station["aqi"] for station in stations if isinstance(station.get("aqi"), int)
    ]

    highest_aqi = max(valid_aqi_values) if valid_aqi_values else "--"

    highest_station = next(
        (station for station in stations if station.get("aqi") == highest_aqi),
        stations[0] if stations else {},
    )

    fire_risk = (
        all_fire_alerts[0]["event"]
        if all_fire_alerts
        else "No active NWS fire weather alert"
    )

    output = {
        "aqi": highest_aqi,
        "ozone": highest_station.get("ozone", "--") if highest_station else "--",
        "pm25": highest_station.get("pm25", "--") if highest_station else "--",
        "pm10": highest_station.get("pm10", "--") if highest_station else "--",
        "fireRisk": fire_risk,
        "fireAlerts": all_fire_alerts,
        "updated": utah_now().strftime("%Y-%m-%d %I:%M %p MDT"),
        "source": "AirNow API + NWS API",
        "location": "Eastern Utah / Uinta Basin monitor points",
        "stations": stations,
        "note": "AirNow values are live AQI observations near selected Eastern Utah points. NWS fire weather alerts are active alerts by point.",
    }

    with open(LIVE_AQ_FILE, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)

    append_history_snapshot(output)
    update_chpc_live_file()

    print("\n====================")
    print("LIVE AQ UPDATED")
    print("====================")
    print(f"Saved: {LIVE_AQ_FILE}")


if __name__ == "__main__":
    main()
