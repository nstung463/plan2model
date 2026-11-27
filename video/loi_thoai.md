# Lời thoại video demo – Plan2Model (bản đầy đủ)

Tổng thời lượng: khoảng 13–14 phút (bản rút gọn ở cuối file: 8–9 phút).

Cách đọc file này:
- Chữ *in nghiêng trong ngoặc* là việc cần làm trên màn hình. Không đọc ra.
- Dấu **[dừng]** là nghỉ khoảng 1 giây, để dễ cắt và chèn hình.
- Phần trong khung "> " là lời nói.
- Không cần đọc đúng từng chữ. Nói theo ý mình cho tự nhiên là được.
- Các con số trong lời thoại phần 4 là số của **ảnh chụp mô phỏng**, ảnh mặc định của app. Nếu mày đổi ảnh khác thì đọc số trên màn hình.

Chuẩn bị trước khi quay:
- Chạy app bằng lệnh `streamlit run app.py`, mở trình duyệt toàn màn hình.
- Sidebar: chọn **Ảnh mẫu**, ảnh **"Ảnh chụp mô phỏng"**.
- Ở tab **Quá trình xử lý**, chọn **Bước 1**.
- Phần 4 dùng nút **"Bước sau"** để tự chuyển theo lời nói. Không dùng nút "Tự chạy", vì mỗi bước nói dài ngắn khác nhau.

---

## 1. Mở đầu (khoảng 20 giây)

*(Đoạn này sẽ được thay bằng phần tiêu đề.)*

> Em chào thầy. Em là Nguyễn Sơn Tùng. Nhóm em có bốn người: bạn Nguyễn Thu Trang, bạn Nguyễn Văn Thụ, bạn Nguyễn Hoàng Khôi Minh, và em.
> Đề tài của nhóm em là **Plan2Model**.
> Ý tưởng rất đơn giản: mình chụp một tờ bản vẽ mặt bằng bằng điện thoại, rồi máy tự vẽ lại thành file CAD và dựng luôn mô hình 3D của căn nhà.

**[dừng]**

---

## 2. Vì sao làm đề tài này (khoảng 30 giây)

> Thầy biết là rất nhiều nhà, nhiều căn hộ cũ chỉ còn bản vẽ giấy.
> Mỗi lần muốn sửa nhà, làm nội thất hay quản lý toà nhà, người ta phải ngồi vẽ lại từ đầu trên AutoCAD, mất cả tiếng cho một tầng.
> Trong khi đó ai cũng có điện thoại trong túi.
> Nên nhóm em đặt câu hỏi: liệu chỉ cần chụp một tấm, rồi dùng các kỹ thuật xử lý ảnh học trong môn, có làm được phần việc đó không?

**[dừng]**

---

## 3. Tổng quan cách làm (khoảng 30 giây)

*(Đoạn này sẽ được thay bằng sơ đồ các khối.)*

> Hệ thống của nhóm em có năm khối lớn.
> **Một**, tìm tờ giấy trong ảnh và nắn nó cho thẳng.
> **Hai**, làm sạch ảnh: làm đều ánh sáng rồi đổi sang đen trắng.
> **Ba**, tìm tường.
> **Bốn**, tách từng phòng và tính diện tích.
> **Năm**, chuyển kết quả thành đường nét để xuất file CAD và dựng 3D.
>
> Nhóm em không dùng học sâu cho hệ thống chính, chỉ dùng xử lý ảnh cổ điển. Như vậy máy chạy nhanh, không cần dữ liệu để huấn luyện, và giải thích được từng bước.
> Bây giờ em mở app để thầy xem từng bước máy làm gì.

**[dừng]**

---

## 4. Đi qua từng bước xử lý (khoảng 7 phút)

Mỗi bước gồm 2 phần: nói ý tưởng khi nhìn ảnh, rồi cuộn xuống khung **"Kỹ thuật & hàm sử dụng"** để nói hàm, công thức và code.

*(Mở app, đang ở tab "Quá trình xử lý", Bước 1.)*

### 4.1 Ảnh đầu vào

