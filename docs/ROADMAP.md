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

### 🎯 Bước 1: Xây dựng Bộ Dữ Liệu Tinh Khiết & Tiền Xử Lý Quang Học (ĐÃ HOÀN TẤT 100%)
1. **Gói dữ liệu Phase 1.A (Vết nứt bề mặt dễ — Chuẩn Tinh Khiết 100%)**:
   - Quy mô thực tế: **19,133 ảnh sạch 100% có ground-truth mask/polygon** (Train: 15,390 | Val: 1,879 | Test: 1,864).
   - Nguồn dữ liệu thuần bê tông & mặt đường phẳng: `crack_segmentation_dataset` (9,633 ảnh), `Ultralytics_CrackSeg` (4,028 ảnh), `Roads_and_Bridges` (2,741 ảnh), `3DCrack_v1` (1,240 ảnh), `DamSegment Easy/Medium` (997 ảnh).
   - **Loại bỏ 100% rác**: Không có ảnh từ `BFDD` (loại bỏ vì lẫn bong tróc vôi vữa/sơn bề mặt tòa nhà), không có `detr` (loại bỏ hoàn toàn tường gạch, rêu mốc, clipart).
   - Khống chế đúng **500 ảnh âm sạch (tỷ lệ chuẩn 2.61%)** từ METU Negative để chống báo động giả.
   - **Tiền xử lý quang học 4 bước**: Bilateral Filter ($d=5, \sigma=50$) làm mịn cát bụi + Chuyển CIE-LAB + Adaptive CLAHE ($clip=2.5, tile=8\times 8$) trên kênh L khuếch đại rãnh nứt vi mô chìm.
   - **Chuẩn xuất kép (Dual-Export Format — 57,401 files)**:
     - Chuẩn 1: YOLO Polygon `.txt` (`labels/`) $\to$ Huấn luyện **YOLOv8-seg, YOLOv11-seg**.
     - Chuẩn 2: Binary Mask `.png` (`masks/`) $\to$ Huấn luyện **SegFormer, Mask2Former (Hugging Face)**.
   - Đóng gói hoàn tất: `outputs/kaggle/phase1_a_easy_surfaces.zip` (**1,632.94 MB**).
   - Script Notebook Kaggle YOLOv11: `scripts/training/kaggle_phase1_a_yolo11_notebook.py`.
   - Script Notebook Kaggle SegFormer: `scripts/training/kaggle_phase1_a_segformer_notebook.py`.
2. **Gói dữ liệu Phase 2 Mới (Bong tróc & Cốt thép - Độc lập hoàn toàn)**:
   - Quy mô thực tế: **4,457 ảnh sạch 100% polygon segmentation** (Train: 3,566 | Val: 435 | Test: 456).
   - **Triệt tiêu 100% nhãn `crack`** để tránh xung đột với Phase 1.
   - 3 Lớp khuyết tật: `0: spalling` (2,214 instances), `1: exposed_rebar` (4,097 instances), `2: corrosion` (1,382 instances).
   - Tích hợp **700 ảnh âm nền bê tông sạch (15.7%)** với nhãn rỗng.
   - Tiền xử lý quang học: Mild Bilateral ($d=3, \sigma=20$) giữ nguyên góc cạnh bong tróc + CLAHE + HSV Saturation boost x1.15 làm nổi bật gỉ sét.
   - Đóng gói hoàn tất: `outputs/kaggle/phase2_clean_multidefect.zip` (**517.09 MB**).

### 🎯 Bước 2: Giải Đấu Huấn Luyện Đa Mô Hình (Multi-Model Tournament SOTA)
- **Đấu thủ 1 — YOLOv8m-seg (CNN Baseline)**: `imgsz=1024`, 80 epochs $\to$ Target Box mAP50 $\ge$ 93.5%.
- **Đấu thủ 2 — YOLOv11m-seg (SOTA CNN 2024)**: Kiến trúc C3k2 + SPPF attention $\to$ Target Box mAP50 $\ge$ 94.0%.
- **Đấu thủ 3 — NVIDIA SegFormer-B3/B4 (Hugging Face Transformer)**: Hierarchical Multi-scale Self-Attention $\to$ Target mIoU $\ge$ 85%, F1 $\ge$ 94%.
- **Đấu thủ 4 — Meta Mask2Former (Hugging Face Universal Segmentor)**: Swin Transformer + Masked Attention Query.
- **Hợp thể Ensemble (WBF + Soft-Voting)**: Kết hợp thế mạnh của YOLOv11 và SegFormer để xác lập kỷ lục tuyệt đối mAP50 > 95%.

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
