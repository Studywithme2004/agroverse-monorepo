import os
import json
import random
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# -----------------------------------
# ENV
# -----------------------------------
load_dotenv()

# -----------------------------------
# APP
# -----------------------------------
app = FastAPI(title="Agroverse API")

# -----------------------------------
# CORS (FIXED)
# -----------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agroverse.great-site.net",
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# GLOBAL ERROR HANDLER (NO 500)
# -----------------------------------
@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    print("🔥 ERROR:", exc)
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )

# -----------------------------------
# FIREBASE INIT (ENV BASED)
# -----------------------------------
firebase_enabled = False

try:
    import firebase_admin
    from firebase_admin import credentials, db

    firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    firebase_db_url = os.getenv("FIREBASE_DB_URL")

    if not firebase_json or not firebase_db_url:
        raise Exception("Firebase env missing")

    cred = credentials.Certificate(json.loads(firebase_json))

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {
            "databaseURL": firebase_db_url
        })

    firebase_enabled = True
    print("✅ Firebase initialized")

except Exception as e:
    print("⚠️ Firebase disabled:", e)

# -----------------------------------
# MODELS
# -----------------------------------
class ChatRequest(BaseModel):
    message: str

class CropRequest(BaseModel):
    plant: str

# -----------------------------------
# SENSOR SIMULATOR
# -----------------------------------
def simulate_sensor_data():
    return {
        "temperature": round(random.uniform(20, 40), 2),
        "humidity": round(random.uniform(30, 90), 2),
        "moisture": round(random.uniform(10, 80), 2),
        "sunlight": round(random.uniform(200, 900), 2),
    }

# -----------------------------------
# HEALTH
# -----------------------------------
@app.get("/")
@app.get("/health")
def health():
    return {"status": "FastAPI is running"}

# -----------------------------------
# CHAT API (SAFE DEMO)
# -----------------------------------
@app.post("/api/chat")
async def chat(req: ChatRequest):
    sensor = simulate_sensor_data()

    reply = f"""
Based on current conditions:
🌡 Temp: {sensor['temperature']}°C
💧 Moisture: {sensor['moisture']}%

Advice: Maintain regular irrigation and monitor humidity.
"""

    return {
        "success": True,
        "reply": reply.strip(),
        "sensor_data": sensor
    }

# -----------------------------------
# CROP ANALYSIS
# -----------------------------------
@app.post("/api/analyze-crop")
async def analyze_crop(req: CropRequest):
    sensor = simulate_sensor_data()

    disease = "Healthy"
    suggestion = "Continue current care"

    if sensor["moisture"] < 30:
        suggestion = "Increase irrigation"
    if sensor["humidity"] > 85:
        disease = "Possible fungal infection"

    analysis = {
        "plant": req.plant,
        "disease": disease,
        "suggestion": suggestion
    }

    return {
        "success": True,
        "sensor_data": sensor,
        "analysis": analysis
    }

# -----------------------------------
# ESP32 SENSOR UPDATE
# -----------------------------------
@app.post("/api/update-sensor")
async def update_sensor(request: Request):
    data = await request.json()

    if firebase_enabled:
        try:
            db.reference("users/testUser/sensorData").set(data)
        except Exception as e:
            return {"status": "firebase_error", "error": str(e)}

    return {"status": "received", "data": data}

# -----------------------------------
# TEST FIREBASE
# -----------------------------------
@app.get("/test-firebase")
def test_firebase():
    if not firebase_enabled:
        return {"error": "Firebase not enabled"}

    ref = db.reference("users/testUser/sensorData")
    return ref.get() or {"message": "No data found"}

print("✅ Backend fully loaded")
