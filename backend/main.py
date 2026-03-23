import os
import json
import traceback
import base64

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# 👉 ADD THIS (for image access)
app.mount("/images", StaticFiles(directory="."), name="images")

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

# 👉 NEW MODEL FOR IMAGE
class ImageData(BaseModel):
    image: str

# ---------- Fallback Sensor ----------
def simulate_sensor_data():
    return {
        "temperature": 25,
        "humidity": 60,
        "soil_moisture": 500,
        "sunlight": 700,
    }

# ---------- Root ----------
@app.get("/")
def root():
    return {"status": "Agroverse backend running 🚀"}

# ---------- 📸 IMAGE UPLOAD API (NEW) ----------
@app.post("/api/upload-image")
async def upload_image(data: ImageData):
    try:
        img_data = data.image.split(",")[1]

        with open("latest.jpg", "wb") as f:
            f.write(base64.b64decode(img_data))

        return {"status": "success", "message": "Image saved"}

    except Exception as e:
        print("❌ IMAGE ERROR:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Image upload failed")

# ---------- AI Chat ----------
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
            model="stepfun/step-3.5-flash:free",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"""
Sensor Data:
Temperature: {sensor.get('temperature')} °C
Humidity: {sensor.get('humidity')} %
Soil Moisture: {sensor.get('soil_moisture')}
Sunlight: {sensor.get('sunlight')} lux

User: {req.message}
"""
                }
            ],
            max_output_tokens=250
        )

        reply_text = ""
        if hasattr(response, "output"):
            for item in response.output:
                if hasattr(item, "content"):
                    for c in item.content:
                        if hasattr(c, "text"):
                            reply_text += c.text

        return {
            "status": "success",
            "reply": reply_text or "AI response empty",
            "sensor_data": sensor
        }

    except Exception as e:
        print("❌ CHAT AI ERROR:", str(e))
        traceback.print_exc()

        return {
            "status": "ai_unavailable",
            "reply": "AI unavailable",
            "sensor_data": sensor
        }

# ---------- Crop Analysis ----------
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
            "message": "No sensor data found"
        }

    try:
        response = client.responses.create(
            model="stepfun/step-3.5-flash:free",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"""
Sensor Data:
Temperature: {sensor.get('temperature')} °C
Humidity: {sensor.get('humidity')} %
Soil Moisture: {sensor.get('soil_moisture')}
Sunlight: {sensor.get('sunlight')} lux
Crop: {req.plant}
"""
                }
            ],
            max_output_tokens=300
        )

        analysis_text = ""
        if hasattr(response, "output"):
            for item in response.output:
                if hasattr(item, "content"):
                    for c in item.content:
                        if hasattr(c, "text"):
                            analysis_text += c.text

        return {
            "status": "success",
            "sensor_data": sensor,
            "analysis": analysis_text or "AI response empty"
        }

    except Exception as e:
        print("❌ ANALYSIS AI ERROR:", str(e))
        traceback.print_exc()

        return {
            "status": "fallback",
            "sensor_data": sensor,
            "analysis": "⚠️ AI unavailable"
        }

# ---------- ESP32 Sensor Update ----------
@app.post("/api/update-sensor")
async def update_sensor(request: Request):

    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

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

# ---------- Test Firebase ----------
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

# ----------time history-------------
# main.py

from fastapi import FastAPI, UploadFile, File, Form
from datetime import datetime
import os
import json

app = FastAPI()

DATA_FILE = "history.json"
IMAGE_FOLDER = "images"

os.makedirs(IMAGE_FOLDER, exist_ok=True)

@app.post("/api/upload-data")
async def upload_data(
    temperature: float = Form(...),
    humidity: float = Form(...),
    soil: float = Form(...),
    sunlight: float = Form(...),
    image: UploadFile = File(...)
):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    image_path = f"{IMAGE_FOLDER}/{timestamp}.jpg"

    # Save image
    with open(image_path, "wb") as f:
        f.write(await image.read())

    record = {
        "time": timestamp,
        "temperature": temperature,
        "humidity": humidity,
        "soil": soil,
        "sunlight": sunlight,
        "image": image_path
    }

    # Save JSON
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(record)

    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

    return {"message": "Saved"}

#-------timeapi-----
@app.get("/api/history")
def get_history():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []
















