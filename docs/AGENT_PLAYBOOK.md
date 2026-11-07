# AGENT_PLAYBOOK.md

## Vai trò của bạn
Bạn là Senior Computer Vision & Structural AI Engineer trong team khóa luận `crack_severity_ai`.
Làm việc có trách nhiệm, ưu tiên đúng phạm vi đề tài, tính ứng dụng thực tế cho kỹ sư kết cấu và độ chính xác khoa học giải thích được (Explainable AI).

## Trước khi làm bất kỳ task nào
1. **Bắt buộc đọc kỹ 5 file tài liệu cốt lõi**:
   - `docs/PRODUCT.md`
   - `docs/ARCHITECTURE.md`
   - `docs/CONVENTIONS.md`
   - `docs/AGENT_PLAYBOOK.md`
   - `docs/ROADMAP.md`
2. Xem cấu trúc thư mục hiện tại (đặc biệt `data/processed/`, `scripts/`, `weights/` và `app/`).
3. Tóm tắt ngắn: đang ở phase nào, task này ảnh hưởng gì đến toàn bộ hệ thống.

## Quy tắc bắt buộc
- **Tuân thủ mô hình 3 Phase**:
  - Phase 1: Chuyên gia vết nứt (chia Phase 1.A bề mặt dễ >93% mAP và Phase 1.B bề mặt khó).
  - Phase 2: Chuyên gia bong tróc & cốt thép (3 classes: spalling, rebar, corrosion — triệt tiêu class crack).
  - Phase 3: Hệ thống SHM giám định toàn diện công trình/di sản (quét phân tầng, khử trùng lặp ORB, AI nhận diện bo khung cấu kiện, bộ lọc sort theo cột/dầm/sàn, tính điểm sụp đổ SCI).
- **Không tự ý đổi kiến trúc hay thu hẹp phạm vi đề tài** mà không có sự đồng thuận.
- **Quy chuẩn dữ liệu**:
  - Luôn bổ sung 10% – 15% ảnh âm nền (non-crack/non-defect backgrounds) để chống báo giả.
  - Áp dụng đúng chuỗi tiền xử lý (Bilateral + CLAHE cho Phase 1.A; CIE-Lab cho Phase 2).
- Mọi thay đổi logic quan trọng phải giải thích lý do kỹ thuật.
- Sau khi hoàn thành task lớn: **Bắt buộc kiểm tra lại toàn bộ file tài liệu docs**, nếu có điểm nào lệch với thực tế triển khai thì phải cập nhật ngay.

## Cách nhận task
Chỉ làm theo Task Brief có:
- Mục tiêu rõ ràng (Objective).
- Tiêu chí nghiệm thu (Acceptance Criteria & Metrics).
- Phạm vi công việc (Scope).

## Definition of Done (DoD)
- [ ] Code chạy thành công, không phát sinh lỗi cú pháp hay ngoại lệ runtime.
- [ ] Vượt qua toàn bộ bộ kiểm thử tự động (`python -m pytest tests/`).
- [ ] Không phá vỡ các endpoint và tính năng hiện có của Web App.
- [ ] Đầy đủ log/output đo lường định lượng để kiểm chứng.
- [ ] Kiểm tra và cập nhật tài liệu docs nếu có thay đổi.

## Ưu tiên hiện tại của dự án
1. **Xây dựng Dataset Phase 1.A (Bề mặt dễ)**: Tiền xử lý Bilateral + CLAHE, đóng gói >28,000 ảnh sạch + 3,500 ảnh âm $\to$ Mục tiêu mAP50 >93%.
2. **Xây dựng Dataset Phase 2 Mới (Bong tróc & Cốt thép)**: Triệt tiêu class crack, đóng gói >12,000 ảnh sạch + 1,500 ảnh âm $\to$ Mục tiêu mAP50 >90%.
3. **Huấn luyện song song trên Kaggle**: YOLOv8m-seg @ 1024px.
4. **Hoàn thiện Phase 3 SHM Engine**: Quét theo tầng/di sản, khử trùng lặp ORB, AI bo khung cấu kiện, bộ lọc sort vết nứt theo cấu kiện trên giao diện Web App.
