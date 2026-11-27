"""U-Net (encoder ResNet18 pretrained ImageNet) phân đoạn TƯỜNG trên CubiCasa5K, train trên CPU.

python unet_wall.py train [iters]   -> models/unet_wall.pt (chọn checkpoint theo wall IoU trên val)
Dùng trong eval: from unet_wall import UNetWall; m = UNetWall(); mask = m(bgr)
"""
import glob, os, sys, time, json
import cv2
import numpy as np
import torch
import torch.nn.functional as F
import segmentation_models_pytorch as smp

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = 768        # resize cạnh dài về 768 px (tường còn ~4-10 px)
CROP = 256
MODEL_PATH = os.path.join(HERE, "models", "unet_wall.pt")
MEAN = np.array([0.485, 0.456, 0.406], np.float32); STD = np.array([0.229, 0.224, 0.225], np.float32)
torch.set_num_threads(os.cpu_count())


def build():
    return smp.Unet("resnet18", encoder_weights=None, classes=1)


def to_tensor(rgb):
    x = (rgb.astype(np.float32) / 255 - MEAN) / STD
    return torch.from_numpy(x.transpose(2, 0, 1))


def load_cached(split):
    """Đọc ảnh + mask tường, resize về LONG, cache .npz để train nhanh."""
    from cubicasa_gt import load_gt
    cache_dir = os.path.join(HERE, "data", "cache_unet", split); os.makedirs(cache_dir, exist_ok=True)
    out = []
    for d in sorted(glob.glob(os.path.join(HERE, "data", "cubicasa", split, "*"))):
        if not os.path.isdir(d) or not os.path.exists(os.path.join(d, "model.svg")):
            continue
        c = os.path.join(cache_dir, os.path.basename(d) + ".npz")
        if not os.path.exists(c):
            img = cv2.imread(os.path.join(d, "F1_scaled.png"))
            if img is None:
                continue
            wall, _ = load_gt(os.path.join(d, "model.svg"), img.shape)
            s = LONG / max(img.shape[:2])
            im = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
            m = cv2.resize(wall, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_NEAREST)
            np.savez_compressed(c, img=cv2.cvtColor(im, cv2.COLOR_BGR2RGB), mask=(m > 0).astype(np.uint8))
        z = np.load(c)
        out.append((os.path.basename(d), z["img"], z["mask"]))
    return out


def sample_batch(data, bs, rng):
    xs, ys = [], []
    for _ in range(bs):
        _, img, m = data[rng.integers(len(data))]
        h, w = m.shape
        # ưu tiên crop có tường
        for _try in range(5):
            y0 = rng.integers(0, max(h - CROP, 0) + 1); x0 = rng.integers(0, max(w - CROP, 0) + 1)
            cm = m[y0:y0 + CROP, x0:x0 + CROP]
            if cm.mean() > 0.02: break
        ci = img[y0:y0 + CROP, x0:x0 + CROP]
        ph, pw = CROP - ci.shape[0], CROP - ci.shape[1]
        if ph or pw:
            ci = np.pad(ci, ((0, ph), (0, pw), (0, 0)), constant_values=255); cm = np.pad(cm, ((0, ph), (0, pw)))
        k = rng.integers(4); ci, cm = np.rot90(ci, k), np.rot90(cm, k)
        if rng.random() < 0.5: ci, cm = ci[:, ::-1], cm[:, ::-1]
        ci = ci.astype(np.float32)
        if rng.random() < 0.3: ci = np.repeat(ci.mean(2, keepdims=True), 3, 2)            # ảnh xám
        ci = np.clip(ci * rng.uniform(0.75, 1.15) + rng.uniform(-25, 25), 0, 255)          # sáng/tương phản
        xs.append(to_tensor(ci.astype(np.uint8))); ys.append(torch.from_numpy(cm.copy()).float()[None])
    return torch.stack(xs), torch.stack(ys)


def dice_loss(logits, y):
    p = torch.sigmoid(logits)
    inter = (p * y).sum((1, 2, 3)); den = p.sum((1, 2, 3)) + y.sum((1, 2, 3))
    return (1 - (2 * inter + 1) / (den + 1)).mean()


@torch.no_grad()
def predict_prob(model, rgb):
    h, w = rgb.shape[:2]
    H, W = (h + 31) // 32 * 32, (w + 31) // 32 * 32
    x = np.pad(rgb, ((0, H - h), (0, W - w), (0, 0)), constant_values=255)
    p = torch.sigmoid(model(to_tensor(x)[None]))[0, 0, :h, :w].numpy()
    return p


