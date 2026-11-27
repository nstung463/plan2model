"""Grid search tham số CHỈ trên tập val -> params.json. Tập test không được đụng tới ở đây.

Mục tiêu J = 0.5 * wall_IoU + 0.5 * room_F1 (trung bình trên ảnh val).
Baseline cũng được tune cùng cách để so sánh công bằng.
"""
import itertools, json, os, time
import cv2
import numpy as np
import pipeline as P
from eval_cubicasa import HERE, WALL_M, load_split, prf, room_scores

DOORS = [1.2, 1.6, 2.0]


def J(rows):
    return float(np.mean([0.5 * r[0] + 0.5 * r[1] for r in rows]))


def eval_walls(items, walls_list, T_list, door):
    rows = []
    for it, w, T in zip(items, walls_list, T_list):
        _, rooms = P.segment_rooms(w, T / WALL_M, max_door_m=door)
        rs = room_scores(rooms, it["gt_rooms"]) or {"room_F1": 0.0}
        rows.append((prf(w, it["gt_wall"])[0], rs["room_F1"]))
    return rows


def main():
    t0 = time.time()
    items = load_split("val")
    print("val images:", len(items))
    log, best = [], {}

    # --- Baseline Otsu & v1: tune k, door ---
    grays = [cv2.cvtColor(it["img"], cv2.COLOR_BGR2GRAY) for it in items]
    otsu_ink = [cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1] for g in grays]
    v1_ink = [P.sauvola(P.flatten_illumination(g)) for g in grays]
    for name, inks in [("otsu", otsu_ink), ("v1", v1_ink)]:
        cand = []
        for k in [3, 5, 7, 9, 11, 13]:
            ws = [P.extract_walls(i, k) for i in inks]
            for door in DOORS:
                j = J(eval_walls(items, ws, [k / 0.33] * len(ws), door))
                cand.append((j, {"k": k, "door": door})); log.append((name, k, door, j))
        best[name] = max(cand, key=lambda c: c[0])
        print(name, "best", best[name])

    # --- Đề xuất: tune r_max, ratio, kmin, door ---
    cand = []
    for r_max in [10, 14, 20]:
        cands = [P.wall_candidates(it["img"], r_max=r_max) for it in items]
        for ratio, kmin in itertools.product([0.25, 0.33, 0.4, 0.5], [3, 5]):
            out = [P.extract_walls_adaptive(c, ratio=ratio, kmin=kmin) for c in cands]
            ws, Ts = [o[0] for o in out], [o[1] for o in out]
            for door in DOORS:
                prm = {"r_max": r_max, "ratio": ratio, "kmin": kmin, "door": door}
                j = J(eval_walls(items, ws, Ts, door))
                cand.append((j, prm)); log.append(("full", prm, j))
        print("r_max", r_max, "done", round(time.time() - t0), "s")
    best["full"] = max(cand, key=lambda c: c[0])
    print("full best", best["full"])

    # --- Ablation k cố định (cùng r_max, door với bản đầy đủ): tune k ---
    fb = best["full"][1]
    cands = [P.wall_candidates(it["img"], r_max=fb["r_max"]) for it in items]
    cand = []
    for k in [5, 7, 9, 11, 13]:
        ws = [P.extract_walls(c, k) for c in cands]
        j = J(eval_walls(items, ws, [k / fb["ratio"]] * len(ws), fb["door"]))
        cand.append((j, k))
    best["fixed_k"] = max(cand, key=lambda c: c[0])
    print("fixed_k best", best["fixed_k"])

    params = {"otsu": best["otsu"][1], "v1": best["v1"][1], "full": best["full"][1], "fixed_k": best["fixed_k"][1],
              "_val_J": {k: round(v[0], 4) for k, v in best.items()},
              "_note": "Tune tren CubiCasa5K val (45 anh), J = 0.5*wall_IoU + 0.5*room_F1"}
    json.dump(params, open(os.path.join(HERE, "params.json"), "w"), indent=2)
    json.dump([list(map(str, l)) for l in log], open(os.path.join(HERE, "output", "cc", "tune_log.json"), "w"), indent=0)
    print(json.dumps(params, indent=2), "\n", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
