"""Sinh toàn bộ project HyperFrames từ lời nói đã cắt (words_edit.json)."""
import csv, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from hflib import *  # noqa

HF = r"F:\Project_Nhom_MSE\video\hf"
W = r"F:\Project_Nhom_MSE\video\work"
ed = json.load(open(os.path.join(W, "words_edit.json"), encoding="utf-8"))
D = ed["duration"]
DT = round(D + 4.5, 3)
WD = Words(ed["words"])
A = WD.find
S = "assets/steps/"


def AE(p, after=0.0):
    return WD.find(p, after, end=True)


# ---------------- mốc phần lớn ----------------
T = {}
T["s1"] = 0.0
T["s2"] = A("vì sao") - 0.3
T["s3"] = A("tổng quát") - 0.3
T["s41"] = A("đầu tiên là ảnh đầu vào", T["s3"]) - 0.3
T["s42"] = A("có 4 góc rồi", T["s41"]) - 0.3
T["s43"] = A("tiếp theo là đến bước 3", T["s42"]) - 0.3
T["s44"] = A("đổi sang đen trắng", T["s43"]) - 0.8
T["s45"] = A("lấp tường rỗng", T["s44"]) - 1.0
T["s46"] = A("giữ lại nét dày", T["s45"]) - 1.0
T["s47"] = A("đổi sang mét", T["s46"]) - 1.2
T["s48"] = A("bước tiếp theo là tách phòng", T["s47"]) - 0.3
T["s49"] = A("vector hóa", T["s48"]) - 1.2
T["s5"] = A("đến mô hình 3d", T["s49"]) - 0.6
T["s6"] = A("thử với bản vẽ thật", T["s5"]) - 0.3
T["s7"] = A("kết quả tổng thể", T["s6"]) - 0.3
T["s8"] = A("về code", T["s7"]) - 0.5
T["s9"] = A("hạn chế và kết luận", T["s8"]) - 0.3
ORDER = ["s1", "s2", "s3", "s41", "s42", "s43", "s44", "s45", "s46", "s47", "s48", "s49", "s5", "s6", "s7", "s8", "s9"]
for k in ORDER:
    T[k] = round(max(T[k], 0), 3)
ENDS = {k: (T[ORDER[i + 1]] if i + 1 < len(ORDER) else DT) for i, k in enumerate(ORDER)}
print({k: round(v, 1) for k, v in T.items()})

scenes = []


def new(sid, title=None):
    s = Scene(sid, T[sid], ENDS[sid], title)
    scenes.append(s)
    return s


# ======================= S1 mở đầu =========================
s = new("s1")
letters = "Plan2Model"
inner = "".join(f'<span id="s1-L{i}" style="display:inline-block">{c}</span>' for i, c in enumerate(letters))
t_proj = A("plan2model")
LOGO0 = 0.0
s.raw(f'<div id="s1-logo" class="clip abs" data-start="0" data-duration="{s.dur}" '
      f'style="left:96px;top:300px;"><div id="s1-logo-in" style="font-weight:900;font-size:200px;letter-spacing:-0.045em;line-height:1;">{inner}'
      f'<div style="height:14px;width:100%;background:{ACC};margin-top:18px;transform-origin:left;" id="s1-bar"></div></div></div>')
for i in range(len(letters)):
    s.js.append(f'tl.fromTo("#s1-L{i}",{{opacity:0.25,filter:"blur(8px)"}},{{opacity:1,filter:"blur(0px)",duration:0.18,ease:"power2.out"}},{0.05 + i * 0.05:.3f});')
s.js.append(f'tl.fromTo("#s1-bar",{{scaleX:0}},{{scaleX:1,duration:0.7,ease:"expo.out"}},{s.L(t_proj):.3f});')
s.exit("s1-logo", s.dur, "up")
# thành viên khi được gọi tên
names = [("Nguyễn Sơn Tùng", "tùng"), ("Nguyễn Thu Trang", "trang"), ("Nguyễn Văn Thụ", "thụ"), ("Nguyễn Hoàng Khôi Minh", "minh")]
for i, (nm, key) in enumerate(names):
    try:
        t = A(key)
    except KeyError:
        t = 1.0 + i * 1.2
    s.text(f'<span style="font-weight:800;font-size:40px">{esc(nm)}</span>', 96, 600 + i * 62, t - 0.1, t_proj - 0.3, enter="left")
