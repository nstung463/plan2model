"""Lõi xử lý dùng chung cho app demo: ảnh -> tường -> phòng -> DXF / JSON / HTML 3D."""
import io, json, os, time
import cv2
import numpy as np
import ezdxf
import pipeline as P

HERE = os.path.dirname(os.path.abspath(__file__))


def rectify_auto(img, corners, long_side=1400, aspect=None):
    """Nắn phối cảnh. aspect = cạnh dài / cạnh ngắn của tờ giấy (A-series = 1.414).
    Nếu None: suy từ độ dài cạnh tứ giác (bị lệch khi chụp nghiêng nhiều)."""
    c = corners
    w = max(np.linalg.norm(c[1] - c[0]), np.linalg.norm(c[2] - c[3]))
    h = max(np.linalg.norm(c[3] - c[0]), np.linalg.norm(c[2] - c[1]))
    if aspect:
        W, H = (long_side, int(round(long_side / aspect))) if w >= h else (int(round(long_side / aspect)), long_side)
    else:
        s = long_side / max(w, h)
        W, H = int(round(w * s)), int(round(h * s))
    M = cv2.getPerspectiveTransform(c, np.float32([[0, 0], [W, 0], [W, H], [0, H]]))
    return cv2.warpPerspective(img, M, (W, H), flags=cv2.INTER_CUBIC)


