# PRODUCT.md – crack_severity_ai

## Mục tiêu sản phẩm
Xây dựng hệ thống thị giác máy tính và học sâu có giám sát hỗ trợ công tác kiểm định, bảo trì và đánh giá an toàn công trình xây dựng (bê tông, tường, mặt đường, sàn/dầm cầu, công trình nhà cao tầng và di sản kiến trúc):
1. **Phase 1: Chuyên gia Phân đoạn Vết nứt Bề mặt (Crack Specialist)**:
   - **Phase 1.A (Bề mặt DỄ - Tường, Đường, Bê tông phẳng)**: Tập trung tối đa hóa độ chính xác vượt SOTA thế giới (mục tiêu >93% mAP50) với tiền xử lý nâng cao (Bilateral Filter + Adaptive CLAHE) và bổ sung 10-15% ảnh âm nền (non-crack backgrounds).
   - **Phase 1.B (Bề mặt KHÓ - Di sản, Gạch men, Mạch vữa)**: Xử lý khử bóng phản quang (Retinex) và lọc hoa văn nền phức tạp.
2. **Phase 2: Chuyên gia Khuyết tật Kết cấu Phá hủy (Structural Damage Specialist)**:
   - Độc lập hoàn toàn với Phase 1, **loại bỏ triệt để nhãn `crack`** để tránh xung đột định dạng.
   - Nhận diện phân đoạn 3 lớp hư hỏng thể tích: **Bong tróc bê tông (`spalling`)**, **Lộ cốt thép chịu lực (`exposed_rebar`)**, và **Gỉ sét ăn mòn kim loại (`corrosion`)**.
   - Mục tiêu mAP50 >90% (vượt kỷ lục SOTA thế giới hiện nay ~89.5%).
3. **Phase 3: Hệ thống Giám định Sức khỏe Kết cấu Toàn diện (SHM Engine & Building/Heritage Assessment)**:
   - Kiểm định đơn lẻ từng ảnh hoặc kiểm định toàn bộ công trình (quét theo từng tầng hoặc khối di sản như Tháp Bà Ponagar).
   - Khử trùng lặp diện tích không gian bằng thuật toán ORB Homography khi chụp nhiều góc.
   - AI tự động nhận diện và bo khung cấu kiện (Cột 3.0x, Nút dầm-cột 3.5x, Dầm 2.5x, Bản sàn/Trần 1.5x, Tường 1.0x, Cổ cột móng 4.0x).
   - Ánh xạ khuyết tật vào cấu kiện chịu lực để xếp hạng mức độ nguy cơ.
   - Bảng điều khiển phân tích & lọc/sắp xếp đa tiêu chí (Sort theo số vết nứt trên Cột, Dầm, Sàn...; Sort theo chỉ số nguy cơ sụp đổ SCI 0-100%).

## Phạm vi
- Input: Ảnh số hai chiều (2D) thu thập từ máy ảnh, điện thoại thông minh, flycam/UAV.
- Đối tượng chính: Vết nứt bề mặt, vùng bê tông bong tróc (spalling), cốt thép chịu lực bị lộ (exposed rebar), hiện tượng gỉ sét ăn mòn, và cấu kiện kết cấu chịu lực.
- Ứng dụng trọng tâm:
  - Kiểm định định kỳ công trình đang khai thác (Structural Health Monitoring).
  - Đánh giá hiện trạng an toàn kết cấu các dự án dở dang, đình trệ để nghiệm thu điều kiện tái khởi công.
  - Khảo sát hư hỏng các công trình di sản văn hóa kiến trúc cổ.
- Không dùng dữ liệu 3D laser scanner, ảnh nhiệt hay cảm biến chuyên dụng gắn trong kết cấu.

## Người dùng mục tiêu
- Kỹ sư kiểm định chất lượng công trình, kỹ sư kết cấu (PE - Professional Engineer), tư vấn giám sát xây dựng.
- Ban quản lý dự án, chủ đầu tư các tòa nhà cao tầng và đơn vị quản lý di tích di sản.
- Nghiên cứu viên, sinh viên ngành Kỹ thuật Xây dựng và Khoa học Máy tính / Computer Vision.

## Ràng buộc quan trọng
- Phân loại mức độ nghiêm trọng và nguy cơ sụp đổ phải tham chiếu tiêu chuẩn kỹ thuật xây dựng chính thống:
  - Vết nứt: ACI 224R-01, TCVN 9381:2012.
  - Bong tróc & lộ cốt thép: TCVN 9381:2012, ACI 562-19 (Đánh giá, sửa chữa kết cấu bê tông hiện hữu), ACI 318.
- Đo lường kích thước phải có kiểm chứng sai số định lượng (đã nghiệm thu $\le 1\text{px}$).
- Đảm bảo tính giải thích cao (explainable AI), có báo cáo in PDF chuẩn quy trình doanh nghiệp có chữ ký PE sign-off.