# ảnh -> CAD -> 3D khi nói ý tưởng
for j, (src, key, cap) in enumerate([(S + "demo_input_0.jpg", "chụp", "Ảnh chụp"), (S + "demo_vector_0.jpg", "vẽ lại", "File CAD"),
                                      (S + "demo_model_0.jpg", "mô hình", "Mô hình 3D")]):
    try:
        t = A(key, t_proj)
    except KeyError:
        t = t_proj + 1.5 + j * 2
    s.card(src, 96 + j * 470, 600, 420, 300, t - 0.1, None, cap=cap, enter="rise")

# ======================= S2 vì sao =========================
s = new("s2", "Vì sao làm đề tài này?")
t = s.t0 + 1.0
s.card(S + "cc_input_0.jpg", 96, 190, 640, 624, t, None, cap="Bản vẽ giấy của một căn hộ cũ", enter="drop")
try:
    t_cad = A("autocad", s.t0)
except KeyError:
    t_cad = s.t0 + 6
s.text('Vẽ lại trên AutoCAD', 820, 260, t_cad - 0.2, None, style="font-size:40px;font-weight:800")
s.count(820, 320, 230, 0, 1, t_cad, dec=0, suffix='<span style="font-size:90px;color:#14171A"> giờ / tầng</span>', comma=True, prefix="≈ ")
try:
    t_snap = A("chụp một tấm", s.t0)
except KeyError:
    t_snap = s.ENDS if False else s.t1 - 5
s.card(S + "demo_input_0.jpg", 820, 560, 440, 330, t_snap, None, cap="Chỉ cần chụp một tấm", enter="big")
s.text('<b>?</b> Dùng kỹ thuật xử lý ảnh trong môn', 1300, 600, t_snap + 1.2, None, w=260, style="font-size:30px")

# ======================= S3 tổng quan =======================
s = new("s3", "Hệ thống có 5 khối")
blocks = [("Tìm & nắn tờ giấy", "demo_page_1", "một"), ("Làm sạch ảnh", "demo_binar_2", "hai"), ("Tìm tường", "demo_opening_1", "ba"),
          ("Tách phòng", "demo_rooms_0", "bốn"), ("CAD & 3D", "demo_model_0", "năm")]
after = s.t0 + 0.5
x0 = 96
for i, (lab, img, key) in enumerate(blocks):
    try:
        t = A(key, after)
    except KeyError:
        t = after + 1.5
    after = t + 0.3
    x = x0 + i * 292
    s.card(S + img + ".jpg", x, 250, 262, 190, t, None, enter="rise", pad=8)
    s.text(f'<span style="font-weight:900;font-size:30px;color:{ACC}">{i + 1}</span><br><span style="font-weight:800;font-size:30px">{esc(lab)}</span>',
           x, 470, t + 0.1, None, w=262, enter="blur")
    if i:
        s.raw(f'<div id="s3-ar{i}" class="clip abs" data-start="{s.L(t)}" data-duration="{round(s.dur - s.L(t), 3)}" style="left:{x - 28}px;top:338px;width:24px;height:4px;"><div id="s3-ar{i}-in" style="width:100%;height:100%;background:{INK};transform-origin:left;"></div></div>')
        s.js.append(f'tl.fromTo("#s3-ar{i}-in",{{scaleX:0}},{{scaleX:1,duration:0.3,ease:"power2.out"}},{s.L(t) - 0.15:.3f});')
try:
    t_dl = A("học sâu", s.t0)
except KeyError:
    t_dl = s.t1 - 10
s.text('<span style="font-size:54px;font-weight:900;position:relative">Học sâu<span id="s3-strike" style="position:absolute;left:-6px;right:-6px;top:52%;height:8px;background:' + ACC + ';display:block;transform-origin:left"></span></span>',
       96, 640, t_dl - 0.1, None, enter="blur")
