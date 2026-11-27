# REVIEW – Plan2Model video (bản 1)

## Quyết định dựng
- Một video duy nhất 8:47, dựng từ lời Tùng (quay mặt, iPhone). Lời được chép bằng faster-whisper large-v3-turbo (tiếng Việt), sửa tay ~70 chữ nghe nhầm.
- Cắt 6 chỗ: câu "muốn tách phòng…" nói lặp, "bằng một số trùng hoàn toàn", "mức này tăng là thật", "nên không giải thích được", đoạn kết đọc 2 lần, câu "subscribe" whisper tự bịa ở cuối. Khoảng lặng > 0,75 s rút còn ~0,35 s. 570 s → 523 s lời.
- Chất liệu: bàn vẽ kỹ thuật (giấy can lạnh #E9ECEA, lưới 48/240 px), mực #14171A, một màu nhấn cam #E04410 (đã tối hơn #FF5A1F để đạt tương phản 3,5:1). Font Be Vietnam Pro (đủ dấu tiếng Việt), code IBM Plex Mono.
- Mặt Tùng: khung tròn 296 px góc dưới phải suốt video; vòng cam loé lên ở 8 lần đổi phần lớn.
- Mọi hình là ảnh thật xuất từ chính pipeline của nhóm (`prototype/core.py` + `explain.py`), ảnh mô phỏng mặc định của app và bản vẽ CubiCasa `high_quality_architectural_875`. Mô hình 3D dựng bằng Three.js từ `demo_model.json` thật.
- Chuyển cảnh: blur swap trên cùng nền giấy (nền không bao giờ cắt), ảnh thay ảnh tại cùng vị trí, iris "đổ nước" ở bước tách phòng, wipe màn kết, 3D mọc tường từ mặt bằng 2D; whoosh nhẹ (0,22) ở 8 lần đổi phần.
- Phụ đề tiếng Việt 4–7 từ/nhóm, tô cam từ đang nói, nền trắng 92% vừa chữ, tránh khung mặt.

## Bản 2: app thật + code kiểu VS Code
- Quay app Streamlit thật (localhost:8501) bằng Chrome headless của HyperFrames + CDP screencast, con trỏ chuột vẽ thêm vì headless không có:
  mở app, 11 bước (bấm số bước → ảnh → cuộn tới "Kỹ thuật & hàm"), tab 3D xoay/zoom, mẫu CubiCasa 2090 + tắt "Lấp tường rỗng" (0,820 → 0,681), tab Xuất file bấm DXF.
  Script: `work/record_app.mjs`, ghép: `work/frames2mp4.py`, clip ở `assets/app/`.
- Mỗi cảnh 4.x mở bằng 6–7 s app thật trong khung trình duyệt, phóng vào vùng ảnh rồi trả về; cảnh 3D, CubiCasa, xuất file cũng có clip app.
- Cảnh source code thay bằng giao diện kiểu VS Code: cây thư mục thật, `pipeline.py` (sauvola, tô dòng 53–54, 65), `eval_cubicasa.py`, terminal `pip install -r requirements.txt` / `streamlit run app.py` → Local URL.
- Mẫu 875 (số mày đọc 0,59/0,77) không có trong danh sách mẫu của app, nên clip CubiCasa dùng mẫu 2090 và có nhãn ghi rõ; phần đọc số vẫn dùng khung số liệu 875.
- Render theo đoạn 60 s (`work/render_chunks.sh`) vì renderer ghi khung ra đĩa (~2 MB/khung), rồi ghép + track âm thanh tổng (`work/finalize.sh`).

## Đã đo / đã nhìn
- `hyperframes check`: ok, 0 lỗi. Cảnh báo giữ lại: track dày (chỉ ảnh hưởng hiển thị Studio), file captions dài (251 nhóm), vài dòng chữ ngắn hơn ngưỡng đọc vì lời nói chuyển ý nhanh.
- Snapshot từng cảnh ở đầu/cuối, cảnh 3D, công tắc ablation, màn kết.
- Âm thanh: giọng lọc ồn nhẹ + nén + chuẩn hoá -16 LUFS. Không nghe thử được, chỉ đo.

## Chưa có / hạn chế
- **Không có nhạc nền**: MusicGen local không chạy được vì ổ C đầy (Windows không nới được paging file). Thêm sau: đặt file vào `assets/bgm.wav` rồi chạy lại `work/build.py` (tự gắn ở volume 0,10).
- Lời nói "81 đỉnh, hơn 100.000 điểm ảnh tường" khác số pipeline hiện tại (74 đỉnh, 89.631 px) → trên màn hình không hiện hai số này.
- Cảnh yếu nhất: phần kết quả lúc đầu khá trống phía trên trước khi cột mọc.

## Bản 3
- Gỡ câu kêu đăng ký kênh do Whisper tự bịa ở phụ đề cuối (522,8–523,0 s); chỉ render lại đoạn c08, 23 khung khác bản trước.
