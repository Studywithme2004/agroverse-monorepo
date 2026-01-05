import os
import json
import random
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
FIREBASE_KEY_JSON = os.getenv("FIREBASE_KEY_JSON")

# ---------- FastAPI ----------
app = FastAPI(title="Agroverse AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- OpenAI ----------
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# ---------- Firebase ----------
firebase_enabled = False
db = None

try:
    import firebase_admin
    from firebase_admin import credentials, db as firebase_db

    cred = credentials.Certificate(json.loads(FIREBASE_KEY_JSON))
    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            cred,
            {
                "databaseURL":
                "https://agro-98c7b-default-rtdb.firebaseio.com/"
            }
        )

    db = firebase_db
    firebase_enabled = True
    print("✅ Firebase initialized")

except Exception as e:
    print("⚠️ Firebase disabled:", e)

# ---------- Models ----------
class ChatRequest(BaseModel):
    message: str

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

@app.post("/api/chat")
async def chat(req: ChatRequest):
    sensor = simulate_sensor_data()

    response = client.responses.create(
        model="gpt-4o-mini",
        input=f"""
Sensor Data:
Temperature: {sensor['temperature']}
Humidity: {sensor['humidity']}
Soil Moisture: {sensor['soil_moisture']}
Sunlight: {sensor['sunlight']}

User: {req.message}
"""
    )

    return {
        "reply": response.output_text,
        "sensor_data": sensor
    }

@app.post("/api/update-sensor")
async def update_sensor(request: Request):
    data = await request.json()

    if not firebase_enabled:
        return {"status": "firebase_disabled", "data": data}

    ref = db.reference("users/testUser/sensorData")
    ref.set(data)

    return {"status": "stored", "data": data}

@app.get("/test-firebase")
def test_firebase():
    if not firebase_enabled:
        return {"error": "Firebase not enabled"}

    ref = db.reference("users/testUser/sensorData")
    return ref.get() or {"message": "No data found"}

print("✅ Backend fully loaded")
