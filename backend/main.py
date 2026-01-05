import os
import json
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Load ENV ----------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
FIREBASE_KEY_JSON = os.getenv("FIREBASE_KEY_JSON")

if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY not set")

# ---------- OpenAI Client ----------
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# ---------- FastAPI ----------
app = FastAPI(title="Agroverse AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Models ----------
class ChatRequest(BaseModel):
    message: str

class SensorData(BaseModel):
    crop: str
    temperature: float
    humidity: float
    soil_moisture: int
    sunlight: int

# ---------- Firebase ----------
firebase_enabled = False

try:
    import firebase_admin
    from firebase_admin import credentials, db

    cred = credentials.Certificate(json.loads(FIREBASE_KEY_JSON))

    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            cred,
            {
                "databaseURL": "https://agro-98c7b-default-rtdb.firebaseio.com/"
            }
        )

    firebase_enabled = True
    print("✅ Firebase initialized")

except Exception as e:
    print("⚠️ Firebase disabled:", e)

# ---------- Root ----------
@app.get("/")
def root():
    return {"status": "Agroverse backend running 🚀"}

# ---------- ESP32 SENSOR ENDPOINT (FIXED) ----------
@app.post("/api/update-sensor")
def update_sensor(data: SensorData):

    if firebase_enabled:
        ref = db.reference("users/testUser/sensorData")
        ref.set(data.dict())

    return {
        "status": "success",
        "received": data
    }

# ---------- AI CHAT ----------
@app.post("/api/chat")
def chat(req: ChatRequest):

    sensor = {
        "temperature": round(random.uniform(20, 35), 1),
        "humidity": round(random.uniform(40, 80), 1),
        "soil_moisture": random.randint(300, 800),
        "sunlight": random.randint(100, 1000)
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You are an agricultural AI assistant.\n"
                f"Temperature: {sensor['temperature']}°C\n"
                f"Humidity: {sensor['humidity']}%\n"
                f"Soil Moisture: {sensor['soil_moisture']}\n"
                f"Sunlight: {sensor['sunlight']} lux"
            )
        },
        {"role": "user", "content": req.message}
    ]

    response = client.responses.create(
        model="gpt-4o-mini",
        input=messages
    )

    return {
        "reply": response.output_text,
        "sensor_data": sensor
    }

print("✅ Backend fully loaded")
