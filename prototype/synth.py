"""Sinh 1 bản vẽ mặt bằng tổng hợp + ground truth, rồi giả lập ảnh chụp điện thoại.

Đơn vị bản vẽ: mét. Tỉ lệ trên trang: PX_PER_M pixel / mét.
"""
import json
import cv2
import numpy as np

PX_PER_M = 60
PAGE_W, PAGE_H = 1000, 800
OX, OY = 140, 130  # gốc toạ độ của nhà trên trang (pixel)
EXT_T, INT_T = 0.25, 0.15  # độ dày tường ngoài / trong (m)

# Tường: (x1, y1, x2, y2, dày) theo mét, đường tâm tường
WALLS = [
    (0, 0, 12, 0, EXT_T), (12, 0, 12, 9, EXT_T), (12, 9, 0, 9, EXT_T), (0, 9, 0, 0, EXT_T),
    (5, 0, 5, 9, INT_T), (0, 6, 5, 6, INT_T), (5, 4.5, 12, 4.5, INT_T), (8.5, 4.5, 8.5, 9, INT_T),
]
# Cửa đi: (tường index, vị trí bắt đầu, bề rộng) dọc theo tường (m)
DOORS = [(4, 2.0, 1.0), (4, 6.8, 0.9), (5, 1.5, 0.9), (6, 1.0, 0.9), (7, 2.0, 0.8), (2, 8.5, 1.0)]
# Cửa sổ trên tường ngoài: (tường index, vị trí, bề rộng)
WINDOWS = [(0, 1.5, 2.0), (0, 8.0, 2.0), (1, 6.0, 1.5), (3, 4.0, 1.5)]
ROOMS = [  # tên, (x0, y0, x1, y1)
    ("Phong khach", (0, 0, 5, 6)), ("Bep", (0, 6, 5, 9)), ("Ngu 1", (5, 0, 12, 4.5)),
    ("WC", (5, 4.5, 8.5, 9)), ("Ngu 2", (8.5, 4.5, 12, 9)),
]


def m2px(x, y):
    return int(round(OX + x * PX_PER_M)), int(round(OY + y * PX_PER_M))


def _wall_rect(w):
    x1, y1, x2, y2, t = w
    h = t / 2
    return min(x1, x2) - h, min(y1, y2) - h, max(x1, x2) + h, max(y1, y2) + h


def _point_along(w, s):
    x1, y1, x2, y2, _ = w
    L = np.hypot(x2 - x1, y2 - y1)
    return x1 + (x2 - x1) * s / L, y1 + (y2 - y1) * s / L


def _cut(mask, w, s, width, value):
    """Cắt (value=0) một đoạn tường để tạo lỗ cửa."""
    t = w[4]
    a = _point_along(w, s)
    b = _point_along(w, s + width)
    x0, x1 = sorted([a[0], b[0]])
    y0, y1 = sorted([a[1], b[1]])
    if abs(w[0] - w[2]) < 1e-6:  # tường đứng
        x0, x1 = w[0] - t / 2 - 0.02, w[0] + t / 2 + 0.02
    else:
        y0, y1 = w[1] - t / 2 - 0.02, w[1] + t / 2 + 0.02
    cv2.rectangle(mask, m2px(x0, y0), m2px(x1, y1), value, -1)
    return (x0, y0, x1, y1)


