import json
import random
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

    import firebase_admin
    from firebase_admin import credentials, db as firebase_db

    cred = credentials.Certificate(json.loads(FIREBASE_KEY_JSON))



    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            cred,
            {"databaseURL": "https://agro-98c7b-default-rtdb.firebaseio.com/"}
        )

    db = firebase_db
    firebase_enabled = True
    print("✅ Firebase initialized")

except Exception as e:
    print(⚠️ Firebase disabled:", e)

# ---------- Models ----------
class ChatRequest(BaseModel):
@app.post("/api/chat")
async def chat(req: ChatRequest):
    sensor = simulate_sensor_data()
    response = client.responses.create(
        model="gpt-4o-mini",
        input=f"""


Sensor Data:
Temperature: {sensor['temperature']} °C
Humidity: {sensor['humidity']} %


User: {req.message}
"""
    )
    return {"reply": response.output_text, "sensor_data": sensor}

# ---- Crop Analysis (for frontend) ----
@app.post("/api/analyze-crop")
async def analyze_crop(req: CropRequest):
    sensor = simulate_sensor_data()

    prompt = f"""
Analyze the crop '{req.plant}' using this sensor data:

@@ -104,28 +116,43 @@
2. Possible diseases
3. Improvement suggestions
"""
    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )
    return {"sensor_data": sensor, "analysis": response.output_text}

# ---- ESP32 Sensor Update ----
@app.post("/api/update-sensor")
async def update_sensor(request: Request):
    data = await request.json()
    if not firebase_enabled:
        return {"status": "firebase_disabled", "data": data}

    ref = db.reference("users/testUser/sensorData")
    ref.set(data)

    return {"status": "stored", "data": data}

# ---- Test Firebase ----
@app.get("/test-firebase")
def test_firebase():
    if not firebase_enabled:
        return {"error": "Firebase not enabled"}

    ref = db.reference("users/testUser/sensorData")
    return ref.get() or {"message": "No data found"}

print("✅ Backend fully loaded")




