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
- Đã quét 5 bộ có mask/txt (~21k file): 3DCrack_v1, crack_segmentation_dataset, DeepCrack, Roads_and_Bridges, Ultralytics_CrackSeg
- primary đã build chuẩn hóa: 18.790 ảnh (train 14.972 / val 1.921 / test 1.897), nhãn YOLO polygon class 0 = crack, khớp image-label 100%, khử trùng md5
- Ảnh âm (background, label rỗng): 1.353 ảnh tách riêng ở data/processed/phase1/negatives/
- Bundle Kaggle: outputs/kaggle/phase1_primary.zip (primary + ảnh âm gộp split + data.yaml) — dùng scripts/package_kaggle_phase1.py để tạo lại
- Phase 2: mới ở giai đoạn thiết kế hướng tiếp cận

## Quyết định kỹ thuật đã chốt
- Phase 1: YOLOv8 (Ultralytics)
- Train chính trên Kaggle, mang best.pt về weights/phase1/
- Không hard-code số mức độ nghiêm trọng cho đến khi chốt tiêu chuẩn
- Lớp B (single/multi plane) chỉ là tín hiệu hỗ trợ, không phải tiêu chí duy nhất