"""Thư viện nhỏ sinh composition HyperFrames (HTML tĩnh, mỗi phần tử có id và thời gian cố định)."""
import json, re, unicodedata, html as _html

INK, ACC, GROUND, PAPER = "#14171A", "#E04410", "#E9ECEA", "#FFFFFF"
ROOMC = ["#5BC0EB", "#FDA65D", "#9BE08C", "#C7A5F5", "#6C8EF5"]

FONTS = "\n".join(
    f"@font-face{{font-family:'BVP';font-weight:{w};font-style:normal;font-display:block;"
    f"src:url('assets/fonts/bvp-{s}-{w}.woff2') format('woff2');unicode-range:{r};}}"
    for w in (400, 600, 800, 900)
    for s, r in [("latin", "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"),
                 ("latin-ext", "U+0100-02AF,U+0304,U+0308,U+0329,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"),
                 ("vietnamese", "U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB")])

BASE_CSS = FONTS + f"""
#root{{position:absolute;inset:0;font-family:'BVP',sans-serif;color:{INK};}}
.abs{{position:absolute;}}
.card{{position:absolute;background:{PAPER};padding:12px;box-shadow:0 18px 40px rgba(20,23,26,.18),0 2px 6px rgba(20,23,26,.08);}}
.card img{{display:block;width:100%;height:100%;object-fit:contain;}}
.cap{{position:absolute;left:0;right:0;top:100%;margin-top:12px;font-weight:600;font-size:30px;color:{INK};opacity:.85;}}
.title{{position:absolute;left:96px;top:70px;font-weight:900;font-size:64px;letter-spacing:-0.02em;line-height:1.05;white-space:nowrap;}}
.title .w{{display:inline-block;}}
.code{{position:absolute;font-family:'IBM Plex Mono',monospace;font-size:28px;font-weight:600;background:{INK};color:#F4F5F2;padding:16px 24px;white-space:pre;line-height:1.45;}}
.code .k{{color:{ACC};}}
.big{{position:absolute;font-weight:900;color:{ACC};letter-spacing:-0.03em;line-height:1;}}
.note{{position:absolute;font-weight:600;font-size:34px;line-height:1.3;}}
.note b{{font-weight:900;color:{ACC};}}
"""


def esc(s):
    return _html.escape(s, quote=False)


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
    return re.sub(r"[^a-z0-9]", "", s)


class Words:
    def __init__(self, words):
        self.w = words
        self.text, self.idx = "", []
        for i, w in enumerate(words):
            n = norm(w["text"])
            self.text += n
            self.idx += [i] * len(n)

    def find(self, phrase, after=0.0, end=False):
        p = norm(phrase)
        start_char = next((c for c, i in enumerate(self.idx) if self.w[i]["start"] >= after - 0.01), len(self.text))
        k = self.text.find(p, start_char)
        if k < 0:
            print("MISS:", phrase, round(after,1))
            raise KeyError(f"không thấy '{phrase}' sau {after:.1f}s")
        i0, i1 = self.idx[k], self.idx[k + len(p) - 1]
        return self.w[i1]["end"] if end else self.w[i0]["start"]


