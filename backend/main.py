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
    allow_origins=["*"],  # tighten in production
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
    return {
        "temperature": round(random.uniform(20, 35), 1),
        "humidity": round(random.uniform(40, 80), 1),
        "soil_moisture": round(random.uniform(300, 800)),
        "sunlight": round(random.uniform(100, 1000))
    }

# ---------- Root ----------
@app.get("/")
def root():
    return {"status": "Agroverse FastAPI running 🚀"}

# ---------- AI Chat ----------
@app.post("/api/chat")
async def chat(request: ChatRequest):
    sensor = simulate_sensor_data()
    sensor_context = (
        f"Temperature: {sensor['temperature']} °C\n"
        f"Humidity: {sensor['humidity']} %\n"
        f"Soil Moisture: {sensor['soil_moisture']}\n"
        f"Sunlight: {sensor['sunlight']} lux\n"
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert agricultural AI assistant. "
                "Analyze crop health using live IoT sensor data and give clear, practical farming advice.\n"
                + sensor_context
            )
        },
        {"role": "user", "content": request.message}
    ]

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=messages
        )
        return {"reply": response.output_text, "sensor_data": sensor}

    except Exception as e:
        return {"error": str(e), "sensor_data": sensor}

# ---------- Crop Analysis ----------
@app.post("/api/analyze-crop")
async def analyze_crop(request: CropRequest):
    sensor = simulate_sensor_data()
    prompt = (
        f"Analyze the crop '{request.plant}' using sensor data:\n"
        f"Temperature: {sensor['temperature']} °C\n"
        f"Humidity: {sensor['humidity']} %\n"
        f"Soil Moisture: {sensor['soil_moisture']}\n"
        f"Sunlight: {sensor['sunlight']} lux\n\n"
        "Provide:\n"
        "1. Crop health report\n"
        "2. Possible diseases\n"
        "3. Improvement suggestions"
    )

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt
        )
        return {"sensor_data": sensor, "analysis": response.output_text}

    except Exception as e:
        return {"error": str(e), "sensor_data": sensor}

# ---------- Firebase ----------
try:
    import firebase_admin
    from firebase_admin import credentials, db

    if not FIREBASE_KEY_JSON:
        raise RuntimeError("❌ FIREBASE_KEY_JSON not set")

    cred_dict = json.loads(FIREBASE_KEY_JSON)
    cred = credentials.Certificate(cred_dict)

    firebase_admin.initialize_app(
        cred,
        {"databaseURL": "https://agro-98c7b-default-rtdb.firebaseio.com/"}
    )

    @app.get("/test-firebase")
    def test_firebase():
        ref = db.reference("users/testUser/sensorData")
        return ref.get() or {"message": "No data found"}

    print("✅ Firebase initialized")

except Exception as e:
    print("⚠️ Firebase disabled:", e)


from fastapi import Request

@app.post("/api/update-sensor")
async def update_sensor(request: Request):
    try:
        data = await request.json()
        ref = db.reference("users/testUser/sensorData")
        ref.set(data)  # store live data in Firebase
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ---------- Debug ----------
print("✅ OpenAI loaded")
