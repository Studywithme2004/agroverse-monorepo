from fastapi import FastAPI
from firebase_admin import credentials, db
import firebase_admin

app = FastAPI()

# ---------- ROOT TEST ----------
@app.get("/")
def root():
    return {"status": "Agroverse API running ✅"}

# ---------- FIREBASE INIT ----------
cred = credentials.Certificate("firebase-key.json")

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://agroverseai-default-rtdb.firebaseio.com/"
})

# ---------- FIREBASE TEST ----------
@app.get("/test-firebase")
def test_firebase():
    ref = db.reference("users/testUser/sensorData")
    return ref.get() or {"message": "No data yet"}