> Đây là ảnh đầu vào. Em giả lập một tấm ảnh chụp bằng điện thoại: tờ giấy nằm nghiêng trên mặt bàn gỗ, ánh sáng không đều, và có bóng tay ở góc dưới.
> Đây là những chuyện hay gặp nhất khi người ta chụp thật. Các bước sau sẽ lần lượt xử lý từng chuyện một.

*(Bấm "Bước sau".)*

### 4.2 Tìm tờ giấy

> Việc đầu tiên là tìm tờ giấy nằm ở đâu.
> Ảnh bên trái là kết quả của bộ lọc **Canny**. Nói dễ hiểu, Canny tìm những chỗ mà độ sáng thay đổi đột ngột, tức là các đường cạnh. Mép tờ giấy trắng trên nền bàn gỗ tối là một cạnh rất rõ.
> Sau đó máy nối các cạnh lại thành các đường viền khép kín, lấy đường lớn nhất, rồi làm đơn giản nó đi. Nếu đơn giản xong mà còn đúng bốn góc thì đó là tờ giấy.
> Thầy thấy ở ảnh bên phải, bốn chấm đỏ đánh số một đến bốn là bốn góc máy tìm được.

*(Cuộn xuống khung "Kỹ thuật & hàm sử dụng".)*

> Trong code, bước này dùng năm hàm của OpenCV. **GaussianBlur** làm mờ ảnh cho bớt nhiễu. **Canny** tìm cạnh. Canny có bốn bước nhỏ: làm mờ, tính độ dốc sáng tối bằng bộ lọc Sobel, làm mảnh cạnh chỉ còn một điểm ảnh, rồi dùng hai ngưỡng 40 và 120: cạnh mạnh thì giữ, cạnh yếu chỉ giữ nếu nối được với cạnh mạnh.
> Sau đó **findContours** dò đường viền, và **approxPolyDP** rút gọn đường viền thành đa giác.

*(Bấm "Bước sau".)*

### 4.3 Nắn thẳng

> Có bốn góc rồi thì máy kéo tờ giấy về thành hình chữ nhật, giống như mình chụp thẳng từ trên xuống. Mấy app scan tài liệu trên điện thoại cũng làm đúng việc này.
> Về mặt toán, từ bốn cặp điểm, máy giải ra một ma trận ba nhân ba, gọi là **ma trận homography**. Thầy thấy ma trận đó ở góc dưới bên phải.
> Để dễ hình dung, em vẽ một lưới ô vuông lên ảnh gốc. Trên ảnh nghiêng các ô bị méo, nhưng sau khi nắn thì tất cả thành ô vuông đều nhau.
> Bước này quan trọng vì nếu không nắn, phòng hình chữ nhật sẽ thành hình thang và diện tích tính ra bị sai.

*(Cuộn xuống khung "Kỹ thuật & hàm sử dụng", chỉ vào công thức.)*

> Hàm dùng ở đây là **getPerspectiveTransform** để tính ma trận, và **warpPerspective** để nắn ảnh.
> Công thức ở đây: lấy toạ độ cũ nhân với ma trận H, rồi chia cho w. Chính phép chia này làm cho những đường song song trên tờ giấy bị chụm lại khi chụp nghiêng, và giờ mình làm ngược lại.
> Ma trận có tám ẩn, mỗi góc cho hai phương trình, nên đúng bốn góc là đủ.

*(Bấm "Bước sau".)*

### 4.4 Làm đều ánh sáng

> Tiếp theo là xử lý ánh sáng. Thầy nhìn ảnh giữa: đây là "nền giấy" mà máy ước lượng. Chỗ màu vàng là giấy sáng, chỗ tím đậm ở góc dưới là chỗ bị bóng tay.
> Cách máy ước lượng nền là dùng phép **đóng hình thái học** với một hình tròn khá lớn. Nét mực thì mảnh hơn hình tròn đó nên bị xoá mất, chỉ còn lại độ sáng của tờ giấy.
> Sau đó máy lấy ảnh chia cho nền. Chỗ nào bị tối thì được kéo sáng lên tương ứng.
>
> Thầy nhìn biểu đồ bên phải cho dễ thấy. Đây là độ sáng dọc theo đường kẻ vàng trên ảnh trái.
> Đường màu cam là nền: nó đi xuống ở chỗ có bóng.
> Đường màu xanh là sau khi làm đều: nền phẳng lại gần 255, tức là trắng, chỉ còn những chỗ có nét mực là tụt xuống.

