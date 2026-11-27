"""Đánh giá U-Net trên test (cùng hậu xử lý phòng như phương pháp cuối) + bootstrap so với phương pháp cổ điển.

python eval_unet.py   (sau khi đã chạy: python unet_wall.py train 3000)
-> output/cc/test/unet_summary.json, in ra dict để dán vào report/build_report.py (UNET = {...})
"""
import csv, json, os
import numpy as np
from eval_cubicasa import HERE, WALL_M, load_split, prf, room_scores
import pipeline as P
from unet_wall import UNetWall, MODEL_PATH

params = json.load(open(os.path.join(HERE, "params.json")))
door, T_final = params["full"]["door"], params["fixed_k"] / params["full"]["ratio"]  # cùng tỉ lệ px/m với phương pháp cuối
model = UNetWall()
rows = []
for it in load_split("test"):
    w = model(it["img"])
    _, rooms = P.segment_rooms(w, T_final / WALL_M, max_door_m=door)
    iou, pr, rc = prf(w, it["gt_wall"])
    r = dict(image=it["name"], wall_IoU=iou, wall_P=pr, wall_R=rc); r.update(room_scores(rooms, it["gt_rooms"]) or {})
    rows.append(r)

summ = {k: round(float(np.mean([r[k] for r in rows if k in r])), 3) for k in ["wall_IoU", "wall_P", "wall_R", "room_mIoU", "room_F1"]}
meta = json.load(open(MODEL_PATH.replace(".pt", ".json")))
summ["sec"] = round(meta["train_sec"])

# bootstrap: U-Net − phương pháp cuối (k = 7)
base = {r["image"]: r for r in csv.DictReader(open(os.path.join(HERE, "output", "cc", "test", "results.csv"), encoding="utf-8"))
        if r["variant"] == "  - k co dinh (tune tren val)"}
rng = np.random.default_rng(0)
for k in ["wall_IoU", "room_F1"]:
    d = np.array([r[k] - float(base[r["image"]][k]) for r in rows if k in r and base[r["image"]].get(k)])
    bs = [rng.choice(d, len(d)).mean() for _ in range(5000)]
    summ[f"delta_{k}"] = f"{d.mean():+.3f} [{np.percentile(bs, 2.5):+.3f}, {np.percentile(bs, 97.5):+.3f}]"
json.dump(summ, open(os.path.join(HERE, "output", "cc", "test", "unet_summary.json"), "w"), indent=2)
print(json.dumps(summ, indent=2))
