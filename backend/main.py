import os
import json
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
    allow_origins=["*"],
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
        print("⚠️ Firebase not enabled")

except Exception:
    print("⚠️ Firebase init failed")
    traceback.print_exc()

# ---------- Models ----------
class ChatRequest(BaseModel):
    message: str

class CropRequest(BaseModel):
    plant: str = "Tomato"

# ---------- Fallback ----------
def simulate_sensor_data():
    return {
        "temperature": 25,
        "humidity": 60,
        "soil_moisture": 500,
        "sunlight": 700,
    }

# ---------- Routes ----------
@app.get("/")
def root():
    return {"status": "Agroverse backend running 🚀"}

# ---- AI Chat ----
@app.post("/api/chat")
async def chat(req: ChatRequest):

    sensor = None

    if firebase_enabled:
        try:
            ref = db.reference("users/testUser/sensorData")
            sensor = ref.get()
        except:
            traceback.print_exc()

    if not sensor:
        sensor = simulate_sensor_data()

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=f"""
Sensor Data:
Temperature: {sensor.get('temperature')} °C
Humidity: {sensor.get('humidity')} %
Soil Moisture: {sensor.get('soil_moisture')}
Sunlight: {sensor.get('sunlight')} lux

User: {req.message}
""",
            max_output_tokens=250
        )

        try:
            reply_text = response.output[0].content[0].text
        except:
            reply_text = "AI parsing failed"

        return {
            "status": "success",
            "reply": reply_text,
            "sensor_data": sensor
        }

    except Exception:
        traceback.print_exc()
        return {
            "status": "ai_unavailable",
            "reply": "AI unavailable",
            "sensor_data": sensor
        }

# ---- Crop Analysis ----
@app.post("/api/analyze-crop")
async def analyze_crop(req: CropRequest):

    sensor = None

    if firebase_enabled:
        try:
            ref = db.reference("users/testUser/sensorData")
            sensor = ref.get()
        except:
            traceback.print_exc()

    if not sensor:
        return {
            "status": "no_data",
            "message": "No sensor data found. Please send data from ESP32 first."
        }

    prompt = f"""
Analyze the crop '{req.plant}' using this sensor data:

Temperature: {sensor.get('temperature')} °C
Humidity: {sensor.get('humidity')} %
Soil Moisture: {sensor.get('soil_moisture')}
Sunlight: {sensor.get('sunlight')} lux

Provide:
1. Crop health report
2. Possible diseases
3. Improvement suggestions
"""

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            max_output_tokens=300
        )

        try:
            analysis_text = response.output[0].content[0].text
        except:
            analysis_text = "AI parsing failed"

        return {
            "status": "success",
            "sensor_data": sensor,
            "analysis": analysis_text
        }

    except Exception:
        traceback.print_exc()

        return {
            "status": "fallback",
            "sensor_data": sensor,
            "analysis": f"""
Crop: {req.plant}

Temperature: {sensor.get('temperature')}°C
Humidity: {sensor.get('humidity')}%
Soil Moisture: {sensor.get('soil_moisture')}
Sunlight: {sensor.get('sunlight')}

⚠️ AI unavailable.
Suggestion:
- Maintain soil moisture between 40–70%
- Ensure proper sunlight
"""
        }

# ---- ESP32 Sensor Update ----
@app.post("/api/update-sensor")
async def update_sensor(request: Request):

    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not data:
        raise HTTPException(status_code=400, detail="Empty data")

    print("📡 Incoming Sensor:", data)

    if not firebase_enabled:
        return {"status": "firebase_disabled", "data": data}

    try:
        ref = db.reference("users/testUser/sensorData")
        ref.set(data)
        return {"status": "stored", "data": data}

    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Firebase write failed")

# ---- Test Firebase ----
@app.get("/test-firebase")
def test_firebase():
    if not firebase_enabled:
        return {"error": "Firebase not enabled"}

    try:
        ref = db.reference("users/testUser/sensorData")
        return ref.get() or {"message": "No data found"}
    except:
        traceback.print_exc()
        return {"error": "Firebase read failed"}

print("✅ Backend fully loaded")
