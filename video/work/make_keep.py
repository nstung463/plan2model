"""Tạo keep.json: giữ phần có tiếng nói, rút các khoảng lặng dài còn ~0.45 s, bỏ các đoạn vấp (cuts.json)."""
import json, os
W = os.path.dirname(os.path.abspath(__file__))
words = json.load(open(os.path.join(W, "words_fixed.json"), encoding="utf-8"))
cuts = json.load(open(os.path.join(W, "cuts.json"), encoding="utf-8")) if os.path.exists(os.path.join(W, "cuts.json")) else []
SRC_END = 570.03
PAD_IN, PAD_OUT, MAXGAP = 0.12, 0.22, 0.75


def in_cut(t):
    return any(a <= t < b for a, b in cuts)


ws = [w for w in words if not in_cut((w["start"] + w["end"]) / 2)]
keep = []
a = max(ws[0]["start"] - 0.35, 0)
prev_end = ws[0]["end"]
for w in ws[1:]:
    gap = w["start"] - prev_end
    cut_between = any(prev_end <= c0 < w["start"] + 0.01 or prev_end < c1 <= w["start"] for c0, c1 in cuts)
    if gap > MAXGAP or cut_between:
        keep.append([round(a, 3), round(min(prev_end + PAD_OUT, w["start"]), 3)])
        a = max(w["start"] - PAD_IN, prev_end + PAD_OUT) if not cut_between else w["start"] - 0.08
    prev_end = max(prev_end, w["end"])
keep.append([round(a, 3), round(min(prev_end + 0.8, SRC_END), 3)])
json.dump(keep, open(os.path.join(W, "keep.json"), "w"), indent=0)
tot = sum(b - a for a, b in keep)
print(len(keep), "đoạn, tổng", round(tot, 1), "s (gốc", SRC_END, ")")