def draw_plan():
    page = np.full((PAGE_H, PAGE_W), 255, np.uint8)
    gt_wall = np.zeros((PAGE_H, PAGE_W), np.uint8)
    for w in WALLS:
        x0, y0, x1, y1 = _wall_rect(w)
        cv2.rectangle(gt_wall, m2px(x0, y0), m2px(x1, y1), 255, -1)
    openings = []
    for wi, s, wd in DOORS:
        openings.append(("door", wi, _cut(gt_wall, WALLS[wi], s, wd, 0)))
    for wi, s, wd in WINDOWS:
        openings.append(("window", wi, _cut(gt_wall, WALLS[wi], s, wd, 0)))

    page[gt_wall > 0] = 25  # mực tường

    # Vẽ chi tiết mảnh (cửa sổ, cung cửa, chữ, đường kích thước) -> nhiễu cho thuật toán
    for kind, wi, (x0, y0, x1, y1) in openings:
        w = WALLS[wi]
        vertical = abs(w[0] - w[2]) < 1e-6
        if kind == "window":
            cv2.rectangle(page, m2px(x0, y0), m2px(x1, y1), 40, 1)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if vertical:
                cv2.line(page, m2px(cx, y0), m2px(cx, y1), 40, 1)
            else:
                cv2.line(page, m2px(x0, cy), m2px(x1, cy), 40, 1)
        else:
            r = int(((y1 - y0) if vertical else (x1 - x0)) * PX_PER_M)
            c = m2px(x0, y0) if not vertical else m2px(x1, y0)
            cv2.ellipse(page, c, (r, r), 0, 0, 90, 60, 1)
            cv2.line(page, c, (c[0], c[1] + r), 60, 1)

    font = cv2.FONT_HERSHEY_SIMPLEX
    for name, (x0, y0, x1, y1) in ROOMS:
        cx, cy = m2px((x0 + x1) / 2, (y0 + y1) / 2)
        area = (x1 - x0) * (y1 - y0)
        for i, txt in enumerate([name.upper(), f"{area:.1f} m2"]):
            (tw, th), _ = cv2.getTextSize(txt, font, 0.55, 1)
            cv2.putText(page, txt, (cx - tw // 2, cy + i * 24), font, 0.55, 30, 1, cv2.LINE_AA)
    # Đường kích thước phía trên + bên trái
    y = OY - 45
    cv2.line(page, m2px(0, 0)[0:1] + (y,), m2px(12, 0)[0:1] + (y,), 50, 1)
    for xm in (0, 5, 12):
        x = m2px(xm, 0)[0]
        cv2.line(page, (x, y - 8), (x, y + 8), 50, 1)
    cv2.putText(page, "5000", (m2px(2.1, 0)[0], y - 8), font, 0.45, 40, 1, cv2.LINE_AA)
    cv2.putText(page, "7000", (m2px(8.1, 0)[0], y - 8), font, 0.45, 40, 1, cv2.LINE_AA)
    # Khung tên
    cv2.rectangle(page, (30, 30), (PAGE_W - 30, PAGE_H - 30), 60, 2)
    cv2.rectangle(page, (PAGE_W - 330, PAGE_H - 110), (PAGE_W - 30, PAGE_H - 30), 60, 1)
    cv2.putText(page, "MAT BANG TANG 1 - TL 1:100", (PAGE_W - 318, PAGE_H - 75), font, 0.5, 30, 1, cv2.LINE_AA)
    cv2.putText(page, "Nhom MSE - IVP 2026", (PAGE_W - 318, PAGE_H - 48), font, 0.45, 30, 1, cv2.LINE_AA)
    return page, gt_wall


def simulate_photo(page, seed=7):
    """Đặt tờ giấy lên mặt bàn gỗ, nghiêng phối cảnh, đổ bóng, nhiễu, mờ."""
    rng = np.random.default_rng(seed)
    H, W = 1200, 1600
    # Nền gỗ
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    grain = np.sin(xx / 9 + 3 * np.sin(yy / 140)) * 12 + rng.normal(0, 6, (H, W))
    bg = np.dstack([90 + grain, 120 + grain, 160 + grain]).clip(0, 255).astype(np.uint8)

    src = np.float32([[0, 0], [PAGE_W, 0], [PAGE_W, PAGE_H], [0, PAGE_H]])
    dst = np.float32([[260, 230], [1380, 150], [1450, 1020], [170, 1080]])
    M = cv2.getPerspectiveTransform(src, dst)
    paper = cv2.cvtColor(page, cv2.COLOR_GRAY2BGR)
    paper = (paper.astype(np.float32) * np.array([0.97, 0.99, 1.0])).astype(np.uint8)  # giấy hơi ngả vàng
    warped = cv2.warpPerspective(paper, M, (W, H))
    mask = cv2.warpPerspective(np.full((PAGE_H, PAGE_W), 255, np.uint8), M, (W, H))
    img = np.where(mask[..., None] > 0, warped, bg).astype(np.float32)

    # Ánh sáng không đều + bóng điện thoại/tay ở góc
    light = 0.75 + 0.35 * (xx / W) * (1 - 0.4 * yy / H)
    shadow = 1 - 0.45 * np.exp(-(((xx - 450) / 260) ** 2 + ((yy - 950) / 200) ** 2))
    img *= (light * shadow)[..., None]
    img += rng.normal(0, 5, img.shape)
    img = cv2.GaussianBlur(img.clip(0, 255).astype(np.uint8), (3, 3), 0.8)
    ok, enc = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return cv2.imdecode(enc, cv2.IMREAD_COLOR)


def ground_truth_json():
    return {
        "px_per_m": PX_PER_M, "origin_px": [OX, OY],
        "rooms": [{"name": n, "area_m2": (b[2] - b[0]) * (b[3] - b[1])} for n, b in ROOMS],
    }


if __name__ == "__main__":
    import os, sys
    out = sys.argv[1] if len(sys.argv) > 1 else "data"
    os.makedirs(out, exist_ok=True)
    page, gt = draw_plan()
    cv2.imwrite(f"{out}/plan_clean.png", page)
    cv2.imwrite(f"{out}/gt_wall.png", gt)
    cv2.imwrite(f"{out}/photo.jpg", simulate_photo(page))
    json.dump(ground_truth_json(), open(f"{out}/gt.json", "w"), indent=2)
    print("saved to", out)
