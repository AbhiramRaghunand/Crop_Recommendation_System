from unittest import result
from fastapi import FastAPI,APIRouter,Depends,HTTPException,Header
import numpy as np
import json
import requests
from datetime import date
from schemas.cropInput import cropInput
from utils.weatherAPI import get_weather
from utils.ndviAPI import get_farm_data
from utils.nutrientCalci import calculate_nutrient_needs
from utils.waterRequirnment import get_daily_water_req
from utils.textRec import generate_recommendations
from sqlalchemy.orm import Session
from database.database import get_db
from database.farmer import Farmer
from database.fields import Field
from database.model_input import ModelInput
from database.model_output import ModelOutput
from database.recommendations import Recommendation
from utils.auth import get_current_farmer
from utils.fertilizer_recommender import recommend_fertilizer
from utils.prepare_model_input import prepare_model_input
from utils.prepare_model_output import prepare_model_output
from utils.text_parser import parse_recommendations
import joblib
from typing import Optional,Dict, Any
from sqlalchemy import desc
import traceback
from datetime import timedelta
import os

# from models.model_utils import predict_crop
encoder = joblib.load("models/pkl/encoders.pkl")
modelA=joblib.load("models/pkl/crop_stage_model.pkl")
modelB1=joblib.load("models/pkl/fertilizer_type_model.pkl")
modelB2=joblib.load("models/pkl/fertilizer_quantity_model.pkl")
modelC=joblib.load("models/pkl/irrigation_model.pkl")
modelD=joblib.load("models/pkl/yeild_model.pkl")

router=APIRouter()

def safe_get_last_model_input(db: Session, field_id: int) -> Optional[ModelInput]:
    """
    Return last ModelInput row for field_id or None.
    """
    try:
        return db.query(ModelInput).filter(ModelInput.field_id == field_id).order_by(desc(ModelInput.id)).first()
    except Exception:
        return None
    
def reconstruct_crop_input_from_modelinput(db_input: Optional[ModelInput], field: Field, farmer: Farmer) -> cropInput:
    """
    Try to reconstruct a cropInput object from last ModelInput snapshot.
    If not possible, fallback to using Field + Farmer info with sensible defaults.
    """
    # We'll attempt to find sensible keys in db_input.input_snap
    # NOTE: prepare_model_input may have stored a feature dict; we try to read original-like keys if present.
    try:
        if db_input and db_input.input_snap:
            snap = db_input.input_snap  # assume JSON/dict
            # Try common keys (these depend on your prepare_model_input implementation)
            crop = snap.get("Crop") or snap.get("crop") or field.crop or ""
            sowing_date = snap.get("sowing_date") or snap.get("Sowing_Date") or getattr(field, "sowing_date", None)
            n = snap.get("Nitrogen") or snap.get("Soil_N") or 0
            p = snap.get("Phosphorous") or snap.get("Soil_P") or 0
            k = snap.get("Potassium") or snap.get("Soil_K") or 0

        
            sowing_date = date.today() - timedelta(days=snap.get("days_since_sowing", 0))

            # Build a cropInput Pydantic model — if your cropInput expects different names, adapt these keys.
            return cropInput(
                crop=crop,
                n=n,
                p=p,
                k=k,
                sowing_date=date.today()
            )
    except Exception:
        # ignore and fallback
        traceback.print_exc()

    # Fallback
    return cropInput(
        crop=(field.crop or ""),
        n=0,
        p=0,
        k=0,
        sowing_date=getattr(field, "sowing_date", date.today())
    )



import os
import json
import requests


def format_phone(number: str) -> str:
    number = str(number).strip()

    if number.startswith("+91"):
        number = number[3:]
    elif number.startswith("+"):
        number = number[1:]

    if number.startswith("0"):
        number = number[1:]

    if len(number) != 10 or not number.isdigit():
        raise ValueError(f"Invalid phone number: {number}")

    return number