def process(bgr, photo_mode=True, k=7, door_m=1.6, scale_mode="wall", wall_m=0.25, house_width_m=None,
            px_per_m=None, aspect=None, use_flatten=True, use_hollow=True, use_color=True, unet_mask=None):
    """Trả về dict gồm các ảnh trung gian, mask tường, danh sách phòng, đa giác tường, tỉ lệ và thời gian."""
    t, steps = {}, []
    dbg = dict(input=bgr, photo_mode=photo_mode, k=k, door_m=door_m, scale_mode=scale_mode, wall_m=wall_m,
               house_width_m=house_width_m, use_flatten=use_flatten, use_hollow=use_hollow, use_color=use_color,
               unet=unet_mask is not None)
    steps.append(("Ảnh đầu vào", bgr))
    work = bgr
    if photo_mode:
        t0 = time.perf_counter()
        corners, edges = P.find_page(bgr)
        dbg.update(corners=corners, edges=edges)
        det = bgr.copy()
        cv2.polylines(det, [corners.astype(np.int32)], True, (0, 220, 0), max(3, bgr.shape[1] // 250))
        work = rectify_auto(bgr, corners, aspect=aspect)
        t["Tìm & nắn trang"] = time.perf_counter() - t0
        steps += [("Phát hiện tờ giấy", det), ("Nắn phối cảnh", work)]

    t0 = time.perf_counter()
    gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
    even = P.flatten_illumination(gray) if use_flatten else gray
    ink = P.sauvola(even)
    dbg.update(work=work, gray=gray, even=even, ink=ink)
    t["Làm phẳng sáng + Sauvola"] = time.perf_counter() - t0
    steps += [("Làm phẳng chiếu sáng", even), ("Nhị phân Sauvola (tự cài)", ink)]

    t0 = time.perf_counter()
    if unet_mask is not None:
        walls = unet_mask
        steps.append(("Mask tường (U-Net)", walls))
    else:
        cand = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        dbg["ink_closed"] = cand.copy()
        if use_color:
            hsv = cv2.cvtColor(work, cv2.COLOR_BGR2HSV)
            color = (((hsv[..., 1] > 110) & (hsv[..., 2] > 90)) * 255).astype(np.uint8)
            dbg["color"] = color
            cand |= color
        dbg["pre_hollow"] = cand.copy()
        if use_hollow:
            cand = P.fill_hollow_walls(cand, r_max=14)
        dbg["cand"] = cand
        walls = P.extract_walls(cand, k)
        steps += [("Ứng viên tường (lấp tường rỗng)", cand), ("Mask tường (opening)", walls)]
    t["Tách tường"] = time.perf_counter() - t0

    # Tỉ lệ px/m
    dbg["walls"] = walls
    ys, xs = np.nonzero(walls)
    dbg["thick_px"] = P.estimate_thickness(walls)
    if scale_mode == "width" and house_width_m and xs.size:
        ppm = (xs.max() - xs.min() + 1) / house_width_m
    elif scale_mode == "manual" and px_per_m:
        ppm = px_per_m
    else:
        ppm = P.estimate_thickness(walls) / wall_m

    t0 = time.perf_counter()
    closed, rooms = P.segment_rooms(walls, ppm, max_door_m=door_m)
    rooms.sort(key=lambda r: -r["area_m2"])
    for i, r in enumerate(rooms):
        r["name"] = f"Phòng {i + 1}"
        r["short"] = f"P{i + 1}"  # cv2.putText không vẽ được dấu tiếng Việt
    t["Tách phòng"] = time.perf_counter() - t0
    steps.append(("Đóng cửa (closing theo phương)", closed))
    dbg.update(closed=closed, ppm=ppm)

    polys = P.wall_polygons(walls)
    vis = work.copy(); ov = vis.copy()
    pal = [(102, 179, 255), (255, 204, 102), (153, 230, 153), (255, 153, 204), (255, 153, 102), (102, 230, 255),
           (204, 204, 102), (180, 140, 255)]
    for i, r in enumerate(rooms):
        ov[r["mask"] > 0] = pal[i % len(pal)]
    ov[walls > 0] = (40, 40, 40)
    vis = cv2.addWeighted(vis, 0.35, ov, 0.65, 0)
    for r in rooms:
        cx, cy = map(int, r["centroid"])
        fs = max(0.5, work.shape[1] / 1800)
        for j, txt in enumerate([r["short"], f'{r["area_m2"]:.1f} m2']):
            (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, fs, 2)
            cv2.putText(vis, txt, (cx - tw // 2, cy + j * int(th * 1.6)), cv2.FONT_HERSHEY_SIMPLEX, fs, (0, 0, 0), 2, cv2.LINE_AA)
    steps.append(("Kết quả: tường + phòng", vis))
    return dict(work=work, walls=walls, rooms=rooms, wall_polys=polys, ppm=ppm, timing=t, steps=steps, overlay=vis,
                dbg=dbg)


def _to_m(p, ppm, origin):
    return (float((p[0] - origin[0]) / ppm), float(-(p[1] - origin[1]) / ppm))


def to_model(res):
    ys, xs = np.nonzero(res["walls"])
    origin = (xs.min(), ys.min()) if xs.size else (0, 0)
    ppm = res["ppm"]
    return {
        "walls": [{"outer": [_to_m(p, ppm, origin) for p in w["outer"]],
                   "holes": [[_to_m(p, ppm, origin) for p in h] for h in w["holes"]]} for w in res["wall_polys"]],
        "rooms": [{"name": r["name"], "area": round(r["area_m2"], 1),
                   "poly": [_to_m(p, ppm, origin) for p in r["poly_px"]],
                   "c": _to_m(r["centroid"], ppm, origin)} for r in res["rooms"]],
    }


def to_dxf_bytes(model):
    doc = ezdxf.new(); doc.units = ezdxf.units.M
    msp = doc.modelspace()
    for lay, col in [("WALL", 7), ("ROOM", 3), ("TEXT", 2)]:
        doc.layers.add(lay, color=col)
    for w in model["walls"]:
        for ring in [w["outer"], *w["holes"]]:
            msp.add_lwpolyline(ring, close=True, dxfattribs={"layer": "WALL"})
    for r in model["rooms"]:
        msp.add_lwpolyline(r["poly"], close=True, dxfattribs={"layer": "ROOM"})
        msp.add_text(f'{r["name"]} {r["area"]}m2', height=0.25, dxfattribs={"layer": "TEXT"}).set_placement(r["c"])
    buf = io.StringIO(); doc.write(buf)
    return buf.getvalue().encode("utf-8")


def viewer_html(model, height=520):
    tpl = open(os.path.join(HERE, "viewer3d.html"), encoding="utf-8").read()
    return tpl.replace("__MODEL__", json.dumps(model)).replace("__HEIGHT__", str(height))