*(Cuộn xuống khung "Kỹ thuật & hàm sử dụng".)*

> Trong code, em dùng **morphologyEx** với tham số **MORPH_CLOSE**, phần tử cấu trúc là hình elip 41 nhân 41, rồi **GaussianBlur** cho nền mượt.
> Ý tưởng toán học là: ảnh chụp bằng độ phản xạ của giấy nhân với ánh sáng chiếu vào. Nền ước lượng chính là ánh sáng, nên chia cho nền thì chỉ còn lại tờ giấy và nét mực.

*(Bấm "Bước sau".)*

### 4.5 Đổi sang đen trắng (Sauvola)

> Bước này máy quyết định mỗi điểm ảnh là mực hay là giấy.
> Cách thông thường là phương pháp **Otsu**: chọn một ngưỡng chung cho cả tấm ảnh, ở đây là 157. Điểm nào tối hơn 157 thì là mực.
> Thầy xem ảnh bên trái: vì chỉ có một ngưỡng nên cả vùng bị bóng đổ biến thành một mảng đen, bản vẽ ở đó mất luôn.
>
> Nhóm em dùng thuật toán **Sauvola**. Thay vì một ngưỡng chung, nó tính một ngưỡng riêng cho từng điểm, dựa vào một ô nhỏ 25 nhân 25 xung quanh điểm đó.
> Nó nhìn độ sáng trung bình của ô và độ chênh lệch sáng tối trong ô. Ô nào toàn giấy trắng thì ngưỡng khác, ô nào có nét mực thì ngưỡng khác.
> Ảnh giữa là bản đồ ngưỡng đó. Thầy thấy ngưỡng thay đổi theo từng vùng, từ khoảng 130 tới khoảng 200, chứ không phải một con số.
> Kết quả là ảnh bên phải, sạch hơn hẳn.
>
> Thuật toán này nhóm em **tự viết lại**, không gọi hàm Sauvola có sẵn của thư viện. Để chạy nhanh, nhóm em dùng **ảnh tích phân**: nhờ nó, tính trung bình của một ô chỉ tốn bốn phép cộng trừ, dù ô to cỡ nào.
> Nhóm em đã so với hàm có sẵn trong thư viện scikit-image, kết quả khớp 99,99% điểm ảnh.

*(Cuộn xuống khung "Kỹ thuật & hàm sử dụng", chỉ vào công thức Sauvola và đoạn code.)*

> Đây là công thức Sauvola: ngưỡng T bằng m nhân với một cộng k nhân s chia R trừ một. m là độ sáng trung bình, s là độ lệch chuẩn trong ô.
> Ô toàn giấy trắng thì s gần bằng 0, ngưỡng sẽ thấp hơn trung bình khá nhiều, nên không sinh ra chấm nhiễu. Ô có nét mực thì s lớn, ngưỡng gần trung bình, nên tách được nét.
> Còn đây là code. Em gọi **cv2.integral** để tạo ảnh tích phân, rồi lấy tổng của mỗi ô bằng bốn phép cộng trừ ở bốn góc, như dòng này. Phần còn lại em viết bằng numpy, tính cho cả ảnh cùng một lúc.

*(Bấm "Bước sau".)*

### 4.6 Lấp tường rỗng

