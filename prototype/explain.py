"""Dựng phần 'Quá trình xử lý' cho app: mỗi bước gồm ảnh trực quan + lời giải thích + vài con số.

Đầu vào là res["dbg"] do core.process() giữ lại. Không thay đổi kết quả của pipeline.
"""
import cv2
import numpy as np
import pandas as pd

import pipeline as P
from tech import tech_for

INK = (30, 30, 30)
RED = (60, 60, 230)        # BGR
GREEN = (60, 180, 60)
ORANGE = (40, 150, 255)
BLUE = (220, 140, 40)
PALETTE = [(102, 179, 255), (255, 204, 102), (153, 230, 153), (255, 153, 204), (255, 153, 102), (102, 230, 255),
           (204, 204, 102), (180, 140, 255)]


# ---------------- tiện ích vẽ ----------------
def rgb(im):
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB) if im.ndim == 3 else im


def paint(shape, layers):
    """Nền trắng, vẽ lần lượt từng (mask, màu BGR)."""
    out = np.full((*shape[:2], 3), 255, np.uint8)
    for m, c in layers:
        out[m > 0] = c
    return out


def heat(a, cmap=cv2.COLORMAP_INFERNO):
    a = a.astype(np.float32)
    a = (a - a.min()) / max(float(a.max() - a.min()), 1e-6)
    return cv2.applyColorMap((a * 255).astype(np.uint8), cmap)


