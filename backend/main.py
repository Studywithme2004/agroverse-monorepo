import os
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

if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY not set in .env")

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# ---------- FastAPI ----------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Request Models ----------
class ChatRequest(BaseModel):
    message: str
    history: list = []

class CropRequest(BaseModel):
    plant: str = "Tomato"

# ---------- Simulated Sensor Data ----------
def simulate_sensor_data():
    """Simulate live sensor data for testing/dashboard"""
    return {
        "temperature": round(random.uniform(20, 35), 1),  # °C
        "humidity": round(random.uniform(40, 80), 1),     # %
        "soil_moisture": round(random.uniform(300, 800)), # arbitrary units
        "sunlight": round(random.uniform(100, 1000))      # lux
    }

# ---------- Root ----------
@app.get("/")
def root():
    return {"status": "FastAPI is running"}

# ---------- AI Chat API ----------
@app.post("/api/chat")
async def chat(request: ChatRequest):
    sensor = simulate_sensor_data()
    sensor_context = f"""
Live Farm Sensor Data:
- Temperature: {sensor['temperature']} °C
- Humidity: {sensor['humidity']} %
- Soil Moisture: {sensor['soil_moisture']}
- Sunlight: {sensor['sunlight']} lux
"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert agricultural AI assistant. "
                "Analyze crop health using live IoT sensor data and "
                "give clear, practical farming advice.\n"
                + sensor_context
            )
        },
        {
            "role": "user",
            "content": request.message
        }
    ]

    try:
        response = client.responses.create(
            model="openai/gpt-4o-mini",
            input=messages
        )
        reply = response.output_text

    except Exception as e:
        print("🔥 AI ERROR:", e)
        return {
            "error": str(e),
            "sensor_data": sensor
        }

    return {
        "reply": reply,
        "sensor_data": sensor
    }

# ---------- Crop Analysis API ----------
@app.post("/api/analyze-crop")
async def analyze_crop(request: CropRequest):
    sensor = simulate_sensor_data()
    sensor_context = f"""
Live Plant Sensor Data:
- Temperature: {sensor['temperature']} °C
- Humidity: {sensor['humidity']} %
- Soil Moisture: {sensor['soil_moisture']}
- Sunlight: {sensor['sunlight']} lux
"""

    prompt = f"""
You are an expert agricultural AI assistant.
Analyze the crop "{request.plant}" using the sensor data below:
{sensor_context}

Please provide:
1. Full crop report
2. Possible diseases
3. Clear suggestions for improving crop health
"""

    try:
        response = client.responses.create(
            model="openai/gpt-4o-mini",
            input=prompt
        )
        reply = response.output_text

    except Exception as e:
        print("🔥 AI ERROR:", e)
        return {
            "error": str(e),
            "sensor_data": sensor
        }

    return {
        "sensor_data": sensor,
        "analysis": reply
    }

# ---------- Firebase Test ----------
try:
    import firebase_admin
    from firebase_admin import credentials, db

    # 🔴 Make sure this file exists
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://agroverseai-default-rtdb.firebaseio.com/"
    })

    @app.get("/test-firebase")
    def test_firebase():
        try:
            ref = db.reference("users/testUser/sensorData")
            data = ref.get()
            print("Firebase data:", data)
            return data or {"message": "No data yet"}
        except Exception as e:
            print("Firebase error:", e)
            return {"error": str(e)}

except ModuleNotFoundError:
    print("⚠️ Firebase not installed. Skipping Firebase endpoints.")

# ---------- Debug ----------
print("✅ OpenAI Key Loaded:", OPENAI_API_KEY[:8], "...")
print("✅ OpenAI Base URL:", OPENAI_BASE_URL)