> Bây giờ tới phần tìm tường. Có một vấn đề: nhiều bản vẽ không tô đen tường, mà chỉ vẽ hai đường viền song song, ruột ở giữa để trắng.
> Bước sau đó máy sẽ giữ nét dày và xoá nét mảnh. Mà mỗi đường viền thì rất mảnh, nên nếu để nguyên, tường sẽ bị xoá mất.
>
> Nên nhóm em thêm bước **lấp tường rỗng**. Máy xét từng vùng trắng bị mực bao kín, và hỏi hai câu:
> Vùng này có **hẹp** không, và có **dài** không?
> Để đo độ hẹp, máy dùng **biến đổi khoảng cách**: với mỗi điểm trắng, tính xem nó cách nét mực gần nhất bao xa. Điểm xa nhất cho biết nửa bề rộng của vùng.
> Ruột tường thì vừa hẹp vừa dài, nên được tô kín lại, là phần màu đỏ trên ảnh. Còn phòng thì rất rộng, nên không bị tô nhầm.
> Ở ảnh này máy lấp được 6 khe. Thầy xem ảnh phóng to bên phải cho rõ.

*(Cuộn xuống khung "Kỹ thuật & hàm sử dụng".)*

> Trong code, em dùng ba hàm. **connectedComponentsWithStats** đánh số từng vùng trắng và trả về diện tích, khung bao của nó. **distanceTransform** tính khoảng cách từ mỗi điểm tới nét mực gần nhất. Rồi em lấy giá trị lớn nhất trong mỗi vùng, gọi là r.
> Điều kiện để lấp là bốn điều trong công thức này: r từ 1,5 tới 14 điểm ảnh, diện tích chia r bình phương từ 6 trở lên, cạnh dài hơn 6 lần r, và không chạm mép ảnh.

*(Bấm "Bước sau".)*

### 4.7 Giữ lại nét dày (phép mở)

> Tới đây trên ảnh vẫn còn rất nhiều thứ không phải tường: chữ, ký hiệu cửa, đồ nội thất, đường kích thước.
> Điểm chung là tường luôn là nét dày nhất. Nên máy dùng phép **mở**, gồm hai bước với một ô vuông 7 nhân 7 điểm ảnh.
>
> Bước một là **co**: một điểm chỉ còn là mực nếu cả ô vuông quanh nó đều là mực. Nét nào mảnh hơn 7 điểm ảnh sẽ biến mất hoàn toàn. Nét dày thì chỉ bị gọt mỏng đi. Thầy thấy ở ảnh trái.
> Bước hai là **giãn**: nở phần còn lại ra đúng bằng chừng đó, để tường trở về độ dày ban đầu.
>
> Ảnh giữa: màu đen là tường được giữ lại, màu hồng là những nét đã bị xoá. Ở ảnh này khoảng một phần ba lượng mực bị xoá đi, toàn là chữ và ký hiệu.
> Con số 7 này nhóm em không tự đặt, mà thử nhiều giá trị trên một tập ảnh riêng rồi chọn số tốt nhất.

*(Cuộn xuống khung "Kỹ thuật & hàm sử dụng", chỉ vào công thức.)*

> Đây là định nghĩa trong môn: phép mở A mở B bằng A co B, rồi giãn B. Phép co giữ lại những điểm mà ô vuông đặt ở đó nằm trọn trong mực. Phép giãn thì ngược lại.
> Trong code chỉ có một dòng: **morphologyEx** với **MORPH_OPEN** và ô vuông 7 nhân 7. Sau đó **connectedComponentsWithStats** bỏ các mảnh nhỏ hơn 400 điểm ảnh.

*(Bấm "Bước sau".)*

### 4.8 Đổi từ điểm ảnh sang mét

> Có tường rồi, nhưng máy mới chỉ biết kích thước theo điểm ảnh. Muốn tính mét vuông thì phải biết một mét bằng bao nhiêu điểm ảnh.
> App có ba cách. Ở đây em nhập bề rộng thật của căn nhà là 12,25 mét. Máy đo bề rộng tường trên ảnh, là đường đỏ, rồi chia ra được 84,5 điểm ảnh cho một mét.
> Cách thứ hai là đo độ dày tường. Ảnh phải là bản đồ khoảng cách: chỗ càng sáng là càng xa mép tường, nên đường sáng nhất chính là tim tường. Từ đó máy đo được tường dày khoảng 19 điểm ảnh, rồi giả định tường thật dày 25 phân để suy ra tỉ lệ.