def val_iou(model, data, thr=0.5):
    model.eval()
    ious = []
    for _, img, m in data:
        p = predict_prob(model, img) > thr
        ious.append((p & (m > 0)).sum() / max((p | (m > 0)).sum(), 1))
    model.train()
    return float(np.mean(ious))


def train(iters=3000, bs=8, lr=1e-3, eval_every=250):
    tr, va = load_cached("train"), load_cached("val")
    print(f"train {len(tr)} anh, val {len(va)} anh")
    model = smp.Unet("resnet18", encoder_weights="imagenet", classes=1)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=iters, pct_start=0.1)
    rng = np.random.default_rng(0); torch.manual_seed(0)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    best, hist, t0, start = -1, [], time.time(), 1
    ckpt = MODEL_PATH.replace(".pt", "_ckpt.pt")
    if os.path.exists(ckpt):  # chạy tiếp sau khi tiến trình bị dừng giữa chừng
        s = torch.load(ckpt, weights_only=False)
        model.load_state_dict(s["model"]); opt.load_state_dict(s["opt"]); sched.load_state_dict(s["sched"])
        best, hist, start = s["best"], s["hist"], s["it"] + 1
        t0 -= s["sec"]; rng = np.random.default_rng(s["it"])
        print(f"resume tu it {s['it']} (best val {best:.3f})", flush=True)
    elif len(sys.argv) > 3 and sys.argv[3].startswith("--from-weights="):
        # lần chạy đầu bị crash trước khi có checkpoint đầy đủ: nạp trọng số tốt nhất, đưa lịch LR tới đúng bước
        k = int(sys.argv[3].split("=")[1])
        model.load_state_dict(torch.load(MODEL_PATH))
        for _ in range(k): sched.step()
        start, rng = k + 1, np.random.default_rng(k)
        prev = json.load(open(MODEL_PATH.replace(".pt", "_prev.json"))) if os.path.exists(MODEL_PATH.replace(".pt", "_prev.json")) else {}
        best, hist, t0 = prev.get("best", -1), prev.get("hist", []), t0 - prev.get("sec", 0)
        print(f"tiep tuc tu trong so it {k} (optimizer khoi tao lai)", flush=True)
    for it in range(start, iters + 1):
        x, y = sample_batch(tr, bs, rng)
        logits = model(x)
        loss = F.binary_cross_entropy_with_logits(logits, y, pos_weight=torch.tensor(3.0)) + dice_loss(logits, y)
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
        if it % 50 == 0:
            print(f"it {it} loss {loss.item():.3f}  {time.time() - t0:.0f}s", flush=True)
        if it % eval_every == 0 or it == iters:
            v = val_iou(model, va)
            hist.append({"it": it, "loss": float(loss.item()), "val_wall_IoU": v, "sec": time.time() - t0})
            print(f"== it {it} val wall IoU {v:.3f}", flush=True)
            if v > best:
                best = v; torch.save(model.state_dict(), MODEL_PATH)
            torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "sched": sched.state_dict(),
                        "best": best, "hist": hist, "it": it, "sec": time.time() - t0}, ckpt)
    # chọn ngưỡng trên val
    model.load_state_dict(torch.load(MODEL_PATH)); model.eval()
    thr_scores = {t: val_iou(model, va, t) for t in [0.3, 0.4, 0.5, 0.6, 0.7]}
    thr = max(thr_scores, key=thr_scores.get)
    meta = {"best_val_IoU@0.5": best, "thr": thr, "thr_scores": thr_scores, "iters": iters, "bs": bs,
            "n_train": len(tr), "n_val": len(va), "long_side": LONG, "history": hist, "train_sec": time.time() - t0}
    json.dump(meta, open(MODEL_PATH.replace(".pt", ".json"), "w"), indent=2)
    print(json.dumps({k: v for k, v in meta.items() if k != "history"}, indent=2))


class UNetWall:
    """Dự đoán mask tường ở độ phân giải gốc."""
    def __init__(self, path=MODEL_PATH):
        self.model = build(); self.model.load_state_dict(torch.load(path)); self.model.eval()
        meta = json.load(open(path.replace(".pt", ".json")))
        self.thr = meta["thr"]

    def __call__(self, bgr):
        h, w = bgr.shape[:2]
        s = LONG / max(h, w)
        small = cv2.cvtColor(cv2.resize(bgr, None, fx=s, fy=s, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        p = predict_prob(self.model, small)
        p = cv2.resize(p, (w, h), interpolation=cv2.INTER_LINEAR)
        return ((p > self.thr) * 255).astype(np.uint8)


if __name__ == "__main__":
    if sys.argv[1] == "train":
        train(int(sys.argv[2]) if len(sys.argv) > 2 else 3000)
