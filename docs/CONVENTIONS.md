# CONVENTIONS.md

## Code
- Python 3.10+
- Ưu tiên code rõ ràng, có type hint đầy đủ
- Mỗi script độc lập phải chạy được trực tiếp từ thư mục gốc dự án (`d:\crack_severity_ai`)
- Sử dụng logging chuẩn hoặc print có cấu trúc rõ ràng

## Quy tắc Dữ liệu & Huấn luyện (Data Conventions)
- **Phase 1.A (Easy Crack)**: Label chuẩn YOLO polygon, 1 class duy nhất: `0: crack`.
- **Phase 2 (Damage)**: Label chuẩn YOLO polygon, 3 classes độc lập:
  - `0: spalling`
  - `1: exposed_rebar`
  - `2: corrosion`
  - **TUYỆT ĐỐI KHÔNG** để nhãn `crack` trong Phase 2 để tránh xung đột định dạng với Phase 1.
- **Tỷ lệ Ảnh Âm Tính (Backgrounds)**: Mọi tập train lớn bắt buộc chèn 10% - 15% ảnh âm (file nhãn `.txt` rỗng) từ `METU Negative`, `SDNET UD` hoặc `spall nonAccepted` để triệt tiêu báo giả.
- **Tiền xử lý ảnh (Preprocessing)**: Mọi bước lọc (Bilateral, CLAHE, Lab, Retinex) phải đồng bộ giữa script build dataset và pipeline inference của App.
- Mọi script xử lý dữ liệu phải có tính tái lặp (deterministic split bằng random seed hoặc hash).

## Đặt tên & Cấu trúc Thư mục
- Scripts:
  - Dữ liệu: `scripts/data/build_phase1_a_easy.py`, `scripts/data/build_phase2_clean.py`
  - Huấn luyện: `scripts/training/kaggle_*.py`
  - Đánh giá: `scripts/evaluation/phase3_shm_engine.py`
- Weights:
  - Phase 1: `weights/phase1/results_phase1_a/best.pt`
  - Phase 2: `weights/phase2/results_phase2_clean/best.pt`
- Báo cáo và biểu đồ: `outputs/reports/` và `outputs/figures/`

## Git
- Không commit file dữ liệu thô (.jpg, .png lớn) vào git repository.
- Không commit file weights `.pt` nặng (>10MB).
