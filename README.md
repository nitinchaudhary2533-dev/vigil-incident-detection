# VIGIL: Closed-Loop Incident Detection and Response (College Mini Project Prototype)

VIGIL is a prototype that detects weapons (currently **pistol** only) in camera video, computes a
confidence score, stores a SHA-256 hash of the evidence clip in a tamper-evident ledger, and shows
a **simulated** alert for the nearest response team.

> **Disclaimer:** This is an educational prototype. It is not ready for real-world security or
> policing use. The model is weak and can raise false alarms. A human must review every alert.

## Pipeline

Camera -> YOLOv8 detection -> multi-frame confirmation -> score and tier
-> clip saved + SHA-256 hash -> hash-chained ledger
-> FastAPI backend -> web dashboard (map, operator Confirm / False alarm)
-> nearest response team alert (simulated)

## Features

- **Multi-frame confirmation:** an alarm is not raised from a single frame. The object must appear
  in several consecutive frames.
- **Tiers:** LOW, MEDIUM and HIGH, based on score and confirmation. Currently **only HIGH incidents**
  are written to the ledger.
- **Evidence:** on a HIGH incident, a short clip (H.264) covering the seconds before the incident is
  saved, and its SHA-256 hash is written to the ledger.
- **Hash-chained ledger:** each record contains the hash of the previous record. `verify.py` detects
  changes to the ledger or the clips (tamper-evident, not tamper-proof).
- **Dashboard:** incident table, live map, clip link, and operator Confirm / False alarm buttons.
- **Alert simulation:** the nearest response team to the camera is chosen using the haversine distance.

## Files

| File | Purpose |
|---|---|
| step3.py | Detector: camera, tiers, clip, hash, ledger |
| server.py | FastAPI backend, also serves the dashboard |
| dashboard.html | Incident table, map, operator buttons |
| verify.py | Integrity check for the ledger and clips |
| start_vigil.bat | One-click start on Windows |
| reset_demo.bat | Clears demo data |
| test_folder.py, test_images.bat | Test the models on a folder of images |
| requirements.txt | Python dependencies |

## Setup (Windows)

1. Install Python 3.10 or newer.
2. In a terminal:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. Download the trained model `weapon_v2.pt` from [add model link here] and place it in the
   project folder.

## Run

Double-click `start_vigil.bat`. It starts the server and the detector and opens the dashboard at
http://127.0.0.1:8000/dashboard. Press `q` in the detector window to quit.

Manual way (two separate terminals, venv activated):

```
uvicorn server:app
python step3.py
```

## Verify integrity

```
python verify.py
```

If the ledger or a clip was modified, it prints `ENTRY WAS CHANGED`, `CHAIN BROKEN` or
`clip was changed`.

## Model and results

- Model: YOLOv8s, trained on two public datasets combined (about 8,800 training and 1,245
  validation images).
- Classes: `pistol`, `knife`.
- Validation mAP50: all 0.896, pistol 0.838, knife 0.953.
- **Note:** these numbers are measured on the validation images of the same datasets used for
  training. On different, real CCTV footage the accuracy can be much lower.

## Limitations

- The `knife` class is disabled: it raised many false alarms on everyday objects such as pens,
  spoons and bottles.
- The `pistol` class also gives weak scores on images that differ from the training data, and can
  produce low-score false detections.
- Trained only on public datasets, not tested on real CCTV footage.
- The alert is only a simulation. There is no integration with ERSS-112 or any real emergency system.
- Only HIGH incidents are written to the ledger. MEDIUM and LOW appear only in the terminal.
- One real event can create several incidents (no event grouping yet).
- Operator decisions (`reviews.jsonl`) are not part of the hash chain.
- The dashboard has no login, and CORS allows all origins (for local testing only).
- Camera location and response team coordinates are fixed values.

## Future work

- Improve the model with hard negative images, and bring back the knife class
- Event grouping and real notifications (for example Telegram)
- RTSP / IP camera input, and running on an edge device (Jetson)
- Operator login and signed decisions, privacy and data retention rules

## Credits and licence

- Datasets (CC BY 4.0), Roboflow Universe: "CCTV Weapon Detect" (prospace-gi6e4) and
  "Detect weapon" (akekykyky).
- YOLOv8 by [Ultralytics](https://github.com/ultralytics/ultralytics), licensed AGPL-3.0.
- This project is released under the AGPL-3.0 licence (see the LICENSE file).

## Author

[Nitin], [GL Bajaj Group of Institutions Mathura, CSE, 2nd year]