s.js.append(f'tl.fromTo("#s3-strike",{{scaleX:0}},{{scaleX:1,duration:0.35,ease:"power3.out"}},{s.L(t_dl) + 0.6:.3f});')
try:
    t_cd = A("cổ điển", s.t0)
except KeyError:
    t_cd = t_dl + 2.5
s.text('<span style="font-size:54px;font-weight:900">→ Xử lý ảnh cổ điển</span>', 400, 640, t_cd - 0.4, None, enter="left")
for j, (lab, key) in enumerate([("Chạy nhanh", "nhanh"), ("Không cần dữ liệu huấn luyện", "dữ liệu"), ("Giải thích được từng bước", "giải thích")]):
    try:
        t = A(key, t_cd - 1)
    except KeyError:
        t = t_cd + 1 + j
    s.text(f'<b>✓</b> {esc(lab)}', 400 + j * 0 , 740 + j * 52, t - 0.1, None, enter="left", style="font-size:36px")

# ======================= S4.1 đầu vào + tìm giấy =========================
s = new("s41", "Ảnh đầu vào → tìm tờ giấy")
s.appwin("assets/app/open.mp4", s.t0 + 0.1, 7.2, mstart=0.0)
s.code('$ streamlit run app.py' + chr(10) + '  Local URL: <span class="k">http://localhost:8501</span>', 1060, 150, s.t0 + 0.4, s.t0 + 3.4, z=60)
t = s.t0 + 0.6
c1 = s.card(S + "demo_input_0.jpg", 96, 190, 900, 675, t, None, enter="rise")
for lab, key, (lx, ly) in [("Giấy nằm nghiêng", "nghiêng", (1040, 250)), ("Ánh sáng không đều", "ánh sáng", (1040, 330)), ("Bóng tay ở góc dưới", "bóng tay", (1040, 410))]:
    try:
        tt = A(key, s.t0)
    except KeyError:
        tt = t + 2
    s.text(f'<b>—</b> {esc(lab)}', lx, ly, tt - 0.1, None, enter="left", style="font-size:36px")
try:
    t_canny = A("lọc", s.t0)
except KeyError:
    t_canny = s.t0 + 12
c2 = s.card(S + "demo_page_0.jpg", 96, 190, 900, 675, t_canny, None, cap="Bản đồ cạnh (Canny)", enter="scale")
s.code('edges = cv2.<span class="k">Canny</span>(blur, 40, 120)', 1040, 520, t_canny + 0.3)
try:
    t_4 = A("4 góc", t_canny)
except KeyError:
    t_4 = t_canny + 8
s.card(S + "demo_page_1.jpg", 96, 190, 900, 675, t_4 - 0.3, None, cap="4 góc máy tìm được", enter="scale")
s.count(1040, 640, 220, 0, 4, t_4, dec=0, suffix='<span style="font-size:64px;color:#14171A"> góc</span>')

# ======================= S4.2 nắn thẳng =========================
s = new("s42", "Nắn thẳng: biến đổi phối cảnh")
s.appwin("assets/app/step03.mp4", s.t0 + 0.1, 6.8, mstart=0.3, punch=((1.6, 1.32, 26, 74), (4.4, 1.0, 50, 50)))
s.card(S + "demo_rectify_0.jpg", 96, 210, 660, 495, s.t0 + 0.4, None, cap="Lưới vuông trên ảnh nghiêng", enter="left")
try:
    t_h = A("homography", s.t0)
except KeyError:
    t_h = s.t0 + 8
rows = list(csv.reader(open(os.path.join(HF, "assets/steps/demo_rectify_chart.csv"), encoding="utf-8")))[1:]
mat = "".join("<tr>" + "".join(f'<td style="padding:6px 18px;text-align:right">{float(v):.3f}</td>' for v in r[1:]) + "</tr>" for r in rows)
s.text(f'<div style="font-weight:800;font-size:30px;margin-bottom:8px">Ma trận homography H (3×3)</div>'
       f'<table style="font-family:IBM Plex Mono,monospace;font-size:30px;font-weight:600;border-left:5px solid {INK};border-right:5px solid {INK};border-collapse:collapse">{mat}</table>',
       820, 230, t_h - 0.6, None, enter="blur")
s.code('H = cv2.<span class="k">getPerspectiveTransform</span>(4 góc, chữ nhật)\nphang = cv2.<span class="k">warpPerspective</span>(anh, H, (W, H))', 820, 470, t_h + 0.6)
try:
    t_after = A("sau khi nắn", s.t0)
except KeyError:
    t_after = t_h + 4
s.card(S + "demo_rectify_1.jpg", 820, 640, 380, 260, t_after - 0.3, None, cap="Sau khi nắn: ô vuông đều", enter="right", pad=8)
try:
    t_thang = A("hình thang", s.t0)
except KeyError:
    t_thang = t_after + 3
s.text('Không nắn → phòng chữ nhật thành <b>hình thang</b>, diện tích sai', 1240, 680, t_thang - 0.3, None, w=300, style="font-size:30px")

# ======================= S4.3 ánh sáng =========================
s = new("s43", "Làm đều ánh sáng")
s.appwin("assets/app/step04.mp4", s.t0 + 0.1, 6.8, mstart=0.3, punch=((1.6, 1.32, 26, 74), (4.4, 1.0, 50, 50)))
s.card(S + "demo_light_0.jpg", 96, 200, 440, 300, s.t0 + 0.5, None, cap="Ảnh xám", enter="rise", pad=8)
try:
    t_close = A("phép đóng", s.t0)
except KeyError:
    t_close = s.t0 + 4
s.card(S + "demo_light_1.jpg", 576, 200, 440, 300, t_close + 0.6, None, cap="Nền giấy ước lượng (tối = bóng)", enter="rise", pad=8)
s.code('nen = cv2.<span class="k">morphologyEx</span>(xam, MORPH_CLOSE, elip 41×41)', 96, 580, t_close + 0.3)
try:
    t_div = A("chia cho nền", s.t0)
except KeyError:
    t_div = t_close + 8
s.card(S + "demo_light_2.jpg", 1056, 200, 440, 300, t_div, None, cap="Sau khi làm đều", enter="rise", pad=8)
s.text(f'<span style="font-family:IBM Plex Mono,monospace;font-weight:600;font-size:40px">I′ = 255 · I / <b>nền</b></span>', 96, 680, t_div + 0.2, None)
# biểu đồ độ sáng: vẽ đường
rows = list(csv.DictReader(open(os.path.join(HF, "assets/steps/demo_light_chart.csv"), encoding="utf-8")))
xs = [float(r["x"]) for r in rows]
def path(col, X0=820, Y0=640, Wd=700, Hd=260):
    pts = [(X0 + (x - xs[0]) / (xs[-1] - xs[0]) * Wd, Y0 + Hd - float(r[col]) / 255 * Hd) for x, r in zip(xs, rows)]
    return "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts)
try:
    t_chart = A("biểu đồ", s.t0)
except KeyError:
    t_chart = t_div + 3
lc = s.L(t_chart - 0.2)
s.raw(f'<div id="s43-chart" class="clip abs" data-start="{lc}" data-duration="{round(s.dur - lc, 3)}" style="inset:0;" data-layout-allow-overflow>'
      f'<div id="s43-chart-in" style="position:absolute;inset:0"><svg width="1920" height="1080" style="position:absolute;left:0;top:0">'
      f'<rect x="806" y="620" width="728" height="300" fill="#fff"/>'
      f'<path id="s43-pb" d="{path("Nền ước lượng")}" fill="none" stroke="{ACC}" stroke-width="5"/>'
      f'<path id="s43-pe" d="{path("Sau khi làm đều")}" fill="none" stroke="#2D6CDF" stroke-width="3"/></svg>'
      f'<div class="abs" style="left:820px;top:928px;font-weight:600;font-size:28px"><span style="color:{ACC}">━ nền (tụt ở chỗ bóng)</span>&nbsp;&nbsp;<span style="color:#2D6CDF">━ sau khi làm đều</span></div></div></div>')
for pid, d0 in [("s43-pb", 0), ("s43-pe", 1.6)]:
    s.js.append(f'(function(){{const p=document.getElementById("{pid}");const L=p.getTotalLength();p.style.strokeDasharray=L;'
                f'tl.fromTo(p,{{strokeDashoffset:L}},{{strokeDashoffset:0,duration:1.6,ease:"power2.inOut"}},{lc + 0.3 + d0:.3f});}})();')
s.enter("s43-chart", lc, "blur")

# ======================= S4.4 đen trắng =========================
s = new("s44", "Đổi sang đen trắng")
s.appwin("assets/app/step05.mp4", s.t0 + 0.1, 7.5, mstart=0.3, punch=((1.6, 1.32, 26, 74), (4.4, 1.0, 50, 50)))
try:
    t_otsu = A("otsu", s.t0)
except KeyError:
    t_otsu = s.t0 + 3
s.card(S + "demo_binar_0.jpg", 96, 200, 640, 437, t_otsu - 0.2, None, cap="Otsu: một ngưỡng chung = 157", enter="left")
try:
    t_sv = A("sauvola", t_otsu + 2)
except KeyError:
    t_sv = t_otsu + 8
s.card(S + "demo_binar_1.jpg", 800, 200, 640, 437, t_sv, None, cap="Sauvola: ngưỡng riêng cho từng điểm (132 – 202)", enter="right")
try:
    t_clean = A("sạch hơn", t_sv)
except KeyError:
    t_clean = t_sv + 8
s.card(S + "demo_binar_2.jpg", 800, 200, 640, 437, t_clean - 0.3, None, cap="Kết quả Sauvola", enter="scale")
s.text('<span style="font-family:IBM Plex Mono,monospace;font-weight:600;font-size:38px">T = m · (1 + k · (s / R − 1))</span>', 96, 740, t_sv + 2.0, None)
try:
    t_tp = A("tích phân", t_sv)
except KeyError:
    t_tp = t_clean + 2
s.code('ii = cv2.<span class="k">integral</span>(g)        # ảnh tích phân\nS  = ii[Y1,X1] - ii[Y0,X1] - ii[Y1,X0] + ii[Y0,X0]', 96, 820, t_tp - 0.2)
try:
    t_99 = A("99", t_tp)
except KeyError:
    t_99 = t_tp + 4
s.count(1080, 720, 150, 0, 99.99, t_99 - 0.5, dec=2, suffix='<span style="font-size:60px"> %</span>', dur=0.8)
s.text('khớp với scikit-image', 1090, 880, t_99 + 0.3, None, style="font-size:32px")

# ======================= S4.5 lấp tường rỗng =========================
s = new("s45", "Lấp tường rỗng")
s.appwin("assets/app/step06.mp4", s.t0 + 0.1, 6.8, mstart=0.3, punch=((1.6, 1.32, 26, 74), (4.4, 1.0, 50, 50)))
s.card(S + "demo_hollow_0.jpg", 96, 200, 640, 437, s.t0 + 0.5, None, cap="Tường chỉ vẽ 2 nét viền", enter="rise")
try:
    t_hd = A("hẹp", s.t0)
except KeyError:
    t_hd = s.t0 + 8
s.text('Vùng trắng bị mực bao kín, vừa <b>hẹp</b> vừa <b>dài</b> → ruột tường → tô kín', 96, 720, t_hd - 0.3, None, w=640)
try:
    t_dt = A("khoảng cách", t_hd)
except KeyError:
    t_dt = t_hd + 3
s.code('d = cv2.<span class="k">distanceTransform</span>(trang, DIST_L2, 3)', 96, 860, t_dt - 0.2)
try:
    t_6 = A("lấp được", t_dt)
except KeyError:
    t_6 = t_dt + 6
s.card(S + "demo_hollow_1.jpg", 800, 200, 640, 437, t_dt + 0.8, None, cap="Đỏ: phần được tô", enter="right")
z = s.card(S + "demo_hollow_2.jpg", 1000, 170, 440, 440, t_6 - 0.2, None, enter="big")
s.count(800, 720, 180, 0, 6, t_6, dec=0, suffix='<span style="font-size:60px;color:#14171A"> khe được lấp</span>')

# ======================= S4.6 phép mở =========================
s = new("s46", "Giữ lại nét dày: phép mở")
s.appwin("assets/app/step07.mp4", s.t0 + 0.1, 6.8, mstart=0.3, punch=((1.6, 1.32, 26, 74), (4.4, 1.0, 50, 50)))
s.card(S + "demo_binar_2.jpg", 96, 200, 640, 437, s.t0 + 0.4, None, cap="Trước: còn chữ, ký hiệu, nội thất", enter="left")
try:
    t_mo = A("phép mở", s.t0)
except KeyError:
    t_mo = s.t0 + 6
s.count(820, 210, 150, 0, 7, t_mo - 0.2, dec=0, suffix='<span style="font-size:80px"> × 7</span>')
s.code('tuong = cv2.<span class="k">morphologyEx</span>(muc, MORPH_OPEN, ô 7×7)', 820, 400, t_mo + 0.5)
try:
    t_co = A("phép co", t_mo)
except KeyError:
    t_co = t_mo + 2
s.text('<b>Co</b>: xoá mọi nét mảnh hơn 7 px<br><b>Giãn</b>: trả tường về độ dày cũ', 820, 510, t_co - 0.2, None, w=700)
try:
    t_hong = A("màu hồng", t_co)
except KeyError:
    t_hong = t_co + 5
s.card(S + "demo_opening_1.jpg", 96, 200, 640, 437, t_hong - 1.0, None, cap="Đen: tường giữ lại · Hồng: nét bị xoá", enter="scale")
s.card(S + "demo_opening_2.jpg", 820, 640, 280, 280, t_hong + 0.6, None, enter="big", pad=8)
try:
    t_7 = A("tập ảnh riêng", t_hong)
except KeyError:
    t_7 = t_hong + 4
s.text('Số 7 chọn bằng thử nghiệm trên <b>tập ảnh riêng</b>', 1140, 700, t_7 - 1.0, None, w=400, style="font-size:30px")

# ======================= S4.7 tỉ lệ + bịt khe =========================
s = new("s47", "Đổi sang mét · bịt khe cửa")
s.appwin("assets/app/step09.mp4", s.t0 + 0.1, 6.5, mstart=0.3, punch=((1.6, 1.32, 26, 74), (4.4, 1.0, 50, 50)))
s.card(S + "demo_scale_0.jpg", 96, 200, 640, 437, s.t0 + 0.4, None, cap="Bề rộng nhà nhập vào: 12,25 m", enter="rise")
try:
    t_845 = A("84", s.t0)
except KeyError:
    t_845 = s.t0 + 5
s.count(820, 220, 150, 0, 84.5, t_845 - 0.2, dec=1, suffix='<span style="font-size:60px;color:#14171A"> px / m</span>')
try:
    t_khe = A("bịt khe", s.t0)
except KeyError:
    t_khe = t_845 + 6
s.card(S + "demo_doors_0.jpg", 96, 200, 640, 437, t_khe - 0.5, None, cap="Xanh lá: đoạn bịt khe cửa", enter="scale")
s.code('cv2.<span class="k">morphologyEx</span>(tuong, MORPH_CLOSE, đoạn thẳng 185×1)\ncv2.<span class="k">morphologyEx</span>(tuong, MORPH_CLOSE, đoạn thẳng 1×185)', 820, 420, t_khe + 0.3)
try:
    t_xl = A("xanh lá", t_khe)
except KeyError:
    t_xl = t_khe + 6
s.card(S + "demo_doors_1.jpg", 820, 600, 300, 300, t_xl - 0.6, None, enter="big", pad=8)
s.text('Thước dài <b>2,2 m</b>: hai đầu tường thẳng hàng, gần hơn thước → nối lại', 1160, 640, t_xl - 0.2, None, w=380, style="font-size:30px")

# ======================= S4.8 tách phòng =========================
s = new("s48", "Tách phòng")
s.appwin("assets/app/step10.mp4", s.t0 + 0.1, 6.8, mstart=0.3, punch=((1.6, 1.32, 26, 74), (4.4, 1.0, 50, 50)))
s.card(S + "demo_doors_0.jpg", 96, 200, 760, 519, s.t0 + 0.3, None, enter="rise")
try:
    t_nuoc = A("đổ nước", s.t0)
except KeyError:
    t_nuoc = s.t0 + 3
rid = s.card(S + "demo_rooms_0.jpg", 96, 200, 760, 519, t_nuoc, None, enter="none")
s.js.append(f'tl.fromTo("#{rid}-in",{{clipPath:"circle(0% at 45% 40%)"}},{{clipPath:"circle(85% at 45% 40%)",duration:2.2,ease:"power2.inOut"}},{s.L(t_nuoc):.3f});')
s.code('n, nhan, tk, tam = cv2.<span class="k">connectedComponentsWithStats</span>(\n    trong, connectivity=<span class="k">4</span>)', 920, 220, t_nuoc + 1.5)
try:
    t_5 = A("5 phòng", t_nuoc)
except KeyError:
    t_5 = t_nuoc + 10
s.count(920, 420, 200, 0, 5, t_5 - 0.2, dec=0, suffix='<span style="font-size:70px;color:#14171A"> phòng</span>')
areas = [24.3, 23.1, 12.0, 11.7, 11.2]
s.text("".join(f'<div style="display:flex;align-items:center;gap:14px;margin:6px 0"><span style="width:28px;height:28px;background:{ROOMC[i]};display:inline-block"></span>{str(a).replace(".", ",")} m²</div>' for i, a in enumerate(areas)),
       920, 640, t_5 + 0.6, None, style="font-size:30px;font-weight:700")
try:
    t_tt = A("thông thủy", t_5)
except KeyError:
    t_tt = t_5 + 4
s.text('Diện tích <b>thông thủy</b> (phần sàn bên trong tường)', 1180, 660, t_tt - 0.3, None, w=360, style="font-size:30px")

# ======================= S4.9 vector + 3D =========================
s = new("s49", "Vector hoá → CAD")
s.appwin("assets/app/step11.mp4", s.t0 + 0.1, 6.8, mstart=0.3, punch=((1.6, 1.32, 26, 74), (4.4, 1.0, 50, 50)))
s.card(S + "demo_rooms_0.jpg", 96, 200, 760, 519, s.t0 + 0.3, None, enter="rise")
try:
    t_dp = A("douglas", s.t0)
except KeyError:
    t_dp = s.t0 + 4
s.card(S + "demo_vector_0.jpg", 96, 200, 760, 519, t_dp - 0.3, None, cap="Đa giác tường và các đỉnh (đỏ)", enter="scale")
s.code('vien = cv2.<span class="k">findContours</span>(tuong, RETR_CCOMP, ...)\nda_giac = cv2.<span class="k">approxPolyDP</span>(vien, 1.5, True)', 920, 230, t_dp + 0.4)
try:
    t_28 = A("2,8", t_dp)
except KeyError:
    t_28 = t_dp + 6
s.count(920, 430, 180, 0, 2.8, t_28 - 0.2, dec=1, suffix='<span style="font-size:70px;color:#14171A"> m cao</span>')
try:
    t_1s = A("chưa tới", t_28)
except KeyError:
    t_1s = t_28 + 3
s.text('Cả quá trình: <b>&lt; 1 giây</b>', 920, 680, t_1s - 0.4, None, style="font-size:48px;font-weight:800")

scenes_meta = dict(T=T, ENDS=ENDS, D=D)
json.dump(scenes_meta, open(os.path.join(W, "scenes_meta.json"), "w"), indent=1)
exec(open(os.path.join(W, "build2.py"), encoding="utf-8").read())
