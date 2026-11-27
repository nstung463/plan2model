# Cảnh source code kiểu VS Code (chạy bằng exec trong build2.py). Code và cây thư mục là thật của dự án.
import re as _re

s = new("s8")
ROOTP = r"F:\Project_Nhom_MSE"
KW = set("def return import from as for in if else elif not and or while with class lambda None True False try except pass break continue yield".split())


def hl(line):
    out, i = [], 0
    for m in _re.finditer(r'(#.*$)|("[^"]*"|\'[^\']*\')|(\b\d+\.?\d*\b)|(\b[A-Za-z_]\w*\b)|(\s+)|(.)', line):
        c, st_, num, word, ws, other = m.groups()
        if c:
            out.append(f'<span style="color:#6A9955">{esc(c)}</span>')
        elif st_:
            out.append(f'<span style="color:#CE9178">{esc(st_)}</span>')
        elif num:
            out.append(f'<span style="color:#B5CEA8">{num}</span>')
        elif word:
            nxt = line[m.end():m.end() + 1]
            if word in KW:
                out.append(f'<span style="color:#C586C0">{word}</span>' if word in ("return", "import", "from", "for", "in", "if", "else", "while", "with") else f'<span style="color:#569CD6">{word}</span>')
            elif nxt == "(":
                out.append(f'<span style="color:#DCDCAA">{word}</span>')
            elif word in ("np", "cv2", "P", "json", "os", "csv"):
                out.append(f'<span style="color:#4EC9B0">{word}</span>')
            else:
                out.append(f'<span style="color:#9CDCFE">{word}</span>')
        elif ws:
            out.append(ws)
        else:
            out.append(esc(other))
    return "".join(out)


def code_block(path, a, b, pre):
    src = open(os.path.join(ROOTP, path), encoding="utf-8").read().split(chr(10))
    rows = []
    for n in range(a, b + 1):
        rows.append(f'<div id="{pre}-l{n}" style="display:flex;height:31px;white-space:pre"><span style="width:62px;text-align:right;padding-right:22px;color:#858585">{n}</span>'
                    f'<span>{hl(src[n - 1])}</span></div>')
    return "".join(rows)


X0, Y0, WW, HH = 40, 34, 1840, 1012
SB, ACT = 330, 54
EX = X0 + ACT + SB          # mép trái vùng soạn thảo
EW = WW - ACT - SB
TOPBAR, TABS = 34, 42
CODE_Y = Y0 + TOPBAR + TABS
CSS = "font-family:'IBM Plex Mono',monospace;font-size:21px;font-weight:500;"

tree = [("PROJECT_NHOM_MSE", 0, "root"), ("prototype", 1, "dir"), ("data", 2, "dirc"), ("models", 2, "dirc"), ("output", 2, "dirc"),
        ("core.py", 2, "py"), ("cubicasa_gt.py", 2, "py"), ("eval_cubicasa.py", 2, "py"), ("eval_unet.py", 2, "py"), ("explain.py", 2, "py"),
        ("fetch_cubicasa.py", 2, "py"), ("params.json", 2, "js"), ("pipeline.py", 2, "py"), ("RESULTS.md", 2, "md"), ("synth.py", 2, "py"),
        ("tech.py", 2, "py"), ("tune.py", 2, "py"), ("unet_wall.py", 2, "py"), ("report", 1, "dirc"), ("video", 1, "dirc"),
        ("app.py", 1, "py"), ("README.md", 1, "md"), ("requirements.txt", 1, "txt")]
ICON = {"py": ("#3B8EEA", "py"), "md": ("#519ABA", "M↓"), "js": ("#CBCB41", "{}"), "txt": ("#9DA5B4", "≡")}
rows = []
for i, (nm, lv, kind) in enumerate(tree):
    pad = 14 + lv * 16
    if kind == "root":
        rows.append(f'<div style="height:30px;line-height:30px;padding-left:12px;font-weight:700;font-size:17px;color:#BBBBBB;letter-spacing:.04em">⌄ {nm}</div>')
        continue
    if kind in ("dir", "dirc"):
        arrow = "⌄" if kind == "dir" else "›"
        rows.append(f'<div style="height:30px;line-height:30px;padding-left:{pad}px;color:#CCCCCC">{arrow}&nbsp; {nm}</div>')
        continue
    col, ic = ICON[kind]
    rid = "s8-tr-" + _re.sub(r"\W", "_", nm)
    rows.append(f'<div id="{rid}" style="height:30px;line-height:30px;padding-left:{pad + 14}px;color:#CCCCCC">'
                f'<span style="color:{col};font-weight:700;font-size:15px;display:inline-block;width:30px">{ic}</span>{nm}</div>')
