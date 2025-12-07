# start_server.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"message": "BLE Tracker API is running!"}

@app.get("/api/tags")
def get_tags():
    return [
        {"name": "WHEELCHAIR_A", "mac": "AA:BB:CC:DD:EE:01"},
        {"name": "WHEELCHAIR_B", "mac": "AA:BB:CC:DD:EE:02"}
    ]

if __name__ == "__main__":
    print("Server starting...")
    print("Open: http://localhost:5000")
    print("Press Ctrl+C to stop")
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")