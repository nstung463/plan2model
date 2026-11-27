# Phần 2 của build.py (chạy bằng exec trong cùng namespace)

# ======================= S5 mô hình 3D (Three.js) =========================
s = new("s5")
MODEL = json.load(open(os.path.join(HF, "assets/steps/demo_model.json"), encoding="utf-8"))
labels = "".join(
    f'<div id="s5-lab{i}" class="abs" style="left:0;top:0;font-weight:800;font-size:30px;background:#fff;padding:6px 12px;'
    f'border-left:8px solid {ROOMC[i % 5]};white-space:nowrap;opacity:0">{str(r["area"]).replace(".", ",")} m²</div>'
    for i, r in enumerate(MODEL["rooms"]))
s.raw(f'<div id="s5-stage" class="clip abs" data-start="0" data-duration="{s.dur}" style="inset:0" data-layout-allow-overflow data-layout-allow-overlap>'
      f'<div id="s5-stage-in" style="position:absolute;inset:0"><canvas id="s5-c" width="1920" height="1080" style="position:absolute;inset:0;width:1920px;height:1080px;background:#E9ECEA"></canvas>{labels}</div></div>')
s.text('Mô hình 3D chạy ngay trên trình duyệt', 96, 80, s.t0 + 0.8, None, style="font-size:52px;font-weight:900")
s.js.append("""
(function(){
const MODEL=%s;
const COLS=[0x5BC0EB,0xFDA65D,0x9BE08C,0xC7A5F5,0x6C8EF5];
const cv=document.getElementById('s5-c');
const r=new THREE.WebGLRenderer({canvas:cv,antialias:true,preserveDrawingBuffer:true,alpha:false,premultipliedAlpha:false});
r.setPixelRatio(1);r.setSize(1920,1080,false);r.setClearColor(0xE9ECEA,1);r.shadowMap.enabled=true;r.shadowMap.type=THREE.PCFSoftShadowMap;
r.outputEncoding=THREE.sRGBEncoding;
const lin=h=>new THREE.Color(h).convertSRGBToLinear();
const sc=new THREE.Scene();sc.background=new THREE.Color(0xE9ECEA).convertSRGBToLinear();const cam=new THREE.PerspectiveCamera(30,1920/1080,0.1,300);
sc.add(new THREE.HemisphereLight(0xffffff,0xc8ccc9,0.75));
const sun=new THREE.DirectionalLight(0xffffff,0.55);sun.position.set(-10,22,14);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);
sun.shadow.bias=-0.0008;sun.shadow.normalBias=0.02;Object.assign(sun.shadow.camera,{left:-14,right:14,top:14,bottom:-14,near:1,far:70});
sun.target.position.set(6,0,4);sc.add(sun.target);sc.add(sun);
const shp=p=>{const s=new THREE.Shape();p.forEach(([x,y],i)=>i?s.lineTo(x,y):s.moveTo(x,y));s.closePath();return s};
const walls=new THREE.Group();sc.add(walls);
MODEL.walls.forEach(w=>{const s=shp(w.outer);(w.holes||[]).forEach(h=>s.holes.push(new THREE.Path(shp(h).getPoints())));
 const g=new THREE.ExtrudeGeometry(s,{depth:2.8,bevelEnabled:false});g.rotateX(-Math.PI/2);
 const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:lin(0xFBFBF8),roughness:.85}));m.castShadow=true;walls.add(m);
 walls.add(new THREE.LineSegments(new THREE.EdgesGeometry(g,25),new THREE.LineBasicMaterial({color:lin(0x14171A)})));});
const floors=[];
MODEL.rooms.forEach((rm,i)=>{const g=new THREE.ShapeGeometry(shp(rm.poly));g.rotateX(-Math.PI/2);
 const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:lin(COLS[i%%5]),roughness:.95,transparent:true,opacity:1}));m.position.y=0.012;m.receiveShadow=true;sc.add(m);floors.push(m);});
const gr=new THREE.Mesh(new THREE.PlaneGeometry(90,90),new THREE.ShadowMaterial({opacity:0.16}));gr.rotation.x=-Math.PI/2;gr.receiveShadow=true;sc.add(gr);
const gh=new THREE.GridHelper(90,90,lin(0xC9CDCB),lin(0xD8DBD9));gh.position.set(6,-0.002,4);sc.add(gh);
const C=new THREE.Vector3(6.1,0.6,3.95);const V=new THREE.Vector3();
const labs=MODEL.rooms.map((rm,i)=>({el:document.getElementById('s5-lab'+i),p:new THREE.Vector3(rm.c[0],0.2,-rm.c[1])}));
const ease=x=>x<0?0:x>1?1:1-Math.pow(1-x,3);
function render(t){
 const rise=ease((t-0.6)/1.8);walls.scale.y=Math.max(0.0005,rise);
 const tilt=ease((t-0.3)/3.2);
 const el=1.5-tilt*0.78, a=-0.15-tilt*0.55+Math.max(0,t-3.5)*0.16, d=25-tilt*3;
 cam.position.set(C.x+d*Math.cos(el)*Math.sin(a),d*Math.sin(el),C.z+d*Math.cos(el)*Math.cos(a));cam.up.set(0,1,0);cam.lookAt(C);
 cam.updateMatrixWorld();
 labs.forEach((L,i)=>{V.copy(L.p).project(cam);const x=(V.x+1)/2*1920,y=(1-V.y)/2*1080;const o=ease((t-2.6-i*0.15)/0.4);
  L.el.style.transform='translate('+(x-60).toFixed(1)+'px,'+(y-22).toFixed(1)+'px)';L.el.style.opacity=o.toFixed(3);});
 r.render(sc,cam);}
const st={t:0};
tl.fromTo(st,{t:0},{t:%s,duration:%s,ease:"none",onUpdate:()=>render(st.t)},0);
render(0);
})();
""" % (json.dumps(MODEL, ensure_ascii=False), s.dur, s.dur))
s.css.append("")
s.appwin("assets/app/3d.mp4", s.t0 + 4.2, s.dur - 4.3, mstart=2.6, punch=((0.9, 1.6, 30, 80),), label="localhost:8501 · tab Mô hình 3D")

