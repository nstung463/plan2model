"""Phần 'Kỹ thuật & hàm' của từng bước: chủ đề trong môn, các hàm OpenCV/NumPy đã gọi, công thức, đoạn code.

Mỗi mục: topic (chủ đề), funcs [(hàm, tham số, tác dụng)], formulas [LaTeX], algo (các bước thuật toán), code.
"""


def tech_for(key, d, ppm):
    k = d.get("k", 7)
    L = int(d.get("door_m", 1.6) * ppm)
    T = {
        "input": dict(
            topic="Biểu diễn ảnh số",
            funcs=[("cv2.imdecode", "IMREAD_COLOR", "Giải mã file JPG/PNG thành ma trận H × W × 3, kiểu uint8"),
                   ("img.shape", "", "Lấy kích thước ảnh (cao, rộng, số kênh)")],
            formulas=[r"I:\ \Omega\subset\mathbb{Z}^2 \to \{0,\dots,255\}^3,\quad I(x,y)=(B,G,R)"],
            algo=["OpenCV lưu ảnh theo thứ tự kênh **B, G, R** (không phải R, G, B).",
                  "Gốc toạ độ ở góc trên bên trái, trục y hướng xuống."],
            code='img = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)\nh, w = img.shape[:2]'),

        "page": dict(
            topic="Phát hiện biên · Đường viền · Xấp xỉ đa giác",
            funcs=[("cv2.GaussianBlur", "kernel 5×5", "Làm mờ để giảm nhiễu trước khi tìm cạnh"),
                   ("cv2.Canny", "ngưỡng 40 / 120", "Tìm cạnh: gradient Sobel → làm mảnh cạnh → ngưỡng kép"),
                   ("cv2.dilate", "kernel 3×3", "Nối các đoạn cạnh bị đứt"),
                   ("cv2.findContours", "RETR_EXTERNAL", "Dò đường viền ngoài cùng của các vùng cạnh"),
                   ("cv2.approxPolyDP", "ε = 2% chu vi", "Douglas–Peucker: rút đường viền thành đa giác ít đỉnh"),
                   ("cv2.contourArea", "", "Diện tích đa giác, loại vùng nhỏ hơn 20% ảnh")],
            formulas=[r"G=\sqrt{G_x^2+G_y^2},\qquad \theta=\arctan\frac{G_y}{G_x}",
                      r"\text{cạnh mạnh: } G>120,\quad \text{cạnh yếu: } 40<G\le120 \text{ (giữ nếu nối với cạnh mạnh)}"],
            algo=["Thu nhỏ ảnh về cạnh dài 800 px cho nhanh.",
                  "**Canny** gồm 4 bước: làm mờ Gauss → tính gradient bằng Sobel → *non-maximum suppression* (chỉ giữ điểm lớn nhất theo hướng gradient, cạnh mỏng 1 px) → *hysteresis* (ngưỡng kép 40/120).",
                  "Lấy 5 đường viền lớn nhất, với mỗi đường chạy Douglas–Peucker. Đường nào còn đúng 4 đỉnh và đủ lớn là tờ giấy.",
                  "Sắp xếp 4 đỉnh theo thứ tự: trên-trái có x+y nhỏ nhất, dưới-phải có x+y lớn nhất, trên-phải có y−x nhỏ nhất, dưới-trái có y−x lớn nhất."],
            code='''small = cv2.GaussianBlur(small, (5, 5), 0)
edges = cv2.Canny(small, 40, 120)
edges = cv2.dilate(edges, np.ones((3, 3), np.uint8))
cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:5]:
    approx = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
    if len(approx) == 4 and cv2.contourArea(approx) > 0.2 * small.size:
        return order_corners(approx / scale)'''),

        "rectify": dict(
            topic="Biến đổi hình học · Phép chiếu phối cảnh (homography)",
            funcs=[("cv2.getPerspectiveTransform", "4 cặp điểm", "Giải hệ 8 phương trình tìm 8 ẩn của ma trận H"),
                   ("cv2.warpPerspective", "INTER_CUBIC", "Dời mọi điểm ảnh theo H, nội suy bậc ba"),
                   ("cv2.perspectiveTransform", "H⁻¹", "Chiếu lưới ô vuông ngược lên ảnh gốc (chỉ để minh hoạ)")],
            formulas=[r"\begin{bmatrix}x'\\y'\\w\end{bmatrix}=H\begin{bmatrix}x\\y\\1\end{bmatrix},\qquad u=\frac{x'}{w},\ v=\frac{y'}{w}",
                      r"H=\begin{bmatrix}h_{11}&h_{12}&h_{13}\\h_{21}&h_{22}&h_{23}\\h_{31}&h_{32}&1\end{bmatrix}\ \ (8\text{ ẩn})"],
            algo=["Mỗi cặp điểm (x, y) ↔ (u, v) cho 2 phương trình, 4 cặp cho đủ 8 phương trình.",
                  "Phép chia cho w là thứ làm các đường song song trên giấy hội tụ trong ảnh nghiêng, và ngược lại.",
                  "warpPerspective làm *ánh xạ ngược*: với mỗi điểm ảnh đích, tính vị trí trên ảnh nguồn bằng H⁻¹ rồi nội suy, nên ảnh không bị lỗ.",
                  "Tỉ lệ khung chữ nhật đích lấy theo khổ giấy (A-series 1:√2) để không bị méo."],
            code='''M = cv2.getPerspectiveTransform(corners, np.float32([[0, 0], [W, 0], [W, H], [0, H]]))
work = cv2.warpPerspective(img, M, (W, H), flags=cv2.INTER_CUBIC)'''),

        "light": dict(
            topic="Tăng cường ảnh · Hình thái học trên ảnh xám",
            funcs=[("cv2.cvtColor", "BGR2GRAY", "Đổi sang ảnh xám"),
                   ("cv2.getStructuringElement", "ELLIPSE 41×41", "Tạo phần tử cấu trúc hình tròn"),
                   ("cv2.morphologyEx", "MORPH_CLOSE", "Phép đóng xám: xoá nét tối mảnh hơn 41 px → còn nền"),
                   ("cv2.GaussianBlur", "kernel 31×31", "Làm mượt nền ước lượng"),
                   ("np.clip", "0…255", "Chia ảnh cho nền và giới hạn giá trị")],
            formulas=[r"Y=0.299R+0.587G+0.114B",
                      r"B=G_{31}*\big((I\oplus S)\ominus S\big)",
                      r"I'(x,y)=\min\!\Big(255,\ 255\cdot\frac{I(x,y)}{B(x,y)+1}\Big)"],
            algo=["Trên ảnh xám, **giãn** (⊕) = lấy giá trị lớn nhất trong vùng, **co** (⊖) = lấy giá trị nhỏ nhất.",
                  "Giấy sáng, mực tối. Giãn với hình tròn 41 px làm nét mực tối bị giấy sáng xung quanh 'lấp' mất; co lại để trả nền về đúng vị trí.",
                  "Mô hình ảnh: I = độ phản xạ × chiếu sáng. Chia cho nền B (≈ chiếu sáng) còn lại độ phản xạ, tức nền phẳng."],
            code='''bg = cv2.morphologyEx(gray, cv2.MORPH_CLOSE,
                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
bg = cv2.GaussianBlur(bg, (31, 31), 0)
even = np.clip(gray / (bg + 1.0) * 255, 0, 255).astype(np.uint8)'''),

        "binar": dict(
            topic="Phân đoạn ảnh · Phân ngưỡng toàn cục (Otsu) và cục bộ (Sauvola)",
            funcs=[("cv2.threshold", "THRESH_OTSU", "Otsu, chỉ dùng để so sánh"),
                   ("cv2.integral", "g và g²", "Ảnh tích phân của ảnh và của bình phương ảnh"),
                   ("numpy (tự viết)", "cửa sổ 25, k = 0,2, R = 128", "Tính m, s, T cho mọi điểm cùng lúc (vector hoá)")],
            formulas=[r"\text{Otsu: } t^*=\arg\max_t\ \omega_0(t)\,\omega_1(t)\,\big(\mu_0(t)-\mu_1(t)\big)^2",
                      r"\text{Sauvola: } T(x,y)=m(x,y)\Big[1+k\Big(\frac{s(x,y)}{R}-1\Big)\Big]",
                      r"\textstyle\sum_{\text{ô}} g = ii(y_1,x_1)-ii(y_0,x_1)-ii(y_1,x_0)+ii(y_0,x_0)",
                      r"m=\frac{\sum g}{n},\qquad s=\sqrt{\frac{\sum g^2}{n}-m^2}"],
            algo=["**Otsu** thử mọi ngưỡng 0…255, chọn ngưỡng làm hai nhóm (mực / giấy) tách nhau rõ nhất. Một ngưỡng cho cả ảnh.",
                  "**Sauvola**: ô có độ lệch chuẩn s nhỏ (toàn giấy) → ngưỡng thấp hơn m nhiều, không sinh nhiễu; ô có nét mực (s lớn) → ngưỡng gần m.",
                  "**Ảnh tích phân** ii(y, x) = tổng mọi điểm phía trên-trái. Tổng của một ô bất kỳ chỉ cần 4 phép cộng trừ, độ phức tạp O(1) mỗi điểm, không phụ thuộc kích thước ô.",
                  "Kiểm tra: so với skimage.filters.threshold_sauvola khớp 99,99% điểm ảnh."],
            code='''ii, ii2 = cv2.integral(g), cv2.integral(g * g)
S  = ii[Y1, X1]  - ii[Y0, X1]  - ii[Y1, X0]  + ii[Y0, X0]
S2 = ii2[Y1, X1] - ii2[Y0, X1] - ii2[Y1, X0] + ii2[Y0, X0]
m = S / n
s = np.sqrt(np.maximum(S2 / n - m * m, 0))
T = m * (1 + k * (s / R - 1))
ink = (g <= T) * 255          # mực = 255'''),

        "color": dict(
            topic="Xử lý ảnh màu · Không gian màu HSV",
            funcs=[("cv2.cvtColor", "BGR2HSV", "Đổi sang Hue – Saturation – Value"),
                   ("so sánh numpy", "S > 110, V > 90", "Chọn điểm màu đậm, không quá tối"),
                   ("|= (bitwise OR)", "", "Gộp với kết quả đen trắng")],
            formulas=[r"V=\max(R,G,B),\qquad S=\frac{V-\min(R,G,B)}{V}"],
            algo=["Giấy trắng, mực đen, mực xám đều có S thấp. Chỉ vùng tô màu mới có S cao.",
                  "Tường tô vàng nhạt có độ xám gần giấy nên Sauvola bỏ sót, nhưng S thì rất cao."],
            code='''hsv = cv2.cvtColor(work, cv2.COLOR_BGR2HSV)
cand |= ((hsv[..., 1] > 110) & (hsv[..., 2] > 90)) * 255'''),

        "hollow": dict(
            topic="Hình thái học · Biến đổi khoảng cách · Gán nhãn vùng liên thông",
            funcs=[("cv2.bitwise_not", "", "Đảo ảnh: vùng trắng (giấy) thành đối tượng"),
                   ("cv2.connectedComponentsWithStats", "4-liên thông", "Đánh số từng vùng trắng, lấy hộp bao và diện tích"),
                   ("cv2.distanceTransform", "DIST_L2, mask 3", "Khoảng cách từ mỗi điểm trắng tới mực gần nhất"),
                   ("np.maximum.at", "", "Lấy khoảng cách lớn nhất r trong từng vùng")],
            formulas=[r"D(p)=\min_{q\,\in\,\text{mực}}\ \lVert p-q\rVert_2,\qquad r_i=\max_{p\in\text{vùng } i} D(p)",
                      r"\text{lấp nếu: } 1.5\le r_i\le 14,\quad \frac{A_i}{r_i^2}\ge 6,\quad \max(w_i,h_i)>6\,r_i,\quad \text{không chạm biên}"],
            algo=["r là bán kính hình tròn lớn nhất đặt lọt trong vùng, tức **nửa bề rộng** của vùng.",
                  "Khe giữa 2 viền tường: r nhỏ (hẹp) nhưng diện tích lớn so với r² (dài). Phòng: r rất lớn → bị loại.",
                  "Ô chữ cái, ký hiệu: r nhỏ nhưng ngắn (A/r² nhỏ) → bị loại.",
                  "Mỗi điều kiện tính một lần cho cả vùng (vector hoá theo nhãn), nên chạy nhanh."],
            code='''free = cv2.bitwise_not(ink)
n, lab, stats, _ = cv2.connectedComponentsWithStats(free, connectivity=4)
dt = cv2.distanceTransform(free, cv2.DIST_L2, 3)
rmax = np.zeros(n, np.float32); np.maximum.at(rmax, lab.ravel(), dt.ravel())
elong = area / np.maximum(rmax, 1) ** 2
ok = inner & (rmax >= 1.5) & (rmax <= 14) & (elong >= 6) & (np.maximum(bw, bh) > 6 * rmax)
cand = np.where(ok[lab], 255, ink)'''),

        "opening": dict(
            topic="Hình thái học nhị phân · Phép mở (opening)",
            funcs=[("cv2.getStructuringElement", f"MORPH_RECT {k}×{k}", "Phần tử cấu trúc hình vuông"),
                   ("cv2.morphologyEx", "MORPH_OPEN", "Co rồi giãn"),
                   ("cv2.connectedComponentsWithStats", "diện tích > 400", "Bỏ các mảnh vụn còn sót")],
            formulas=[r"A\ominus B=\{\,z \mid B_z\subseteq A\,\}\quad\text{(co)}",
                      r"A\oplus B=\{\,z \mid B_z\cap A\neq\varnothing\,\}\quad\text{(giãn)}",
                      rf"A\circ B=(A\ominus B)\oplus B,\qquad B=\text{{vuông }}{k}\times{k}"],
            algo=[f"**Co**: đặt tâm ô vuông {k}×{k} tại mỗi điểm; điểm chỉ giữ lại nếu cả ô nằm trọn trong mực.",
                  f"Nét có bề dày < {k} px không chứa nổi ô vuông nên mất hẳn. Phép giãn sau đó không thể khôi phục thứ đã mất.",
                  "**Giãn**: nở lại phần còn sót đúng bằng ô vuông → tường trở về đúng hình dạng.",
                  "Tính chất: phép mở **không làm to** đối tượng (A∘B ⊆ A) và làm lại lần nữa không đổi (luỹ đẳng)."],
            code=f'''ker = cv2.getStructuringElement(cv2.MORPH_RECT, ({k}, {k}))
walls = cv2.morphologyEx(cand, cv2.MORPH_OPEN, ker)
n, lab, stats, _ = cv2.connectedComponentsWithStats(walls)
keep = stats[:, cv2.CC_STAT_AREA] > 400; keep[0] = False
walls = (keep[lab] * 255).astype(np.uint8)'''),

        "unet": dict(
            topic="Học sâu · Phân đoạn ngữ nghĩa (so sánh)",
            funcs=[("smp.Unet", "encoder resnet18, ImageNet", "Mạng mã hoá – giải mã có kết nối tắt"),
                   ("torch.sigmoid", "", "Đổi đầu ra thành xác suất là tường"),
                   ("ngưỡng", "chọn trên val", "Xác suất → mask nhị phân")],
            formulas=[r"\mathcal{L}=\mathrm{BCE}_{w=3}+\big(1-\mathrm{Dice}\big)"],
            algo=["Huấn luyện trên 300 ảnh train, ảnh cạnh dài 768, cắt mảnh 256×256, AdamW + OneCycle, chạy trên CPU."],
            code='prob = torch.sigmoid(model(x))\nwalls = (prob > thr) * 255'),

        "scale": dict(
            topic="Biến đổi khoảng cách · Đo đạc trên ảnh",
            funcs=[("np.nonzero", "", "Toạ độ các điểm tường → hộp bao, bề rộng nhà (px)"),
                   ("cv2.distanceTransform", "DIST_L2", "Khoảng cách tới mép tường; tim tường có giá trị lớn nhất"),
                   ("np.median", "nửa trên", "Ước lượng độ dày tường ổn định, ít bị ảnh hưởng bởi khối đặc")],
            formulas=[r"\text{ppm}=\frac{W_{px}}{W_{m}}\quad\text{hoặc}\quad \text{ppm}=\frac{2\cdot\mathrm{median}(D)}{t_{tường}}",
                      r"\text{diện tích (m}^2)=\frac{N_{px}}{\text{ppm}^2}"],
            algo=["Theo bề rộng: đo từ điểm tường trái nhất tới phải nhất, chia cho bề rộng thật người dùng nhập.",
                  "Theo độ dày: giá trị D ở tim tường = nửa độ dày. Lấy trung vị của nửa trên các giá trị D, nhân 2, kẹp trong 8…40 px."],
            code='''ys, xs = np.nonzero(walls)
ppm = (xs.max() - xs.min() + 1) / house_width_m          # cách 1
dt = cv2.distanceTransform(walls, cv2.DIST_L2, 3)
v = dt[walls > 0]; v = v[v > np.percentile(v, 50)]
ppm = np.clip(2 * np.median(v), 8, 40) / wall_m           # cách 2'''),

        "doors": dict(
            topic="Hình thái học nhị phân · Phép đóng (closing) với phần tử đoạn thẳng",
            funcs=[("cv2.getStructuringElement", f"MORPH_RECT {L}×1 và 1×{L}", "Đoạn thẳng ngang và đứng, dài = khe cửa tối đa"),
                   ("cv2.morphologyEx", "MORPH_CLOSE", "Giãn rồi co: lấp khe hẹp hơn phần tử cấu trúc"),
                   ("cv2.bitwise_or", "", "Gộp kết quả 2 hướng với tường gốc")],
            formulas=[r"A\bullet B=(A\oplus B)\ominus B",
                      rf"L=\text{{khe cửa}}\times\text{{ppm}}={d.get('door_m', 1.6)}\times{ppm:.1f}\approx{L}\text{{ px}}"],
            algo=["Phép đóng là 'đối ngẫu' của phép mở: nó lấp các khe, lỗ nhỏ hơn phần tử cấu trúc.",
                  "Giãn với đoạn ngang L: hai đầu tường cùng hàng cách nhau < L px chạm nhau. Co lại: phần thừa biến mất, chỉ còn đoạn nối.",
                  "Dùng đoạn thẳng thay ô vuông: chỉ nối theo đúng phương của tường, không làm phình tường hay lấp góc phòng."],
            code=f'''closed = walls.copy()
for shape in [({L}, 1), (1, {L})]:
    ker = cv2.getStructuringElement(cv2.MORPH_RECT, shape)
    closed |= cv2.morphologyEx(walls, cv2.MORPH_CLOSE, ker)'''),

        "rooms": dict(
            topic="Gán nhãn vùng liên thông · Phân tích vùng",
            funcs=[("cv2.bitwise_not", "", "Phần không phải tường"),
                   ("cv2.connectedComponentsWithStats", "connectivity = 4", "Đánh số vùng, trả về hộp bao, diện tích, trọng tâm"),
                   ("cv2.findContours", "RETR_EXTERNAL", "Đường viền mỗi phòng"),
                   ("cv2.approxPolyDP", "ε = 3 px", "Đa giác phòng gọn")],
            formulas=[r"p\sim q \iff \exists\ \text{đường đi 4-liên thông từ } p \text{ tới } q \text{ không qua tường}",
                      r"A_{m^2}=\frac{N_{px}}{\text{ppm}^2},\quad \text{giữ nếu } A\ge1.5\,m^2 \text{ và không chạm biên}"],
            algo=["Thuật toán gán nhãn quét ảnh 2 lượt (two-pass) hoặc loang (flood fill): giống đổ nước, lan tới đâu cùng nhãn tới đó.",
                  "Dùng **4-liên thông** (chỉ trên/dưới/trái/phải) để nước không 'rò' qua chỗ hai tường chạm nhau ở góc chéo.",
                  "Vùng chạm mép ảnh chắc chắn nằm ngoài nhà."],
            code='''free = cv2.bitwise_not(closed)
n, lab, stats, cents = cv2.connectedComponentsWithStats(free, connectivity=4)
for i in range(1, n):
    x, y, bw, bh, area = stats[i]
    if touches_border or area / ppm**2 < 1.5: continue
    rooms.append(...)'''),

        "vector": dict(
            topic="Biểu diễn đường viền · Xấp xỉ đa giác Douglas–Peucker",
            funcs=[("cv2.findContours", "RETR_CCOMP, CHAIN_APPROX_SIMPLE", "Viền ngoài + viền lỗ bên trong (cây 2 cấp)"),
                   ("cv2.approxPolyDP", "ε = 1,5 px", "Bỏ đỉnh thừa"),
                   ("ezdxf / Three.js", "", "Ghi đa giác ra DXF, dựng khối 3D")],
            formulas=[r"\text{giữ điểm } p_k \text{ nếu } d\big(p_k,\ \overline{p_0p_n}\big)>\varepsilon"],
            algo=["**Douglas–Peucker** (đệ quy): nối điểm đầu và cuối thành đoạn thẳng.",
                  "Tìm điểm xa đoạn đó nhất. Nếu xa hơn ε thì giữ điểm đó, chia đôi đường và làm tiếp cho từng nửa.",
                  "Nếu mọi điểm đều gần hơn ε thì thay cả đoạn bằng một đường thẳng.",
                  "RETR_CCOMP cho biết viền nào là lỗ của viền nào, để tường bao quanh sân trong không bị tô kín."],
            code='''cnts, hier = cv2.findContours(walls, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
for i, c in enumerate(cnts):
    if hier[0][i][3] != -1: continue                  # chỉ lấy viền ngoài
    outer = cv2.approxPolyDP(c, 1.5, True)
    holes = [cv2.approxPolyDP(cnts[j], 1.5, True) for j in children(i)]'''),

        "model": dict(
            topic="Từ ảnh 2D đến mô hình: đổi toạ độ, đùn khối (extrude)",
            funcs=[("ezdxf.new / add_lwpolyline", "layer WALL, ROOM", "Ghi đa giác vào file DXF, đơn vị mét"),
                   ("add_text", "layer TEXT", "Tên + diện tích phòng"),
                   ("THREE.ExtrudeGeometry", "depth = 2,8 m", "Kéo đa giác tường lên thành khối"),
                   ("THREE.ShapeGeometry", "", "Mặt sàn mỗi phòng"),
                   ("OrbitControls", "", "Xoay, phóng to bằng chuột")],
            formulas=[r"(X,Y)=\Big(\frac{x-x_0}{\text{ppm}},\ -\frac{y-y_0}{\text{ppm}}\Big)\ \text{(m)}"],
            algo=["Đổi toạ độ điểm ảnh sang mét, lật trục y (ảnh y hướng xuống, CAD y hướng lên).",
                  "Mỗi đa giác tường (kèm lỗ) thành một khối lăng trụ cao 2,8 m."],
            code='''doc = ezdxf.new(); doc.units = ezdxf.units.M
msp.add_lwpolyline(ring, close=True, dxfattribs={"layer": "WALL"})
// Three.js
const g = new THREE.ExtrudeGeometry(shape, { depth: 2.8, bevelEnabled: false });'''),
    }
    return T.get(key)
