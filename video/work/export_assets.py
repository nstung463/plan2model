"""Xuất ảnh từng bước của pipeline (đúng như app) ra PNG cho HyperFrames."""
import json, os, sys
import cv2, numpy as np
ROOT = r"F:\Project_Nhom_MSE"
sys.path.insert(0, os.path.join(ROOT, "prototype"))
import core, explain, synth  # noqa: E402

OUT = os.path.join(ROOT, "video", "hf", "assets", "steps")
os.makedirs(OUT, exist_ok=True)


def save(name, im_rgb, max_side=1400):
    im = cv2.cvtColor(np.asarray(im_rgb), cv2.COLOR_RGB2BGR) if im_rgb.ndim == 3 else im_rgb
    s = min(1.0, max_side / max(im.shape[:2]))
    if s < 1:
        im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    p = os.path.join(OUT, name + ".jpg")
    cv2.imwrite(p, im, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return {"file": "assets/steps/" + name + ".jpg", "w": im.shape[1], "h": im.shape[0]}


def dump(tag, res):
    steps = explain.build_steps(res)
    meta = []
    for st in steps:
        imgs = [dict(caption=c, **save(f"{tag}_{st['key']}_{i}", im)) for i, (c, im) in enumerate(st["images"])]
        meta.append(dict(key=st["key"], title=st["title"], stats=st["stats"], images=imgs))
        if st["chart"] is not None:
            st["chart"].to_csv(os.path.join(OUT, f"{tag}_{st['key']}_chart.csv"), encoding="utf-8")
    return meta


page, _ = synth.draw_plan()
photo = synth.simulate_photo(page)
res = core.process(photo, True, k=7, door_m=2.2, scale_mode="width", house_width_m=12.25)
info = {"demo": dump("demo", res),
        "demo_rooms": [dict(area=round(r["area_m2"], 1)) for r in res["rooms"]],
        "demo_time_s": res.get("t", None) if isinstance(res.get("t"), (int, float)) else None}
json.dump(core.to_model(res), open(os.path.join(OUT, "demo_model.json"), "w", encoding="utf-8"), ensure_ascii=False)

d = os.path.join(ROOT, "prototype", "data", "cubicasa", "test", "high_quality_architectural_875")
img = cv2.imread(os.path.join(d, "F1_scaled.png"))
for tag, hollow in [("cc", True), ("ccoff", False)]:
    r = core.process(img, False, k=7, door_m=1.6, scale_mode="manual", px_per_m=112.0, use_hollow=hollow)
    info[tag] = dump(tag, r)
    info[tag + "_rooms"] = len(r["rooms"])
json.dump(info, open(os.path.join(OUT, "steps.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: [(s["key"], [i["caption"] for i in s["images"]], s["stats"]) for s in v] if isinstance(v, list) and v and isinstance(v[0], dict) and "key" in v[0] else v
                  for k, v in info.items() if k in ("demo", "demo_rooms", "cc_rooms", "ccoff_rooms")}, ensure_ascii=False, indent=0, default=str))
