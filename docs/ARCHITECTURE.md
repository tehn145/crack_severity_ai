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
- Bundle Kaggle: outputs/kaggle/phase1_primary_20261022.zip (primary + ảnh âm gộp split + data.yaml) — dùng scripts/package_kaggle_phase1.py để tạo lại
- Phase 2: mới ở giai đoạn thiết kế hướng tiếp cận

## Serving / demo (v3.0 enterprise — 2026-10-25)
- app/ — FastAPI + SPA 5 màn hình (Dashboard / Wizard kiểm tra / Hồ sơ / Phân tích / Thiết lập)
- **Quy trình công ty**: quản lý dự án (projects) → wizard 4 bước → hồ sơ có luồng
  Draft → Chờ duyệt → Đã duyệt (phân vai demo Kỹ sư/Quản lý) → báo cáo in có badge trạng
  thái + 2 ô chữ ký (kỹ sư / người duyệt)
- Dashboard: KPI cards + Chart.js (severity doughnut, cấu kiện bar, trend line) + bảng gần đây
- View Phân tích: benchmark v1, so sánh SOTA (arXiv:2508.10256) với progress bar, cấu hình model/dữ liệu, lộ trình v1→v3
- API: /api/predict (severity khi có GSD), /api/inspections (+detail, +status approve),
  /api/projects, /api/dashboard, /api/model-info, /api/stats, export CSV, report HTML in-PDF
- Phase 2 rule-based (thang ĐỀ XUẤT chờ chốt): app/severity.py — 4 mức ACI 224R-01/TCVN 9381:2012
- Overlay canvas tương tác (bấm vết ↔ tô sáng, bật/tắt mask/khung, tải PNG), paste clipboard, ảnh mẫu
- Triển khai: Dockerfile + docker-compose, CI/CD GitHub Actions → HF Spaces (docs/DEVOPS.md)
- Test: pytest 14/14 + scripts/e2e_app_v3.py (predict→save→approve→report E2E)

## Quyết định kỹ thuật đã chốt
- Phase 1: YOLOv8 (Ultralytics)
- Train chính trên Kaggle, mang best.pt về weights/phase1/
- Không hard-code số mức độ nghiêm trọng cho đến khi chốt tiêu chuẩn
- Lớp B (single/multi plane) chỉ là tín hiệu hỗ trợ, không phải tiêu chí duy nhất