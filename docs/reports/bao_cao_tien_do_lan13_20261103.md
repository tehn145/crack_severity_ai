# BÁO CÁO TIẾN ĐỘ KHÓA LUẬN TỐT NGHIỆP (LẦN 13)
**Ngày báo cáo:** 03 tháng 11 năm 2026  
**Đề tài:** Phát hiện và phân loại vết nứt bề mặt công trình xây dựng từ ảnh hai chiều sử dụng mô hình học sâu  
*(Detection and Classification of Surface Cracks on Civil Infrastructure from Two-Dimensional Images Using Deep Learning Models)*  
**GVHD:** TS. Phan Xuân Thiện  
**Sinh viên thực hiện:**  
- Ngô Kim Thành – 23521447  
- Trần Công Thành – 23521463  

---

## 1. Mục tiêu và Những Việc Trọng Tâm Đã Triển Khai Trong Tuần

Trong tuần qua, nhóm đã thực hiện bước chuyển dịch chiến lược mang tính đột phá về phạm vi đề tài, kho dữ liệu và giải pháp mô hình:

1. **Mở rộng phạm vi và bối cảnh ứng dụng thực tế của đề tài**:
   - **Tòa nhà cao tầng khó tiếp cận & Trụ tháp cầu dây văng cao**: Xử lý ảnh chụp từ Flycam/Drone (UAV) với góc nghiêng, khoảng cách xa, điều kiện rung lắc.
   - **Công trình tạm dừng thi công thời gian dài / Tòa nhà hoang cần tái khởi động**: Kiểm tra độ an toàn chịu lực tổng thể, suy thoái bề mặt do thời tiết sau nhiều năm phơi mưa nắng trước khi cho phép tiếp tục thi công.
   - **Di tích kiến trúc lịch sử, công trình cổ**: Kiểm định vết nứt trên tường gạch vữa cổ, tường đá khối phục vụ trùng tu, bảo tồn di sản văn hóa và đảm bảo an toàn tuyệt đối cho người tham quan.
   - **Hạ tầng giao thông đa dạng**: Mặt đường nhựa, bản mặt cầu bê tông, tường chắn.
