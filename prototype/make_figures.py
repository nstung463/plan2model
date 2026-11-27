"""Sinh hình cho báo cáo -> report/figures/*.png"""
import csv, glob, json, os, sys
import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import synth, pipeline as P
from cubicasa_gt import load_gt

FIG = os.path.join(HERE, "..", "report", "figures"); os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def label(img, text):
    img = img.copy() if img.ndim == 3 else cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    cv2.rectangle(img, (0, 0), (img.shape[1], 34), (255, 255, 255), -1)
    cv2.putText(img, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
    return img


def fit(img, w=520, h=420):
    img = img if img.ndim == 3 else cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    s = min(w / img.shape[1], h / img.shape[0])
    r = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    out = np.full((h, w, 3), 255, np.uint8)
    y, x = (h - r.shape[0]) // 2, (w - r.shape[1]) // 2
    out[y:y + r.shape[0], x:x + r.shape[1]] = r
    return out


def grid(imgs, cols):
    while len(imgs) % cols: imgs.append(np.full_like(imgs[0], 255))
    rows = [np.hstack([np.pad(i, ((4, 4), (4, 4), (0, 0)), constant_values=200) for i in imgs[k:k + cols]]) for k in range(0, len(imgs), cols)]
    return np.vstack(rows)


# --- Hình 1: pipeline trên ảnh mô phỏng chụp điện thoại ---
page, gt = synth.draw_plan(); photo = synth.simulate_photo(page)
R = P.run(photo, synth.PX_PER_M)
det = photo.copy(); cv2.polylines(det, [R["corners"].astype(np.int32)], True, (0, 220, 0), 8)
rooms = R["flat"].copy(); ov = rooms.copy()
pal = [(255, 179, 102), (102, 204, 255), (153, 230, 153), (204, 153, 255), (102, 153, 255)]
for i, r in enumerate(R["rooms"]): ov[r["mask"] > 0] = pal[i % 5]
rooms = cv2.addWeighted(rooms, 0.45, ov, 0.55, 0)
steps = [("(a) Phone photo", photo), ("(b) Page detection", det), ("(c) Rectified", R["flat"]),
         ("(d) Illumination flattened", R["even"]), ("(e) Sauvola binarization", R["ink"]),
         ("(f) Wall mask", R["walls"]), ("(g) Door closing", R["closed"]), ("(h) Room segmentation", rooms)]
cv2.imwrite(os.path.join(FIG, "fig_pipeline_steps.png"), grid([label(fit(im), t) for t, im in steps], 4))

# --- Hình 2: ví dụ CubiCasa (3 nhóm) + nhãn ---
ex = []
for cat in ["high_quality_architectural", "high_quality", "colorful"]:
    d = sorted(glob.glob(os.path.join(HERE, "data", "cubicasa", "test", cat + "_*")))[1]
    img = cv2.imread(os.path.join(d, "F1_scaled.png")); w, rs = load_gt(os.path.join(d, "model.svg"), img.shape)
    o = img.copy(); o[w > 0] = (0, 0, 230)
    for i, r in enumerate(rs): o[r["mask"] > 0] = pal[i % 5]
    ex += [label(fit(img, 460, 400), cat.replace("_", " ")), label(fit(cv2.addWeighted(img, 0.4, o, 0.6, 0), 460, 400), "ground truth")]
cv2.imwrite(os.path.join(FIG, "fig_cubicasa_examples.png"), grid(ex, 2))

# --- Hình 3: lấp tường rỗng (chọn vùng có nhiều tường được lấp ĐÚNG nhất) ---
best = None
for cd in sorted(glob.glob(os.path.join(HERE, "data", "cubicasa", "test", "*_*"))):
    im = cv2.imread(os.path.join(cd, "F1_scaled.png")); gw, _ = load_gt(os.path.join(cd, "model.svg"), im.shape)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    ink = cv2.morphologyEx(P.sauvola(P.flatten_illumination(gray)), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    filled = P.fill_hollow_walls(ink, 14)
    good = ((filled > 0) & (ink == 0) & (gw > 0)).astype(np.float32)
    ii = cv2.integral(good); H, W = good.shape; ch, cw = min(720, H), min(960, W)
    for y in range(0, H - ch + 1, 60):
        for x in range(0, W - cw + 1, 60):
            v = ii[y + ch, x + cw] - ii[y, x + cw] - ii[y + ch, x] + ii[y, x]
            if best is None or v > best[0]:
                best = (v, im, ink, filled, (slice(y, y + ch), slice(x, x + cw)))
_, img, ink, filled, sl = best
k = 7
panels = [("(a) Input", img[sl]), ("(b) Sauvola ink", ink[sl]), ("(c) Opening on (b)", P.extract_walls(ink, k)[sl]),
          ("(d) Hollow walls filled", filled[sl]), ("(e) Opening on (d)", P.extract_walls(filled, k)[sl])]
cv2.imwrite(os.path.join(FIG, "fig_hollow_fill.png"), grid([label(fit(im, 480, 360), t) for t, im in panels], 5))

# --- Hình 4: biểu đồ kết quả test ---
S = json.load(open(os.path.join(HERE, "output", "cc", "test", "summary.json")))
names = ["B0 Otsu (k tune tren val)", "B1 Sauvola v1 (k tune tren val)", "  - bo lap tuong rong", "De xuat (day du)", "  - k co dinh (tune tren val)"]
lab = ["Otsu\n(baseline)", "Sauvola v1", "Proposed\nw/o hollow fill", "Proposed\n(adaptive k)", "Proposed\n(k = 7, final)"]
fig, ax = plt.subplots(figsize=(8.2, 3.6))
x = np.arange(len(names)); bw = 0.38
b1 = ax.bar(x - bw / 2, [S[n]["wall_IoU"] for n in names], bw, label="Wall IoU", color="#3b6fb6")
b2 = ax.bar(x + bw / 2, [S[n]["room_F1"] for n in names], bw, label="Room F1 (IoU≥0.5)", color="#e3923a")
for b in list(b1) + list(b2):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.01, f"{b.get_height():.2f}", ha="center", fontsize=8.5)
ax.set_xticks(x, lab); ax.set_ylim(0, 0.7); ax.set_ylabel("Score (test, n = 60)")
ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, loc="upper left")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig_results_bar.png"), dpi=200); plt.close(fig)

