# Phần 3: phụ đề + index.html (nền, mặt, watermark, âm thanh) + ghi file

# ---------------- phụ đề ----------------
words = ed["words"]
groups, cur = [], []
for i, w in enumerate(words):
    if cur:
        gap = w["start"] - cur[-1]["end"]
        prev = cur[-1]["text"]
        if gap >= 0.35 or len(cur) >= 7 or prev.endswith((".", "?", "!", ",")) and len(cur) >= 3:
            groups.append(cur)
            cur = []
    cur.append(w)
if cur:
    groups.append(cur)
cap_html, cap_js = [], []
for gi, g in enumerate(groups):
    a = round(max(g[0]["start"] - 0.08, 0.1), 3)
    nxt = groups[gi + 1][0]["start"] - 0.05 if gi + 1 < len(groups) else D
    b = round(min(max(g[-1]["end"] + 0.35, a + 0.6), nxt, D - 0.05), 3)
    spans = " ".join(f'<span id="cw{gi}_{k}">{esc(w["text"])}</span>' for k, w in enumerate(g))
    cap_html.append(f'<div id="cg{gi}" class="clip cgrp" data-start="{a}" data-duration="{round(b - a, 3)}"><div class="cbox" id="cg{gi}-in">{spans}</div></div>')
    cap_js.append(f'tl.fromTo("#cg{gi}-in",{{opacity:0}},{{opacity:1,duration:0.12,ease:"power2.out"}},{a:.3f});')
    for k, w in enumerate(g):
        ws_ = max(w["start"], a)
        we_ = min(max(w["end"], ws_ + 0.08), b - 0.12)
        if we_ > ws_:
            cap_js.append(f'tl.set("#cw{gi}_{k}",{{color:"{ACC}"}},{ws_:.3f});tl.set("#cw{gi}_{k}",{{color:"{INK}"}},{we_:.3f});')
    cap_js.append(f'tl.to("#cg{gi}-in",{{opacity:0,duration:0.1,ease:"power2.in"}},{b - 0.1:.3f});tl.set("#cg{gi}-in",{{opacity:0,visibility:"hidden"}},{b:.3f});')
captions = f"""<template>
<style>
{FONTS}
#root{{position:absolute;inset:0;font-family:'BVP',sans-serif;}}
.cgrp{{position:absolute;left:0;width:1540px;bottom:56px;text-align:center;overflow:visible;}}
.cbox{{display:inline-block;background:rgba(255,255,255,.92);color:{INK};font-weight:700;font-size:40px;line-height:1.25;padding:10px 22px;max-width:1360px;box-shadow:0 6px 18px rgba(20,23,26,.12);}}
</style>
<div id="root" data-composition-id="captions" data-width="1920" data-height="1080" data-start="0" data-duration="{D}">
{chr(10).join(cap_html)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(cap_js)}
window.__timelines["captions"] = tl;
</script>
</template>
"""

# ---------------- âm thanh: nhạc nền + hiệu ứng ở chỗ đổi phần lớn ----------------
audio = ['<audio id="voice" class="clip" src="assets/voice.wav" data-start="0" data-duration="%s" data-track-index="20" data-volume="1"></audio>' % D]
if os.path.exists(os.path.join(HF, "assets/bgm.wav")):
    audio.append(f'<audio id="bgm" class="clip" src="assets/bgm.wav" data-start="0" data-duration="{DT}" data-track-index="21" data-volume="0.10" data-fade-in="1.5" data-fade-out="4"></audio>')
whoosh = ["whoosh.mp3"]
big_cuts = ["s2", "s3", "s41", "s5", "s6", "s7", "s8", "s9"]
sfx = []
for i, k in enumerate(big_cuts):
    sfx.append(f'<audio id="sfx{i}" class="clip" src="assets/sfx/whoosh.mp3" data-start="{max(T[k] - 0.15, 0):.3f}" data-duration="0.57" data-track-index="22" data-volume="0.22"></audio>')

# ---------------- index.html ----------------
hosts = []
for i, sc in enumerate(scenes):
    hosts.append(f'<div id="{sc.id}" data-composition-id="{sc.id}" data-composition-src="compositions/{sc.id}.html" data-start="{sc.t0}" '
                 f'data-duration="{sc.dur}" data-track-index="{1 + (i % 2)}" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:{10 + i}"></div>')
    open(os.path.join(HF, "compositions", sc.id + ".html"), "w", encoding="utf-8").write(sc.render())