# ======================= S6 CubiCasa thật =========================
s = new("s6", "Thử với bản vẽ thật: CubiCasa5K")
s.card(S + "cc_input_0.jpg", 96, 190, 700, 682, s.t0 + 0.5, None, cap="Bản vẽ thật, có đáp án vẽ tay", enter="drop")
_tw = A("wall", s.t0)
s.appwin("assets/app/cubicasa.mp4", s.t0 + 0.3, _tw - s.t0 - 1.0, mstart=0.0, punch=((4.5, 1.3, 70, 22),), label="localhost:8501 · mẫu CubiCasa5K kiến trúc 2090")
try:
    t_iou = A("wall", s.t0)
except KeyError:
    t_iou = s.t0 + 7
s.card(S + "cc_pred.jpg", 96, 190, 700, 682, t_iou - 0.3, None, cap="Xanh: đúng · Đỏ: thừa · Cam: thiếu", enter="scale")
s.text('<span style="font-size:40px;font-weight:900">Wall IoU</span><br><span style="font-size:28px">tường máy tìm trùng tường thật</span>', 880, 200, t_iou - 0.1, None, w=320)
n_iou = s.count(880, 320, 140, 0, 0.59, A("0,59", t_iou) - 0.3, dec=2)
try:
    t_f1 = A("room", t_iou)
except KeyError:
    t_f1 = t_iou + 6
s.text('<span style="font-size:40px;font-weight:900">Room F1</span><br><span style="font-size:28px">tách phòng đúng tới đâu</span>', 1240, 200, t_f1 - 0.1, None, w=300)
n_f1 = s.count(1240, 320, 140, 0, 0.77, A("0,77", t_f1) - 0.3, dec=2)
try:
    t_off = A("tắt", t_f1)
except KeyError:
    t_off = t_f1 + 6
# công tắc lấp tường rỗng
sw = (f'<div style="display:flex;align-items:center;gap:22px;font-weight:800;font-size:36px">'
      f'<div style="width:110px;height:58px;border-radius:29px;background:{ACC};position:relative" id="s6-sw-bg">'
      f'<div id="s6-knob" style="position:absolute;top:6px;left:58px;width:46px;height:46px;border-radius:23px;background:#fff"></div></div>'
      f'Lấp tường rỗng: <span id="s6-swt">BẬT</span></div>')
s.text(sw, 880, 560, t_off - 1.4, None)
ls = s.L(t_off)
s.js.append(f'tl.to("#s6-knob",{{x:-52,duration:0.25,ease:"power2.inOut"}},{ls:.3f});')
s.js.append(f'tl.to("#s6-sw-bg",{{backgroundColor:"#9AA0A3",duration:0.25}},{ls:.3f});')
s.js.append(f'tl.set("#s6-swt",{{textContent:"TẮT"}},{ls + 0.12:.3f});')
for nid, v0, v1 in [(n_iou, 0.59, 0.20), (n_f1, 0.77, 0.0)]:
    s.js.append(f'(function(){{const o={{v:{v0}}};const el=document.getElementById("{nid}-v");'
                f'tl.fromTo(o,{{v:{v0}}},{{v:{v1},duration:1.0,ease:"power2.inOut",immediateRender:false,onUpdate:()=>{{el.textContent=o.v.toFixed(2).replace(".",",");}}}},{ls + 0.5:.3f});}})();')
