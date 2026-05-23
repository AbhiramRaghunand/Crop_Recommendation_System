# utils/water_calculator.py

IDEAL_WATER_MM_DAY = {
    "bajra":     {"water_mm_day": 4.5, "notes": "Moderate demand; 350-450 mm total over 90-100 days"},
    "barley":    {"water_mm_day": 4.0, "notes": "Rabi crop; 400-450 mm total over ~100 days"},
    "cotton":    {"water_mm_day": 5.0, "notes": "Moderate-high water crop; 500-700 mm total over 120 days"},
    "groundnut": {"water_mm_day": 3.5, "notes": "Moderate; 350-400 mm total over 110-120 days"},
    "maize":     {"water_mm_day": 5.0, "notes": "Moderate-high; 450-550 mm total over 90-110 days"},
    "milliets":   {"water_mm_day": 4.5, "notes": "Similar to bajra; 350-450 mm total"},
    "oilseeds":  {"water_mm_day": 4.0, "notes": "Varies by crop; 400 mm average"},
    "pigeonpea": {"water_mm_day": 4.5, "notes": "Long duration crop (~150 days); 600-700 mm total"},
    "pulses":    {"water_mm_day": 3.5, "notes": "Low water crop; 300-400 mm total"},
    "rice":      {"water_mm_day": 8.0, "notes": "High water demand; 1100-1300 mm total over 140-150 days"},
    "sorghum":   {"water_mm_day": 5.0, "notes": "Moderate; 450-500 mm total over 90-100 days"},
    "soybean":   {"water_mm_day": 4.0, "notes": "Moderate; 350-450 mm total over 100 days"},
    "sugarcane": {"water_mm_day": 10.0, "notes": "Very high water crop; 2000-2200 mm total over 11-12 months"},
    "tobacco":   {"water_mm_day": 6.0, "notes": "Moderate-high; 500-600 mm total over 100 days"},
    "wheat":     {"water_mm_day": 4.0, "notes": "Moderate; 400-450 mm total over 100-110 days"}
}
def get_daily_water_req(crop_name: str):
    crop = crop_name.lower()
    if crop not in IDEAL_WATER_MM_DAY:
        raise ValueError(f"No daily water data found for '{crop_name}'")
    return IDEAL_WATER_MM_DAY[crop]["water_mm_day"]