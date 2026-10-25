import cv2
from ultralytics import YOLO
import json
import hashlib
import os
import time
from collections import deque
from ultralytics import YOLO
import subprocess
import imageio_ffmpeg

WATCH_CLASSES = {1: "pistol"}
LOW_LIMIT=0.40
HIGH_LIMIT=0.70
CONFIRM_FRAMES=5
COOLDOWN=15
FPS=15

CAMERA_ID = "CAM-001"
CAMERA_LAT = 27.5000
CAMERA_LON = 77.7000

os.makedirs("evidence", exist_ok=True)

def sha256_of_files(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()

def entry_hash(record):
    body = {k: v for k, v in record.items() if k != "entry_hash"}
    text = json.dumps(body, sort_keys=True)
    return hashlib.sha256(text.encode()).hexdigest()

def last_hash():
    last = "0" * 64
    if os.path.exists("ledger.jsonl"):
        with open("ledger.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    last = json.loads(line)["entry_hash"]
    return last

def save_clips(frames, path):
    temp_path = path.replace(".mp4", "_raw.mp4")
    height, width = frames[0].shape[:2]
    writer = cv2.VideoWriter(temp_path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (width, height))
    for fr in frames:
        writer.write(fr)
    writer.release()

    # H.264 me convert karo taaki browser me chale
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [ffmpeg, "-y", "-i", temp_path,
         "-vcodec", "libx264", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", path],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    os.remove(temp_path)

model = YOLO("weapon_v2.pt")
cap = cv2.VideoCapture(0)
buffer = deque(maxlen=45)
streak = 0
last_incident = 0

while True:
    ok, frame = cap.read()
    if not ok:
        break
    buffer.append(frame)

    result = model(frame, classes=list(WATCH_CLASSES.keys()), verbose=False)[0]

    best = 0.0
    best_label = None
    for box in result.boxes:
        cls_id = int(box.cls[0])
        if cls_id in WATCH_CLASSES:
            score = float(box.conf[0])
            if score > best:
                best = score
                best_label = WATCH_CLASSES[cls_id]

    if best >= 0.5:
        streak += 1
    else:
        streak = 0

    if best < LOW_LIMIT:
        tier = "NONE"
    elif best >= HIGH_LIMIT and streak >= CONFIRM_FRAMES:
        tier = "HIGH"
    else:
        tier = "MEDIUM"

    if tier == "HIGH" and time.time() - last_incident > COOLDOWN:
        last_incident = time.time()
        incident_id = "INC-" + str(int(time.time()))
        clip_path = "evidence/" + incident_id + ".mp4"
        save_clips(list(buffer), clip_path)

        record = {
            "id": incident_id,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "label": best_label,
            "camera_id": CAMERA_ID,
            "lat": CAMERA_LAT,
            "lon": CAMERA_LON,
            "score": round(best, 3),
            "tier": tier,
            "clip": clip_path,
            "clip_sha256": sha256_of_files(clip_path),
        }
        record["prev_hash"] = last_hash()
        record["entry_hash"] = entry_hash(record)
        
        with open("ledger.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        print("INCIDENT RECORDED:", record)
        print(tier, round(best, 2), streak)
    cv2.imshow("VIGIL", result.plot())
    if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
        break

cap.release()
cv2.destroyAllWindows()