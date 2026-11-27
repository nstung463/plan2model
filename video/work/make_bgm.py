"""Nhạc nền chạy local bằng MusicGen-small (đã có sẵn trong cache HF): một đoạn ~28 s rồi lặp crossfade."""
import os, sys
import numpy as np, soundfile as sf, torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration

out = sys.argv[1]
target = float(sys.argv[2])
prompt = ("calm minimal electronic underscore for a technical presentation, soft felt piano and warm synth pads, "
          "light brushed percussion, steady 96 bpm, unobtrusive, no vocals, clean mix")
CACHE = r"F:\hf_cache\hub"
torch.manual_seed(7)
torch.set_num_threads(16)
proc = AutoProcessor.from_pretrained("facebook/musicgen-small", cache_dir=CACHE)
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small", cache_dir=CACHE, low_cpu_mem_usage=True)
inp = proc(text=[prompt], padding=True, return_tensors="pt")
with torch.no_grad():
    audio = model.generate(**inp, do_sample=True, guidance_scale=3.0, max_new_tokens=int(28 * 50))
sr = model.config.audio_encoder.sampling_rate
seed = audio[0, 0].numpy().astype(np.float32)
seed = seed / (np.abs(seed).max() + 1e-6) * 0.8
sf.write(out.replace(".wav", "_seed.wav"), seed, sr)
# lặp với crossfade 3 s cho đủ độ dài
xf = int(3 * sr)
track = seed.copy()
ramp = np.linspace(0, 1, xf, dtype=np.float32)
while len(track) < target * sr:
    tail = track[-xf:] * (1 - ramp) + seed[:xf] * ramp
    track = np.concatenate([track[:-xf], tail, seed[xf:]])
track = track[: int(target * sr)]
fo = int(4 * sr)
track[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)
track[: int(1.5 * sr)] *= np.linspace(0, 1, int(1.5 * sr), dtype=np.float32)
sf.write(out, track, sr)
print("ok", len(track) / sr)
