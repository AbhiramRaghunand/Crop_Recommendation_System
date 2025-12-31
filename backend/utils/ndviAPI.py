"""
agro_data_service.py
------------------------------------
Creates a farm polygon using (lat, lon, area in acres),
registers it with OpenWeather Agro API,
and retrieves NDVI + soil moisture data.
"""

import math
import time
import requests
import pyproj
from shapely.geometry import Point, Polygon
from shapely.ops import transform
import os
import json
from dotenv import load_dotenv

# ============================================================
# CONFIGURATION
# ============================================================
load_dotenv()
API_KEY = os.getenv("AGROMONITORING_API_KEY")  # <-- replace with your real Agro API key
BASE_URL = "http://api.agromonitoring.com/agro/1.0"

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_polygon(lat: float, lon: float, area_acres: float):
    """
    Create a simple axis-aligned square polygon around (lat, lon).
    AgroMonitoring prefers simple non-rotated polygons.
    """
    area_m2 = area_acres * 4046.86
    side_m = math.sqrt(area_m2)

    # Convert meters to lat/lon degrees (approx)
    lat_offset = (side_m / 111320) / 2  # 1 deg lat = 111.32 km
    lon_offset = (side_m / (111320 * math.cos(math.radians(lat)))) / 2

    polygon = [
        [lon - lon_offset, lat - lat_offset],
        [lon + lon_offset, lat - lat_offset],
        [lon + lon_offset, lat + lat_offset],
        [lon - lon_offset, lat + lat_offset],
        [lon - lon_offset, lat - lat_offset]
    ]

    # Round to safe precision
    return [[round(lon, 6), round(lat, 6)] for lon, lat in polygon]


# ============================================================
# AGRO API FUNCTIONS
# ============================================================

def register_field(lat: float, lon: float, area_acres: float, name="Farm_Field"):
    """Registers a farm polygon and returns its polygon ID."""
    polygon = create_polygon(lat, lon, area_acres)
    payload = {
        "name": name,
        "geo_json": {
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "Polygon", "coordinates": [polygon]}
        }
    }
    # print("DEBUG JSON SENT TO AGRO:",json.dumps(payload,indent=2))
    url = f"{BASE_URL}/polygons?appid={API_KEY}&duplicated=true"
    res = requests.post(url, json=payload)
    if res.status_code != 200 and res.status_code != 201:
        print("AGRO ERROR RESPONSE:", res.text)
    res.raise_for_status()
    return res.json()["id"]

def get_ndvi(polygon_id: str, days: int = 30):
    """Fetch NDVI data for a given polygon and time range."""
    end = int(time.time())
    end=end-24*3600
    start = end - (days * 24 * 3600)

    url = f"{BASE_URL}/ndvi/history?start={start}&end={end}&polyid={polygon_id}&appid={API_KEY}"
    res = requests.get(url)
    if res.status_code==404:
        return []
    res.raise_for_status()
    data = res.json()

    ndvi_list = []
    for entry in data:
        date = time.strftime("%Y-%m-%d", time.gmtime(entry["dt"]))
        ndvi = entry["data"].get("max")
        ndvi_list.append({"date": date, "ndvi": ndvi})

    return ndvi_list

def get_soil(polygon_id: str):
    """Fetch soil moisture and temperature for the given polygon."""
    url = f"{BASE_URL}/soil?polyid={polygon_id}&appid={API_KEY}"
    res = requests.get(url)
    res.raise_for_status()
    data = res.json()
    return {
        "moisture": data.get("moisture"),
        "temperature": data.get("t0"),
        "timestamp": time.strftime("%Y-%m-%d %H:%M", time.gmtime(data["dt"]))
    }

# ============================================================
# MAIN FUNCTION
# ============================================================

def get_farm_data(lat: float, lon: float, area_acres: float, name="My_Farm",existing_polygon_id=None):
    """
    Creates polygon, registers it, and retrieves NDVI + soil moisture.
    """
    # print("farmer.polygon_id BEFORE:", repr(existing_polygon_id))

    if existing_polygon_id:
        polygon_id = existing_polygon_id
    else:
        polygon_id = register_field(lat, lon, area_acres, name)
    if not polygon_id:
        raise Exception("Could not create or retrieve polygon from Agro API.")
    
    ndvi_data = get_ndvi(polygon_id)
    latest_ndvi = ndvi_data[-1]["ndvi"] if ndvi_data else None
    soil_data = get_soil(polygon_id)


    return {
        "polygon_id": polygon_id,
        "latest_ndvi": latest_ndvi,
        "ndvi_history": ndvi_data,
        "soil": soil_data
    }

# ============================================================
# TEST RUN (for standalone testing)
# ============================================================

# if __name__ == "__main__":
#     # Example: Bengaluru region, 3.5 acres
#     result = get_farm_data(12.9716, 77.5946, 3.5, "Abhiram_Farm")
#     print(result)
