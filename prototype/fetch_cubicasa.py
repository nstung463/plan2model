"""Rút một tập con CubiCasa5K từ Zenodo bằng HTTP range (không tải cả file 5.2 GB).

python fetch_cubicasa.py <split: test|val|train> <so_mau>
  -> data/cubicasa/<split>/<category>_<id>/{F1_scaled.png, model.svg}
Lấy đều 3 nhóm, theo thứ tự trong file split chính thức (không chọn tay).
"""
import os, sys
from remotezip import RemoteZip

URL = "https://zenodo.org/api/records/2613548/files/cubicasa5k.zip/content"
SPLIT = sys.argv[1] if len(sys.argv) > 1 else "test"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 60
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cubicasa", SPLIT)
os.makedirs(OUT, exist_ok=True)

with RemoteZip(URL) as z:
    ids = z.read(f"cubicasa5k/{SPLIT}.txt").decode().split()
    picked = []
    for cat in ["high_quality_architectural", "high_quality", "colorful"]:
        picked += [t for t in ids if f"/{cat}/" in t][: N // 3]
    for t in picked:
        rel = t.strip("/")
        cat, sid = rel.split("/")[-2:]
        d = os.path.join(OUT, f"{cat}_{sid}")
        if os.path.exists(os.path.join(d, "model.svg")):
            continue
        os.makedirs(d, exist_ok=True)
        for f in ["F1_scaled.png", "model.svg"]:
            with open(os.path.join(d, f), "wb") as fh:
                fh.write(z.read(f"cubicasa5k/{rel}/{f}"))
        print("ok", SPLIT, cat, sid)
print("done", SPLIT, len(picked))