def send_sms_fast2sms(phone: str, message: str) -> bool:
    api_key = os.getenv("FAST2SMS_API_KEY")
    if not api_key:
        print("FAST2SMS_API_KEY missing!")
        return False

    url = "https://www.fast2sms.com/dev/bulkV2"

    payload = {
        "sender_id": "TXTIND",
        "message": message,
        "language": "english",
        "route": "q",              # 🔥 THIS IS THE CORRECT ONE FOR BULKV2
        "numbers": format_phone(phone)
    }

    headers = {
        "authorization": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

        print("Fast2SMS HTTP Status:", response.status_code)
        print("RAW RESPONSE:", response.text)  # 🔥 Extremely important

        # If no JSON returned → treat as failure
        try:
            data = response.json()
        except:
            print("Fast2SMS returned NON-JSON response.")
            return False

        # Successful message looks like:
        # {"return": true, "request_id": "...", "message": ["SMS sent successfully."]}
        return data.get("return") is True

    except Exception as e:
        print("SMS send failed:", str(e))
        return False



def predict_stage_from_modelA(ndvi: Dict[str, Any], weather: Dict[str, Any], days_since_sowing: int, crop_encoded: int) -> str:
    """
    Runs modelA.predict and returns the stage string.
    Assumes modelA.predict returns an array-like of strings or ints mapped to strings.
    """
    try:
        x = [[ndvi["latest_ndvi"], weather.get("humidity", 0), days_since_sowing, crop_encoded]]
        pred = modelA.predict(x)
        # pred[0] may be bytes/np.str_ etc.
        return str(pred[0])
    except Exception:
        traceback.print_exc()
        return "unknown"

def weather_changed(current: Dict[str, Any], previous: Optional[Dict[str, Any]]) -> bool:
    """
    Determine whether weather has changed meaningfully.
    previous may be None.
    """
    if not previous:
        return True
    try:
        # tolerant access
        cur_temp = float(current.get("temp", 0))
        prev_temp = float(previous.get("temp", 0))
        if abs(cur_temp - prev_temp) > 3:
            return True

        cur_hum = float(current.get("humidity", 0))
        prev_hum = float(previous.get("humidity", 0))
        if abs(cur_hum - prev_hum) > 15:
            return True

        cur_rain = float(current.get("rainfall", 0))
        prev_rain = float(previous.get("rainfall", 0))
        if abs(cur_rain - prev_rain) > 10:
            return True

    except Exception:
        # on any parsing error, treat as changed to be safe
        return True

    return False


# --- Reusable internal generation ------------------------------------------------

def generate_recommendation_internal(db: Session, farmer: Farmer, field: Field, data: cropInput) -> Dict[str, Any]:
    """
    Core logic extracted from your endpoint — runs the models, writes ModelInput/ModelOutput/Recommendation
    Returns a dict with keys: recommendation_text, parsed (dict), model_output, model_input_id, model_output_id
    """
    try:
        # update field crop if provided
        if data.crop:
            field.crop = data.crop
            db.add(field)
            db.flush()

        lat, lon, area = field.latitude, field.longitude, field.area
        soil_type = field.soil_type
        lang = farmer.language

        # get weather and ndvi
        weather = get_weather(lat, lon)

        invalid_polygon = (
            farmer.polygon_id is None or
            str(farmer.polygon_id).strip() == "" or
            str(farmer.polygon_id).strip().upper() == "NULL"
        )
        ndvi = get_farm_data(lat, lon, area, farmer.name, existing_polygon_id=None if invalid_polygon else farmer.polygon_id)

        # if polygon id was missing, update farmer
        if (not farmer.polygon_id) or str(farmer.polygon_id).strip() == "":
            try:
                farmer.polygon_id = ndvi.get("polygon_id")
                db.add(farmer)
                db.flush()
            except Exception:
                pass

        # water requirement
        waterReq = get_daily_water_req(data.crop)
        today = date.today()
        days_since_sowing = (today - data.sowing_date).days if data.sowing_date else 0

        # encode crop and soil
        crop_encoder = encoder["Crop"]
        crop_name = (data.crop or "").strip().lower()
        encoder_map = {cls.lower(): i for i, cls in enumerate(crop_encoder.classes_)}
        crop_encoded = encoder_map.get(crop_name, -1)

        soil_encoder = encoder["Soil_Type"]
        soil_name = (soil_type or "").strip().lower()
        soil_map = {cls.lower(): i for i, cls in enumerate(soil_encoder.classes_)}
        # NOTE: your original code had a bug using encoder_map twice. Fixing:
        soil_encoded = soil_map.get(soil_name, -1)

        # prepare model input (your existing helper)
        model_input = prepare_model_input(data, crop_encoded, soil_encoded, days_since_sowing, weather, ndvi, waterReq)

        # store ModelInput
        db_input = ModelInput(field_id=field.id, input_snap=model_input)
        db.add(db_input)
        db.flush()
        db.refresh(db_input)
        model_input_id = db_input.id

        # stage via modelA
        user_input_stage = {
            "latest_ndvi": ndvi.get("latest_ndvi", 0),
            "humidity": weather.get("humidity", 0),
            "days_since_sowing": days_since_sowing,
            "crop_encoded": crop_encoded
        }
        stage = predict_stage_from_modelA(ndvi, weather, days_since_sowing, crop_encoded)

        # fertilizer recommendation (your helper)
        user_input = {
            "Temperature": weather.get("temp"),
            "Humidity": weather.get("humidity"),
            "Moisture": ndvi.get("soil", {}).get("moisture"),
            "Soil_Type": soil_type,
            "Crop": data.crop,
            "Nitrogen": data.n,
            "Phosphorous": data.p,
            "Potassium": data.k
        }
        fertilizer = recommend_fertilizer(user_input)

        # irrigation
        user_input_irrigation = {
            "crop_encoded": crop_encoded,
            "moisture": ndvi.get("soil", {}).get("moisture"),
            "rainfall": weather.get("rainfall"),
            "latest_ndvi": ndvi.get("latest_ndvi"),
            "waterReq": waterReq
        }
        irrigation = modelC.predict([[user_input_irrigation["crop_encoded"], user_input_irrigation["moisture"], user_input_irrigation["rainfall"], user_input_irrigation["latest_ndvi"], user_input_irrigation["waterReq"]]])

        # yield
        user_input_yield = {
            "temp": weather.get("temp"),
            "rainfall": weather.get("rainfall"),
            "moisture": ndvi.get("soil", {}).get("moisture"),
            "soil_encoded": soil_encoded,
            "crop_encoded": crop_encoded,
            "stage": stage,
            "latest_ndvi": ndvi.get("latest_ndvi")
        }
        yield_pred = modelD.predict([[user_input_yield["temp"], user_input_yield["rainfall"], user_input_yield["moisture"], user_input_yield["soil_encoded"], user_input_yield["crop_encoded"], user_input_yield["stage"], user_input_yield["latest_ndvi"]]])

        preds = {
            "crop_stage": str(stage),
            "fertilizer": fertilizer,
            "irrigation": float(irrigation[0]),
            "yield": float(yield_pred[0])
        }

        model_output = prepare_model_output(preds)
        db_output = ModelOutput(
            field_id=field.id,
            model_input_id=model_input_id,
            predicted_yield=model_output.get("yield"),
            irrigation=model_output.get("irrigation"),
            required_n=model_output.get("required_n"),
            required_p=model_output.get("required_p"),
            required_k=model_output.get("required_k"),
            crop_stage=model_output.get("crop_stage")
        )
        db.add(db_output)
        db.flush()
        db.refresh(db_output)
        model_output_id = db_output.id

        output = generate_recommendations(preds, data.crop, lang)
        parsed_output = parse_recommendations(output)
        fert = parsed_output.get("fertilizer", {}) or {}
        irr = parsed_output.get("irrigation", {}) or {}
        weather_warning = parsed_output.get("weather_warning")

        db_recommendation = Recommendation(
            field_id=field.id,
            model_output_id=model_output_id,
            recommendation_text=output
        )
        db.add(db_recommendation)
        db.flush()
        db.refresh(db_recommendation)

        # commit only at the top-level caller
        return {
            "recommendation_text": output,
            "parsed": parsed_output,
            "model_input_id": model_input_id,
            "model_output_id": model_output_id,
            "stage": stage,
            "ndvi": ndvi,
            "weather": weather
        }

    except Exception as e:
        print("🔴 generate_recommendation_internal error:", str(e))
        traceback.print_exc()
        raise

@router.post("/recommend")
def recommendations(data: cropInput, db: Session = Depends(get_db), authorization: str = Header(default=None), user=Depends(get_current_farmer)):
    """
    Existing endpoint — now uses generate_recommendation_internal and commits at end.
    """
    try:
        farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()
        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found")
        
        field = db.query(Field).filter(Field.farmer_id == farmer.id).first()
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")

        # Call the internal generator (it will update DB rows for model inputs/outputs/recommendations)
        result = generate_recommendation_internal(db, farmer, field, data)
        # print("DEBUG: Recommendation generated successfully.")
    except Exception as e:
        print("🔥 BACKEND ERROR:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        # send SMS immediately (if configured)
    # try:
    #     # print("DEBUG: Checking if SMS send is needed.")
    #     # print("DEBUG farmer object repr:", repr(farmer))
    #     # print("DEBUG farmer.phone raw:", getattr(farmer, "phone", None))
    #     # print("DEBUG type:", type(getattr(farmer, "phone", None)))

    #     if getattr(farmer, "phone", None):
    #         print("DEBUG FARMER PHONE =", farmer.phone)
    #         # print("DEBUG RESULT =", result)
    #         print("DEBUG ENTERING SMS BLOCK NOW")

    #         sms_text = result["recommendation_text"]
    #         send_sms_fast2sms(farmer.phone, sms_text)
    #         print("Sending sms to", farmer.phone)
    #         # update last_stage & last_weather to avoid immediate duplicate from scheduler
    #         field.last_stage = result.get("stage")
    #         field.last_weather = json.dumps(result.get("weather", {}))
    #         db.add(field)
    # except Exception as e:
    #     print("SMS send failed:", e)

        # final commit and return
    # print("DEBUG: Committing DB changes now.")
    db.commit()
    return {"recommendations": result["recommendation_text"]}

    


# --- Automation wrapper to be called by scheduler ---------------------------

# Try to import a SessionLocal for manual DB sessions (scheduler usage).
# If your project exposes SessionLocal in database.database, it will be used.
try:
    from database.database import SessionLocal
except Exception:
    SessionLocal = None
    # we will use get_db generator fallback below

def _get_manual_db_session():
    """
    Return a DB Session usable in non-FastAPI contexts.
    Tries SessionLocal first, otherwise uses next(get_db()) generator.
    """
    if SessionLocal:
        return SessionLocal()
    else:
        # get_db is a generator that yields a session; calling next() will give a session
        gen = get_db()
        session = next(gen)
        return session
    
def run_automated_recommendation_for_all_fields(send_sms: bool = True):
    """
    Loop through all fields, detect stage & weather change using Model A and last stored weather,
    and call generate_recommendation_internal when needed.
    This function is safe to call from an APScheduler job.
    """
    db = _get_manual_db_session()
    try:
        # load all fields
        fields = db.query(Field).all()
        for field in fields:
            try:
                farmer = db.query(Farmer).filter(Farmer.id == field.farmer_id).first()
                if not farmer:
                    print(f"[automate] farmer not found for field {field.id}")
                    continue

                # reconstruct input from last ModelInput if present (option A)
                last_input = safe_get_last_model_input(db, field.id)
                data_for_run = reconstruct_crop_input_from_modelinput(last_input, field, farmer)

                # Get current weather & NDVI
                lat, lon, area = field.latitude, field.longitude, field.area
                weather = get_weather(lat, lon)
                invalid_polygon = (
                    farmer.polygon_id is None or
                    str(farmer.polygon_id).strip() == "" or
                    str(farmer.polygon_id).strip().upper() == "NULL"
                )
                ndvi = get_farm_data(lat, lon, area, farmer.name, existing_polygon_id=None if invalid_polygon else farmer.polygon_id)

                # compute days since sowing and crop_encoded like in your endpoint
                today = date.today()
                days_since_sowing = (today - data_for_run.sowing_date).days if data_for_run.sowing_date else 0
                crop_encoder = encoder["Crop"]
                crop_name = (data_for_run.crop or "").strip().lower()
                encoder_map = {cls.lower(): i for i, cls in enumerate(crop_encoder.classes_)}
                crop_encoded = encoder_map.get(crop_name, -1)

                # Predict stage via Model A
                predicted_stage = predict_stage_from_modelA(ndvi, weather, days_since_sowing, crop_encoded)

                # Load last stored stage & last weather from Field; expects last_stage and last_weather fields on Field
                last_stage = getattr(field, "last_stage", None)
                last_weather = getattr(field, "last_weather", None)
                # if last_weather stored as JSON string, parse it
                if isinstance(last_weather, str):
                    try:
                        last_weather = json.loads(last_weather)
                    except Exception:
                        last_weather = None

                # Decide if update required
                stage_changed = (predicted_stage != last_stage)
                weather_changed_flag = weather_changed(weather, last_weather)

                if stage_changed or weather_changed_flag:
                    print(f"[automate] Field {field.id} triggered (stage_changed={stage_changed}, weather_changed={weather_changed_flag})")

                    # run the same recommendation flow
                    result = generate_recommendation_internal(db, farmer, field, data_for_run)

                    # send SMS (if farmer.phone exists)
                    try:
                        sms_text = result["recommendation_text"]
                        if send_sms and getattr(farmer, "phone", None):
                            send_sms_fast2sms(farmer.phone, sms_text)
                            print(f"[automate] SMS sent to Farmer: {farmer.id}, phone: {farmer.phone}")
                        else:
                            print(f"[automate] SMS disabled or phone missing. Farmer: {farmer.id}, phone: {getattr(farmer, 'phone', None)}")
                    except Exception:
                        traceback.print_exc()

                    # update field last_stage and last_weather
                    try:
                        field.last_stage = predicted_stage
                        # store last_weather as JSON string or JSON field if supported
                        field.last_weather = json.dumps(weather)
                        db.add(field)
                    except Exception:
                        traceback.print_exc()

                    # commit after each update to ensure state is saved
                    db.commit()
                else:
                    print(f"[automate] Field {field.id} - no significant changes (stage: {predicted_stage}).")
            except Exception as fe:
                print(f"[automate] error processing field {field.id}: {fe}")
                traceback.print_exc()
                # continue with next field
        # end for
    finally:
        try:
            db.close()
        except Exception:
            pass


# --- Small scheduler helper (optional) -------------------------------------

def start_scheduler(daily_hour_interval: int = 24):
    """
    Optional helper to start APScheduler job to call run_automated_recommendation_for_all_fields.
    Call start_scheduler() from your main.py on app startup.
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except Exception:
        print("APScheduler not installed. Install with `pip install apscheduler` to use scheduling.")
        return

    scheduler = BackgroundScheduler()
    # schedule at interval of hours
    scheduler.add_job(lambda: run_automated_recommendation_for_all_fields(send_sms=True), "interval", hours=daily_hour_interval)
    scheduler.start()
    print("[scheduler] started - interval hours =", daily_hour_interval)

# ---------------------------------------------------------------------------
# End of file