s.card(S + "ccoff_opening_1.jpg", 96, 190, 700, 682, t_off + 0.4, None, cap="Tắt lấp tường rỗng: tường viền bị xoá như chữ (hồng)", enter="scale")
try:
    t_bk = A("không tách", t_off)
except KeyError:
    t_bk = t_off + 3
s.text('Không tách được <b>phòng nào</b>', 880, 680, t_bk - 0.3, None, style="font-size:40px;font-weight:800")
try:
    t_most = A("nhiều nhất", t_off)
except KeyError:
    t_most = t_bk + 5
s.text('→ khối ảnh hưởng <b>nhiều nhất</b>', 880, 760, t_most - 0.8, None, style="font-size:40px;font-weight:800")

# ======================= S7 kết quả =========================
s = new("s7", "Kết quả trên 60 bản vẽ thật")
# chia dữ liệu
split = (f'<div style="display:flex;gap:18px;align-items:flex-end;font-weight:800;font-size:30px">'
         f'<div><div style="width:270px;height:70px;background:#C9CDCB"></div>45 ảnh: chọn tham số</div>'
         f'<div><div style="width:360px;height:70px;background:{INK}"></div>60 ảnh: chấm 1 lần duy nhất</div></div>')
s.text(split, 96, 200, s.t0 + 1.0, A("otsu", s.t0) - 0.2, enter="left")
try:
    t_ot = A("otsu", s.t0)
except KeyError:
    t_ot = s.t0 + 9
# biểu đồ cột: 2 nhóm x 3 cột
groups = [("Wall IoU", [0.47, 0.56, 0.77]), ("Room F1", [0.32, 0.45, 0.57])]
names = [("Otsu", "#9AA0A3"), ("Nhóm em", ACC), ("U-Net", INK)]
try:
    t_un = A("u-net", t_ot)
except KeyError:
    t_un = t_ot + 12
BASE_Y, HMAX = 900, 420
for gi, (gname, vals) in enumerate(groups):
    gx = 96 + gi * 700
    s.text(f'<span style="font-size:36px;font-weight:900">{gname}</span>', gx, BASE_Y + 14, t_ot - 0.5, None)
    for bi, ((nm, col), v) in enumerate(zip(names, vals)):
        tb = t_un + 0.3 if bi == 2 else (t_ot + (0.2 if gi == 0 else 2.0) + bi * 0.4)
        if gi == 1 and bi < 2:
            try:
                tb = A("room f1", t_ot) + bi * 0.4
            except KeyError:
                pass
        if gi == 1 and bi == 2:
            try:
                tb = A("0,57", t_un) - 0.6
            except KeyError:
                tb = t_un + 2
        bx = gx + bi * 200
        hpx = int(v * HMAX / 0.8)
        bid = s.uid("bar")
        lb = s.L(tb)
        s.raw(f'<div id="{bid}" class="clip abs" data-start="{lb}" data-duration="{round(s.dur - lb, 3)}" style="left:{bx}px;top:{BASE_Y - hpx - 60}px;width:170px;height:{hpx + 60}px" data-layout-allow-overflow>'
              f'<div id="{bid}-in" style="position:absolute;inset:0">'
              f'<div style="position:absolute;left:0;right:0;top:0;text-align:center;font-weight:900;font-size:40px;color:{col if col != "#9AA0A3" else INK}">{str(v).replace(".", ",")}</div>'
              f'<div id="{bid}-b" style="position:absolute;left:0;right:0;bottom:0;height:{hpx}px;background:{col};transform-origin:bottom"></div>'
              f'<div style="position:absolute;left:0;right:0;bottom:10px;text-align:center;font-weight:800;font-size:28px;color:#fff">{nm}</div></div></div>')
        s.js.append(f'tl.fromTo("#{bid}-b",{{scaleY:0}},{{scaleY:1,duration:0.8,ease:"expo.out"}},{lb:.3f});')
        s.js.append(f'tl.fromTo("#{bid}-in",{{opacity:0}},{{opacity:1,duration:0.2}},{lb:.3f});')
try:
    t_bs = A("bootstrap", s.t0)
except KeyError:
    t_bs = t_ot + 6
s.text('Bootstrap 5000 lần: mức tăng là <b>thật</b>', 1500 - 140, 330, t_bs - 0.3, None, w=420, style="font-size:30px")
try:
    t_nhung = A("nhưng", t_un)
except KeyError:
    t_nhung = t_un + 6
