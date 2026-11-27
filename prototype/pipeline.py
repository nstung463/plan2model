"""Pipeline: ảnh chụp bản vẽ -> nắn phẳng -> nhị phân -> tường -> phòng -> vector (DXF/JSON).

Các bước dùng kiến thức nhiều bài học: biên (Canny), contour + approxPolyDP, homography,
hình thái học (top-hat/closing/opening), ngưỡng thích nghi Sauvola (TỰ CÀI ĐẶT bằng ảnh tích phân),
thành phần liên thông, Hough (HoughLinesP) để vector hoá tường.
"""
import time
import cv2
import numpy as np

OUT_W, OUT_H = 1000, 800  # kích thước trang sau khi nắn (biết tỉ lệ khổ giấy)


# ---------- 1. Tìm tờ giấy + nắn phối cảnh ----------
def order_corners(pts):
    pts = pts.reshape(4, 2).astype(np.float32)
    s, d = pts.sum(1), np.diff(pts, axis=1).ravel()
    return np.float32([pts[s.argmin()], pts[d.argmin()], pts[s.argmax()], pts[d.argmax()]])


def find_page(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    scale = 800 / max(gray.shape)
    small = cv2.resize(gray, None, fx=scale, fy=scale)
    small = cv2.GaussianBlur(small, (5, 5), 0)
    edges = cv2.Canny(small, 40, 120)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8))
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:5]:
        approx = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
        if len(approx) == 4 and cv2.contourArea(approx) > 0.2 * small.size:
            return order_corners(approx / scale), edges
    raise RuntimeError("Khong tim thay to giay 4 goc")


def rectify(img, corners):
    dst = np.float32([[0, 0], [OUT_W, 0], [OUT_W, OUT_H], [0, OUT_H]])
    H = cv2.getPerspectiveTransform(corners, dst)
    return cv2.warpPerspective(img, H, (OUT_W, OUT_H), flags=cv2.INTER_CUBIC)


# ---------- 2. Làm phẳng chiếu sáng + nhị phân ----------
def flatten_illumination(gray):
    """Ước lượng nền bằng closing (xoá nét mực), chia ảnh cho nền."""
    bg = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
    bg = cv2.GaussianBlur(bg, (31, 31), 0)
    return np.clip(gray.astype(np.float32) / (bg.astype(np.float32) + 1) * 255, 0, 255).astype(np.uint8)


def sauvola(gray, window=25, k=0.2, R=128.0):
    """TỰ CÀI ĐẶT ngưỡng Sauvola: T = m * (1 + k*(s/R - 1)), dùng ảnh tích phân O(1)/pixel."""
    g = gray.astype(np.float64)
    ii = cv2.integral(g)
    ii2 = cv2.integral(g * g)
    r = window // 2
    h, w = g.shape
    y0 = np.clip(np.arange(h) - r, 0, h); y1 = np.clip(np.arange(h) + r + 1, 0, h)
    x0 = np.clip(np.arange(w) - r, 0, w); x1 = np.clip(np.arange(w) + r + 1, 0, w)
    Y0, X0 = np.meshgrid(y0, x0, indexing="ij"); Y1, X1 = np.meshgrid(y1, x1, indexing="ij")
    n = (Y1 - Y0) * (X1 - X0)
    S = ii[Y1, X1] - ii[Y0, X1] - ii[Y1, X0] + ii[Y0, X0]
    S2 = ii2[Y1, X1] - ii2[Y0, X1] - ii2[Y1, X0] + ii2[Y0, X0]
    m = S / n
    s = np.sqrt(np.maximum(S2 / n - m * m, 0))
    T = m * (1 + k * (s / R - 1))
    return ((g <= T) * 255).astype(np.uint8)  # mực = 255


# ---------- 3. Tách tường ----------
def extract_walls(ink, min_thick=7, min_area=400):
    """Tường = nét dày. Opening với phần tử cấu trúc ~ độ dày tối thiểu sẽ xoá chữ, cung cửa, nét kích thước."""
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (min_thick, min_thick))
    walls = cv2.morphologyEx(ink, cv2.MORPH_OPEN, k)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(walls)
    keep_ids = np.zeros(n, bool)
    keep_ids[1:] = stats[1:, cv2.CC_STAT_AREA] > min_area
    return (keep_ids[lab] * 255).astype(np.uint8)


def fill_hollow_walls(ink, r_max=14, min_elong=6.0):
    """Tường rỗng (2 nét viền song song): vùng trắng bị mực bao kín, hẹp (bán kính nội tiếp <= r_max)
    và dài (diện tích / r^2 lớn) -> lấp đầy."""
    free = cv2.bitwise_not(ink)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(free, connectivity=4)
    dt = cv2.distanceTransform(free, cv2.DIST_L2, 3)
    rmax = np.zeros(n, np.float32)
    np.maximum.at(rmax, lab.ravel(), dt.ravel())
    h, w = ink.shape
    x, y, bw, bh, area = stats.T
    inner = (x > 0) & (y > 0) & (x + bw < w) & (y + bh < h)
    elong = area / np.maximum(rmax, 1) ** 2
    ok = inner & (rmax >= 1.5) & (rmax <= r_max) & (elong >= min_elong) & (np.maximum(bw, bh) > 6 * rmax)
    ok[0] = False
    return np.where(ok[lab], 255, ink).astype(np.uint8)