def focus_box(change, frac=0.33):
    """Ô vuông (y0, y1, x0, x1) chứa nhiều pixel thay đổi nhất, để phóng to cho dễ nhìn."""
    h, w = change.shape
    s = max(64, int(min(h, w) * frac))
    dens = cv2.boxFilter((change > 0).astype(np.float32), -1, (s, s), normalize=False, borderType=cv2.BORDER_CONSTANT)
    if dens.max() <= 0:
        return None
    cy, cx = np.unravel_index(np.argmax(dens), dens.shape)
    y0 = int(np.clip(cy - s // 2, 0, h - s)); x0 = int(np.clip(cx - s // 2, 0, w - s))
    return y0, y0 + s, x0, x0 + s


def crop(im, box):
    y0, y1, x0, x1 = box
    return cv2.resize(im[y0:y1, x0:x1], None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)


def mark_box(im, box, color=(0, 200, 255)):
    out = im.copy()
    y0, y1, x0, x1 = box
    cv2.rectangle(out, (x0, y0), (x1, y1), color, max(2, im.shape[1] // 300))
    return out


def thick(im):
    return max(2, im.shape[1] // 350)


def sauvola_threshold(gray, window=25, k=0.2, R=128.0):
    """Bản đồ ngưỡng T(x, y) của Sauvola, chỉ để hiển thị (cùng công thức với pipeline.sauvola)."""
    g = gray.astype(np.float32)
    m = cv2.boxFilter(g, -1, (window, window), borderType=cv2.BORDER_REPLICATE)
    m2 = cv2.boxFilter(g * g, -1, (window, window), borderType=cv2.BORDER_REPLICATE)
    s = np.sqrt(np.maximum(m2 - m * m, 0))
    return m * (1 + k * (s / R - 1)), m, s


# ---------------- các bước ----------------
def build_steps(res):
    d = res["dbg"]
    work, walls, rooms, ppm = d["work"], d["walls"], res["rooms"], d["ppm"]
    steps = []

    def add(key, short, title, what, how, why, images, stats=(), chart=None, chart_caption=None):
        steps.append(dict(key=key, short=short, title=title, what=what, how=how, why=why,
                          images=[(c, rgb(i)) for c, i in images], stats=list(stats),
                          chart=chart, chart_caption=chart_caption))

    # 1. Ảnh đầu vào
    h0, w0 = d["input"].shape[:2]
    add("input", "Ảnh gốc", "Ảnh đầu vào",
        "Đây là ảnh người dùng đưa vào: ảnh chụp tờ bản vẽ bằng điện thoại, hoặc ảnh scan/ảnh xuất từ phần mềm.",
        "Máy đọc ảnh thành một ma trận điểm ảnh. Mỗi điểm có 3 giá trị màu xanh dương, xanh lá, đỏ, từ 0 đến 255.",
        "Ảnh chụp thật thường bị nghiêng, sáng không đều, có bóng tay, có nhiễu. Các bước sau sẽ xử lý lần lượt từng vấn đề đó.",
        [("Ảnh gốc", d["input"])],
        [("Kích thước", f"{w0} × {h0} px"), ("Loại ảnh", "Ảnh chụp" if d["photo_mode"] else "Ảnh scan")])

    # 2–3. Tìm tờ giấy + nắn phối cảnh
    if d["photo_mode"]:
        c = d["corners"]
        det = d["input"].copy()
        cv2.polylines(det, [c.astype(np.int32)], True, (0, 220, 0), thick(det) * 2)
        r = max(8, w0 // 70)
        for i, (x, y) in enumerate(c):
            cv2.circle(det, (int(x), int(y)), r, (0, 0, 255), -1)
            cv2.putText(det, str(i + 1), (int(x) + r, int(y) - r), cv2.FONT_HERSHEY_SIMPLEX, r / 12, (0, 0, 255), max(2, r // 4))
        edges = cv2.cvtColor(255 - d["edges"], cv2.COLOR_GRAY2BGR)
        add("page", "Tìm tờ giấy", "Tìm tờ giấy trong ảnh",
            "Máy tìm 4 góc của tờ giấy để biết phần nào là bản vẽ, phần nào là mặt bàn.",
            "Bước 1: dùng bộ lọc Canny để tìm cạnh, tức là những chỗ độ sáng đổi đột ngột (ảnh trái).\n\n"
            "Bước 2: nối các cạnh thành đường viền khép kín, lấy đường viền lớn nhất.\n\n"
            "Bước 3: làm đơn giản đường viền đó bằng thuật toán Douglas–Peucker. Nếu còn đúng 4 đỉnh và chiếm hơn 20% ảnh thì đó là tờ giấy.",
            "Nếu không cắt riêng tờ giấy ra thì vân gỗ trên mặt bàn cũng bị coi là nét vẽ.",
            [("Bản đồ cạnh (Canny)", edges), ("4 góc tìm được", det)],
            [("Số đỉnh", "4"), ("Diện tích tờ giấy", f"{cv2.contourArea(c) / (w0 * h0) * 100:.0f}% ảnh")])

        H, W = work.shape[:2]
        Hm = cv2.getPerspectiveTransform(c, np.float32([[0, 0], [W, 0], [W, H], [0, H]]))
        grid = d["input"].copy()
        inv = np.linalg.inv(Hm)
        for t in np.linspace(0, 1, 9):  # lưới vuông trên ảnh thẳng, chiếu ngược lên ảnh nghiêng
            for a, b in [((t * W, 0), (t * W, H)), ((0, t * H), (W, t * H))]:
                pts = cv2.perspectiveTransform(np.float32([[a, b]]), inv)[0].astype(np.int32)
                cv2.line(grid, tuple(pts[0]), tuple(pts[1]), (0, 200, 255), thick(grid))
        mat = pd.DataFrame(Hm / Hm[2, 2]).round(4)
        mat.columns = ["", " ", "  "]
        add("rectify", "Nắn thẳng", "Nắn thẳng tờ giấy (biến đổi phối cảnh)",
            "Kéo tờ giấy đang nằm nghiêng về thành hình chữ nhật, giống như chụp thẳng từ trên xuống.",
            "Từ 4 cặp điểm (4 góc trên ảnh ↔ 4 góc hình chữ nhật), máy giải ra một ma trận 3×3 gọi là ma trận homography H. "
            "Sau đó mỗi điểm ảnh được dời về vị trí mới theo ma trận này.\n\n"
            "Ảnh bên trái vẽ lưới ô vuông: trên ảnh gốc các ô bị méo, sau khi nắn thì các ô vuông đều trở lại.",
            "Nếu không nắn thì tường bị xiên, phòng hình chữ nhật thành hình thang và diện tích tính sai.",
            [("Lưới vuông nhìn trên ảnh nghiêng", grid), ("Sau khi nắn thẳng", work)],
            [("Kích thước sau nắn", f"{W} × {H} px")], chart=mat, chart_caption="Ma trận homography H")

    # 4. Làm đều ánh sáng
    gray, even = d["gray"], d["even"]
    bg = cv2.GaussianBlur(cv2.morphologyEx(gray, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))),
                          (31, 31), 0)
    hh = gray.shape[0]
    row = hh // 8 + int(np.argmax(bg[hh // 8: hh - hh // 8].std(axis=1)))  # hàng có nền thay đổi nhiều nhất
    xs = np.arange(0, gray.shape[1], max(1, gray.shape[1] // 400))
    prof = pd.DataFrame({"x": xs, "Ảnh xám": gray[row, xs].astype(int), "Nền ước lượng": bg[row, xs].astype(int),
                         "Sau khi làm đều": even[row, xs].astype(int)}).set_index("x")
    gl = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    cv2.line(gl, (0, row), (gray.shape[1], row), (0, 200, 255), thick(gl))
    add("light", "Ánh sáng", "Làm đều ánh sáng" + ("" if d["use_flatten"] else " (đang TẮT)"),
        "Xoá chỗ sáng chỗ tối và bóng tay, để nền giấy trắng đều ở mọi chỗ.",
        "Bước 1: đổi ảnh sang ảnh xám.\n\n"
        "Bước 2: ước lượng 'nền giấy'. Máy dùng phép đóng hình thái (closing) với một hình tròn 41 px: nét mực mảnh hơn hình tròn nên bị xoá đi, "
        "chỉ còn lại độ sáng của giấy (ảnh giữa, màu càng sáng là giấy càng sáng).\n\n"
        "Bước 3: lấy ảnh chia cho nền: I' = 255 · I / nền. Chỗ nào tối thì được kéo sáng lên tương ứng.",
        "Bước đen trắng phía sau sẽ nhầm vùng bóng tối là mực nếu không làm đều trước.",
        [("Ảnh xám (đường vàng: hàng dùng để vẽ biểu đồ bên dưới)", gl), ("Nền giấy ước lượng", heat(bg)), ("Sau khi làm đều", even)],
        [("Độ sáng nền thấp nhất", f"{int(bg.min())}"), ("Độ sáng nền cao nhất", f"{int(bg.max())}")],
        chart=prof, chart_caption="Độ sáng dọc theo đường vàng: đường nền lên xuống theo bóng, sau khi chia thì nền phẳng gần 255, chỉ nét mực tụt xuống")

    # 5. Sauvola
    T, m, s = sauvola_threshold(even)
    otsu_t, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    add("binar", "Đen trắng", "Đổi sang đen trắng bằng ngưỡng Sauvola (tự cài đặt)",
        "Quyết định mỗi điểm ảnh là mực (đen) hay giấy (trắng).",
        f"Cách thông thường (Otsu) chọn **một ngưỡng chung** cho cả ảnh, ở đây là {otsu_t:.0f}. Chỗ nào tối hơn ngưỡng là mực. "
        "Vì vậy vùng bị bóng đổ biến thành một mảng đen (ảnh trái).\n\n"
        "Sauvola thì tính **ngưỡng riêng cho từng điểm**, dựa vào ô 25×25 xung quanh nó: T = m · (1 + k · (s/R − 1)), "
        "với m là độ sáng trung bình, s là độ lệch chuẩn của ô đó, k = 0,2 và R = 128. Ảnh giữa là bản đồ ngưỡng T.\n\n"
        "Nhóm tự viết thuật toán này, dùng ảnh tích phân để tính trung bình của mỗi ô chỉ với 4 phép cộng trừ. "
        "So với hàm có sẵn của scikit-image thì kết quả khớp 99,99% điểm ảnh.",
        "Nét bản vẽ có đậm có nhạt, giấy có chỗ sáng chỗ tối, nên một ngưỡng chung không dùng được.",
        [(f"Otsu, một ngưỡng chung = {otsu_t:.0f}", 255 - otsu), ("Bản đồ ngưỡng Sauvola T(x,y)", heat(T)),
         ("Kết quả Sauvola", 255 - d["ink"])],
        [("Ngưỡng Otsu", f"{otsu_t:.0f}"), ("Ngưỡng Sauvola", f"{np.percentile(T, 5):.0f} – {np.percentile(T, 95):.0f}"),
         ("Tỉ lệ điểm là mực", f"{(d['ink'] > 0).mean() * 100:.1f}%")])

    if d["unet"]:
        add("unet", "U-Net", "Tìm tường bằng mạng U-Net",
            "Ở chế độ so sánh, mask tường được lấy từ mạng học sâu U-Net thay cho các bước hình thái học.",
            "U-Net (encoder ResNet-18) được huấn luyện trên 300 ảnh CubiCasa5K, đầu ra là xác suất mỗi điểm là tường. "
            "Ngưỡng xác suất được chọn trên tập val.",
            "Dùng để so sánh: phương pháp cổ điển của nhóm đứng ở đâu so với học sâu.",
            [("Mask tường U-Net", 255 - walls)])
    else:
        # 6. Kênh màu
        if d["use_color"] and "color" in d and (d["color"] > 0).mean() > 0.001:
            col = d["color"]
            add("color", "Kênh màu", "Lấy thêm tường tô màu",
                "Một số bản vẽ tô tường bằng màu (vàng, đỏ, xám đậm). Bước này lấy thêm những điểm có màu đậm.",
                "Đổi ảnh sang hệ màu HSV (sắc độ, độ bão hoà, độ sáng). Điểm nào có độ bão hoà S > 110 và độ sáng V > 90 "
                "thì được tính là tường, rồi gộp vào kết quả đen trắng.",
                "Tường màu vàng nhạt khi đổi sang ảnh xám có thể sáng gần bằng giấy, Sauvola sẽ bỏ sót.",
                [("Điểm màu đậm (cam)", paint(col.shape, [(d["ink_closed"], (200, 200, 200)), (col, ORANGE)]))],
                [("Điểm màu được thêm", f"{(col > 0).mean() * 100:.1f}%")])

        # 7. Lấp tường rỗng
        pre, cand = d["pre_hollow"], d["cand"]
        added = cv2.subtract(cand, pre)
        nfill = cv2.connectedComponents(added)[0] - 1
        vis = paint(cand.shape, [(pre, INK), (added, RED)])
        box = focus_box(added) if nfill > 0 else None
        imgs = [("Trước khi lấp", 255 - pre), ("Sau khi lấp (đỏ: phần được tô)", mark_box(vis, box) if box else vis)]
        if box:
            imgs.append(("Phóng to vùng có nhiều thay đổi", crop(vis, box)))
        add("hollow", "Lấp tường rỗng", "Lấp tường rỗng" + ("" if d["use_hollow"] else " (đang TẮT)"),
            "Nhiều bản vẽ không tô kín tường mà chỉ vẽ 2 đường viền song song. Bước này tô kín phần ruột ở giữa.",
            "Máy xét từng vùng trắng bị mực bao kín. Với mỗi vùng, phép biến đổi khoảng cách (distance transform) cho biết "
            "điểm sâu nhất cách mép bao xa, gọi là r (bằng nửa bề rộng của khe).\n\n"
            "Một vùng được coi là 'ruột tường' nếu nó **hẹp** (1,5 ≤ r ≤ 14 px), **dài** (diện tích / r² ≥ 6, cạnh dài > 6r) "
            "và **không chạm mép ảnh**. Phòng thì rộng, không thoả điều kiện hẹp, nên không bị tô nhầm.",
            "Bước giữ nét dày phía sau sẽ xoá mất tường rỗng vì mỗi đường viền rất mảnh. "
            "Trên tập test, tắt bước này làm điểm tìm tường giảm mạnh nhất trong các khối.",
            imgs,
            [("Số khe được lấp", f"{nfill}"), ("Điểm ảnh được thêm", f"{(added > 0).sum():,}".replace(",", "."))])

        # 8. Opening
        k = d["k"]
        ker = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
        eroded = cv2.erode(cand, ker)
        removed = cv2.subtract(cand, walls)
        vis = paint(cand.shape, [(removed, (170, 170, 250)), (walls, INK)])
        box = focus_box(removed)
        imgs = [(f"Sau bước co (erosion {k}×{k})", 255 - eroded),
                ("Sau bước giãn: đen là tường, hồng là nét bị xoá", mark_box(vis, box) if box else vis)]
        if box:
            imgs.append(("Phóng to", crop(vis, box)))
        nwall = cv2.connectedComponents(walls)[0] - 1
        add("opening", "Giữ nét dày", "Giữ lại nét dày: phép mở (opening)",
            "Tường là nét dày nhất trên bản vẽ. Bước này xoá chữ, ký hiệu cửa, nội thất, đường kích thước, chỉ giữ tường.",
            f"Phép mở gồm 2 bước với một ô vuông {k}×{k} px:\n\n"
            f"1. **Co** (erosion): một điểm chỉ còn là mực nếu cả ô {k}×{k} quanh nó đều là mực. Nét nào mảnh hơn {k} px biến mất hoàn toàn, "
            "nét dày thì chỉ bị gọt mỏng đi (ảnh trái).\n\n"
            "2. **Giãn** (dilation): nở phần còn lại ra đúng bằng ô đó, trả nét dày về độ dày cũ.\n\n"
            "Cuối cùng bỏ những mảnh nhỏ hơn 400 điểm ảnh. "
            f"Kích thước k = 7 được chọn bằng cách thử nhiều giá trị trên tập val.",
            "Nếu để chữ và nét cửa lại thì phòng sẽ bị cắt vụn và mô hình 3D có tường giả.",
            imgs,
            [("Kích thước ô k", f"{k} px"), ("Mực bị xoá", f"{(removed > 0).sum() / max((cand > 0).sum(), 1) * 100:.0f}%"),
             ("Số mảnh tường", f"{nwall}")])

    # 9. Tỉ lệ
    dt = cv2.distanceTransform(walls, cv2.DIST_L2, 3)
    ys, xs = np.nonzero(walls)
    sc = paint(walls.shape, [(walls, INK)])
    if xs.size:
        x0, x1 = int(xs.min()), int(xs.max())
        yb = min(walls.shape[0] - 10, int(ys.max()) + max(15, walls.shape[0] // 40))
        cv2.line(sc, (x0, yb), (x1, yb), RED, thick(sc))
        for x in (x0, x1):
            cv2.line(sc, (x, yb - 15), (x, yb + 15), RED, thick(sc))
    mode = d["scale_mode"]
    if mode == "width":
        how = (f"Người dùng nhập bề rộng thật của nhà là {d['house_width_m']} m. Máy đo bề rộng phần tường trên ảnh "
               f"(đường đỏ) là {x1 - x0 + 1} px, suy ra {ppm:.1f} px tương ứng 1 m.")
    elif mode == "wall":
        how = (f"Máy đo độ dày tường trên ảnh bằng distance transform (ảnh phải: càng sáng là càng xa mép tường, "
               f"nên đường sáng nhất là tim tường). Độ dày đo được khoảng {d['thick_px']:.1f} px. "
               f"Giả định tường thật dày {d['wall_m']} m, suy ra {ppm:.1f} px/m.")
    else:
        how = f"Người dùng nhập trực tiếp {ppm:.1f} px/m."
    add("scale", "Tỉ lệ", "Đổi từ điểm ảnh sang mét",
        "Tìm xem 1 mét ngoài đời bằng bao nhiêu điểm ảnh, để tính diện tích và chiều cao mô hình 3D theo mét.",
        how + "\n\nCó 3 cách: nhập bề rộng nhà, giả định độ dày tường, hoặc nhập thẳng số px/m.",
        "Không có tỉ lệ thì chỉ biết phòng rộng bao nhiêu điểm ảnh, không biết bao nhiêu mét vuông.",
        [("Bề rộng tường trên ảnh", sc), ("Khoảng cách tới mép tường", heat(dt, cv2.COLORMAP_VIRIDIS))],
        [("Tỉ lệ", f"{ppm:.1f} px/m"), ("Độ dày tường đo được", f"{d['thick_px']:.1f} px"),
         ("1 điểm ảnh", f"{100 / ppm:.1f} cm")])

    # 10. Bịt khe cửa
    closed = d["closed"]
    L = int(d["door_m"] * ppm)
    bridge = cv2.subtract(closed, walls)
    vis = paint(walls.shape, [(walls, INK), (bridge, GREEN)])
    box = focus_box(bridge)
    imgs = [("Tường + đoạn bịt khe (xanh lá)", mark_box(vis, box) if box else vis)]
    if box:
        imgs.append(("Phóng to", crop(vis, box)))
    add("doors", "Bịt khe cửa", "Bịt các khe cửa",
        "Chỗ cửa đi, cửa sổ là khe hở trên tường. Phải bịt lại thì mỗi phòng mới thành một vùng kín.",
        f"Máy dùng phép đóng (closing = giãn rồi co) với một **đoạn thẳng** dài L = {d['door_m']} m × {ppm:.1f} px/m ≈ {L} px, "
        "làm 2 lần: một lần đoạn nằm ngang, một lần đoạn đứng.\n\n"
        f"Hai đầu tường cùng nằm trên một đường thẳng, cách nhau ít hơn {L} px, sẽ được nối lại (phần xanh lá). "
        "Dùng đoạn thẳng thay vì ô vuông để không làm dày các bức tường khác.",
        f"Khe nhỏ hơn {d['door_m']} m là cửa thì cần bịt. Khe lớn hơn thường là lối thông giữa 2 không gian mở nên giữ nguyên.",
        imgs,
        [("Độ dài khe tối đa", f"{d['door_m']} m ≈ {L} px"), ("Điểm ảnh được thêm", f"{(bridge > 0).sum():,}".replace(",", "."))])

    # 11. Tách phòng
    free = cv2.bitwise_not(closed)
    n, lab, stats, cents = cv2.connectedComponentsWithStats(free, connectivity=4)
    h, w = free.shape
    vis = np.full((h, w, 3), 255, np.uint8)
    n_out = n_small = 0
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if x == 0 or y == 0 or x + bw >= w or y + bh >= h:
            vis[lab == i] = (225, 225, 225); n_out += 1
        elif area / ppm ** 2 < 1.5:
            vis[lab == i] = (0, 220, 255); n_small += 1
    for i, r in enumerate(rooms):
        vis[r["mask"] > 0] = PALETTE[i % len(PALETTE)]
    vis[closed > 0] = INK
    fs = max(0.6, w / 1500)
    for r in rooms:
        cx, cy = map(int, r["centroid"])
        for j, txt in enumerate([r["short"], f'{r["area_m2"]:.1f} m2']):
            (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, fs, 2)
            cv2.putText(vis, txt, (cx - tw // 2, cy + j * int(th * 1.6)), cv2.FONT_HERSHEY_SIMPLEX, fs, (0, 0, 0), 2, cv2.LINE_AA)
    add("rooms", "Tách phòng", "Tách từng phòng và tính diện tích",
        "Mỗi vùng trắng được tường bao kín là một phòng.",
        "Máy đánh số các vùng trắng liền nhau (gán nhãn thành phần liên thông, chỉ đi ngang và dọc). Sau đó lọc:\n\n"
        "- Vùng **chạm mép ảnh** là bên ngoài nhà → bỏ (màu xám).\n"
        "- Vùng **nhỏ hơn 1,5 m²** là hộp kỹ thuật, khe tủ → bỏ (màu vàng).\n"
        "- Còn lại là phòng (tô màu).\n\n"
        "Diện tích = số điểm ảnh của vùng ÷ (px/m)². Đây là diện tích thông thủy, tức phần sàn bên trong tường.",
        "Đây là thông tin người làm nội thất, quản lý toà nhà cần nhất: có bao nhiêu phòng, mỗi phòng bao nhiêu m².",
        [("Kết quả tách phòng", vis)],
        [("Số vùng trắng", f"{n - 1}"), ("Ngoài nhà (bỏ)", f"{n_out}"), ("Quá nhỏ (bỏ)", f"{n_small}"),
         ("Số phòng", f"{len(rooms)}")])

    # 12. Vector hoá
    vec = np.full((h, w, 3), 255, np.uint8)
    nv = 0
    for i, r in enumerate(rooms):
        cv2.fillPoly(vec, [r["poly_px"].astype(np.int32)], PALETTE[i % len(PALETTE)])
    for p in res["wall_polys"]:
        for ring in [p["outer"], *p["holes"]]:
            cv2.polylines(vec, [ring.astype(np.int32)], True, BLUE, thick(vec))
            for x, y in ring:
                cv2.circle(vec, (int(x), int(y)), thick(vec) + 2, RED, -1)
            nv += len(ring)
    npx = int((walls > 0).sum())
    add("vector", "Vector hoá", "Chuyển từ điểm ảnh sang đường nét (vector hoá)",
        "Phần mềm CAD không làm việc với điểm ảnh mà với đường thẳng và đa giác. Bước này đổi mask tường thành đa giác.",
        "Bước 1: dò đường viền của mỗi mảng tường, kể cả lỗ bên trong (findContours).\n\n"
        "Bước 2: làm đơn giản đường viền bằng Douglas–Peucker: bỏ những đỉnh nằm gần như thẳng hàng, sai lệch không quá 1,5 px. "
        "Các chấm đỏ là các đỉnh còn lại.\n\n"
        "Bước 3: đổi toạ độ điểm ảnh sang mét bằng tỉ lệ ở bước trước.",
        "File nhẹ, sửa được trong AutoCAD, và dùng để dựng khối 3D.",
        [("Đa giác tường (xanh) và các đỉnh (đỏ)", vec)],
        [("Điểm ảnh tường", f"{npx:,}".replace(",", ".")), ("Số đỉnh đa giác", f"{nv}"),
         ("Số đa giác tường", f"{len(res['wall_polys'])}")])

    # 13. 3D + DXF
    add("model", "3D & CAD", "Dựng mô hình 3D và xuất file CAD",
        "Từ các đa giác, máy dựng khối 3D và ghi ra file DXF.",
        "**3D:** mỗi đa giác tường được kéo lên cao 2,8 m (extrude), sàn mỗi phòng được tô một màu, kèm nhãn tên và diện tích. "
        "Mô hình hiển thị trên trình duyệt bằng Three.js (tab Mô hình 3D).\n\n"
        "**DXF:** ghi đa giác tường vào lớp WALL, đa giác phòng vào lớp ROOM, tên và diện tích vào lớp TEXT, đơn vị mét. "
        "Mở được bằng AutoCAD và nhập được vào Revit.",
        "Đây là đầu ra cuối cùng: thay cho việc ngồi vẽ lại bản vẽ bằng tay.",
        [("Kết quả cuối", res["overlay"])],
        [("Chiều cao tường", "2,8 m"), ("Lớp DXF", "WALL · ROOM · TEXT")])
    for x in steps:
        x["tech"] = tech_for(x["key"], d, ppm)
    return steps