# --- Hình 5: theo nhóm ảnh ---
cats = ["high_quality_architectural", "high_quality", "colorful"]
fig, ax = plt.subplots(figsize=(7.5, 3.2))
for i, (n, l, c) in enumerate([("B0 Otsu (k tune tren val)", "Otsu", "#9aa5b1"), ("  - bo lap tuong rong", "w/o hollow fill", "#c9a7e0"), ("  - k co dinh (tune tren val)", "Proposed (final)", "#3b6fb6")]):
    v = [S[n][f"wall_IoU[{c_}]"] for c_ in cats]
    bars = ax.bar(np.arange(3) + (i - 1) * 0.26, v, 0.26, label=l, color=c)
    for b in bars: ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.01, f"{b.get_height():.2f}", ha="center", fontsize=8)
ax.set_xticks(range(3), ["Architectural", "High quality", "Colorful"]); ax.set_ylabel("Wall IoU"); ax.set_ylim(0, 0.75)
ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, ncol=3, loc="upper left")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig_results_by_category.png"), dpi=200); plt.close(fig)

# --- Hình 6: định tính tốt / trung vị / tệ ---
rows = [r for r in csv.DictReader(open(os.path.join(HERE, "output", "cc", "test", "results.csv"), encoding="utf-8")) if r["variant"] == "De xuat (day du)"]
rows.sort(key=lambda r: float(r["wall_IoU"]))
pick = [("best", rows[-1]), ("median", rows[len(rows) // 2]), ("worst", rows[0])]
ims = [label(fit(cv2.imread(os.path.join(HERE, "output", "cc", "test", f"pred_{r['image']}.jpg")), 520, 460), f"{t}: IoU {float(r['wall_IoU']):.2f}") for t, r in pick]
cv2.imwrite(os.path.join(FIG, "fig_qualitative.png"), grid(ims, 3))
print("figures ->", os.path.abspath(FIG))
