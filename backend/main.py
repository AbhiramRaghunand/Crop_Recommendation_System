from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes import recommend, recommendation_history, crop_suitability, suitability_history
from dotenv import load_dotenv
# from routes.recommend import start_scheduler
from routes.recommend import start_scheduler
import os
load_dotenv()
# print("DEBUG ENV KEY:", os.getenv("FAST2SMS_API_KEY"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler(daily_hour_interval=24)
    print("⏳ Background Schedulers Activated")
    
    yield  # App is running

    # Shutdown (optional)
    print("🛑 Shutting down CropWise API...")
# from models.model_loader import StageModel
app=FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # or specify your frontend URL e.g. ["http://localhost:5173"]
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*","Authorization","Content-Type"]
)

app.include_router(recommend.router)
app.include_router(recommendation_history.router)
app.include_router(crop_suitability.router)
app.include_router(suitability_history.router)


@app.get("/")
def root():
    return {"message":"CropWise is running "}