*(Cuộn xuống khung "Kỹ thuật & hàm sử dụng".)*

> Ở đây em dùng lại **distanceTransform**. Giá trị ở tim tường bằng một nửa độ dày, nên em lấy trung vị rồi nhân hai. Dùng trung vị thay cho trung bình để không bị mấy khối đặc như cầu thang làm lệch.

*(Bấm "Bước sau".)*

### 4.9 Bịt khe cửa

> Muốn tách phòng thì mỗi phòng phải là một vùng kín. Nhưng tường có chỗ hở là cửa đi và cửa sổ.
> Nên máy bịt các khe đó lại bằng phép **đóng**, tức là giãn rồi co. Nhưng thay vì dùng ô vuông, máy dùng một **đoạn thẳng** dài 2,2 mét, làm một lần nằm ngang và một lần đứng.
> Có thể hình dung như mình cầm một cây thước dài 2,2 mét: hai đầu tường nào nằm thẳng hàng và cách nhau ngắn hơn cây thước thì được nối lại. Phần nối là màu xanh lá.
> Dùng đoạn thẳng thay vì ô vuông là để không làm dày mấy bức tường khác.

*(Cuộn xuống khung "Kỹ thuật & hàm sử dụng".)*

> Phép đóng là ngược lại với phép mở: giãn trước rồi co sau, nên nó lấp các khe nhỏ hơn phần tử cấu trúc.
> Trong code vẫn là **morphologyEx**, nhưng với **MORPH_CLOSE**, và phần tử cấu trúc là hình chữ nhật dài 185 nhân 1 điểm ảnh, tức một đoạn thẳng. Chạy một lần ngang, một lần dọc, rồi gộp lại bằng **bitwise_or**.

*(Bấm "Bước sau".)*

### 4.10 Tách phòng

> Bây giờ mỗi phòng đã là một vùng trắng kín. Máy đi đánh số từng vùng trắng liền nhau.
> Thầy có thể hình dung như đổ nước vào từng phòng: nước lan tới đâu thì đó là một phòng, gặp tường thì dừng.
> Sau đó máy lọc ra. Vùng nào chạm mép ảnh là bên ngoài nhà, bỏ đi, là màu xám. Vùng nào nhỏ hơn 1,5 mét vuông, như hộp kỹ thuật, khe tủ, cũng bỏ.
> Còn lại là phòng. Diện tích thì bằng số điểm ảnh chia cho bình phương của tỉ lệ.
> Ở ảnh này máy tìm được đủ 5 phòng.
> Diện tích ở đây là diện tích **thông thủy**, tức phần sàn bên trong tường, nên sẽ nhỏ hơn một chút so với số ghi trên bản vẽ, vì bản vẽ thường tính tới tim tường.

*(Cuộn xuống khung "Kỹ thuật & hàm sử dụng".)*

> Hàm chính là **connectedComponentsWithStats** với tham số **connectivity bằng 4**. Bốn liên thông nghĩa là nước chỉ chảy lên, xuống, trái, phải, không chảy chéo. Như vậy nước không rò qua chỗ hai bức tường chạm nhau ở góc.
> Hàm này trả luôn diện tích và trọng tâm từng vùng, nên em dùng trọng tâm để đặt nhãn tên phòng.

*(Bấm "Bước sau".)*

### 4.11 Vector hoá

> Phần mềm CAD không làm việc với điểm ảnh, mà với đường thẳng và đa giác. Nên bước này đổi mảng tường thành đa giác.
> Máy dò đường viền của tường, rồi làm đơn giản nó bằng thuật toán **Douglas–Peucker**: những điểm gần như nằm thẳng hàng thì bỏ đi, chỉ giữ lại các góc.
> Các chấm đỏ là các đỉnh còn lại. Thầy thấy: hơn một trăm nghìn điểm ảnh tường, giờ chỉ còn 81 đỉnh. File vì vậy rất nhẹ, và sửa được trong AutoCAD.

*(Cuộn xuống khung "Kỹ thuật & hàm sử dụng".)*

