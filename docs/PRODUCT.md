# PRODUCT.md – crack_severity_ai

## Mục tiêu sản phẩm
Xây dựng hệ thống học sâu có giám sát theo mô hình 2 giai đoạn để:
1. Phát hiện vết nứt bề mặt công trình từ ảnh 2D (Phase 1)
2. Phân loại mức độ nghiêm trọng của vết nứt (Phase 2)

Hỗ trợ công tác kiểm định và bảo trì công trình xây dựng (bê tông, tường, mặt đường, mặt cầu).

## Phạm vi
- Input: ảnh số hai chiều (2D)
- Đối tượng chính: vết nứt bề mặt
- Không dùng dữ liệu 3D, ảnh nhiệt, cảm biến chuyên dụng
- Có thể tích hợp UAV/robot sau này (không bắt buộc trong khóa luận)

## Người dùng mục tiêu
- Kỹ sư kiểm định công trình
- Sinh viên / nghiên cứu viên làm SHM bằng computer vision

## Ràng buộc quan trọng
- Phân loại mức độ nghiêm trọng phải tham chiếu tiêu chuẩn (ACI 224R-01, TCVN 9381:2012)
- Chưa chốt cứng số lượng mức độ (đang nghiên cứu)
- Ưu tiên giải pháp có thể giải thích được với hội đồng