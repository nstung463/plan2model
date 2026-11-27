# Lời đọc trước camera – Plan2Model (khoảng 10 phút)

Quay **một video duy nhất**: mặt + giọng, đọc liền một mạch từ đầu tới cuối. Không cần mở laptop, không cần bấm app hay VS Code. Cắt cảnh, hình app, code, biểu đồ, phụ đề tao tự dựng bằng HyperFrames, khớp theo lời mày nói.

- Đầu video im 2 giây rồi mới nói. Cuối video im 2 giây rồi mới tắt.
- Hết mỗi đoạn thì nghỉ khoảng 1 giây. Hết mỗi phần (tiêu đề lớn) thì nghỉ 2 giây. Tao cắt cảnh ở các chỗ nghỉ này.
- Lỡ vấp: im 2 giây rồi nói lại nguyên câu đó, quay tiếp, không dừng máy. Tao cắt chỗ vấp.
- Chỗ "thầy thấy", "ở ảnh này", "dòng này" cứ nói bình thường, hình sẽ được khớp vào đúng lúc đó.
- Tên hàm, công thức sẽ hiện chữ trên màn hình, nên lời nói chỉ cần giải thích ý nghĩa.
- Số liệu đều là số thật, đọc đúng như ghi. Phần 6 dùng bản vẽ CubiCasa `high_quality_architectural_875`.
- Quay ngang 1920×1080, mặt ở giữa khung, có ánh sáng phía trước mặt. Mic gần miệng, phòng yên tĩnh.
- Quay xong bỏ file vào `F:\Project_Nhom_MSE\video\raw\` rồi nhắn tao.

---

### 1. Mở đầu

Em chào thầy. Em là Nguyễn Sơn Tùng. Nhóm em có bốn người: bạn Nguyễn Thu Trang, bạn Nguyễn Văn Thụ, bạn Nguyễn Hoàng Khôi Minh, và em. Đề tài của nhóm em là **Plan2Model**: chụp một tờ bản vẽ mặt bằng bằng điện thoại, rồi máy tự vẽ lại thành file CAD và dựng luôn mô hình 3D của căn nhà.

---

### 2. Vì sao làm đề tài này

Rất nhiều nhà cũ chỉ còn bản vẽ giấy. Muốn sửa nhà hay làm nội thất, người ta phải vẽ lại từ đầu trên AutoCAD, mất cả tiếng cho một tầng. Nên nhóm em muốn thử: chỉ cần chụp một tấm, dùng các kỹ thuật xử lý ảnh học trong môn, có làm được việc đó không.

---

### 3. Tổng quan cách làm

Hệ thống có năm khối. Một, tìm tờ giấy và nắn cho thẳng. Hai, làm sạch ảnh. Ba, tìm tường. Bốn, tách phòng và tính diện tích. Năm, xuất file CAD và dựng 3D.

Nhóm em không dùng học sâu cho hệ thống chính, chỉ dùng xử lý ảnh cổ điển. Nên máy chạy nhanh, không cần dữ liệu huấn luyện, và giải thích được từng bước. Bây giờ em đi qua từng bước trên app.

---

### 4. Đi qua từng bước xử lý

#### 4.1 Ảnh đầu vào và tìm tờ giấy

Đây là ảnh đầu vào: một tấm ảnh chụp giả lập, tờ giấy nằm nghiêng trên bàn gỗ, ánh sáng không đều, có bóng tay ở góc dưới.

Đầu tiên máy tìm tờ giấy. Bộ lọc **Canny** tìm những chỗ độ sáng thay đổi đột ngột, tức là các cạnh. Máy nối các cạnh thành đường viền, lấy đường lớn nhất, rút gọn lại. Nếu còn đúng bốn góc thì đó là tờ giấy, là bốn chấm đỏ thầy thấy ở đây.

#### 4.2 Nắn thẳng

Có bốn góc rồi, máy kéo tờ giấy về hình chữ nhật, giống như chụp thẳng từ trên xuống. Từ bốn cặp điểm, máy giải ra một ma trận ba nhân ba gọi là **homography**. Lưới ô vuông này cho thấy: trước khi nắn các ô bị méo, sau khi nắn thì đều nhau. Không nắn thì phòng hình chữ nhật thành hình thang, diện tích sẽ sai.

#### 4.3 Làm đều ánh sáng

Tiếp theo là xử lý bóng đổ. Máy dùng phép **đóng hình thái học** với một hình tròn lớn. Nét mực mảnh hơn hình tròn nên bị xoá, chỉ còn lại độ sáng của nền giấy. Lấy ảnh chia cho nền thì chỗ tối được kéo sáng lên. Thầy xem biểu đồ: đường cam là nền bị tụt ở chỗ có bóng, còn đường xanh sau khi làm đều thì phẳng lại.

#### 4.4 Đổi sang đen trắng

Bước này quyết định mỗi điểm là mực hay giấy. Cách thông thường là **Otsu**, dùng một ngưỡng chung cho cả ảnh. Thầy thấy vùng bị bóng biến thành một mảng đen, mất luôn bản vẽ.

Nhóm em dùng **Sauvola**: mỗi điểm có ngưỡng riêng, tính từ độ sáng trung bình và độ chênh lệch sáng tối trong một ô 25 nhân 25 xung quanh. Kết quả sạch hơn hẳn.

Thuật toán này nhóm em tự viết lại, dùng **ảnh tích phân** để tính trung bình của một ô chỉ bằng bốn phép cộng trừ. So với hàm có sẵn của thư viện scikit-image thì khớp 99,99% điểm ảnh.

#### 4.5 Lấp tường rỗng

Bây giờ tới phần tìm tường. Nhiều bản vẽ không tô đen tường mà chỉ vẽ hai đường viền song song. Mỗi đường viền rất mảnh, nên bước sau sẽ xoá mất.

Vì vậy máy xét từng vùng trắng bị mực bao kín: nếu vùng đó vừa **hẹp** vừa **dài** thì đó là ruột tường, tô kín lại. Độ hẹp được đo bằng **biến đổi khoảng cách**, tức khoảng cách từ mỗi điểm tới nét mực gần nhất. Phòng thì rộng nên không bị tô nhầm. Ở ảnh này máy lấp được 6 khe, là phần màu đỏ.

#### 4.6 Giữ lại nét dày

Trên ảnh còn nhiều thứ không phải tường: chữ, ký hiệu cửa, đồ nội thất. Điểm chung là tường luôn là nét dày nhất. Nên máy dùng phép **mở** với ô vuông 7 nhân 7: phép co xoá mọi nét mảnh hơn 7 điểm ảnh, rồi phép giãn trả tường về độ dày cũ.

Thầy thấy màu đen là tường được giữ, màu hồng là phần bị xoá, toàn là chữ và ký hiệu. Con số 7 này nhóm em chọn bằng cách thử trên một tập ảnh riêng, không tự đặt.

#### 4.7 Đổi sang mét và bịt khe cửa

Để tính mét vuông, người dùng nhập bề rộng thật của căn nhà, ở đây là 12,25 mét, máy suy ra được 84,5 điểm ảnh cho một mét.

Muốn tách phòng thì mỗi phòng phải kín, nhưng tường bị hở ở cửa. Máy bịt khe bằng phép **đóng**, dùng một **đoạn thẳng** dài 2,2 mét, một lần ngang, một lần dọc. Hai đầu tường nào thẳng hàng và gần hơn 2,2 mét thì được nối lại, là phần màu xanh lá. Dùng đoạn thẳng để không làm dày các bức tường khác.

#### 4.8 Tách phòng

Giờ máy đánh số từng vùng trắng liền nhau, giống như đổ nước vào từng phòng, gặp tường thì dừng. Máy dùng **bốn liên thông**, tức nước chỉ chảy lên xuống trái phải, nên không rò qua góc tường.

Vùng chạm mép ảnh là bên ngoài nhà, vùng nhỏ hơn 1,5 mét vuông cũng bỏ. Còn lại là phòng. Ở ảnh này máy tìm đủ 5 phòng. Diện tích ở đây là diện tích thông thủy, nên nhỏ hơn một chút so với số trên bản vẽ.

#### 4.9 Vector hoá và dựng 3D

Cuối cùng, phần mềm CAD cần đường thẳng chứ không cần điểm ảnh. Thuật toán **Douglas–Peucker** bỏ các điểm gần thẳng hàng, chỉ giữ góc: hơn một trăm nghìn điểm ảnh tường còn 81 đỉnh. Mỗi đa giác được kéo lên cao 2,8 mét thành mô hình 3D, và ghi ra file DXF. Cả quá trình chạy chưa tới một giây.

---

### 5. Mô hình 3D

Đây là mô hình 3D. Thầy có thể xoay, phóng to, nhìn từ trên xuống, mỗi phòng có tên và diện tích. Mô hình chạy thẳng trên trình duyệt.

---

### 6. Thử với bản vẽ thật

Ảnh mô phỏng thì dễ. Bây giờ em thử với bản vẽ thật trong bộ dữ liệu **CubiCasa5K**, gồm năm nghìn bản vẽ căn hộ có đáp án vẽ tay, nên chấm điểm được.

Có hai con số. **Wall IoU** đo tường máy tìm trùng với tường thật bao nhiêu, bằng 1 là trùng hoàn toàn. Ở ảnh này là 0,59. **Room F1** đo tách phòng đúng tới đâu, ở đây là 0,77.

Nếu em tắt bước lấp tường rỗng, Wall IoU tụt xuống 0,20 và không tách được phòng nào. Vì tường chỉ vẽ viền không được tô kín, nên bị xoá đi như chữ. Đây là khối ảnh hưởng nhiều nhất.

---

### 7. Kết quả tổng thể

Nhóm em chấm trên 60 bản vẽ thật. Mọi tham số đều chọn trên một bộ 45 ảnh khác, còn 60 ảnh này chỉ dùng đúng một lần để chấm điểm cuối.

So với Otsu, Wall IoU tăng từ 0,47 lên 0,56, Room F1 tăng từ 0,32 lên 0,45. Kiểm tra bằng bootstrap năm nghìn lần thì mức tăng này là thật, không phải do may mắn.

Nhóm em cũng so với mô hình học sâu **U-Net**, huấn luyện trên 300 bản vẽ. U-Net tốt hơn, Wall IoU 0,77, Room F1 0,57. Nhưng nó cần dữ liệu có đáp án, cần thời gian huấn luyện, và không giải thích được. Còn cách của nhóm em không cần học, chạy dưới một giây, và sai ở đâu nhìn vào là biết. Hướng tốt nhất sau này là kết hợp cả hai.

---

### 8. Source code

Về code, phần lõi nằm trong file **pipeline.py**, mỗi bước em vừa trình bày là một hàm. Ví dụ đây là hàm Sauvola nhóm em tự viết, dòng này tạo ảnh tích phân, dòng này tính ngưỡng đúng theo công thức. File **eval_cubicasa.py** là phần chấm điểm. Toàn bộ code để trên GitHub, link trong báo cáo.

---

### 9. Hạn chế và kết luận

Cuối cùng, người dùng tải được file DXF, mở bằng AutoCAD, đã chia sẵn lớp tường, lớp phòng và lớp chữ.

Hệ thống còn ba hạn chế: bản vẽ tay nét mờ dễ bỏ sót tường; cầu thang, quầy bếp đôi khi bị nhận nhầm là tường; và phòng thông nhau không có tường ngăn thì chưa tách được. Sắp tới nhóm em muốn thử nhiều ảnh chụp thật hơn, và cho máy tự đọc tỉ lệ trên bản vẽ.

Tóm lại, nhóm em đã làm được hệ thống đi từ ảnh chụp tới file CAD và mô hình 3D, chỉ bằng các kỹ thuật xử lý ảnh trong môn. Em cảm ơn thầy đã xem.