def wall_candidates(bgr, use_flatten=True, use_hollow=True, use_color=True, r_max=14):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    ink = sauvola(flatten_illumination(gray) if use_flatten else gray)
    ink = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))  # nối nét gạch chéo
    if use_color:  # tường tô màu đậm (vàng/đỏ/xám đậm)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        ink |= (((hsv[..., 1] > 110) & (hsv[..., 2] > 90)) * 255).astype(np.uint8)
    if use_hollow:
        ink = fill_hollow_walls(ink, r_max=r_max)
    return ink


def estimate_thickness(mask, t_min=8.0, t_max=40.0):
    """Ước lượng độ dày tường (robust): opening nhẹ bỏ nét mảnh, lấy TRUNG VỊ của nửa trên
    distance transform (gần đường tâm nét), kẹp [t_min, t_max] để chặn khối đặc lớn (cầu thang, nội thất)."""
    m = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    dt = cv2.distanceTransform(m, cv2.DIST_L2, 3)
    v = dt[m > 0]
    if v.size == 0:
        return 12.0
    v = v[v > np.percentile(v, 50)]
    return float(np.clip(2 * np.median(v), t_min, t_max))


def extract_walls_adaptive(cand, ratio=0.33, kmin=5):
    T = estimate_thickness(cand)
    k = max(kmin, int(round(T * ratio)) | 1)
    w = extract_walls(cand, k)
    return w, T, k


# ---------- 4. Đóng lỗ cửa + tách phòng ----------
def segment_rooms(walls, px_per_m, max_door_m=2.2):  # cửa đi ~0.8-1m, cửa sổ tới ~2m
    L = int(max_door_m * px_per_m)
    closed = walls.copy()
    for kshape in [(L, 1), (1, L)]:  # closing theo phương ngang rồi dọc: nối 2 đầu tường cùng phương
        closed = cv2.bitwise_or(closed, cv2.morphologyEx(walls, cv2.MORPH_CLOSE,
                                                         cv2.getStructuringElement(cv2.MORPH_RECT, kshape)))
    free = cv2.bitwise_not(closed)
    n, lab, stats, cents = cv2.connectedComponentsWithStats(free, connectivity=4)
    h, w = free.shape
    rooms = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if x == 0 or y == 0 or x + bw >= w or y + bh >= h:
            continue  # vùng ngoài nhà (chạm biên)
        a_m2 = area / px_per_m ** 2
        if a_m2 < 1.5:
            continue
        mask = (lab == i).astype(np.uint8) * 255
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        poly = cv2.approxPolyDP(max(cnts, key=cv2.contourArea), 3, True).reshape(-1, 2)
        rooms.append({"area_m2": a_m2, "poly_px": poly, "mask": mask, "centroid": cents[i]})
    return closed, rooms


# ---------- 5. Vector hoá tường ----------
def wall_polygons(walls):
    """Contour có lỗ (RETR_CCOMP) -> đa giác tường (ngoài) + lỗ (trong)."""
    cnts, hier = cv2.findContours(walls, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    polys = []
    if hier is None:
        return polys
    hier = hier[0]
    for i, c in enumerate(cnts):
        if hier[i][3] != -1 or cv2.contourArea(c) < 100:
            continue
        outer = cv2.approxPolyDP(c, 1.5, True).reshape(-1, 2)
        holes, j = [], hier[i][2]
        while j != -1:
            if cv2.contourArea(cnts[j]) > 50:
                holes.append(cv2.approxPolyDP(cnts[j], 1.5, True).reshape(-1, 2))
            j = hier[j][0]
        polys.append({"outer": outer, "holes": holes})
    return polys


def hough_segments(walls):
    skel = cv2.ximgproc.thinning(walls) if hasattr(cv2, "ximgproc") else walls
    lines = cv2.HoughLinesP(skel, 1, np.pi / 180, 40, minLineLength=30, maxLineGap=5)
    return [] if lines is None else lines.reshape(-1, 4)


# ---------- 6. Đánh giá ----------
def iou(a, b):
    a, b = a > 0, b > 0
    return float((a & b).sum() / max((a | b).sum(), 1))


def run(img, px_per_m):
    t = {}
    t0 = time.perf_counter()
    corners, edges = find_page(img); t["detect_page"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    flat = rectify(img, corners); t["rectify"] = time.perf_counter() - t0
    gray = cv2.cvtColor(flat, cv2.COLOR_BGR2GRAY)
    t0 = time.perf_counter()
    even = flatten_illumination(gray); t["illumination"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    ink = sauvola(even); t["sauvola"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    walls = extract_walls(ink); t["walls"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    closed, rooms = segment_rooms(walls, px_per_m); t["rooms"] = time.perf_counter() - t0
    polys = wall_polygons(walls)
    segs = hough_segments(walls)
    return dict(corners=corners, edges=edges, flat=flat, gray=gray, even=even, ink=ink,
                walls=walls, closed=closed, rooms=rooms, wall_polys=polys, segs=segs, timing=t)
