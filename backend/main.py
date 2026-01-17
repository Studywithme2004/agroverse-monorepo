import os
import json
import random
import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Load ENV ----------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
FIREBASE_KEY_JSON = os.getenv("FIREBASE_KEY_JSON")

if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY is missing")

# ---------- FastAPI ----------
app = FastAPI(title="Agroverse AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agroverse.great-site.net",
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- OpenAI Client ----------
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# ---------- Firebase Setup ----------
firebase_enabled = False
db = None

try:
    if FIREBASE_KEY_JSON:
        import firebase_admin
        from firebase_admin import credentials, db as firebase_db

        firebase_config = json.loads(FIREBASE_KEY_JSON)
        cred = credentials.Certificate(firebase_config)

        if not firebase_admin._apps:
            firebase_admin.initialize_app(
                cred,
                {"databaseURL": "https://agro-98c7b-default-rtdb.firebaseio.com/"}
            )

        db = firebase_db
        firebase_enabled = True
        print("✅ Firebase initialized")
    else:
        print("⚠️ FIREBASE_KEY_JSON not found, Firebase disabled")

except Exception as e:
    print("⚠️ Firebase init failed")
    traceback.print_exc()

# ---------- Models ----------
class ChatRequest(BaseModel):
    message: str

class CropRequest(BaseModel):
    plant: str = "Tomato"

# ---------- Utils ----------
def simulate_sensor_data():
    return {
        "temperature": round(random.uniform(20, 35), 1),
        "humidity": round(random.uniform(40, 80), 1),
        "soil_moisture": random.randint(300, 800),
        "sunlight": random.randint(100, 1000),
    }

# ---------- Routes ----------
@app.get("/")
def root():
    return {"status": "Agroverse backend running 🚀"}

# ---- AI Chat ----
@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        sensor = simulate_sensor_data()

        response = client.responses.create(
            model="gpt-4o-mini",
            input=f""",
            max_output_tokens=500
Sensor Data:
Temperature: {sensor['temperature']} °C
Humidity: {sensor['humidity']} %
Soil Moisture: {sensor['soil_moisture']}
Sunlight: {sensor['sunlight']} lux

User: {req.message}
"""
        )

        return {
            "reply": response.output_text,
            "sensor_data": sensor
        }

    except Exception as e:
        print("🔥 CHAT ERROR")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ---- Crop Analysis ----
@app.post("/api/analyze-crop")
async def analyze_crop(req: CropRequest):
    try:
        sensor = simulate_sensor_data()

        prompt = f"""
Analyze the crop '{req.plant}' using this sensor data:

Temperature: {sensor['temperature']} °C
Humidity: {sensor['humidity']} %
Soil Moisture: {sensor['soil_moisture']}
Sunlight: {sensor['sunlight']} lux

Provide:
1. Crop health report
2. Possible diseases
3. Improvement suggestions
"""

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            max_output_tokens=500
        )

        return {
            "sensor_data": sensor,
            "analysis": response.output_text
        }

    except Exception as e:
        print("🔥 ANALYZE-CROP ERROR")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ---- ESP32 Sensor Update ----
@app.post("/api/update-sensor")
async def update_sensor(request: Request):
    data = await request.json()

    if not firebase_enabled:
        return {"status": "firebase_disabled", "data": data}

    try:
        ref = db.reference("users/testUser/sensorData")
        ref.set(data)
        return {"status": "stored", "data": data}

    except Exception as e:
        print("🔥 FIREBASE WRITE ERROR")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ---- Test Firebase ----
@app.get("/test-firebase")
def test_firebase():
    if not firebase_enabled:
        return {"error": "Firebase not enabled"}

    try:
        ref = db.reference("users/testUser/sensorData")
        return ref.get() or {"message": "No data found"}

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

print("✅ Backend fully loaded")