s.text('<b>U-Net</b>: cần dữ liệu có đáp án · cần huấn luyện · khó giải thích<br><b>Nhóm em</b>: không cần học · &lt; 1 giây · sai ở đâu nhìn là biết',
       96, 300, t_nhung - 0.2, None, w=1300, style="font-size:30px")
try:
    t_kh = A("hướng tốt nhất", t_nhung) + 0.4
except KeyError:
    t_kh = t_nhung + 6
s.text('Hướng tốt nhất: <b>kết hợp cả hai</b>', 96, 400, t_kh - 0.4, None, style="font-size:44px;font-weight:900;background:#E9ECEA;padding:6px 0")

exec(open(os.path.join(W, "ide.py"), encoding="utf-8").read())

# ======================= S9 kết luận =========================
s = new("s9")
s.appwin("assets/app/export.mp4", s.t0 + 0.2, 7.2, mstart=0.0, punch=((2.2, 1.35, 55, 40),), label="localhost:8501 · tab Xuất file")
s.card(S + "demo_vector_0.jpg", 96, 160, 640, 437, s.t0 + 0.4, None, cap="File DXF mở bằng AutoCAD", enter="rise")
for j, lay in enumerate(["WALL · tường", "ROOM · phòng", "TEXT · tên + diện tích"]):
    s.text(f'<span style="font-family:IBM Plex Mono,monospace;font-weight:600;font-size:30px;border-left:8px solid {[INK, ROOMC[0], ACC][j]};padding-left:14px">{esc(lay)}</span>',
           800, 200 + j * 64, s.t0 + 1.4 + j * 0.25, None, enter="left")
try:
    t_hc = A("3 hạn chế", s.t0)
except KeyError:
    t_hc = s.t0 + 8
lims = [("Bản vẽ tay nét mờ → dễ sót tường", "nét mờ"), ("Cầu thang, quầy bếp đôi khi nhận nhầm là tường", "cầu thang"),
        ("Phòng thông nhau không có tường ngăn → chưa tách được", "thông nhau")]
s.text('<span style="font-size:44px;font-weight:900">Hạn chế</span>', 800, 420, t_hc - 0.2, None)
for j, (lab, key) in enumerate(lims):
    try:
        tj = A(key, t_hc)
    except KeyError:
        tj = t_hc + 1.5 + j * 2.5
    s.text(f'<b>{j + 1}</b>&nbsp; {esc(lab)}', 800, 490 + j * 92, tj - 0.3, None, enter="left", style="font-size:30px", w=740)
try:
    t_tl = A("tóm lại", t_hc)
except KeyError:
    t_tl = s.t1 - 9
try:
    t_cam = A("cảm ơn", t_tl)
except KeyError:
    t_cam = s.t1 - 3
# màn kết: phủ giấy trắng lên toàn bộ
lk = s.L(t_tl - 0.3)
s.raw(f'<div id="s9-end" class="clip abs" data-start="{lk}" data-duration="{round(s.dur - lk, 3)}" style="inset:0;" data-layout-allow-overlap>'
      f'<div id="s9-end-in" style="position:absolute;inset:0;background:{GROUND}">'
      f'<div style="position:absolute;left:96px;top:250px;font-weight:900;font-size:68px;letter-spacing:-0.02em;line-height:1.15;width:1400px">'
      f'Từ <span style="color:{ACC}">ảnh chụp</span> tới <span style="color:{ACC}">file CAD</span> và <span style="color:{ACC}">mô hình 3D</span>,<br>chỉ bằng xử lý ảnh trong môn.</div>'
      f'<div id="s9-thx" style="position:absolute;left:96px;top:560px;font-weight:900;font-size:120px;letter-spacing:-0.03em">Cảm ơn thầy đã xem.</div>'
      f'<div id="s9-names" style="position:absolute;left:100px;top:760px;font-weight:700;font-size:34px;line-height:1.5">'
      f'Nguyễn Thu Trang · Nguyễn Văn Thụ · Nguyễn Sơn Tùng · Nguyễn Hoàng Khôi Minh</div></div></div>')
s.js.append(f'tl.fromTo("#s9-end-in",{{clipPath:"inset(0 0 0 100%)"}},{{clipPath:"inset(0 0 0 0%)",duration:0.7,ease:"power3.inOut"}},{lk:.3f});')
s.js.append(f'tl.fromTo("#s9-thx",{{opacity:0,filter:"blur(12px)"}},{{opacity:1,filter:"blur(0px)",duration:0.5,ease:"power2.out"}},{s.L(t_cam) - 0.2:.3f});')
s.js.append(f'tl.fromTo("#s9-names",{{opacity:0}},{{opacity:1,duration:0.5}},{s.L(t_cam) + 0.6:.3f});')

exec(open(os.path.join(W, "build3.py"), encoding="utf-8").read())
