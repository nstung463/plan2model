import json, os, sys, time
os.environ.setdefault("HF_HOME", r"F:\hf_cache")
from faster_whisper import WhisperModel

audio = sys.argv[1]
out = sys.argv[2]
model_name = sys.argv[3] if len(sys.argv) > 3 else "large-v3-turbo"
prompt = ("Plan2Model, xử lý ảnh, Canny, homography, Sauvola, Otsu, ảnh tích phân, scikit-image, "
          "biến đổi khoảng cách, phép mở, phép đóng, bốn liên thông, Douglas–Peucker, CubiCasa5K, "
          "Wall IoU, Room F1, U-Net, bootstrap, AutoCAD, DXF, pipeline.py, eval_cubicasa.py, GitHub.")
t0 = time.time()
m = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=16,
                 download_root=os.path.join(os.environ["HF_HOME"], "fw"))
import wave, numpy as np
wf = wave.open(audio); pcm = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
segs, info = m.transcribe(pcm, language="vi", word_timestamps=True, initial_prompt=prompt,
                          vad_filter=True, vad_parameters=dict(min_silence_duration_ms=400),
                          beam_size=5, condition_on_previous_text=False)
res = {"segments": [], "words": []}
for s in segs:
    res["segments"].append({"start": s.start, "end": s.end, "text": s.text.strip()})
    for w in s.words:
        res["words"].append({"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3),
                             "p": round(w.probability, 3)})
    print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text.strip()}", flush=True)
    json.dump(res, open(out + ".partial", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done in", round(time.time() - t0), "s", flush=True)
