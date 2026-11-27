// Quay app Streamlit thật (localhost:8501) bằng Chrome headless + CDP screencast.
// Mỗi cảnh -> thư mục khung JPEG + times.json; sau đó ffmpeg ghép thành MP4 30 fps.
import { createRequire } from "module";
import fs from "fs";
import path from "path";
const require = createRequire("C:/Users/Admin/AppData/Local/npm-cache/_npx/702923228c2ce1e6/node_modules/");
const puppeteer = require("puppeteer-core");

const OUT = "F:/Project_Nhom_MSE/video/work/rec";
const CHROME = "C:/Users/Admin/.cache/hyperframes/chrome/chrome-headless-shell/win64-158.0.8127.88/chrome-headless-shell-win64/chrome-headless-shell.exe";
const only = process.argv.slice(2);
fs.mkdirSync(OUT, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: true,
  args: ["--window-size=1536,864", "--hide-scrollbars", "--disable-gpu-vsync", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
  defaultViewport: { width: 1536, height: 864, deviceScaleFactor: 1.25 },
  userDataDir: "F:/tmp_hf/rec_profile",
});
const page = await browser.newPage();
const cdp = await page.createCDPSession();
await cdp.send("Browser.setDownloadBehavior", { behavior: "allow", downloadPath: "F:/tmp_hf/dl" }).catch(() => {});

// con trỏ chuột giả (headless không vẽ con trỏ)
const CURSOR = `(() => { if (document.getElementById('__cur')) return; const c = document.createElement('div'); c.id='__cur';
 c.innerHTML='<svg width="26" height="34" viewBox="0 0 26 34"><path d="M2 2 L2 27 L8.5 21 L13 31 L17.5 29 L13 19.5 L22 19.5 Z" fill="#111" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>';
 Object.assign(c.style,{position:'fixed',left:'0',top:'0',zIndex:2147483647,pointerEvents:'none',transform:'translate(-200px,-200px)',filter:'drop-shadow(0 2px 3px rgba(0,0,0,.35))'});
 document.documentElement.appendChild(c); })()`;
