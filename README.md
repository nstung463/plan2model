# Plan2Model

Ảnh chụp bản vẽ mặt bằng giấy → bản vẽ CAD (DXF) → mô hình 3D, bằng xử lý ảnh cổ điển (OpenCV).
Dự án nhóm môn **Xử lý Ảnh và Video số**, MSE – FPT University.

| | |
|---|---|
| Báo cáo | [`report/Plan2Model_Report.pdf`](report/Plan2Model_Report.pdf) (bản Word: `report/Plan2Model_Report.docx`) |
| Video demo | [Release v1.0 → `Plan2Model_video.mp4`](https://github.com/nstung463/plan2model/releases/tag/v1.0) (8:47) |
| Trọng số U-Net | [Release v1.0 → `unet_wall.pt`](https://github.com/nstung463/plan2model/releases/tag/v1.0) |
| Kết quả chi tiết | [`prototype/RESULTS.md`](prototype/RESULTS.md) |

## Thành viên

| Thành viên | MSHV | Phần việc chính |
|---|---|---|
| Nguyễn Thu Trang | | |
| Nguyễn Văn Thụ | | |
| Nguyễn Sơn Tùng | | |
| Nguyễn Hoàng Khôi Minh | | |

## Cài đặt

Python ≥ 3.9.

```bash
pip install -r requirements.txt
```

## Chạy demo

```bash
streamlit run app.py
```

Mở `http://localhost:8501`. App có sẵn ảnh chụp mô phỏng, có thể tải ảnh lên, chỉnh tham số, bật/tắt từng khối (ablation),
xem từng bước xử lý, mô hình 3D, và tải về DXF / JSON / HTML 3D.
Ảnh mẫu CubiCasa5K trong app chỉ hiện sau khi tải dữ liệu (bên dưới).

Chạy bằng dòng lệnh (không cần giao diện):

```bash
python prototype/run_demo.py   # ảnh mô phỏng → prototype/output/floorplan.dxf, model.json, demo.html
```

## Dữ liệu

Dữ liệu không đưa lên Git. CubiCasa5K được tải từng phần (HTTP range, ~60 MB) theo split chính thức:

```bash
python prototype/fetch_cubicasa.py val 45
python prototype/fetch_cubicasa.py test 60
python prototype/fetch_cubicasa.py train 300   # chỉ cần để train U-Net
```

## Tái lập kết quả

| Bước | Lệnh |
|---|---|
| Tune tham số trên val | `python prototype/tune.py` → `prototype/params.json` |
| Đánh giá trên test (baseline, đề xuất, ablation, bootstrap) | `python prototype/eval_cubicasa.py test` |
| U-Net (CPU) | `python prototype/unet_wall.py train 3000`, rồi `python prototype/eval_unet.py` |
| Hình cho báo cáo | `python prototype/make_figures.py` |
| Dựng báo cáo Word | `python report/build_report.py` |

## Kết quả chính (CubiCasa5K test, 60 ảnh)

| Phương pháp | Wall IoU | Room F1 |
|---|---|---|
| Baseline Otsu (tune trên val) | 0.473 | 0.316 |
| Baseline Sauvola v1 (tune trên val) | 0.421 | 0.304 |
| **Đề xuất (k = 7)** | **0.560** | **0.454** |
| U-Net ResNet-18 (học sâu, để so sánh) | 0.774 | 0.565 |

- Ablation: bỏ khối lấp tường rỗng làm Room F1 giảm từ 0.447 xuống 0.229. Đây là khối đóng góp lớn nhất.
- Bootstrap 5000 lần: phương pháp đề xuất hơn Otsu +0.080 Wall IoU, khoảng tin cậy 95 % [+0.030, +0.134].
- Tự cài đặt: ngưỡng Sauvola dùng ảnh tích phân (`prototype/pipeline.py`), đã kiểm chứng với `skimage.filters.threshold_sauvola`.

## Cấu trúc

```
app.py                     demo Streamlit
requirements.txt
prototype/
  pipeline.py              các bước xử lý ảnh (Sauvola tự cài, lấp tường rỗng, tách phòng…)
  core.py                  lõi dùng chung cho app: xử lý, xuất DXF/JSON/3D
  synth.py                 sinh bản vẽ tổng hợp + giả lập ảnh chụp điện thoại
  cubicasa_gt.py           đọc nhãn SVG của CubiCasa5K
  fetch_cubicasa.py        tải dữ liệu
  tune.py, eval_cubicasa.py  tune trên val, đánh giá trên test
  unet_wall.py, eval_unet.py U-Net so sánh
  explain.py, tech.py      giải thích từng bước cho app
  params.json              tham số đã đóng băng
  output/                  kết quả: bảng, hình dự đoán, DXF/3D mẫu
report/                    báo cáo (docx, pdf), script dựng báo cáo, hình
video/                     kịch bản và mã dựng video demo (HyperFrames)
```

## Khai báo sử dụng AI

Nhóm dùng Claude (Anthropic) qua Claude Code để hỗ trợ viết và sửa mã, gợi ý thiết kế thí nghiệm, soạn báo cáo và dựng video.
Chi tiết ở Phụ lục C của báo cáo.