explorer = "".join(rows)

frame = f"""
<div id="s8-ide" class="clip abs" data-start="0" data-duration="{s.dur}" style="left:{X0}px;top:{Y0}px;width:{WW}px;height:{HH}px;" data-layout-allow-overflow data-layout-allow-overlap data-layout-ignore>
<div id="s8-ide-in" style="position:absolute;inset:0;background:#1E1E1E;border-radius:10px;overflow:hidden;box-shadow:0 30px 70px rgba(20,23,26,.35);font-family:'BVP',sans-serif">
 <div style="position:absolute;left:0;top:0;right:0;height:{TOPBAR}px;background:#323233;color:#CCCCCC;font-size:17px;display:flex;align-items:center;justify-content:center">Plan2Model — Project_Nhom_MSE</div>
 <div style="position:absolute;left:0;top:{TOPBAR}px;bottom:26px;width:{ACT}px;background:#333333">
   <div style="margin:14px auto 0;width:26px;height:22px;border:3px solid #FFFFFF;border-radius:3px"></div>
   <div style="margin:26px auto 0;width:22px;height:22px;border:3px solid #858585;border-radius:50%"></div></div>
 <div style="position:absolute;left:{ACT}px;top:{TOPBAR}px;bottom:26px;width:{SB}px;background:#252526;font-size:19px">
   <div style="height:38px;line-height:38px;padding-left:18px;color:#BBBBBB;font-size:15px;font-weight:700;letter-spacing:.08em">EXPLORER</div>{explorer}</div>
 <div style="position:absolute;left:{ACT + SB}px;top:{TOPBAR}px;right:0;height:{TABS}px;background:#252526"></div>
 <div style="position:absolute;left:0;right:0;bottom:0;height:26px;background:#007ACC;color:#fff;font-size:16px;display:flex;align-items:center;gap:26px;padding-left:14px">
   <span>⎇ main</span><span>Python 3.13</span><span>UTF-8</span><span style="margin-left:auto;padding-right:16px">Plan2Model</span></div>
</div></div>"""
s.raw(frame)
s.enter("s8-ide", 0, "scale")
s.exit("s8-ide", s.dur, "blur")

# ---- mốc ----
def _A(p, fb):
    try:
        return A(p, s.t0)
    except KeyError:
        return fb
t_pipe = _A("pipeline", s.t0 + 1.2)
t_sv = _A("sauvola", t_pipe + 4)
t_tp = _A("tích phân", t_sv + 2)
t_ng = _A("tính ngưỡng", t_tp + 2)
t_ev = _A("eval", t_ng + 2)
t_gh = _A("toàn bộ code", t_ev + 2)


def tab(nm, active=True):
    return (f'<span style="display:inline-flex;align-items:center;height:{TABS}px;padding:0 22px;background:{"#1E1E1E" if active else "#2D2D2D"};'
            f'color:{"#FFFFFF" if active else "#969696"};font-size:18px;border-top:2px solid {"#007ACC" if active else "transparent"}">'
            f'<span style="color:#3B8EEA;font-weight:700;font-size:14px;margin-right:10px">py</span>{nm}</span>')


def editor(eid, t_in, t_out, tabs_html, body, crumbs):
    self_html = (f'<div style="position:absolute;left:0;top:0;width:{EW}px;height:{TABS}px;display:flex">{tabs_html}</div>'
                 f'<div style="position:absolute;left:0;top:{TABS}px;width:{EW}px;height:30px;line-height:30px;padding-left:20px;color:#A9A9A9;font-size:16px;background:#1E1E1E">{crumbs}</div>'
                 f'<div style="position:absolute;left:0;top:{TABS + 34}px;width:{EW}px;{CSS}color:#D4D4D4">{body}</div>')
    return s.clip(self_html, t_in, t_out, style=f"left:{EX}px;top:{Y0 + TOPBAR}px;width:{EW}px;height:{HH - TOPBAR - 26}px;", eid=eid,
                  attrs="data-layout-allow-overflow data-layout-ignore")