let mx = 768, my = 430;
async function setCur(x, y) { await page.evaluate((x, y, s) => { eval(s); document.getElementById('__cur').style.transform = `translate(${x - 2}px,${y - 2}px)`; }, x, y, CURSOR); }
async function move(x, y, ms = 600) {
  const n = Math.max(8, Math.round(ms / 25));
  const x0 = mx, y0 = my;
  for (let i = 1; i <= n; i++) {
    const t = i / n, e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    mx = x0 + (x - x0) * e; my = y0 + (y - y0) * e;
    await page.mouse.move(mx, my); await setCur(mx, my); await sleep(ms / n);
  }
}
async function click(x, y) { await move(x, y, 700); await sleep(150); await page.mouse.click(x, y); await sleep(200); }
async function clickEl(handle, dx = 0.5, dy = 0.5) {
  await handle.evaluate((e) => e.scrollIntoView({ block: "center", behavior: "instant" }));
  await sleep(250);
  const b = await handle.boundingBox();
  await click(b.x + b.width * dx, b.y + b.height * dy);
}
async function byText(sel, text) {
  const hs = await page.$$(sel);
  for (const h of hs) { const t = await h.evaluate((e) => e.innerText || e.textContent || ""); if (t.includes(text)) return h; }
  throw new Error("không thấy " + sel + " ~ " + text);
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function idle(ms = 300) {
  // chờ Streamlit chạy xong (biểu tượng "Running" biến mất)
  for (let i = 0; i < 120; i++) {
    const busy = await page.evaluate(() => !!document.querySelector('[data-testid="stStatusWidget"]'));
    if (!busy) break; await sleep(250);
  }
  await sleep(ms);
}
async function scrollMain(dy, ms = 1200) {
  const n = Math.round(ms / 30);
  for (let i = 0; i < n; i++) { await page.mouse.wheel({ deltaY: dy / n }); await sleep(30); }
}

// ---- ghi hình ----
let frames = [], recDir = null, recording = false;
cdp.on("Page.screencastFrame", async (f) => {
  try { await cdp.send("Page.screencastFrameAck", { sessionId: f.sessionId }); } catch {}
  if (!recording) return;
  const i = frames.length;
  fs.writeFileSync(path.join(recDir, `f${String(i).padStart(5, "0")}.jpg`), Buffer.from(f.data, "base64"));
  frames.push(f.metadata.timestamp);
});
async function start(name) {
  recDir = path.join(OUT, name); fs.rmSync(recDir, { recursive: true, force: true }); fs.mkdirSync(recDir, { recursive: true });
  frames = []; recording = true;
  await cdp.send("Page.startScreencast", { format: "jpeg", quality: 88, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
  await setCur(mx, my); await sleep(120);
}
async function stop() {
  await sleep(250); recording = false;
  await cdp.send("Page.stopScreencast");
  frames.push(Date.now() / 1000);
  fs.writeFileSync(path.join(recDir, "times.json"), JSON.stringify(frames));
  console.log("REC", path.basename(recDir), frames.length - 1, "frames", (frames.at(-1) - frames[0]).toFixed(1), "s");
}
const want = (n) => only.length === 0 || only.includes(n);

// ---- kịch bản ----
await page.goto("http://localhost:8501", { waitUntil: "networkidle2", timeout: 120000 });
await idle(1500);
await setCur(mx, my);

if (want("open")) {
  await page.goto("about:blank"); await setCur(mx, my);
  await start("open");
  await page.goto("http://localhost:8501", { waitUntil: "domcontentloaded" });
  await setCur(mx, my); await idle(600);
  await page.waitForSelector('[data-testid="stMetric"]', { timeout: 120000 }); await idle(800); await setCur(mx, my);
  await move(380, 200, 900); await sleep(500);
  await move(900, 230, 900); await sleep(1500);
  await stop();
}

// từng bước: thumbnail số i -> ảnh + giải thích -> cuộn xuống khung "Kỹ thuật & hàm"
if (want("steps")) {
  const nSteps = await page.$$eval('[data-testid="stTabs"] button[kind="tertiary"], [data-testid="stTabs"] button[kind="primary"]', (b) => b.filter((x) => /^\d+$/.test(x.innerText.trim())).length);
  console.log("steps", nSteps); const NS = Math.min(nSteps, 12);
  for (let i = 1; i <= NS; i++) {
    await page.evaluate(() => window.scrollTo(0, 0));
    const main = await page.$('[data-testid="stMain"]');
    await main.evaluate((e) => e.scrollTo(0, 0));
    await sleep(300);
    const btn = await byText('[data-testid="stTabs"] button', String(i)).catch(() => null);
    const btns = await page.$$('[data-testid="stTabs"] button');
    let target = null;
    for (const b of btns) { if ((await b.evaluate((e) => e.innerText.trim())) === String(i)) { target = b; break; } }
    await start(`step${String(i).padStart(2, "0")}`);
    await clickEl(target); await idle(400);
    await move(560, 560, 800); await sleep(900);
    await scrollMain(520, 1600); await sleep(1100);
    await scrollMain(600, 1600); await sleep(1400);
    await stop();
  }
  await page.$eval('[data-testid="stMain"]', (e) => e.scrollTo(0, 0));
}

if (want("3d")) {
  await page.$eval('[data-testid="stMain"]', (e) => e.scrollTo(0, 0)); await sleep(300);
  const tab = await byText('[data-testid="stTabs"] [role="tab"]', "Mô hình 3D");
  await start("3d");
  await clickEl(tab); await idle(500); await sleep(2500);
  const fr = await page.$('[data-testid="stIFrame"], iframe');
  const b = await fr.boundingBox();
  const cx = b.x + b.width * 0.5, cy = b.y + b.height * 0.5;
  await move(cx, cy, 700);
  await page.mouse.down(); for (let i = 0; i < 60; i++) { mx += 6; my += (i < 30 ? 1.2 : -1.2); await page.mouse.move(mx, my); await setCur(mx, my); await sleep(30); } await page.mouse.up();
  await sleep(500);
  for (let i = 0; i < 12; i++) { await page.mouse.wheel({ deltaY: -120 }); await sleep(60); }
  await sleep(600);
  await page.mouse.down(); for (let i = 0; i < 50; i++) { mx -= 7; await page.mouse.move(mx, my); await setCur(mx, my); await sleep(30); } await page.mouse.up();
  await sleep(1500);
  await stop();
}

if (want("export")) {
  await page.$eval('[data-testid="stMain"]', (e) => e.scrollTo(0, 0)); await sleep(300);
  const tab = await byText('[data-testid="stTabs"] [role="tab"]', "Xuất file");
  await start("export");
  await clickEl(tab); await idle(400); await sleep(700);
  const dl = await byText('[data-testid="stDownloadButton"] button', "DXF");
  await clickEl(dl); await sleep(1800);
  await stop();
  const t2 = await byText('[data-testid="stTabs"] [role="tab"]', "Quá trình xử lý"); await clickEl(t2); await idle(500);
}

if (want("cubicasa")) {
  await page.$eval('[data-testid="stMain"]', (e) => e.scrollTo(0, 0)); await sleep(300);
  await start("cubicasa");
  const sel = await byText('[data-testid="stSidebar"] [data-testid="stSelectbox"]', "Chọn ảnh mẫu");
  await clickEl(sel, 0.5, 0.75); await sleep(800);
  const opt = await byText('[role="option"]', "kiến trúc · 2090");
  await clickEl(opt); await idle(800);
  await move(900, 210, 900); await sleep(2500);
  // tắt "Lấp tường rỗng"
  const tg = await byText('[data-testid="stSidebar"] [data-testid="stCheckbox"], [data-testid="stSidebar"] label', "Lấp tường rỗng");
  await clickEl(tg, 0.08, 0.5); await idle(800);
  await move(900, 210, 900); await sleep(3000);
  await clickEl(tg, 0.08, 0.5); await idle(800);
  await sleep(1500);
  await stop();
}
await browser.close();
