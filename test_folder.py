import os
from ultralytics import YOLO

IN_DIR = "test_images"
OUT_DIR = "test_results"
MODELS = ["weapon.pt", "weapon_v2.pt"]    # jitne models compare karne hon yahan likho
CONF = 0.25

os.makedirs(IN_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

loaded = {m: YOLO(m) for m in MODELS if os.path.exists(m)}
exts = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
files = [f for f in sorted(os.listdir(IN_DIR)) if f.lower().endswith(exts)]

if not loaded:
    print("Koi model file nahi mili. weapon.pt ya weapon_v2.pt Vigil folder me rakho.")
elif not files:
    print("test_images folder me koi image nahi hai. Images daalo aur dobara chalao.")
else:
    for name in files:
        print(name)
        for m, model in loaded.items():
            r = model(os.path.join(IN_DIR, name), conf=CONF, verbose=False)[0]
            found = [(model.names[int(b.cls[0])], round(float(b.conf[0]), 2)) for b in r.boxes]
            print("   ", m, "->", found if found else "kuch nahi")
            r.save(filename=os.path.join(OUT_DIR, m.replace(".pt", "") + "_" + name))
    print("Box wali images test_results folder me hain.")