> Hàm **findContours** với chế độ **RETR_CCOMP** cho biết viền nào là viền ngoài, viền nào là lỗ bên trong, ví dụ như sân trong.
> Còn **approxPolyDP** là thuật toán Douglas–Peucker. Nó nối điểm đầu với điểm cuối, tìm điểm xa đoạn đó nhất. Nếu xa hơn 1,5 điểm ảnh thì giữ điểm đó lại rồi chia đôi làm tiếp. Nếu không thì thay cả đoạn bằng một đường thẳng.

*(Bấm "Bước sau".)*

### 4.12 Dựng 3D và xuất CAD

> Bước cuối cùng, mỗi đa giác tường được kéo lên cao 2,8 mét để thành khối 3D, sàn mỗi phòng tô một màu. Đồng thời máy ghi ra file DXF để mở bằng AutoCAD.
> Cả quá trình mười mấy bước này chạy chưa tới một giây.

*(Cuộn xuống khung "Kỹ thuật & hàm sử dụng".)*

> File CAD được ghi bằng thư viện **ezdxf**, mô hình 3D dùng **Three.js**: hàm **ExtrudeGeometry** kéo mỗi đa giác tường lên cao 2,8 mét.
> Lúc đổi sang mét em phải lật trục y, vì trong ảnh trục y hướng xuống, còn trong bản vẽ CAD thì hướng lên.

**[dừng]**

---

## 5. Mô hình 3D (khoảng 20 giây)

*(Bấm tab "Mô hình 3D". Kéo chuột xoay chậm, lăn chuột zoom vào một phòng, rồi bấm "Nhìn từ trên".)*

> Còn đây là mô hình 3D. Thầy có thể xoay, phóng to, nhìn từ trên xuống. Mỗi phòng có nhãn tên và diện tích.
> Mô hình chạy thẳng trên trình duyệt, không cần cài phần mềm gì.

**[dừng]**

---

## 6. Thử với bản vẽ thật (khoảng 40 giây)

*(Sidebar: chọn một ảnh CubiCasa5K, ví dụ một ảnh thuộc nhóm "kiến trúc". Quay về tab "Quá trình xử lý", bấm nhanh qua bước "Lấp tường rỗng" và "Tách phòng". Sau đó rê chuột lên ô Wall IoU và Room F1 ở trên cùng.)*

> Ảnh mô phỏng thì dễ. Bây giờ em thử với bản vẽ thật, lấy từ bộ dữ liệu **CubiCasa5K**. Đây là bộ dữ liệu công khai có năm nghìn bản vẽ căn hộ ở Phần Lan, và mỗi bản vẽ đều có đáp án do người vẽ tay. Nhờ vậy mình chấm điểm được.
> Thầy thấy bản vẽ thật phức tạp hơn nhiều: nhiều chữ, nhiều ký hiệu, tường vẽ đủ kiểu.
>
> Trên cùng có hai con số.
> **Wall IoU** đo phần tường máy tìm được trùng với tường thật bao nhiêu. Bằng 1 là trùng hoàn toàn. Ở ảnh này là *(đọc số trên màn hình)*.
> **Room F1** đo máy tách phòng đúng tới đâu: vừa phải tìm đủ phòng, vừa không được tìm ra phòng giả. Ở đây là *(đọc số trên màn hình)*.

**[dừng]**

---

## 7. Tắt thử một bước (khoảng 30 giây)

*(Vẫn ảnh CubiCasa đó. Ở tab "Quá trình xử lý", chọn bước "Lấp tường rỗng". Trong sidebar, mục "Ablation", tắt công tắc "Lấp tường rỗng". Chờ kết quả.)*

> Để thầy thấy bước lấp tường rỗng quan trọng thế nào, em tắt nó đi.
> Thầy thấy ô Wall IoU tụt từ *(số cũ)* xuống *(số mới)*.
> Lý do là các bức tường chỉ vẽ viền giờ không được tô kín, nên tới bước giữ nét dày, chúng bị xoá đi như chữ.

*(Bấm sang bước "Giữ nét dày" để thấy tường bị mất. Sau đó bật lại công tắc.)*

