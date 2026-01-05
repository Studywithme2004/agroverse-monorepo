import os
import json
import random
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# ================= LOAD ENV =================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
FIREBASE_KEY_JSON = os.getenv("FIREBASE_KEY_JSON")

if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY not set")

# ================= OPENAI =================
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# ================= FASTAPI =================
app = FastAPI(title="Agroverse AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= MODELS =================
class ChatRequest(BaseModel):
    message: str

# ================= SENSOR SIM =================
def simulate_sensor_data():
    return {
        "temperature": round(random.uniform(20, 35), 1),
        "humidity": round(random.uniform(40, 80), 1),
        "soil_moisture": random.randint(300, 800),
        "sunlight": random.randint(100, 1000),
    }

# ================= ROOT =================
@app.get("/")
def root():
    return {"status": "Agroverse backend running 🚀"}

# ================= AI CHAT =================
@app.post("/api/chat")
async def chat(request: ChatRequest):
    sensor = simulate_sensor_data()

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert agricultural AI assistant.\n"
                f"Temperature: {sensor['temperature']} °C\n"
                f"Humidity: {sensor['humidity']} %\n"
                f"Soil Moisture: {sensor['soil_moisture']}\n"
                f"Sunlight: {sensor['sunlight']} lux\n"
            )
        },
        {"role": "user", "content": request.message}
    ]

    response = client.responses.create(
        model="gpt-4o-mini",
        input=messages
    )

    return {
        "reply": response.output_text,
        "sensor_data": sensor
    }

# ================= FIREBASE =================
firebase_enabled = False
db = None

try:
    import firebase_admin
    from firebase_admin import credentials, db as firebase_db

    if FIREBASE_KEY_JSON:
        cred_dict = json.loads(FIREBASE_KEY_JSON)
        cred = credentials.Certificate(cred_dict)

        if not firebase_admin._apps:
            firebase_admin.initialize_app(
                cred,
                {"databaseURL": "https://agro-98c7b-default-rtdb.firebaseio.com/"}
            )

        db = firebase_db
        firebase_enabled = True
        print("✅ Firebase initialized")

except Exception as e:
    print("⚠️ Firebase disabled:", e)

# ================= ESP32 SENSOR API =================
@app.post("/api/sensor-data")
async def receive_sensor_data(request: Request):
    data = await request.json()

    if firebase_enabled:
        ref = db.reference("users/testUser/sensorData")
        ref.set(data)

    return {
        "status": "received",
        "firebase": firebase_enabled,
        "data": data
    }

# ================= TEST FIREBASE =================
@app.get("/test-firebase")
def test_firebase():
    if not firebase_enabled:
        return {"error": "Firebase not enabled"}

    ref = db.reference("users/testUser/sensorData")
    return ref.get() or {"message": "No data yet"}

print("✅ Backend fully loaded")
