"""Đọc nhãn model.svg của CubiCasa5K -> mask tường, danh sách phòng (giống cách loader chính thức:
toạ độ polygon dùng trực tiếp trên ảnh F1_scaled.png)."""
import xml.etree.ElementTree as ET
import cv2
import numpy as np

NS = "{http://www.w3.org/2000/svg}"


def _pts(poly):
    v = [float(x) for x in poly.get("points").replace(",", " ").split()]
    return np.array(v, np.float32).reshape(-1, 2)


def load_gt(svg_path, shape):
    h, w = shape[:2]
    root = ET.parse(svg_path).getroot()
    wall = np.zeros((h, w), np.uint8)
    rooms = []
    for g in root.iter(NS + "g"):
        cls = (g.get("class") or "").split()
        if not cls:
            continue
        poly = g.find(NS + "polygon")  # polygon con trực tiếp đầu tiên = hình dạng đối tượng
        if poly is None or not poly.get("points"):
            continue
        p = np.round(_pts(poly)).astype(np.int32)
        if cls[0] == "Wall":
            cv2.fillPoly(wall, [p], 255)
        elif cls[0] == "Space" and len(cls) > 1 and cls[1] not in ("Outdoor", "Undefined"):
            m = np.zeros((h, w), np.uint8)
            cv2.fillPoly(m, [p], 255)
            rooms.append({"type": cls[1], "mask": m})
    for r in rooms:  # phần sàn = vùng phòng trừ tường
        r["mask"][wall > 0] = 0
    return wall, rooms
