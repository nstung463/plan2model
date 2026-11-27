"""Chạy toàn bộ demo: sinh dữ liệu -> pipeline -> đánh giá -> xuất DXF/JSON/HTML 3D."""
import base64, json, os, sys
import cv2
import numpy as np
import ezdxf
from skimage.filters import threshold_sauvola

sys.path.insert(0, os.path.dirname(__file__))
import synth
import pipeline as P

HERE = os.path.dirname(os.path.abspath(__file__))
DATA, OUT = os.path.join(HERE, "data"), os.path.join(HERE, "output")
os.makedirs(DATA, exist_ok=True); os.makedirs(OUT, exist_ok=True)

# 1) Dữ liệu
page, gt_wall = synth.draw_plan()
photo = synth.simulate_photo(page)
cv2.imwrite(f"{DATA}/plan_clean.png", page); cv2.imwrite(f"{DATA}/gt_wall.png", gt_wall)
cv2.imwrite(f"{DATA}/photo.jpg", photo)
ppm = synth.PX_PER_M

# 2) Pipeline
R = P.run(photo, ppm)

# 3) Đánh giá
metrics = {}
metrics["wall_IoU (Sauvola tu cai)"] = P.iou(R["walls"], gt_wall)
_, otsu = cv2.threshold(R["gray"], 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)  # baseline: Otsu toàn cục, không làm phẳng sáng
metrics["wall_IoU (baseline Otsu)"] = P.iou(P.extract_walls(otsu), gt_wall)
sk = (R["even"] <= threshold_sauvola(R["even"], window_size=25, k=0.2)).astype(np.uint8) * 255
metrics["Sauvola tu cai vs skimage (pixel khop)"] = float((sk == R["ink"]).mean())

room_rows = []
for name, (x0, y0, x1, y1) in synth.ROOMS:
    g = np.zeros_like(gt_wall)
    cv2.rectangle(g, synth.m2px(x0, y0), synth.m2px(x1, y1), 255, -1)
    g[gt_wall > 0] = 0
    best = max(R["rooms"], key=lambda r: P.iou(r["mask"], g), default=None)
    gt_area = (x1 - x0) * (y1 - y0)
    room_rows.append({"name": name, "gt_area": gt_area,
                      "pred_area": round(best["area_m2"], 2) if best else None,
                      "IoU": round(P.iou(best["mask"], g), 3) if best else 0})
    if best is not None:
        best["name"] = name
metrics["so phong tim duoc / thuc te"] = f'{len(R["rooms"])} / {len(synth.ROOMS)}'
metrics["room_mIoU"] = float(np.mean([r["IoU"] for r in room_rows]))
metrics["tong thoi gian (ms)"] = round(sum(R["timing"].values()) * 1000, 1)

# 4) Xuất DXF (đơn vị mét)
def to_m(p):
    return ((p[0] - synth.OX) / ppm, -(p[1] - synth.OY) / ppm)

doc = ezdxf.new(); doc.units = ezdxf.units.M
msp = doc.modelspace()
for lay, col in [("WALL", 7), ("ROOM", 3), ("TEXT", 2)]:
    doc.layers.add(lay, color=col)
for wp in R["wall_polys"]:
    for ring in [wp["outer"], *wp["holes"]]:
        msp.add_lwpolyline([to_m(p) for p in ring], close=True, dxfattribs={"layer": "WALL"})
for r in R["rooms"]:
    msp.add_lwpolyline([to_m(p) for p in r["poly_px"]], close=True, dxfattribs={"layer": "ROOM"})
    cx, cy = to_m(r["centroid"])
    msp.add_text(f'{r.get("name", "?")} {r["area_m2"]:.1f}m2', height=0.25,
                 dxfattribs={"layer": "TEXT"}).set_placement((cx, cy))
doc.saveas(f"{OUT}/floorplan.dxf")

# 5) JSON cho viewer 3D
model = {
    "walls": [{"outer": [to_m(p) for p in w["outer"]], "holes": [[to_m(p) for p in h] for h in w["holes"]]}
              for w in R["wall_polys"]],
    "rooms": [{"name": r.get("name", "?"), "area": round(r["area_m2"], 1),
               "poly": [to_m(p) for p in r["poly_px"]], "c": to_m(r["centroid"])} for r in R["rooms"]],
}
json.dump(model, open(f"{OUT}/model.json", "w"), indent=1)

# 6) Ảnh từng bước
vis_page = photo.copy()
cv2.polylines(vis_page, [R["corners"].astype(np.int32)], True, (0, 255, 0), 6)
for c in R["corners"].astype(int):
    cv2.circle(vis_page, tuple(c), 18, (0, 0, 255), -1)
room_vis = R["flat"].copy()
pal = [(255, 179, 102), (102, 204, 255), (153, 230, 153), (204, 153, 255), (102, 153, 255), (255, 230, 102)]
overlay = room_vis.copy()
for i, r in enumerate(R["rooms"]):
    overlay[r["mask"] > 0] = pal[i % len(pal)]
room_vis = cv2.addWeighted(room_vis, 0.45, overlay, 0.55, 0)
hough_vis = cv2.cvtColor(R["walls"], cv2.COLOR_GRAY2BGR) // 3
for x1, y1, x2, y2 in R["segs"]:
    cv2.line(hough_vis, (x1, y1), (x2, y2), (0, 200, 255), 2)

def b64(img, w=520):
    s = w / img.shape[1]
    img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    return "data:image/jpeg;base64," + base64.b64encode(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])[1]).decode()

steps = [
    ("1. Ảnh chụp điện thoại", "Nghiêng, bóng tay, ánh sáng lệch, nền gỗ", photo),
    ("2. Tìm tờ giấy", "Canny → findContours → approxPolyDP (4 đỉnh)", vis_page),
    ("3. Nắn phối cảnh", "Homography 4 điểm → mặt phẳng trang", R["flat"]),
    ("4. Làm phẳng chiếu sáng", "Closing ước lượng nền, chia ảnh / nền", R["even"]),
    ("5. Nhị phân Sauvola (tự cài)", "Ảnh tích phân, cửa sổ 25, k = 0.2", R["ink"]),
    ("6. Tách tường", "Opening hình thái học xoá chữ, cung cửa, nét mảnh", R["walls"]),
    ("7. Vector hoá Hough", "Skeleton → HoughLinesP", hough_vis),
    ("8. Đóng cửa + tách phòng", "Closing theo phương + thành phần liên thông", room_vis),
]
cv2.imwrite(f"{OUT}/rooms.jpg", room_vis)

tpl = open(os.path.join(HERE, "viewer_template.html"), encoding="utf-8").read()
html = (tpl.replace("__MODEL__", json.dumps(model))
           .replace("__STEPS__", json.dumps([{"t": a, "d": b, "src": b64(c)} for a, b, c in steps]))
           .replace("__METRICS__", json.dumps(metrics, ensure_ascii=False))
           .replace("__ROOMS__", json.dumps(room_rows, ensure_ascii=False))
           .replace("__TIMING__", json.dumps({k: round(v * 1000, 1) for k, v in R["timing"].items()})))
open(f"{OUT}/demo.html", "w", encoding="utf-8").write(html)

print(json.dumps(metrics, indent=2, ensure_ascii=False))
print(json.dumps(room_rows, indent=2, ensure_ascii=False))
print("timing ms:", {k: round(v * 1000, 1) for k, v in R["timing"].items()})