2. **Xây dựng và kiểm toán kho dữ liệu đa bề mặt (Dataset V3) quy mô lớn**:
   - Hoàn thành kiểm toán **19 bộ dữ liệu lớn**, phân rã thành **67 bộ dữ liệu con (sub-datasets)** với tổng số **90,342 dòng ảnh thực tế** trên **9 nhóm bề mặt**.
   - Xuất file báo cáo kiểm toán chi tiết: [`outputs/reports/dataset_v3_multi_surface_inventory.xlsx`](file:///d:/crack_severity_ai/outputs/reports/dataset_v3_multi_surface_inventory.xlsx).
3. **Quyết định triển khai Phase 3 -- Kiểm định Bong tróc và Lộ cốt thép (Spalling)**:
   - Mở rộng hệ thống thành chu trình khép kín 3 giai đoạn: *Phân đoạn nứt (Phase 1) $\rightarrow$ Đánh giá mức độ nghiêm trọng (Phase 2) $\rightarrow$ Nhận diện bong tróc \& lộ cốt thép (Phase 3)*.
4. **Nghiên cứu và chọn lọc giải pháp tiền xử lý ảnh nâng cao độ chính xác**:
   - Thử nghiệm các kỹ thuật CLAHE, Bilateral Filter, Black-Hat transform nhằm làm nổi bật vết nứt mảnh và triệt tiêu nhiễu bề mặt gồ ghề.
5. **Hoàn thiện ứng dụng kiểm định thông minh**:
   - Nâng cấp module đo lường sub-pixel, công cụ hiệu chuẩn thước đo GSD tương tác, quản lý hồ sơ kiểm định kỹ thuật số và trích xuất báo cáo PDF có chữ ký.

---

## 2. Kiểm Toán và Phân Chia Kho Dữ Liệu Đa Bề Mặt (Dataset V3)

### 2.1. Thống kê hiện trạng
- **Tổng files quét thô trên đĩa:** **262,234 files** (ảnh, mask, label, patch).
- **Tổng số bộ lớn:** **19 bộ**.
- **Tổng số bộ con bóc tách chi tiết:** **67 bộ con**.
- **Tổng số dòng ảnh kiểm toán chi tiết trong báo cáo:** **90,342 ảnh**.

### 2.2. Ma trận phân bổ 9 nhóm bề mặt vật liệu
| Nhóm bề mặt | Nguồn dữ liệu tiêu biểu | Số lượng | Mục tiêu kiểm định thực địa |
| :--- | :--- | :---: | :--- |
| **1. Bê tông kết cấu** | SDNET2018, METU, 3DCrack, Khanh11k | ~95,000* | Dầm, cột, sàn chịu lực, công trình tái thi công |
| **2. Mặt đường & Cầu** | Roads_and_Bridges, Concrete_and_Pavement | ~23,000* | Mặt đường bê tông nhựa, bản mặt cầu |
| **3. Tường gạch & Đá cổ** | Darbhanga Fort, Masonry Sensors, Wall Crack | 12,946 | Pháo đài, di tích lịch sử, tường gạch vữa cổ |
| **4. Ngói & Gạch men** | Ceramics-defects-detection | 8,920 | Mái ngói di tích, gạch ốp lát bề mặt công trình |
| **5. Tường sơn & Vữa** | Detr_crack_dataset, BD3, Wall Crack EQ | 8,000 | Tường hoàn thiện nội ngoại thất, công trình đình trệ |
| **6. Di tích kiến trúc cổ** | Historical Building Cracks, Darbhanga | 5,013 | Bảo tồn di sản văn hóa, bảo đảm an toàn du khách |
| **7. Đa hư hại / Spalling** | BD3 (Major, Minor, Spalling, Peeling) | 3,965 | Kiểm tra công trình hoang, lộ cốt thép (Phase 3) |
| **8. Façade cao tầng** | BFDD Dataset (Drone Exterior) | 838 | Mặt ngoài nhà cao tầng chụp từ Flycam/Drone |
| **9. Vân đá / Nứt đá** | Sylvie, Forest | 303 | Hard-case test pool kiểm soát báo động giả |

*\* Đã bao gồm các tập ảnh patch cắt nhỏ $224 \times 224$ dùng cho kho khai thác ảnh âm tính.*

### 2.3. Chiến lược phân nhóm chuẩn bị huấn luyện (Training Splits)
1. **Nhóm A + B: Tập huấn luyện sạch (Ground Truth Polygon + Mask chuẩn) -- 26,207 ảnh:**
   - Đã chuẩn hóa về format YOLOv8 Polygon.
   - Phân chia: **Train 80% (20,965 ảnh) : Val 10% (2,621 ảnh) : Test 10% (2,621 ảnh)** phục vụ huấn luyện vòng V3-Core.
2. **Nhóm C + D: Tập đa bề mặt cần Pseudo-labeling -- 18,255 ảnh:**
   - Dùng model V3-Core để suy luận gán nhãn đa giác tự động cho di tích, tường gạch, ngói nứt, mở rộng tập train lên 45,000+ ảnh.
3. **Nhóm E: Kho Negative Mining -- 45,880 ảnh:**
   - Trích xuất lấy mẫu 3,000 -- 5,000 ảnh âm tính khó để huấn luyện triệt tiêu báo động giả.
4. **Loại bỏ trùng lặp (Duplicates):**
   - Loại bỏ CConCrack (10,995 ảnh trùng Khanh11k) và Vol2 (3,746 ảnh trùng Vol1).

---

## 3. Quyết Định Triển Khai Phase 3: Kiểm Định Bong Tróc và Lộ Cốt Thép (Spalling)

### 3.1. Tính cấp thiết trong kỹ thuật xây dựng
Vết nứt bề mặt khi gặp mưa và môi trường ăn mòn sẽ làm cốt thép rỉ sét, nở thể tích gây nứt toác và làm vỡ mảng bê tông bảo vệ (Spalling). Đối với các công trình bị bỏ hoang hoặc tạm dừng thi công nhiều năm, đây là nguyên nhân trực tiếp dẫn tới sập đổ kết cấu.

### 3.2. Chu trình khép kín 3 giai đoạn
- **Phase 1 (Crack Detection):** Phân đoạn vết nứt đa bề mặt (YOLOv8-seg cải tiến).
- **Phase 2 (Severity Classification):** Đo đạc $W_{\max}$, $L$, độ sâu suy diễn qua độ đậm theo chuẩn ACI 224R-01 / TCVN 9381:2012 (L0 -- L3).
- **Phase 3 (Spalling & Rebar Exposure):** Phát hiện bong vỡ bê tông và thanh thép lộ thiên, phân loại 4 cấp nguy hiểm:
  - **SP0 (Bong tróc nông):** Sứt mẻ lớp vữa trát bề mặt ($<20$mm), chưa chạm cốt thép.
  - **SP1 (Bong tróc sâu):** Mất lớp bê tông bảo vệ ($\geq 20$mm), bắt đầu chạm cốt thép.
  - **SP2 (Lộ cốt thép):** Cốt thép lộ thiên, bắt đầu xuất hiện vệt rỉ sét vàng nâu.
  - **SP3 (Nguy hiểm nghiêm trọng):** Cốt thép rỉ bong vảy, ăn mòn $>50\%$ chu vi $\rightarrow$ **Cảnh báo khẩn cấp dừng thi công / sơ tán**.

*Dữ liệu khởi tạo Phase 3:* Trích xuất thành công 500 ảnh spalling trong bộ BD3_original_dataset.

---

## 4. Nghiên Cứu và Chọn Lọc Kỹ Thuật Tiền Xử Lý Ảnh

Nhóm đã thử nghiệm đối chứng các phương pháp nhằm giải quyết bài toán vết nứt mảnh bị đứt nét trên bề mặt gồ ghề hoặc ảnh chụp từ xa:
1. **CLAHE (Contrast Limited Adaptive Histogram Equalization):** Cân bằng sáng thích ứng cục bộ (clip-limit 2.0), làm nổi bật vết nứt chân chim trong góc tối.
2. **Bilateral Filter (Lọc song phương):** Làm mịn các hạt cát, rêu mốc li ti nhưng bảo toàn độ sắc nét mép vết nứt.
3. **Toán tử hình thái học Black-Hat:** Bóc tách các rãnh tối hẹp ra khỏi nền xám sáng của bê tông.
4. **Kết quả:** Chuỗi tiền xử lý **Bilateral Filter + CLAHE** giúp nâng cao độ tương phản tương đối của vết nứt mảnh lên **+24.6%**, khắc phục điểm yếu bỏ sót 75.5% vết nứt nhỏ đã chỉ ra ở lần 12.

---

## 5. Hoàn Thiện Ứng Dụng Kiểm Định Thông Minh

Hệ thống ứng dụng kiểm định hỗ trợ kỹ sư hiện trường đã được nâng cấp:
- **Thước đo hiệu chuẩn GSD tương tác:** Chọn 2 điểm trên ảnh tương ứng vật chuẩn biết trước để tự động tính tỷ lệ mm/pixel.
- **Module đo đạc hình học Sub-pixel:** Tính toán tự động bề rộng $W_{\max}$, chiều dài $L$, diện tích $A$, hướng nứt $\theta$ với sai số $\leq 1$ pixel.
- **Phân hệ quản lý hồ sơ kiểm định:** Lưu trữ theo cấu kiện, quy trình duyệt 2 cấp (Kỹ sư kiểm tra $\rightarrow$ Kỹ sư trưởng phê duyệt).
- **Xuất báo cáo PDF tự động:** Tích hợp biểu đồ rủi ro, hình ảnh phân đoạn và khung chữ ký thẩm định.

---

## 6. Kế Hoạch Tuần Tới

1. **Khởi chạy huấn luyện V3-Core (26,207 ảnh):** Huấn luyện YOLOv8-seg trên Kaggle T4$\times$2 / Cloud A100 ở độ phân giải $960 \times 960$ tích hợp chuỗi tiền xử lý.
2. **Triển khai Pseudo-labeling tự động:** Dùng checkpoint V3-Core suy luận gán nhãn cho 18,000+ ảnh di tích, tường gạch, ngói nứt.
3. **Xây dựng bộ kiểm thử Phase 3 (Spalling):** Gán nhãn đa lớp (Crack, Spalling, Rebar) để hoàn thiện chu trình khép kín.
4. **Chuẩn bị bản thảo Khóa luận tốt nghiệp:** Viết hoàn chỉnh chương 3 (Dữ liệu đa bề mặt) và chương 4 (Kiến trúc mô hình 3 giai đoạn).
