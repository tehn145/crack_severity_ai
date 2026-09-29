# ARCHITECTURE.md

## Tổng quan pipeline
Ảnh 2D
  → Phase 1: Detection (có nứt / không nứt) – YOLOv8
  → Nếu có nứt → Phase 2: Severity Classification
       - Lớp A: đặc trưng vết nứt (morphology, density, branching…)
       - Lớp B: ngữ cảnh cấu kiện (single_plane / multi_plane)
  → Output: mức độ nghiêm trọng

## Cấu trúc dữ liệu Phase 1 (đã thống nhất)
data/processed/phase1/
├── primary/      # dữ liệu sạch nhất (bê tông, tường, đường, cầu) → train trước
├── expanded/     # dữ liệu sạch mở rộng
├── hard_cases/   # vân đá + nứt trang trí (dùng test độ cứng / fine-tune sau)
└── full/         # gộp tất cả

Mỗi subset đều có:
  images/{train,val,test}
  labels/{train,val,test}   # YOLO format

## Trạng thái hiện tại (cập nhật khi có thay đổi)
- Đã gộp nhiều nguồn → khoảng 66k ảnh (chưa sạch)
- primary đã build được ~9.2k ảnh (image-label khớp)
- Đang rà soát / làm sạch tiếp
- Phase 2: mới ở giai đoạn thiết kế hướng tiếp cận

## Quyết định kỹ thuật đã chốt
- Phase 1: YOLOv8 (Ultralytics)
- Train chính trên Kaggle, mang best.pt về weights/phase1/
- Không hard-code số mức độ nghiêm trọng cho đến khi chốt tiêu chuẩn
- Lớp B (single/multi plane) chỉ là tín hiệu hỗ trợ, không phải tiêu chí duy nhất