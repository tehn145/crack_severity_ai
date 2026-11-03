# PRODUCT.md – crack_severity_ai

## Mục tiêu sản phẩm
Xây dựng hệ thống thị giác máy tính và học sâu có giám sát hỗ trợ công tác kiểm định, bảo trì và đánh giá an toàn công trình xây dựng (bê tông, tường, mặt đường, sàn/dầm cầu, công trình nhà cao tầng):
1. **Phát hiện vết nứt bề mặt công trình từ ảnh 2D (Phase 1)**.
2. **Phân loại mức độ nghiêm trọng của vết nứt theo tiêu chuẩn (Phase 2)** (ACI 224R-01, TCVN 9381:2012).
3. **Đánh giá bong tróc bê tông & lộ cốt thép kết cấu (Phase 3 — Spalling & Exposed Rebar)**: Phục vụ kiểm định an toàn chịu lực cho các **tòa nhà bị đình trệ / đắp chiếu nhiều năm trước khi tái khởi công xây dựng tiếp** (theo TCVN 9381:2012 và ACI 562-19).

## Phạm vi
- Input: Ảnh số hai chiều (2D) thu thập từ máy ảnh, điện thoại thông minh, flycam/UAV.
- Đối tượng chính: Vết nứt bề mặt, vùng bê tông bong tróc (spalling), cốt thép chịu lực bị lộ (exposed rebar), hiện tượng gỉ sét ăn mòn.
- Ứng dụng trọng tâm:
  - Kiểm định định kỳ công trình đang khai thác (Structural Health Monitoring).
  - Đánh giá hiện trạng an toàn kết cấu các dự án dở dang, đình trệ để nghiệm thu điều kiện tái khởi công.
- Không dùng dữ liệu 3D laser scanner, ảnh nhiệt hay cảm biến chuyên dụng gắn trong kết cấu.

## Người dùng mục tiêu
- Kỹ sư kiểm định chất lượng công trình, tư vấn giám sát xây dựng.
- Chủ đầu tư, ban quản lý dự án tiếp nhận và tái khởi công công trình đình trệ.
- Nghiên cứu viên, sinh viên ngành Kỹ thuật Xây dựng và Khoa học Máy tính / Computer Vision.

## Ràng buộc quan trọng
- Phân loại mức độ nghiêm trọng phải tham chiếu tiêu chuẩn kỹ thuật xây dựng chính thống:
  - Vết nứt: ACI 224R-01, TCVN 9381:2012.
  - Bong tróc & lộ cốt thép: TCVN 9381:2012, ACI 562-19 (Đánh giá, sửa chữa kết cấu bê tông hiện hữu), ACI 318.
- Đo lường kích thước phải có kiểm chứng sai số định lượng (đã nghiệm thu $\le 1\text{px}$).
- Ưu tiên giải pháp có tính giải thích cao (explainable AI), có báo cáo in PDF chuẩn quy trình doanh nghiệp.
