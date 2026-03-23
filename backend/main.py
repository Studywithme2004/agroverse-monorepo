import os
import json
import traceback
import base64
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Load ENV ----------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
FIREBASE_KEY_JSON = os.getenv("FIREBASE_KEY_JSON")

# ---------- FastAPI ----------
app = FastAPI(title="Agroverse AI Backend")

# ✅ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change later for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Serve images folder
IMAGE_FOLDER = "images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)
app.mount("/images", StaticFiles(directory=IMAGE_FOLDER), name="images")

# ---------- OpenAI ----------
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# ---------- Firebase ----------
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

# ---------- IMAGE UPLOAD ----------
@app.post("/api/upload-image")
async def upload_image(data: ImageData):
    try:
        img_data = data.image.split(",")[1]

        with open(f"{IMAGE_FOLDER}/latest.jpg", "wb") as f:
            f.write(base64.b64decode(img_data))

        return {"status": "success"}

    except Exception as e:
        print("❌ IMAGE ERROR:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Image upload failed")

# ---------- AI CHAT ----------
SYSTEM_PROMPT = "You are Agro AI. Give simple farmer-friendly answers."

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
            input=f"Sensor: {sensor}\nUser: {req.message}",
            max_output_tokens=200
        )

        reply = response.output_text if hasattr(response, "output_text") else "No response"

        return {"reply": reply, "sensor_data": sensor}

    except:
        return {"reply": "AI unavailable", "sensor_data": sensor}

# ---------- CROP ANALYSIS ----------
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
        return {"status": "no_data"}

    try:
        response = client.responses.create(
            model="stepfun/step-3.5-flash:free",
            input=f"Crop: {req.plant}\nSensor: {sensor}",
            max_output_tokens=250
        )

        analysis = response.output_text if hasattr(response, "output_text") else "No analysis"

        return {
            "sensor_data": sensor,
            "analysis": analysis
        }

    except:
        return {
            "sensor_data": sensor,
            "analysis": "AI unavailable"
        }

# ---------- SENSOR UPDATE ----------
@app.post("/api/update-sensor")
async def update_sensor(request: Request):

    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not firebase_enabled:
        return {"status": "no_firebase", "data": data}

    try:
        ref = db.reference("users/testUser/sensorData")
        ref.set(data)
        return {"status": "stored"}

    except:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Firebase error")

# ---------- HISTORY (IMAGE + SENSOR) ----------
DATA_FILE = "history.json"

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

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(record)

    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

    return {"status": "saved"}

@app.get("/api/history")
def get_history():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

print("✅ Backend fully loaded")
