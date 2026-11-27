"""Ghép khung screencast (thời gian biến thiên) thành MP4 30 fps H.264 cho HyperFrames."""
import json, os, subprocess, sys
REC = r"F:\Project_Nhom_MSE\video\work\rec"
OUT = r"F:\Project_Nhom_MSE\video\hf\assets\app"
os.makedirs(OUT, exist_ok=True)
names = sys.argv[1:] or sorted(d for d in os.listdir(REC) if os.path.isdir(os.path.join(REC, d)))
for n in names:
    d = os.path.join(REC, n)
    ts = json.load(open(os.path.join(d, "times.json")))
    lines = []
    for i in range(len(ts) - 1):
        lines.append(f"file 'f{i:05d}.jpg'\nduration {max(ts[i + 1] - ts[i], 0.001):.4f}")
    lines.append(f"file 'f{len(ts) - 2:05d}.jpg'")
    open(os.path.join(d, "list.txt"), "w").write("\n".join(lines))
    out = os.path.join(OUT, n + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt",
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:white,fps=30,format=yuv420p",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-g", "30", out], cwd=d, check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    print(n, dur)