> Bật lại thì kết quả trở về như cũ. Trong báo cáo, nhóm em làm thí nghiệm này cho từng khối, và đây là khối ảnh hưởng nhiều nhất.

**[dừng]**

---

## 8. Kết quả tổng thể (khoảng 45 giây)

*(Đoạn này sẽ được thay bằng biểu đồ.)*

> Về kết quả chung, nhóm em chấm trên 60 bản vẽ thật của CubiCasa5K, chia đều ba loại bản vẽ.
> Để công bằng, nhóm em làm như sau: mọi tham số, như kích thước ô 7 điểm ảnh hay độ dài khe cửa, đều được chọn trên một bộ 45 ảnh khác. Còn 60 ảnh này để riêng ra, chỉ dùng đúng một lần để chấm điểm cuối cùng. Phương pháp so sánh cũng được chọn tham số theo đúng cách đó.
>
> So với cách thông thường là Otsu, phương pháp của nhóm em tìm tường tốt hơn, Wall IoU từ 0,47 lên 0,56.
> Phần tách phòng tăng rõ hơn, Room F1 từ 0,32 lên 0,45.
> Nhóm em cũng kiểm tra thống kê bằng phương pháp bootstrap, lấy mẫu lại năm nghìn lần, thì mức tăng này là thật, không phải do may mắn chọn trúng ảnh dễ.

> Nhóm em cũng so với một mô hình học sâu là **U-Net**, huấn luyện trên 300 bản vẽ có đáp án, chạy khoảng hai tiếng rưỡi trên máy tính thường.
> U-Net tìm tường tốt hơn rõ, Wall IoU 0,77, còn Room F1 là 0,57.
> Nhưng đổi lại nó cần dữ liệu có đáp án để học, cần thời gian huấn luyện, và mình không giải thích được vì sao nó quyết định như vậy.
> Còn cách của nhóm em không cần học gì cả, chạy chưa tới một giây, và bước nào sai thì nhìn vào là biết sai ở đâu.
> Nên nhóm em thấy hướng tốt nhất sau này là kết hợp cả hai.

**[dừng]**

---

## 8b. Đi qua source code (khoảng 2 phút)

*(Mở VS Code, thư mục `F:\Project_Nhom_MSE`. Phóng chữ to lên, bấm Ctrl và dấu cộng 2–3 lần. Thu nhỏ cây thư mục bên trái.)*

> Bây giờ em đi qua source code một chút.
> Toàn bộ code nằm trong thư mục **prototype**. Có ba phần chính.

*(Rê chuột chỉ lần lượt vào từng file trong cây thư mục.)*

> File **pipeline.py** là phần lõi: mỗi bước xử lý ảnh em vừa trình bày là một hàm trong file này.
> File **core.py** gom các bước lại và xuất ra DXF và 3D. App Streamlit gọi file này.
> Còn **eval_cubicasa.py** và **tune.py** là phần chấm điểm và chọn tham số trên CubiCasa.

*(Mở `pipeline.py`, kéo tới hàm `sauvola`, khoảng dòng 50.)*

> Đây là hàm Sauvola nhóm em tự viết. Dòng này gọi **cv2.integral** để tạo ảnh tích phân.
> Rồi tới đây, tổng của mỗi ô được lấy bằng bốn góc: góc dưới phải, trừ góc trên phải, trừ góc dưới trái, cộng góc trên trái.
> Rồi tính trung bình m, độ lệch chuẩn s, và ngưỡng T đúng như công thức lúc nãy.

*(Kéo xuống hàm `fill_hollow_walls`, khoảng dòng 80.)*

> Đây là hàm lấp tường rỗng. Dòng này đánh số các vùng trắng, dòng này tính biến đổi khoảng cách.
> Còn dòng này là các điều kiện để quyết định có lấp hay không, đúng như lúc nãy em nói: vùng phải hẹp, phải dài, và không chạm mép ảnh.

*(Kéo xuống hàm `segment_rooms`, khoảng dòng 129.)*

