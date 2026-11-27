"""Sửa chữ nghe nhầm trong transcript (giữ nguyên mốc thời gian từng từ)."""
import json, os, re, sys
W = os.path.dirname(os.path.abspath(__file__))
tr = json.load(open(os.path.join(W, "transcript.json"), encoding="utf-8"))
words = [dict(w) for w in tr["words"] if w["text"].strip()]

# thay một từ (so khớp chữ thường, bỏ dấu câu)
ONE = {
    "candy": "Canny", "cany": "Canny", "canny": "Canny", "cường": "tường", "savula": "Sauvola", "sauvola": "Sauvola", "sovola": "Sauvola",
    "card": "CAD", "cát": "CAD", "otsu": "Otsu", "ốt": "Otsu", "homography": "homography", "iou": "IoU", "ống": "bóng",
    "vương": "vuông", "f1": "F1", "unet": "U-Net",
}
# thay cụm nhiều từ: (chuỗi từ gốc, chuỗi từ mới) – cùng số từ thì giữ mốc từng từ
MULTI = [
    (["Deep", "Lâm", "Linh"], ["Deep", "Learning", ""]),
    (["cầu", "điện"], ["cổ", "điển"]),
    (["ba", "đều"], ["3D", ""]),
    (["đường", "1"], ["đột", "ngột"]),
    (["cấp", "điểm"], ["cặp", "điểm"]),
    (["Wall", "IOU"], ["Wall", "IoU"]),
    (["áp", "án"], ["đáp", "án"]),
]
EXTRA = json.load(open(os.path.join(W, "fix_extra.json"), encoding="utf-8")) if os.path.exists(os.path.join(W, "fix_extra.json")) else {}


def core(t):
    return re.sub(r"[^\w\-]", "", t.lower())


for i, w in enumerate(words):
    m = re.match(r"^(\W*)(.*?)(\W*)$", w["text"])
    pre, body, post = m.groups()
    c = core(body)
    if c in ONE:
        w["text"] = pre + ONE[c] + post
for src, dst in MULTI + [(e[0], e[1]) for e in EXTRA.get("multi", [])]:
    n = len(src)
    for i in range(len(words) - n + 1):
        if [core(words[i + k]["text"]) for k in range(n)] == [core(x) for x in src]:
            for k in range(n):
                tail = re.match(r"^.*?(\W*)$", words[i + k]["text"]).group(1)
                words[i + k]["text"] = (dst[k] + tail) if dst[k] else ""
# gộp từ rỗng vào từ trước
out = []
for w in words:
    if not w["text"].strip(" ,.?!"):
        if out:
            out[-1]["end"] = w["end"]
        continue
    out.append(w)
json.dump(out, open(os.path.join(W, "words_fixed.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(out), "words")
