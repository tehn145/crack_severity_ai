# ROADMAP.md — Lộ trình Phát triển crack_severity_ai

## 1. Đã hoàn thành (Baseline & Nghiệm thu nền tảng)
* **Phase 1.1 Baseline Core**: 20,129 ảnh, 120 epochs $\to$ Box mAP50 = 73.9%, Mask mAP50 = 57.6%.
* **Phase 1.2 Multi-Surface Expansion**: 22,358 ảnh (bổ sung gạch men, gạch cổ, pháo đài), 60 epochs $\to$ Box mAP50 = 75.2%, Mask mAP50 = 61.4% (tăng +3.8%), tốc độ 4.6ms (~217 FPS).
* **Phase 2 Multi-Defect V1**: 6,256 ảnh, 100 epochs $\to$ Box mAP50 = 64.6%, Rebar đạt 72.6%, Spalling đạt 70.0%.
* **Phase 3 SHM Engine Prototype**:
  * Dual model inference chạy đồng thời Phase 1.2 và Phase 2.
  * Spatial Overlap Deduplication (ORB Feature Matching + Homography).
  * Structural Risk Multiplier theo vai trò chịu lực ($W_c \in [1.0, 3.5]$).
  * Thuật toán chỉ số nguy cơ sụp đổ Structural Collapse Index (SCI 0 - 100%).
  * AI Structural Component Classifier tự động nhận diện cấu kiện (`app/component_classifier.py`).
  * Tích hợp Web App giao diện Phase 3 Console (`/phase3`) và kiểm thử tự động 21/21 tests pass 100%.

---

## 2. Đang triển khai (Kế hoạch Đột phá Kỷ lục SOTA >90%)

### 🎯 Bước 1: Xây dựng Bộ Dữ Liệu Tinh Khiết & Tiền Xử Lý
1. **Gói dữ liệu Phase 1.A (Vết nứt bề mặt dễ - Tường, Đường, Bê tông phẳng)**:
   - Quy mô: **~28,700 ảnh sạch 100%** (25,200 ảnh nứt có mask + 3,500 ảnh âm chống báo giả từ METU Negative & SDNET UD).
   - Tiền xử lý cao cấp: Bilateral Filtering ($d=5, \sigma=50$) làm mịn bề mặt + Adaptive CLAHE ($clip=2.5, tile=8\times 8$) khuếch đại rãnh nứt.
   - Script đóng gói: `scripts/data/build_phase1_a_easy_surfaces.py`.
2. **Gói dữ liệu Phase 2 Mới (Bong tróc & Cốt thép - Độc lập hoàn toàn)**:
   - Quy mô: **~12,700 ảnh sạch 100%** (Rebar Exposure, RC Structure, HRCDS, spallSubImage + 1,500 ảnh âm).
   - **Triệt tiêu 100% nhãn `crack`** để tránh xung đột định dạng với Phase 1.
   - 3 Lớp khuyết tật: `0: spalling`, `1: exposed_rebar`, `2: corrosion`.
   - Tiền xử lý: Chuyển đổi không gian màu CIE-Lab khuếch đại màu gỉ sắt $Fe_2O_3$ đỏ nâu + Retinex triệt tiêu bóng tối dưới hốc vỡ.
   - Script đóng gói: `scripts/data/build_phase2_clean_multidefect.py`.

### 🎯 Bước 2: Huấn Luyện Song Song Trên Kaggle (Target Vượt SOTA)
- **Phase 1.A (Easy Crack)**:
  - Model: `yolov8m-seg.pt` (25.9M params), `imgsz=1024`, `batch=8`, `epochs=80`.
  - Augmentation: `copy_paste=0.4` (CrackPaste), `mosaic=1.0`.
  - **Mục tiêu**: Box mAP50 **≥ 93.5%** (vượt kỷ lục thế giới hiện tại 92.4% của YOLOv8-CA).
- **Phase 2 (Spalling & Rebar)**:
  - Model: `yolov8m-seg.pt`, `imgsz=1024`, `batch=8`, `epochs=100`.
  - **Mục tiêu**: Box mAP50 **≥ 90.5%** (vượt kỷ lục thế giới hiện tại 89.5% của YOLOv8-LSKA).

---

## 3. Kế hoạch tiếp theo — Hoàn thiện Toàn Diện Phase 3 SHM

* **Kiểm định Công trình Phân Tầng & Di Sản Kiến Trúc**:
  * Hỗ trợ quét toàn bộ một tầng (Tầng 1, Tầng 2...) hoặc công trình di sản (như Tháp Bà Ponagar, Cố đô Huế).
  * Khử trùng lặp thị giác ORB Homography để tính tỷ lệ diện tích hư hỏng thực tế so với toàn bộ không gian hình học.
* **AI Bo Khung Cấu Kiện & Ánh Xạ Khuyết Tật (Spatial Containment)**:
  * AI tự động vẽ Bounding Box bao quanh Cột, Dầm, Sàn, Nút dầm-cột, Móng.
  * Tự động xác định vết nứt/spalling nằm trên cấu kiện nào để nhân hệ số nguy cơ chịu lực.
* **Bảng Thống Kê & Lọc Sắp Xếp Đa Tiêu Chí (Sort & Filtering Dashboard)**:
  * Lọc theo cấu kiện: Chỉ xem Cột, Dầm, Sàn, Tường.
  * Sắp xếp số vết nứt / mảng spalling giảm dần (ví dụ: *Cột C12 có 7 vết nứt $\to$ Đưa lên đầu danh sách để kỹ sư ưu tiên gia cường*).
  * Phân cấp mức độ nguy cơ gãy đổ theo thang SCI (0 - 100%) và xuất Báo cáo Thẩm định PE Sign-off in PDF chuẩn quy trình.