> Còn đây là hàm tách phòng. Hai dòng này tạo hai đoạn thẳng, một nằm ngang một đứng, để bịt khe cửa. Dòng này đánh số các phòng với bốn liên thông, rồi lọc bỏ vùng chạm mép và vùng quá nhỏ.

*(Mở `eval_cubicasa.py`, chỉ vào hàm `prf` và `room_scores`, khoảng dòng 15–35.)*

> Cuối cùng là phần chấm điểm. Hàm này tính Wall IoU, tức phần giao chia phần hợp giữa tường máy tìm và tường thật.
> Hàm này ghép từng phòng máy tìm với phòng thật. Hai phòng chỉ được coi là khớp nếu trùng nhau từ một nửa trở lên.
>
> Toàn bộ code và hướng dẫn chạy lại kết quả nhóm em để trên GitHub, link ở trong báo cáo.

**[dừng]**

---

## 9. Xuất file CAD (khoảng 20 giây)

*(Bấm tab "Xuất file", bấm "Tải bản vẽ DXF". Nếu máy có AutoCAD thì mở file vừa tải.)*

> Cuối cùng, người dùng tải được file DXF, mở bằng AutoCAD hay đưa vào Revit đều được.
> Trong file đã chia sẵn ba lớp: lớp tường, lớp phòng, và lớp chữ ghi tên với diện tích từng phòng. Đơn vị là mét.
> Ngoài ra còn tải được mô hình 3D dạng trang web để gửi cho khách xem.

**[dừng]**

---

## 10. Hạn chế và kết luận (khoảng 35 giây)

*(Đoạn này sẽ được thay bằng phần tổng kết.)*

> Tóm lại, nhóm em đã làm được một hệ thống đi từ ảnh chụp bản vẽ tới file CAD và mô hình 3D, chỉ dùng các kỹ thuật xử lý ảnh trong môn: biến đổi phối cảnh, phân ngưỡng, hình thái học, biến đổi khoảng cách, gán nhãn vùng liên thông và tìm đường viền.
>
> Hệ thống vẫn còn vài hạn chế.
> Một, bản vẽ tay nét mờ thì máy dễ bỏ sót tường.
> Hai, cầu thang và quầy bếp cũng là nét dày, nên đôi khi bị nhận nhầm là tường.
> Ba, những phòng thông nhau không có tường ngăn, như bếp với phòng khách, thì máy chưa tách ra được.
>
> Sắp tới nhóm em muốn thử với nhiều ảnh chụp thật hơn, và cho máy tự đọc tỉ lệ ghi trên bản vẽ để người dùng không phải nhập tay.
>
> Em cảm ơn thầy đã xem.

---

## Mẹo khi quay

- Đọc thử một lượt trước khi quay. Chỗ nào nói không tự nhiên thì sửa theo cách mình hay nói.
- Nói chậm hơn bình thường một chút. Nói nhanh thì phụ đề chạy không kịp.
- Ở phần 4, nói xong một bước rồi mới bấm "Bước sau". Đợi ảnh hiện xong rồi mới nói tiếp.
- Khi nói tới ảnh nào thì rê chuột chỉ vào ảnh đó, thầy sẽ dễ theo hơn.
- Lỡ vấp thì dừng 2 giây rồi nói lại câu đó, không cần quay lại từ đầu. Phần vấp sẽ được cắt đi.
- Video dài khoảng 13–14 phút. Nếu thầy giới hạn thời gian thì phần 4 chỉ nói phần **hàm và công thức** cho 4 bước: **Đen trắng, Lấp tường rỗng, Giữ nét dày, Tách phòng**. Các bước còn lại chỉ nói ý tưởng rồi bấm qua. Như vậy còn khoảng 8–9 phút.
- Phần 4 đã nói hàm qua khung trong app, nên phần 8b (VS Code) chỉ cần cho thầy thấy code **có thật** và nằm ở đâu. Không cần đọc từng dòng.
- Khi nói công thức, rê chuột chỉ vào từng ký hiệu. Không cần đọc công thức, chỉ cần nói ý nghĩa của nó.
