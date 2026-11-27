"""Đánh giá trên CubiCasa5K với tham số ĐÃ ĐÓNG BĂNG từ tune.py (chỉnh trên val).

python eval_cubicasa.py [split=test]  -> output/cc/<split>/results.csv, summary.json, ảnh minh hoạ
"""
import csv, glob, json, os, sys, time
import cv2
import numpy as np
import pipeline as P
from cubicasa_gt import load_gt

HERE = os.path.dirname(os.path.abspath(__file__))
WALL_M = 0.25  # giả định độ dày tường ~25 cm để suy ra tỉ lệ px/m


def prf(pred, gt):
    p, g = pred > 0, gt > 0
    tp = (p & g).sum()
    return float(tp / max((p | g).sum(), 1)), float(tp / max(p.sum(), 1)), float(tp / max(g.sum(), 1))


def room_scores(pred_rooms, gt_rooms, thr=0.5):
    if not gt_rooms:
        return None
    ious = (np.array([[P.iou(p["mask"], g["mask"]) for g in gt_rooms] for p in pred_rooms])
            if pred_rooms else np.zeros((0, len(gt_rooms))))
    best_gt = ious.max(0) if len(pred_rooms) else np.zeros(len(gt_rooms))
    used_p, used_g, tp = set(), set(), 0
    for idx in np.argsort(-ious, axis=None):  # ghép 1-1 tham lam theo IoU
        i, j = np.unravel_index(idx, ious.shape)
        if ious[i, j] < thr: break
        if i in used_p or j in used_g: continue
        used_p.add(i); used_g.add(j); tp += 1
    prec = tp / max(len(pred_rooms), 1); rec = tp / len(gt_rooms)
    return dict(room_mIoU=float(best_gt.mean()), room_P=prec, room_R=rec,
                room_F1=2 * prec * rec / max(prec + rec, 1e-9), n_pred=len(pred_rooms), n_gt=len(gt_rooms))


def load_split(split):
    items = []
    for d in sorted(glob.glob(os.path.join(HERE, "data", "cubicasa", split, "*"))):
        if not os.path.isdir(d):
            continue
        img = cv2.imread(os.path.join(d, "F1_scaled.png"))
        gw, gr = load_gt(os.path.join(d, "model.svg"), img.shape)
        items.append(dict(name=os.path.basename(d), img=img, gt_wall=gw, gt_rooms=gr))
    return items


def predict(img, method, prm, cache=None):
    """method: otsu | v1 | full | ablation (full + cờ). Trả về (walls, T)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if method == "otsu":
        _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return P.extract_walls(ink, prm["k"]), prm["k"] / 0.33
    if method == "v1":
        return P.extract_walls(P.sauvola(P.flatten_illumination(gray)), prm["k"]), prm["k"] / 0.33
    flags = dict(use_flatten=prm.get("use_flatten", True), use_hollow=prm.get("use_hollow", True),
                 use_color=prm.get("use_color", True), r_max=prm["r_max"])
    key = tuple(sorted(flags.items()))
    if cache is not None and key in cache:
        cand = cache[key]
    else:
        cand = P.wall_candidates(img, **flags)
        if cache is not None: cache[key] = cand
    if prm.get("fixed_k"):
        return P.extract_walls(cand, prm["fixed_k"]), prm["fixed_k"] / prm["ratio"]
    w, T, _ = P.extract_walls_adaptive(cand, ratio=prm["ratio"], kmin=prm["kmin"])
    return w, T


def score_one(it, method, prm, cache=None):
    t0 = time.perf_counter()
    walls, T = predict(it["img"], method, prm, cache)
    _, rooms = P.segment_rooms(walls, T / WALL_M, max_door_m=prm["door"])
    ms = (time.perf_counter() - t0) * 1000
    iou, pr, rc = prf(walls, it["gt_wall"])
    r = dict(image=it["name"], cat=it["name"].rsplit("_", 1)[0], wall_IoU=iou, wall_P=pr, wall_R=rc, ms=ms)
    r.update(room_scores(rooms, it["gt_rooms"]) or {})
    return r, walls


def variants(params):
    full = params["full"]
    return {
        "B0 Otsu (k tune tren val)": ("otsu", params["otsu"]),
        "B1 Sauvola v1 (k tune tren val)": ("v1", params["v1"]),
        "De xuat (day du)": ("full", full),
        "  - bo lam phang sang": ("full", {**full, "use_flatten": False}),
        "  - bo lap tuong rong": ("full", {**full, "use_hollow": False}),
        "  - bo kenh mau": ("full", {**full, "use_color": False}),
        "  - k co dinh (tune tren val)": ("full", {**full, "fixed_k": params["fixed_k"]}),
    }


def summarize(rows, names):
    summ = {}
    for v in names:
        rs = [r for r in rows if r["variant"] == v]
        m = lambda k, rr=rs: float(np.mean([r[k] for r in rr if k in r]))
        s = {k: round(m(k), 3) for k in ["wall_IoU", "wall_P", "wall_R", "room_mIoU", "room_F1", "ms"]}
        for cat in sorted({r["cat"] for r in rs}):
            s[f"wall_IoU[{cat}]"] = round(m("wall_IoU", [r for r in rs if r["cat"] == cat]), 3)
        summ[v] = s
    return summ


def main(split="test"):
    params = json.load(open(os.path.join(HERE, "params.json")))
    out = os.path.join(HERE, "output", "cc", split); os.makedirs(out, exist_ok=True)
    items = load_split(split)
    V = variants(params)
    rows = []
    for it in items:
        cache = {}
        for vname, (method, prm) in V.items():
            r, walls = score_one(it, method, prm, cache)
            r["variant"] = vname; rows.append(r)
            if vname == "De xuat (day du)":
                vis = it["img"].copy(); g = it["gt_wall"]
                vis[(walls > 0) & (g > 0)] = (0, 180, 0)
                vis[(walls > 0) & (g == 0)] = (0, 0, 255)
                vis[(walls == 0) & (g > 0)] = (255, 120, 0)
                s = 700 / max(vis.shape[:2])
                cv2.imwrite(os.path.join(out, f"pred_{it['name']}.jpg"), cv2.resize(vis, None, fx=s, fy=s, interpolation=cv2.INTER_AREA))
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(os.path.join(out, "results.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=keys); wr.writeheader(); wr.writerows(rows)
    summ = summarize(rows, V)
    summ["_meta"] = {"split": split, "n_images": len(items), "params_from": "params.json (tune tren val)"}
    json.dump(summ, open(os.path.join(out, "summary.json"), "w"), indent=2, ensure_ascii=False)
    print(f"split={split}  n={len(items)}")
    for v in V:
        print(f"{v:34s}", summ[v])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "test")
