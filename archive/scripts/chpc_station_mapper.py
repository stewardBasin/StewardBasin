import os
import json
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

CHPC_URL = "https://utahaq.chpc.utah.edu/jsondata/FixedSiteMapData.json"
OUTPUT_FILE = os.path.join(DATA_DIR, "chpc_live_air_quality.json")

os.makedirs(DATA_DIR, exist_ok=True)

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
        "notes": "Coordinates place this monitor in the Duchesne/Myton corridor. Use as a regional proxy for Duchesne, Myton, and Fruitland until a separate Fruitland feed is identified.",
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
        "notes": "Coordinates place this monitor north of Fort Duchesne, closer to the north Uintah Basin / Whiterocks area. Do not label as Fort Duchesne.",
    },
    {
        "station_code": "A1633",
        "name": "Uintah Basin East / Horsepool Candidate",
        "display_name": "Uintah Basin East Research Candidate",
        "station_key": "Uintah Basin East",
        "region": "Uintah County",
        "confidence": "needs_verification",
        "notes": "Possible eastern Uintah Basin research site. Could be related to Horsepool/Redwash-area research monitoring, but not verified yet.",
    },
]

POLLUTANTS = {
    "PM25": "pm25",
    "PM10": "pm10",
    "OZNE": "ozone",
}


def fetch_chpc():
    response = requests.get(CHPC_URL, timeout=30)
    response.raise_for_status()
    return response.json()


def get_station_value(chpc_data, station_code, pollutant_key):
    pollutant_data = chpc_data.get(pollutant_key, {})
    station = pollutant_data.get(station_code)

    if not station:
        return None

    return {
        "value": station.get("Value"),
        "unit": pollutant_data.get("VarUnit"),
        "timeLocal": station.get("TimeLocal"),
        "timeUTC": station.get("TimeUTC"),
        "lat": station.get("Latitude"),
        "lng": station.get("Longitude"),
        "color": station.get("ValueColor"),
        "source_pollutant_key": pollutant_key,
    }


def main():
    chpc_data = fetch_chpc()
    stations = []

    for site in CHPC_STATIONS:
        station_code = site["station_code"]

        station_record = {
            "station_code": station_code,
            "name": site["name"],
            "display_name": site["display_name"],
            "station_key": site["station_key"],
            "region": site["region"],
            "confidence": site["confidence"],
            "notes": site["notes"],
            "source": "Utah CHPC FixedSiteMapData",
            "source_url": CHPC_URL,
            "updated": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            "pm25": None,
            "pm10": None,
            "ozone": None,
            "lat": None,
            "lng": None,
        }

        for chpc_key, clean_key in POLLUTANTS.items():
            reading = get_station_value(chpc_data, station_code, chpc_key)

            if reading:
                station_record[clean_key] = reading

                if not station_record["lat"]:
                    station_record["lat"] = reading.get("lat")
                    station_record["lng"] = reading.get("lng")

        stations.append(station_record)

    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "source": CHPC_URL,
        "stations": stations,
        "note": "CHPC values are pollutant concentrations, not AirNow AQI values. Station labels are based on coordinate matching and should retain confidence notes.",
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)

    print("\n====================")
    print("CHPC LIVE AQ UPDATED")
    print("====================")
    print(f"Saved: {OUTPUT_FILE}")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()