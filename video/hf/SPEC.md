# SPEC – Plan2Model, video thuyết trình (~9–10 phút)

GOAL:    Thầy xem xong hiểu: một tấm ảnh chụp bản vẽ đi qua 9 bước xử lý ảnh cổ điển thành file CAD + mô hình 3D, và tin số liệu là thật.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps. Bản giao: H.264, CRF ~26, AAC 128k (nhẹ, < 150 MB).
TIME:    độ dài theo lời Tùng sau khi cắt chỗ vấp (~9 phút). Giọng nói là đồng hồ: hình xuất hiện đúng chữ nói ra nó.

LOOK (chất liệu: bàn vẽ kỹ thuật / giấy can CAD):
  ground  #E9ECEA giấy can lạnh, lưới ô 48 px nét #14171A ở 5%, ô lớn 240 px ở 9%; không gradient.
  ink     #14171A cho mọi chữ cần đọc và mọi nét cấu trúc.
  accent  #E04410 (cam chọn đối tượng của CAD, tối hơn để đạt tương phản) – chỉ một tiêu điểm mỗi khung: con số, nét đang nói, dòng code đang nói.
  phụ     màu phòng lấy từ pipeline (xanh #5BC0EB, cam #FDA65D, lục #9BE08C, tím #C7A5F5, lam #6C8EF5) – chỉ xuất hiện trên hình phòng.
  type    Be Vietnam Pro (font do người Việt thiết kế, đủ dấu): tiêu đề 900, 84–96 px, tracking -2%; thân 600/400, 34–44 px. Code: IBM Plex Mono 30 px.
  ảnh     ảnh pipeline thật đặt như tờ giấy trên bàn: viền trắng 14 px, bóng 0 18px 40px rgba(20,23,26,.18). Không ảnh minh hoạ giả.
  mặt     Tùng: khung tròn 300 px góc dưới phải (cách mép 40 px), viền 6 px #14171A + vòng cam 3 px khi mở đầu phần mới.
  watermark  "Plan2Model · Trang · Thụ · Tùng · Minh", Be Vietnam Pro 600 20 px, #14171A 45%, góc trên phải.

OBJECTS: tờ bản vẽ (ảnh thật), ma trận 3x3, biểu đồ độ sáng, công tắc bật/tắt bước, cột điểm số, khung code, mô hình 3D căn nhà (Three.js từ demo_model.json).

MOTION:
  vào     expo.out 0.6–0.9 s; chữ tiêu đề: từng chữ blur 6px→0 trong 0.13 s, cách 0.067 s, không trượt.
  camera  power2.inOut 0.8–1.2 s (punch-in vào vùng phóng to trên ảnh).
  ra      power3.in, ngắn hơn vào 40%.
  stagger danh sách 60 ms; số đếm 0.8 s power2.out.
  chuyển cảnh: 4 loại có nguyên nhân – (1) ảnh của bước trước trượt thành ảnh "trước" của bước sau (carry across),
          (2) zoom xuyên vào vùng phóng to, (3) blur swap trên cùng nền giấy, (4) dip cut ở chỗ đổi phần lớn; không crossfade hai thế giới.

SHOTS (theo phần lời):
  S1 mở đầu  – chữ PLAN2MODEL in từng chữ; tên 4 thành viên hiện khi được gọi; ảnh chụp → bản vẽ → 3D lướt qua khi nói ý tưởng.
  S2 lý do   – chồng bản vẽ giấy, đồng hồ "≈ 1 giờ / tầng" đếm, điện thoại chụp (khung máy ảnh) bắn ra tấm ảnh.
  S3 tổng quan – sơ đồ 5 khối mọc từng khối khi đọc số.
  S4 9 bước  – mỗi bước: ảnh thật lớn ≥ 60% khung, nhãn tên hàm bằng code, 1 con số cam.
  S5 3D      – mô hình 3D xoay 30°/s, camera hạ từ trên xuống.
  S6 CubiCasa – bản vẽ thật, hai đồng hồ điểm, công tắc "Lấp tường rỗng" gạt TẮT, số tụt 0,59 → 0,20.
  S7 kết quả – cột Otsu / Nhóm / U-Net mọc theo lời.
  S8 code    – khung pipeline.py, tô dòng đang nói.
  S9 kết     – 3 hạn chế, câu kết, màn cảm ơn có 4 tên.

BANNED: nền tối/void, glow, neon, hạt bay, gradient tím xanh, glass card, giấy kem + serif nghiêng, nhãn số "01/02", chip viên thuốc,
        mọi thứ căn giữa, mọi thứ fade+trượt lên, chữ trôi khi đang đọc, khung/góc HUD trang trí, 3 thẻ hàng ngang, logo góc,
        bullet slide, phụ đề đè lên mặt.
QA:     đầu mỗi phần, mỗi khoảnh khắc "thầy thấy", con số 0,59→0,20, cột kết quả, khung code, màn kết; đọc được ở 360 px.