class Scene:
    """Một sub-composition. Thời gian truyền vào là thời gian TUYỆT ĐỐI của video; tự đổi sang thời gian cục bộ."""

    def __init__(self, sid, start, end, title=None):
        self.id, self.t0, self.t1 = sid, start, end
        self.dur = round(end - start, 3)
        self.html, self.js, self.css = [], [], []
        self.n = 0
        self.slots = {}
        if title:
            self.title(title)

    def L(self, t):  # tuyệt đối -> cục bộ, kẹp trong cảnh
        return round(min(max(t - self.t0, 0.0), self.dur - 0.05), 3)

    def uid(self, p):
        self.n += 1
        return f"{self.id}-{p}{self.n}"

    # --- phần tử ---------------------------------------------------------------
    def clip(self, inner, t_in, t_out=None, style="", cls="", eid=None, attrs=""):
        eid = eid or self.uid("e")
        a, b = self.L(t_in), self.L(t_out) if t_out is not None else self.dur
        b = max(b, a + 0.2)
        self.html.append(f'<div id="{eid}" class="clip abs {cls}" data-start="{a}" data-duration="{round(b - a, 3)}" '
                         f'style="{style}" {attrs}><div id="{eid}-in" style="position:relative;width:100%;height:100%;">{inner}</div></div>')
        return eid, a, b

    def title(self, text, t=None):
        words = text.split()
        inner = " ".join(f'<span class="w" id="{self.id}-tw{i}">{esc(w)}</span>' for i, w in enumerate(words))
        eid = f"{self.id}-title"
        self.html.append(f'<div id="{eid}" class="clip title" data-start="0" data-duration="{self.dur}"><div id="{eid}-in">{inner}</div></div>')
        t0 = 0.15 if t is None else self.L(t)
        for i in range(len(words)):
            self.js.append(f'tl.fromTo("#{self.id}-tw{i}",{{opacity:0,filter:"blur(6px)"}},{{opacity:1,filter:"blur(0px)",duration:0.13,ease:"power2.out"}},{t0 + i * 0.067:.3f});')
        self.exit(eid, self.dur)

    def card(self, src, x, y, w, h, t_in, t_out=None, cap=None, enter="rise", eid=None, exit_kind="blur", pad=12):
        eid = eid or self.uid("c")
        capd = f'<div class="cap">{esc(cap)}</div>' if cap else ""
        inner = f'<img src="{src}" alt="" style="width:100%;height:100%;object-fit:contain;display:block;">'
        eid, a, b = self.clip(f'<div class="card" id="{eid}-c" style="left:0;top:0;width:{w}px;height:{h}px;padding:{pad}px;">{inner}{capd}</div>',
                              t_in, t_out, style=f"left:{x}px;top:{y}px;width:{w}px;height:{h}px;", eid=eid,
                              attrs='data-layout-allow-overflow')
        self.enter(eid, a, enter)
        # ảnh mới đặt đúng chỗ ảnh cũ: ảnh cũ rời đi khi ảnh mới đã vào (không chồng chú thích)
        prev = self.slots.get((x, y))
        if prev and t_out is None:
            pid, pidx, pa, pb = prev
            nb = round(a + 0.45, 3)
            if pa < nb < pb:
                self.html[pidx] = self.html[pidx].replace(f'data-duration="{round(pb - pa, 3)}"', f'data-duration="{round(nb - pa, 3)}"', 1)
                self.js = [j for j in self.js if not j.startswith(f'tl.to("#{pid}-in",{{opacity:0')]
                self.js.append(f'tl.to("#{pid}-in",{{opacity:0,filter:"blur(6px)",duration:0.25,ease:"power2.in"}},{nb - 0.27:.3f});')
        self.slots[(x, y)] = (eid, len(self.html) - 1, a, b)
        if t_out is not None or exit_kind:
            self.exit(eid, b, exit_kind)
        return eid

    def text(self, html_inner, x, y, t_in, t_out=None, cls="note", style="", enter="blur", w=None, eid=None):
        wcss = f"width:{w}px;" if w else ""
        eid, a, b = self.clip(f'<div class="{cls}" style="position:relative;{wcss}{style}">{html_inner}</div>', t_in, t_out,
                              style=f"left:{x}px;top:{y}px;{wcss}", eid=eid)
        self.enter(eid, a, enter)
        self.exit(eid, b)
        return eid

    def code(self, code_html, x, y, t_in, t_out=None, enter="wipe", z=None):
        zc = f"z-index:{z};" if z else ""
        eid, a, b = self.clip(f'<div class="code" style="position:relative;">{code_html}</div>', t_in, t_out, style=f"left:{x}px;top:{y}px;{zc}")
        self.enter(eid, a, enter)
        self.exit(eid, b)
        return eid

    def count(self, x, y, size, v0, v1, t, dec=2, suffix="", t_out=None, color=ACC, dur=0.9, comma=True, prefix=""):
        eid = self.uid("n")
        fmt0 = f"{v0:.{dec}f}".replace(".", "," if comma else ".")
        eid, a, b = self.clip(f'<div class="big" style="position:relative;font-size:{size}px;color:{color};white-space:nowrap;">{prefix}<span id="{eid}-v">{fmt0}</span>{suffix}</div>',
                              t, t_out, style=f"left:{x}px;top:{y}px;", eid=eid)
        self.enter(eid, a, "pop")
        sep = "," if comma else "."
        self.js.append(f'(function(){{const o={{v:{v0}}};const el=document.getElementById("{eid}-v");'
                       f'tl.fromTo(o,{{v:{v0}}},{{v:{v1},duration:{dur},ease:"power2.out",onUpdate:()=>{{el.textContent=o.v.toFixed({dec}).replace(".","{sep}");}}}},{a + 0.1:.3f});}})();')
        self.exit(eid, b)
        return eid

    def appwin(self, src, t_in, dur, mstart=0.0, punch=(), label="localhost:8501", x=70, y=58, w=1640):
        """Cửa sổ trình duyệt chứa clip app thật. Video được định thời, khung bao ngoài không định thời (chỉ tween)."""
        eid = self.uid("aw")
        a = self.L(t_in)
        b = round(min(a + dur, self.dur - 0.05), 3)
        h = round(w * 9 / 16)
        bar = (f'<div style="height:44px;background:#E3E5E8;display:flex;align-items:center;gap:10px;padding:0 16px;border-bottom:1px solid #C9CDD2">'
               f'<span style="width:13px;height:13px;border-radius:50%;background:#FF5F57"></span><span style="width:13px;height:13px;border-radius:50%;background:#FEBC2E"></span>'
               f'<span style="width:13px;height:13px;border-radius:50%;background:#28C840"></span>'
               f'<span style="margin-left:18px;background:#fff;border-radius:8px;padding:5px 16px;font-family:\'IBM Plex Mono\',monospace;font-size:19px;font-weight:600;color:#3C4043;min-width:420px">{esc(label)}</span>'
               f'<span style="margin-left:auto;font-weight:800;font-size:19px;color:{ACC}">● App thật đang chạy</span></div>')
        self.html.append(
            f'<div id="{eid}" class="abs" style="left:{x}px;top:{y}px;width:{w}px;height:{h + 44}px;opacity:0;z-index:50" data-layout-allow-overflow data-layout-allow-overlap data-layout-ignore>'
            f'<div id="{eid}-z" style="position:absolute;inset:0;background:#fff;box-shadow:0 30px 70px rgba(20,23,26,.30);border-radius:12px;overflow:hidden">{bar}'
            f'<div style="position:absolute;left:0;top:44px;width:{w}px;height:{h}px;overflow:hidden"><div id="{eid}-s" style="position:absolute;inset:0">'
            f'<video id="{eid}-v" class="clip" src="{src}" data-start="{a}" data-duration="{round(b - a, 3)}" data-media-start="{mstart}" muted playsinline '
            f'style="position:absolute;left:0;top:0;width:{w}px;height:{h}px;object-fit:cover;background:#fff"></video></div></div></div></div>')
        self.js.append(f'tl.set("#{eid}",{{opacity:0}},0);')
        self.js.append(f'tl.fromTo("#{eid}",{{opacity:0,scale:0.9,y:40,filter:"blur(12px)"}},{{opacity:1,scale:1,y:0,filter:"blur(0px)",duration:0.75,ease:"expo.out"}},{a:.3f});')
        self.js.append(f'tl.to("#{eid}",{{opacity:0,scale:0.86,y:30,filter:"blur(12px)",duration:0.4,ease:"power3.in"}},{max(b - 0.42, a + 0.8):.3f});')
        for tr, sc, ox, oy in punch:
            self.js.append(f'tl.to("#{eid}-s",{{scale:{sc},transformOrigin:"{ox}% {oy}%",duration:0.9,ease:"power2.inOut"}},{a + tr:.3f});')
        return eid, a, b

    def tween_to(self, eid, t, props, dur=0.6, ease="power2.inOut"):
        self.js.append(f'tl.to("#{eid}-in",{{{props},duration:{dur},ease:"{ease}"}},{self.L(t):.3f});')

    def raw(self, html):
        self.html.append(html)

    # --- chuyển động vào / ra -------------------------------------------------------
    def enter(self, eid, a, kind):
        s = f"#{eid}-in"
        T = {
            "rise": ('{opacity:0,y:46,filter:"blur(10px)"}', '{opacity:1,y:0,filter:"blur(0px)",duration:0.8,ease:"expo.out"}'),
            "left": ('{opacity:0,x:-90,filter:"blur(12px)"}', '{opacity:1,x:0,filter:"blur(0px)",duration:0.75,ease:"expo.out"}'),
            "right": ('{opacity:0,x:90,filter:"blur(12px)"}', '{opacity:1,x:0,filter:"blur(0px)",duration:0.75,ease:"expo.out"}'),
            "scale": ('{opacity:0,scale:0.9,filter:"blur(8px)"}', '{opacity:1,scale:1,filter:"blur(0px)",duration:0.9,ease:"expo.out"}'),
            "big": ('{opacity:0,scale:1.12,filter:"blur(14px)"}', '{opacity:1,scale:1,filter:"blur(0px)",duration:0.9,ease:"expo.out"}'),
            "blur": ('{opacity:0,filter:"blur(8px)"}', '{opacity:1,filter:"blur(0px)",duration:0.2,ease:"power2.out"}'),
            "pop": ('{opacity:0,scale:0.6,filter:"blur(6px)"}', '{opacity:1,scale:1,filter:"blur(0px)",duration:0.55,ease:"back.out(1.6)"}'),
            "wipe": ('{clipPath:"inset(0 100% 0 0)"}', '{clipPath:"inset(0 0% 0 0)",duration:0.5,ease:"power3.out"}'),
            "drop": ('{opacity:0,y:-60,rotation:-3,filter:"blur(8px)"}', '{opacity:1,y:0,rotation:0,filter:"blur(0px)",duration:0.85,ease:"expo.out"}'),
            "none": None,
        }[kind]
        if T:
            self.js.append(f'tl.fromTo("{s}",{T[0]},{T[1]},{a:.3f});')

    def exit(self, eid, b, kind="blur"):
        if not kind:
            return
        s = f"#{eid}-in"
        if kind == "blur":
            self.js.append(f'tl.to("{s}",{{opacity:0,filter:"blur(8px)",duration:0.22,ease:"power3.in"}},{max(b - 0.24, 0):.3f});')
        elif kind == "up":
            self.js.append(f'tl.to("{s}",{{opacity:0,y:-60,filter:"blur(10px)",duration:0.35,ease:"power3.in"}},{max(b - 0.37, 0):.3f});')
        elif kind == "zoom":
            self.js.append(f'tl.to("{s}",{{opacity:0,scale:1.6,filter:"blur(16px)",duration:0.4,ease:"power3.in"}},{max(b - 0.42, 0):.3f});')

    # --- xuất file ------------------------------------------------------------------
    def render(self):
        return f"""<template>
<style>
{BASE_CSS}
{''.join(self.css)}
</style>
<div id="root" data-composition-id="{self.id}" data-width="1920" data-height="1080" data-start="0" data-duration="{self.dur}">
{chr(10).join(self.html)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(self.js)}
window.__timelines["{self.id}"] = tl;
</script>
</template>
"""
