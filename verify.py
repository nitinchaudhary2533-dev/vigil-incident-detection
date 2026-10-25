import json
import hashlib
import os


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


problems = 0
prev = "0" * 64

if not os.path.exists("ledger.jsonl"):
    print("ledger.jsonl not found, first run step3.py and record the incident.")
    raise SystemExit

with open("ledger.jsonl", "r", encoding="utf-8") as f:
    for line_no, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            print(f"Line {line_no}: LINE IS CORRUPT (not valid JSON)")
            problems += 1
            continue

        ok = True

        if record["prev_hash"] != prev:
            print(f"Line {line_no}: CHAIN BROKEN (earlier entry changed or deleted)")
            ok = False

        if record["entry_hash"] != entry_hash(record):
            print(f"Line {line_no}: ENTRY WAS CHANGED")
            ok = False

        clip = record["clip"]
        if not os.path.exists(clip):
            print(f"Line {line_no}: clip is Gayab")
            ok = False
        elif sha256_of_files(clip) != record["clip_sha256"]:
            print(f"Line {line_no}: clip was changed")
            ok = False

        if ok:
            print(f"Line {line_no}: {record['id']} -> ok")
        else:
            problems += 1

        prev = record["entry_hash"]

if problems == 0:
    print("ALL IS WELL, NO ANY CLIP IS CHANGED")
else:
    print(f"{problems} PROBLEM FOUND")