# màn 1: pipeline.py ở hàm sauvola
e1, a1, b1 = editor("s8-ed1", t_pipe - 0.2, t_ev - 0.1, tab("pipeline.py") + tab("app.py", False),
                    code_block(r"prototype\pipeline.py", 48, 67, "pl"), "prototype › pipeline.py › sauvola")
s.enter(e1, a1, "blur")
# màn 2: eval_cubicasa.py
e2, a2, b2 = editor("s8-ed2", t_ev - 0.1, None, tab("pipeline.py", False) + tab("eval_cubicasa.py"),
                    code_block(r"prototype\eval_cubicasa.py", 15, 34, "ev"), "prototype › eval_cubicasa.py › room_scores")
s.enter(e2, a2, "blur")
# chọn file trong explorer
for rid, ta, tb in [("s8-tr-pipeline_py", t_pipe - 0.2, t_ev - 0.1), ("s8-tr-eval_cubicasa_py", t_ev - 0.1, s.t1)]:
    s.js.append(f'tl.set("#{rid}",{{backgroundColor:"rgba(0,0,0,0)"}},0);')
    s.js.append(f'tl.set("#{rid}",{{backgroundColor:"#37373D",color:"#FFFFFF"}},{s.L(ta):.3f});')
    s.js.append(f'tl.set("#{rid}",{{backgroundColor:"rgba(0,0,0,0)",color:"#CCCCCC"}},{s.L(tb):.3f});')
# tô dòng đang nói
for lid, tk in [("pl-l53", t_tp), ("pl-l54", t_tp), ("pl-l65", t_ng)]:
    s.js.append(f'tl.fromTo("#{lid}",{{backgroundColor:"rgba(224,68,16,0)"}},{{backgroundColor:"rgba(224,68,16,0.42)",duration:0.25}},{s.L(tk) - 0.15:.3f});')
    s.js.append(f'tl.to("#{lid}",{{backgroundColor:"rgba(224,68,16,0)",duration:0.4}},{min(s.L(tk) + 2.4, s.L(t_ev) - 0.6):.3f});')
for lid in ("ev-l15", "ev-l21"):
    s.js.append(f'tl.fromTo("#{lid}",{{backgroundColor:"rgba(224,68,16,0)"}},{{backgroundColor:"rgba(224,68,16,0.42)",duration:0.25}},{s.L(t_ev) + 0.6:.3f});')
# terminal: cách chạy
term = (f'<div style="position:absolute;inset:0;background:#181818;border-top:1px solid #3C3C3C">'
        f'<div style="height:34px;line-height:34px;padding-left:20px;font-size:15px;color:#E7E7E7;letter-spacing:.06em;border-bottom:1px solid #2B2B2B">TERMINAL</div>'
        f'<div style="{CSS}padding:10px 20px;line-height:32px;color:#CCCCCC;white-space:pre">'
        f'<div id="s8-c1"><span style="color:#4EC9B0">PS F:\\Project_Nhom_MSE&gt;</span> pip install -r requirements.txt</div>'
        f'<div id="s8-c2"><span style="color:#4EC9B0">PS F:\\Project_Nhom_MSE&gt;</span> streamlit run app.py</div>'
        f'<div id="s8-c3">  You can now view your Streamlit app in your browser.</div>'
        f'<div id="s8-c4">  Local URL: <span style="color:#3B8EEA">http://localhost:8501</span></div></div></div>')
TH = 250
et, at, bt = s.clip(term, t_gh - 0.4, None, style=f"left:{EX}px;top:{Y0 + HH - 26 - TH}px;width:{EW}px;height:{TH}px;", eid="s8-term",
                    attrs="data-layout-allow-overflow data-layout-ignore")
s.js.append(f'tl.fromTo("#s8-term-in",{{y:{TH}}},{{y:0,duration:0.55,ease:"expo.out"}},{at:.3f});')
for k, cid in enumerate(["s8-c1", "s8-c2", "s8-c3", "s8-c4"]):
    s.js.append(f'tl.fromTo("#{cid}",{{opacity:0}},{{opacity:1,duration:0.12}},{at + 0.4 + k * 0.45:.3f});')