open(os.path.join(HF, "compositions", "captions.html"), "w", encoding="utf-8").write(captions)

# lần đổi phần: vòng cam quanh mặt sáng lên
ring_js = 'tl.set("#face-ring",{opacity:0},0);' + "".join(f'tl.to("#face-ring",{{opacity:1,duration:0.2}},{T[k]:.3f});tl.to("#face-ring",{{opacity:0,duration:0.6}},{T[k] + 1.2:.3f});' for k in big_cuts)
# nhãn tên khi Tùng tự giới thiệu
t_name = A("tùng")
index = f"""<!doctype html>
<html lang="vi" data-composition-variables='[{{"id":"accent","type":"color","label":"Màu nhấn","default":"{ACC}"}},{{"id":"ground","type":"color","label":"Màu nền","default":"{GROUND}"}}]'>
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<script src="assets/vendor/three.min.js"></script>
<style>
{FONTS}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:{GROUND};}}
#root{{position:relative;width:1920px;height:1080px;font-family:'BVP',sans-serif;color:{INK};}}
#ground{{position:absolute;inset:0;background-color:{GROUND};
  background-image:linear-gradient(rgba(20,23,26,.09) 2px,transparent 2px),linear-gradient(90deg,rgba(20,23,26,.09) 2px,transparent 2px),
  linear-gradient(rgba(20,23,26,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(20,23,26,.05) 1px,transparent 1px);
  background-size:240px 240px,240px 240px,48px 48px,48px 48px;}}
#facebox{{position:absolute;left:1572px;top:732px;width:308px;height:308px;z-index:200;}}
#face-wrap{{position:absolute;inset:0;border-radius:50%;overflow:hidden;border:6px solid {INK};background:#000;box-shadow:0 14px 34px rgba(20,23,26,.28);}}
#face{{position:absolute;left:0;top:0;width:296px;height:296px;object-fit:cover;}}
#face-ring{{position:absolute;inset:-12px;border-radius:50%;border:5px solid {ACC};opacity:0;}}
#wm{{position:absolute;right:40px;top:30px;font-weight:600;font-size:22px;color:rgba(20,23,26,.68);z-index:210;letter-spacing:.01em;}}
#nameplate{{position:absolute;left:1240px;top:900px;z-index:205;}}
#nameplate-in{{background:{INK};color:#fff;padding:12px 22px 14px;font-weight:800;font-size:30px;line-height:1.15;}}
#nameplate-in small{{display:block;font-weight:700;font-size:28px;color:#FF8A5C;}}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DT}" data-width="1920" data-height="1080">
<div id="ground"></div>
{chr(10).join(hosts)}
<div id="caps" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{D}" data-track-index="5" data-track-kind="captions" data-width="1920" data-height="1080" style="z-index:150"></div>
<div id="facebox"><div id="face-ring"></div><div id="face-wrap">
<video id="face" class="clip" src="assets/face.mp4" data-start="0" data-duration="{D}" data-track-index="10" muted playsinline></video>
</div></div>
<div id="nameplate" class="clip" data-start="{max(t_name - 0.4, 0.2):.3f}" data-duration="4.5" data-track-index="11"><div id="nameplate-in">Nguyễn Sơn Tùng<small>Thuyết trình</small></div></div>
<div id="wm" data-layout-ignore class="clip" data-start="0" data-duration="{DT}" data-track-index="12">Plan2Model · Trang · Thụ · Tùng · Minh</div>
{chr(10).join(audio + sfx)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
tl.fromTo("#face-wrap",{{scale:0.6,opacity:0}},{{scale:1,opacity:1,duration:0.8,ease:"expo.out"}},0);
tl.fromTo("#nameplate-in",{{opacity:0,x:40}},{{opacity:1,x:0,duration:0.6,ease:"expo.out"}},{max(t_name - 0.4, 0.2):.3f});
tl.to("#nameplate-in",{{opacity:0,x:20,duration:0.3,ease:"power3.in"}},{max(t_name - 0.4, 0.2) + 4.1:.3f});
{ring_js}
tl.to("#face-wrap",{{scale:0.7,opacity:0,duration:0.5,ease:"power3.in"}},{D - 0.55:.3f});
window.__timelines["main"] = tl;
</script>
</body>
</html>
"""
open(os.path.join(HF, "index.html"), "w", encoding="utf-8").write(index)
print("scenes:", len(scenes), "caption groups:", len(groups), "duration:", D)
