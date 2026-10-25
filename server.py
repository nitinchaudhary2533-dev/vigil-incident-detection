import json
import os
import time
import math

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEDGER_PATH = os.path.join(BASE_DIR, "ledger.jsonl")
REVIEWS_PATH = os.path.join(BASE_DIR, "reviews.jsonl")

TEAMS = [
    {"name": "Police PCR Van 1", "type": "Police",    "lat": 27.5060, "lon": 77.7040},
    {"name": "Ambulance Unit 7", "type": "Ambulance", "lat": 27.4920, "lon": 77.7030},
    {"name": "Fire Station A",   "type": "Fire",      "lat": 27.5120, "lon": 77.6900},
]


def distance_km(lat1, lon1, lat2, lon2):
    R = 6371
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def nearest_team(lat, lon):
    best = None
    best_d = None
    for t in TEAMS:
        d = distance_km(lat, lon, t["lat"], t["lon"])
        if best is None or d < best_d:
            best, best_d = t, d
    return best, best_d

app = FastAPI(title="VIGIL Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Review(BaseModel):
    decision: str           # "confirmed" ya "false_alarm"
    operator: str = "operator1"


def read_ledger():
    records = []
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return records


def read_reviews():
    latest = {}
    if os.path.exists(REVIEWS_PATH):
        with open(REVIEWS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    latest[r["incident_id"]] = r   # aakhri faisla rakhta hai
    return latest


@app.get("/")
def home():
    return {"app": "VIGIL", "status": "running"}

@app.get("/dashboard")
def dashboard():
    return FileResponse(os.path.join(BASE_DIR, "dashboard.html"))

@app.get("/teams")
def teams():
    return TEAMS


@app.get("/incidents")
def all_incidents():
    records = read_ledger()
    reviews = read_reviews()
    for r in records:
        rev = reviews.get(r["id"])
        r["status"] = rev["decision"] if rev else "pending"

        r["alert"] = None
        if r["tier"] == "HIGH" and r.get("lat") is not None:
            team, dist = nearest_team(r["lat"], r["lon"])
            r["alert"] = {
                "team": team["name"],
                "type": team["type"],
                "distance_km": round(dist, 2),
            }
    records.reverse()
    return records


@app.get("/incidents/{incident_id}")
def one_incident(incident_id: str):
    reviews = read_reviews()
    for record in read_ledger():
        if record["id"] == incident_id:
            rev = reviews.get(incident_id)
            record["status"] = rev["decision"] if rev else "pending"
            return record
    raise HTTPException(status_code=404, detail="Incident not found")


@app.get("/clips/{incident_id}")
def get_clip(incident_id: str):
    for record in read_ledger():
        if record["id"] == incident_id:
            clip_path = os.path.join(BASE_DIR, record["clip"])
            if os.path.exists(clip_path):
                return FileResponse(clip_path, media_type="video/mp4")
    raise HTTPException(status_code=404, detail="Clip is not found")


@app.post("/incidents/{incident_id}/review")
def review_incident(incident_id: str, review: Review):
    if review.decision not in ("confirmed", "false_alarm"):
        raise HTTPException(status_code=400, detail="decision is wrong")
    if not any(r["id"] == incident_id for r in read_ledger()):
        raise HTTPException(status_code=404, detail="Incident not found")

    entry = {
        "incident_id": incident_id,
        "decision": review.decision,
        "operator": review.operator,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(REVIEWS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry