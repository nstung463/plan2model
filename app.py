"""Plan2Model demo: ảnh chụp bản vẽ mặt bằng -> CAD (DXF) -> mô hình 3D.

Chạy:  streamlit run app.py
"""
import glob, json, os, sys, time

import cv2
import numpy as np
import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "prototype"))
import core  # noqa: E402
import explain  # noqa: E402
import pipeline as P  # noqa: E402
import synth  # noqa: E402
from cubicasa_gt import load_gt  # noqa: E402

st.set_page_config(page_title="Plan2Model", page_icon=":material/floor:", layout="wide")

SYNTH = "Ảnh chụp mô phỏng (bản vẽ tổng hợp)"
UNET_PATH = os.path.join(ROOT, "prototype", "models", "unet_wall.pt")


# ---------------- dữ liệu mẫu (cache) ----------------
@st.cache_data
def synthetic_photo():
    page, _ = synth.draw_plan()
    return cv2.imencode(".jpg", synth.simulate_photo(page))[1].tobytes()


@st.cache_data
def cubicasa_samples():
    """Mỗi nhóm: 3 ảnh test có wall IoU cao nhất + 1 ca khó nhất (theo results.csv của phương pháp cuối)."""
    import csv
    test = os.path.join(ROOT, "prototype", "data", "cubicasa", "test")
    res_csv = os.path.join(ROOT, "prototype", "output", "cc", "test", "results.csv")
    score = {}
    if os.path.exists(res_csv):
        for r in csv.DictReader(open(res_csv, encoding="utf-8")):
            if r["variant"].strip() == "- k co dinh (tune tren val)":
                score[r["image"]] = float(r["wall_IoU"])
    out = {}
    for cat, label in [("high_quality_architectural", "kiến trúc"), ("high_quality", "chất lượng cao"), ("colorful", "màu")]:
        ds = sorted(glob.glob(os.path.join(test, cat + "_*")), key=lambda d: -score.get(os.path.basename(d), 0))
        for d in ds[:3]:
            out[f"CubiCasa5K · {label} · {os.path.basename(d).rsplit('_', 1)[1]}"] = d
        if score:
            out[f"CubiCasa5K · {label} · {os.path.basename(ds[-1]).rsplit('_', 1)[1]} (ca khó)"] = ds[-1]
    return out


@st.cache_data
def load_sample_gt(d, shape):
    return load_gt(os.path.join(d, "model.svg"), shape)


@st.cache_resource
def unet_model():
    from unet_wall import UNetWall
    return UNetWall(UNET_PATH)


@st.cache_data(max_entries=16)
def run_pipeline(img_bytes, photo_mode, k, door_m, scale_mode, wall_m, house_width_m, px_per_m, aspect,
                 use_flatten, use_hollow, use_color, use_unet):
    img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
    unet_mask = None
    if use_unet:
        unet_mask = unet_model()(img)
    t0 = time.perf_counter()
    res = core.process(img, photo_mode, k=k, door_m=door_m, scale_mode=scale_mode, wall_m=wall_m,
                       house_width_m=house_width_m, px_per_m=px_per_m, aspect=aspect, use_flatten=use_flatten,
                       use_hollow=use_hollow, use_color=use_color, unet_mask=unet_mask)
    res["total_s"] = time.perf_counter() - t0
    model = core.to_model(res)
    return res, model


def to_rgb(im):
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB) if im.ndim == 3 else im


# ---------------- sidebar: đầu vào + tham số ----------------
with st.sidebar:
    st.header("Đầu vào")
    source = st.segmented_control("Nguồn ảnh", ["Ảnh mẫu", "Tải ảnh lên"], default="Ảnh mẫu", key="source")
    sample_dir, img_bytes, default_photo = None, None, True
    if source == "Tải ảnh lên":
        up = st.file_uploader("Ảnh bản vẽ mặt bằng (JPG/PNG)", type=["jpg", "jpeg", "png"])
        if up is not None:
            img_bytes = up.getvalue()
    else:
        options = [SYNTH] + list(cubicasa_samples())
        choice = st.selectbox("Chọn ảnh mẫu", options, key="sample")
        if choice == SYNTH:
            img_bytes = synthetic_photo()
        else:
            sample_dir = cubicasa_samples()[choice]
            img_bytes = open(os.path.join(sample_dir, "F1_scaled.png"), "rb").read()
            default_photo = False

    mode = st.segmented_control("Loại ảnh", ["Ảnh chụp điện thoại", "Ảnh scan"],
                                default="Ảnh chụp điện thoại" if default_photo else "Ảnh scan", key=f"mode_{default_photo}")
    photo_mode = mode == "Ảnh chụp điện thoại"
    aspect = None
    if photo_mode:
        paper = st.selectbox("Khổ giấy", ["A-series (A4, A3…) 1:1.414", "Tỉ lệ 1:1.25 (ảnh mô phỏng)", "Ước lượng từ ảnh"],
                             index=1 if source == "Ảnh mẫu" else 0, key=f"paper_{source}")
        aspect = {"A-series (A4, A3…) 1:1.414": 2 ** 0.5, "Tỉ lệ 1:1.25 (ảnh mô phỏng)": 1.25}.get(paper)

    st.header("Tỉ lệ bản vẽ")
    scale_opts = {"Bề rộng ngôi nhà (m)": "width", "Giả định độ dày tường": "wall", "Nhập px/m": "manual"}
    scale_label = st.selectbox("Cách tính tỉ lệ", list(scale_opts),
                               index=0 if (source == "Ảnh mẫu" and sample_dir is None) else 2, key=f"scale_{source}_{sample_dir is None}")
    scale_mode = scale_opts[scale_label]
    house_width_m = wall_m = px_per_m = None
    if scale_mode == "width":
        house_width_m = st.number_input("Bề rộng phủ bì của nhà (m)", 2.0, 100.0, 12.25, 0.05)
    elif scale_mode == "wall":
        wall_m = st.number_input("Độ dày tường giả định (m)", 0.05, 0.6, 0.25, 0.01)
    else:
        px_per_m = st.number_input("Pixel trên mét", 5.0, 1000.0, 112.0, 1.0,
                                   help="112 px/m là giá trị tương ứng với tham số đã chọn trên tập val CubiCasa5K.")

    st.header("Tham số")
    k = st.slider("Kích thước opening k (px)", 3, 21, 7, 2, help="Tham số cuối chọn trên tập val: k = 7.")
    door_m = st.slider("Khe cửa tối đa được đóng (m)", 0.5, 3.0, 2.2 if default_photo else 1.6, 0.1,
                       key=f"door_{default_photo}", help="Chọn trên tập val: 1.6 m (CubiCasa). Ảnh mô phỏng: 2.2 m.")
    with st.expander("Ablation: bật/tắt từng khối", expanded=True):
        use_flatten = st.toggle("Làm phẳng chiếu sáng", True, key="use_flatten")
        use_hollow = st.toggle("Lấp tường rỗng", True, key="use_hollow")
        use_color = st.toggle("Kênh màu", True, key="use_color")
    use_unet = False
    if os.path.exists(UNET_PATH):
        use_unet = st.toggle("Dùng U-Net cho mask tường", False, key="use_unet")
    else:
        st.caption(":material/info: Chưa có model U-Net (chạy `unet_wall.py train` để bật so sánh).")

# ---------------- main ----------------
st.title("Plan2Model")
st.caption("Ảnh chụp bản vẽ mặt bằng giấy → bản vẽ CAD (DXF) → mô hình 3D, bằng xử lý ảnh cổ điển.")

if img_bytes is None:
    st.info("Chọn ảnh mẫu hoặc tải ảnh bản vẽ lên ở thanh bên trái.", icon=":material/upload:")
    st.stop()

try:
    res, model = run_pipeline(img_bytes, photo_mode, k, door_m, scale_mode, wall_m, house_width_m, px_per_m, aspect,
                              use_flatten, use_hollow, use_color, use_unet)
except RuntimeError as e:
    st.error(f"{e}. Thử chuyển 'Loại ảnh' sang 'Ảnh scan', hoặc chụp lại để thấy đủ 4 góc tờ giấy.",
             title="Không tìm thấy tờ giấy")
    st.stop()

rooms = res["rooms"]
total_area = sum(r["area_m2"] for r in rooms)

# Đánh giá với ground truth nếu là ảnh CubiCasa (cùng hệ toạ độ ảnh scan)
gt_metrics = None
if sample_dir is not None and not photo_mode:
    gw, gr = load_sample_gt(sample_dir, res["walls"].shape)
    from eval_cubicasa import room_scores
    rs = room_scores(rooms, gr) or {}
    gt_metrics = {"wall_IoU": P.iou(res["walls"], gw), "room_F1": rs.get("room_F1"), "n_gt": len(gr)}

with st.container(horizontal=True):
    st.metric("Số phòng", len(rooms), border=True)
    st.metric("Tổng diện tích sàn", f"{total_area:.1f} m²", border=True)
    st.metric("Thời gian xử lý", f"{res['total_s'] * 1000:.0f} ms", border=True)
    st.metric("Tỉ lệ", f"{res['ppm']:.1f} px/m", border=True)
    if gt_metrics:
        st.metric("Wall IoU (so với nhãn)", f"{gt_metrics['wall_IoU']:.3f}", border=True)
        if gt_metrics["room_F1"] is not None:
            st.metric("Room F1 (so với nhãn)", f"{gt_metrics['room_F1']:.3f}", border=True)

tabproc, tab3d, tabrooms, tabexport = st.tabs(
    [":material/account_tree: Quá trình xử lý", ":material/view_in_ar: Mô hình 3D",
     ":material/table: Phòng & diện tích", ":material/download: Xuất file"])


def letterbox(im, W, H):
    """Thu ảnh vừa khung W×H, phần thừa tô màu nền tối, để các ảnh nhỏ cao bằng nhau."""
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
    s = min(W / im.shape[1], H / im.shape[0])
    sm = cv2.resize(im, (max(1, int(im.shape[1] * s)), max(1, int(im.shape[0] * s))), interpolation=cv2.INTER_AREA)
    out = np.full((H, W, 3), 40, np.uint8)
    y, x = (H - sm.shape[0]) // 2, (W - sm.shape[1]) // 2
    out[y:y + sm.shape[0], x:x + sm.shape[1]] = sm
    return out


@st.cache_data(max_entries=16)
def process_steps(img_bytes, *args):
    res, _ = run_pipeline(img_bytes, *args)
    steps = explain.build_steps(res)
    for x in steps:  # ảnh nhỏ cho dải tổng quan: lấy ảnh "kết quả" (ảnh thứ 2 nếu có ảnh phóng to, ngược lại ảnh cuối)
        im = x["images"][1][1] if len(x["images"]) == 3 and x["key"] in ("hollow", "opening") else x["images"][-1][1]
        if x["key"] == "doors" and len(x["images"]) == 2:
            im = x["images"][0][1]
        x["thumb"] = letterbox(im, 200, 150)
    return steps


STEPS = process_steps(img_bytes, photo_mode, k, door_m, scale_mode, wall_m, house_width_m, px_per_m, aspect,
                      use_flatten, use_hollow, use_color, use_unet)
SHORTS = [f"{i + 1}. {s['short']}" for i, s in enumerate(STEPS)]
ss = st.session_state
if ss.get("step_pick") not in SHORTS:  # đổi ảnh / chế độ làm số bước thay đổi
    ss.step_pick = SHORTS[0]


def go(delta):
    i = SHORTS.index(ss.step_pick) + delta
    ss.step_pick = SHORTS[max(0, min(len(SHORTS) - 1, i))]


def toggle_play():
    ss.autoplay = not ss.get("autoplay", False)
    if ss.autoplay and ss.step_pick == SHORTS[-1]:
        ss.step_pick = SHORTS[0]
    ss.last_tick = time.time()


@st.fragment(run_every=ss.get("play_every", 6) if ss.get("autoplay") else None)
def process_view():
    if ss.get("autoplay") and time.time() - ss.get("last_tick", 0) >= ss.get("play_every", 6) - 0.2:
        ss.last_tick = time.time()
        if ss.step_pick == SHORTS[-1]:
            ss.autoplay = False
            st.rerun(scope="app")
        go(+1)

    with st.container(horizontal=True, vertical_alignment="center"):
        st.button("Bước trước", icon=":material/chevron_left:", on_click=go, args=(-1,),
                  disabled=ss.step_pick == SHORTS[0], key="prev")
        st.button("Bước sau", icon=":material/chevron_right:", on_click=go, args=(+1,),
                  disabled=ss.step_pick == SHORTS[-1], key="next")
        playing = ss.get("autoplay", False)
        if st.button("Dừng" if playing else "Tự chạy từng bước", icon=":material/pause:" if playing else ":material/play_arrow:",
                     on_click=toggle_play, type="primary" if not playing else "secondary", key="play"):
            st.rerun(scope="app")
        ss.play_every = st.select_slider("Mỗi bước (giây)", [3, 4, 6, 8, 10, 15], value=ss.get("play_every", 6),
                                         label_visibility="collapsed", width=180, disabled=playing)
    # --- tổng quan: dải ảnh nhỏ của tất cả các bước, bấm để chọn ---
    cur = SHORTS.index(ss.step_pick)
    for col, (j, st_) in zip(st.columns(len(STEPS), gap="small", vertical_alignment="bottom"), enumerate(STEPS)):
        with col:
            st.image(st_["thumb"], width="stretch", caption=st_["short"])
            st.button(f"{j + 1}", key=f"thumb_{j}", width="stretch", help=st_["title"],
                      type="primary" if j == cur else "tertiary",
                      on_click=lambda j=j: ss.update(step_pick=SHORTS[j]))

    s = STEPS[cur]
    st.progress((cur + 1) / len(STEPS), text=f"Bước {cur + 1}/{len(STEPS)}")

    # --- chi tiết: ảnh bên trái (giới hạn chiều cao), giải thích bên phải ---
    MAXH = 340
    left, right = st.columns([3, 2], gap="large")
    with left:
        imgs = s["images"]
        for col, (cap, im) in zip(st.columns(len(imgs)), imgs):
            h, w = im.shape[:2]
            im = cv2.resize(im, (max(1, int(MAXH * w / h)), MAXH), interpolation=cv2.INTER_AREA)
            col.image(im, caption=cap, width="content")
        if s["chart"] is not None and s["key"] == "light":
            st.line_chart(s["chart"], height=220, x_label="Vị trí theo chiều ngang (px)", y_label="Độ sáng",
                          color=["#9aa3b2", "#ff8c42", "#2b8cff"])
            st.caption(s["chart_caption"])
    with right:
        st.subheader(s["title"])
        st.markdown(f":material/target: **Làm gì:** {s['what']}")
        if s["stats"]:
            with st.container(horizontal=True):
                for lab, val in s["stats"]:
                    st.metric(lab, val, border=True)
        with st.expander(":material/settings: **Cách làm**", expanded=True):
            st.markdown(s["how"])
            if s["chart"] is not None and s["key"] != "light":
                st.caption(s["chart_caption"])
                st.dataframe(s["chart"], hide_index=True)
        with st.expander(":material/help: **Vì sao cần bước này**", expanded=True):
            st.markdown(s["why"])

    # --- kỹ thuật, hàm, công thức, code của bước này ---
    t = s.get("tech")
    if t:
        with st.container(border=True):
            st.markdown(f"#### :material/code: Kỹ thuật & hàm sử dụng\n:gray[Chủ đề trong môn:] **{t['topic']}**")
            st.markdown("**Hàm đã dùng**")
            st.markdown("| Hàm | Tham số | Tác dụng |\n|---|---|---|\n" + "\n".join(
                f"| `{f}` | {p} | {u} |" for f, p, u in t["funcs"]))
            a, b = st.columns(2, gap="large")
            with a:
                st.markdown("**Thuật toán từng bước**")
                st.markdown("\n".join(f"{n}. {line}" for n, line in enumerate(t["algo"], 1)))
            with b:
                st.markdown("**Công thức**")
                for f in t["formulas"]:
                    st.latex(f)
                st.markdown("**Code trong dự án (rút gọn)**")
                st.code(t["code"], language="python")

with tabproc:
    process_view()
    with st.expander("Thời gian chạy từng khối"):
        st.dataframe(pd.DataFrame({"Khối": list(res["timing"]),
                                   "ms": [round(v * 1000, 1) for v in res["timing"].values()]}),
                     hide_index=True, alt="Thời gian từng khối xử lý")

with tab3d:
    c1, c2 = st.columns([3, 2])
    with c1:
        st.iframe(core.viewer_html(model, 520), height=530, alt="Mô hình 3D dựng từ bản vẽ")
    with c2:
        st.image(to_rgb(res["overlay"]), caption="Tường (xám đậm) và phòng", width="stretch")

with tabrooms:
    df = pd.DataFrame([{"Phòng": r["name"], "Diện tích (m²)": round(r["area_m2"], 2),
                        "Tỉ lệ (%)": round(100 * r["area_m2"] / max(total_area, 1e-9), 1)} for r in rooms])
    st.dataframe(df, hide_index=True, alt="Danh sách phòng và diện tích",
                 column_config={"Tỉ lệ (%)": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%")})
    st.caption("Diện tích là diện tích thông thủy (phần sàn bên trong tường), nhỏ hơn diện tích tính theo tim tường.")

with tabexport:
    st.download_button("Tải bản vẽ DXF (AutoCAD / Revit)", core.to_dxf_bytes(model), "plan2model.dxf",
                       mime="application/dxf", icon=":material/architecture:", width="stretch")
    st.download_button("Tải mô hình JSON", json.dumps(model, ensure_ascii=False, indent=1), "plan2model.json",
                       mime="application/json", icon=":material/data_object:", width="stretch")
    st.download_button("Tải trang 3D (HTML)", core.viewer_html(model, 700), "plan2model_3d.html",
                       mime="text/html", icon=":material/view_in_ar:", width="stretch")
    st.download_button("Tải ảnh kết quả (PNG)", cv2.imencode(".png", res["overlay"])[1].tobytes(), "plan2model.png",
                       mime="image/png", icon=":material/image:", width="stretch")
    st.caption("DXF có 3 layer: WALL (đa giác tường), ROOM (đa giác phòng), TEXT (tên + diện tích), đơn vị mét.")
