# Kết quả CubiCasa5K (giao thức tune/test chuẩn)

- **Tune**: 45 ảnh từ `val.txt` chính thức (15 ảnh/nhóm). Grid search, mục tiêu J = 0.5·wall_IoU + 0.5·room_F1 → `params.json`.
- **Test**: 60 ảnh từ `test.txt` chính thức (20 ảnh/nhóm), chạy với tham số đã đóng băng. Không chỉnh gì thêm sau khi xem test.
- Baseline được tune cùng giao thức (k, ngưỡng cửa) để so sánh công bằng.
- Room F1: ghép 1-1 tham lam, IoU ≥ 0.5. Chỉ tính phòng, bỏ Outdoor/Undefined.

## Bảng chính (test, n = 60)

| Phương pháp | Wall IoU | Wall P | Wall R | Room mIoU | Room F1 |
|---|---|---|---|---|---|
| B0 Otsu (tune trên val) | 0.473 | 0.727 | 0.556 | 0.258 | 0.316 |
| B1 Sauvola v1 (tune trên val) | 0.421 | 0.649 | 0.525 | 0.345 | 0.304 |
| Đề xuất, k tự ước lượng | 0.552 | 0.672 | 0.756 | 0.387 | 0.447 |
| **Đề xuất, k = 7 (chọn trên val)** | **0.560** | 0.692 | 0.743 | 0.344 | **0.454** |

## Ablation (từ bản đề xuất)

| Bỏ khối | Wall IoU | Room F1 |
|---|---|---|
| Không bỏ gì | 0.552 | 0.447 |
| Lấp tường rỗng | 0.435 | 0.229 |
| Kênh màu | 0.544 | 0.426 |
| Làm phẳng sáng | 0.557 | 0.447 |

## Kiểm định (bootstrap theo cặp ảnh, 5000 lần, CI 95%)

“Đề xuất” trong bảng này là bản k tự ước lượng. Báo cáo so sánh bằng bản cuối (k = 7): so với Otsu là +0.088 [+0.038, +0.142] Wall IoU và +0.138 [+0.064, +0.216] Room F1.

| So sánh | Δ Wall IoU | Δ Room F1 |
|---|---|---|
| Đề xuất − Otsu | +0.080 [+0.030, +0.134] | +0.131 [+0.054, +0.210] |
| Đề xuất − bỏ lấp tường rỗng | +0.118 [+0.077, +0.161] | +0.218 [+0.143, +0.295] |
| k tự ước lượng − k = 7 | −0.008 [−0.014, −0.002] | −0.007 [−0.059, +0.046] |

## Kết luận
1. Phương pháp đề xuất hơn baseline Otsu có ý nghĩa thống kê, cả về tường lẫn phòng.
2. Lấp tường rỗng là đóng góp lớn nhất. Với nhóm bản vẽ kiến trúc, wall IoU tăng từ 0.21 lên 0.47.
3. Tự ước lượng độ dày tường **không giúp** trên CubiCasa (ảnh `F1_scaled` có tỉ lệ khá đồng đều). Trên val, k cố định = 7 cũng tốt hơn, nên **phương pháp cuối dùng k = 7** (quyết định này dựa trên val, không phải test).
4. Làm phẳng sáng không ảnh hưởng trên ảnh scan, như dự đoán. Tác dụng của nó cần kiểm chứng trên ảnh chụp điện thoại.

## Ghi chú về thời gian (ms)
Các biến thể dùng chung cache ảnh ứng viên trong cùng một ảnh, nên cột `ms` trong `summary.json` chỉ so sánh được giữa các biến thể tự tính lại từ đầu. Thời gian thực của bản đề xuất khoảng 0.5 s/ảnh trên CPU. Sauvola tự cài là khối chậm nhất.
