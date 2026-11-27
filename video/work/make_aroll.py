"""Cắt a-roll theo danh sách đoạn giữ (keep.json) -> face.mp4 (mặt, vuông, câm) + voice.wav (giọng đã xử lý)
và words_edit.json (mốc thời gian từ theo timeline đã cắt)."""
import json, os, subprocess, sys

W = r"F:\Project_Nhom_MSE\video\work"
HF = r"F:\Project_Nhom_MSE\video\hf\assets"
SRC = r"F:\Project_Nhom_MSE\video\raw\IMG_3007.MOV"
keep = json.load(open(os.path.join(W, "keep.json"), encoding="utf-8"))  # [[start, end], ...] giây trong file gốc
words = json.load(open(os.path.join(W, "words_fixed.json"), encoding="utf-8"))

# 1) ánh xạ thời gian gốc -> thời gian sau cắt
out, acc = [], 0.0
for a, b in keep:
    for w in words:
        if w["start"] >= a - 0.05 and w["end"] <= b + 0.05:
            out.append({**w, "start": round(w["start"] - a + acc, 3), "end": round(min(w["end"], b) - a + acc, 3)})
    acc += b - a
json.dump({"duration": round(acc, 3), "words": out}, open(os.path.join(W, "words_edit.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)
print("edited duration", round(acc, 2), "s,", len(out), "words")

# 2) filter_complex: trim + concat, crossfade âm 20 ms ở mỗi mối nối để không bị tách tiếng
F = 0.02
parts_v, parts_a = [], []
for i, (a, b) in enumerate(keep):
    parts_v.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}]")
    parts_a.append(f"[0:2]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d={F},afade=t=out:st={b - a - F}:d={F}[a{i}]")
n = len(keep)
fc = ";".join(parts_v + parts_a)
fc += ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vc]"
fc += ";" + "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[ac]"
# mặt: crop vuông quanh đầu, 600x600; giọng: lọc ồn nhẹ, cắt trầm, nén, chuẩn hoá -16 LUFS
fc += ";[vc]crop=820:820:650:10,scale=600:600,fps=30[face]"
fc += ";[ac]highpass=f=80,afftdn=nr=10:nf=-40,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000[voice]"
script = os.path.join(W, "fc.txt")
open(script, "w", encoding="utf-8").write(fc)
cmd = ["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex_script", script,
       "-map", "[face]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-g", "30", "-pix_fmt", "yuv420p", "-an",
       os.path.join(HF, "face.mp4"),
       "-map", "[voice]", "-c:a", "pcm_s16le", os.path.join(HF, "voice.wav")]
subprocess.run(cmd, check=True)
print("ok")
