# ROADMAP.md — Lộ trình Phát triển crack_severity_ai

## 1. Đã xong (Giai đoạn Phase 1 & Hệ thống Serving)
* **Thu thập & Chuẩn hóa dữ liệu Phase 1**:
  * Chuẩn hóa toàn bộ nguồn (mask + txt) về YOLO polygon thuần (class 0 = crack).
  * Xây dựng tập `primary v2` gồm 17.594 ảnh + 4.048 ảnh âm nền, chia split 80/10/10 bằng hash deterministic.
  * Tách riêng 303–306 ảnh vân đá OOD (`hard_cases`) phục vụ đo lường báo giả chuyên biệt.
* **Huấn luyện & Đánh giá Phase 1 v1**:
  * YOLOv8s-seg @640, Kaggle T4 $\to$ `weights/phase1/best.pt`.
  * Đo kiểm trên test set: mức ảnh đạt 0.999, FP trên ảnh âm chỉ 2.2%, F1 instance 0.655.
  * So sánh với SOTA (arXiv:2508.10256): DeepCrack Dice đạt 0.819 (sát ResUNet 0.833).
* **Nền tảng phục vụ (Serving & DevOps)**:
  * Backend FastAPI + SQLite + SPA UI 6 phân hệ (Dashboard, Wizard kiểm định 4 bước, Hồ sơ, Phase 2, Model, Thiết lập).
  * Dockerfile + docker-compose, CI/CD GitHub Actions deploy tự động lên Hugging Face Spaces.
  * Bộ kiểm thử: 28/28 pytest unit tests + 7/7 bước E2E tests pass.

## 2. Đã xong (Giai đoạn Phase 2 — Đánh giá mức độ vết nứt)
* **Thang 4 mức L0–L3** chốt theo ACI 224R-01 và TCVN 9381:2012 ([docs/standards/severity_definition.md](file:///d:/crack_severity_ai/docs/standards/severity_definition.md)).
* **Lớp A đầy đủ**: Chiều dài, bề rộng trung bình, **bề rộng lớn nhất (`width_max`)** bằng Distance Transform chính xác hiệu chỉnh nửa pixel, diện tích, góc trục chính (moments), phân nhánh (skeleton Zhang-Suen), độ tương phản `contrast_ratio` (proxy cho độ sâu).
* **Kiểm chứng đo lường** (`scripts/validate_measurements.py`): Sai số `width_max` $\le 1\text{px}$, chiều dài $0\text{px}$, góc $0^\circ$, nhận diện nhánh chính xác $\to$ **ĐẠT NGHIỆM THU**.
* **Đa yếu tố**: Giải quyết trường hợp vết nứt dài nhưng mảnh hoặc vết nứt đậm sâu (tự động cộng mức, chặn tại L3, vết xuyên cấu kiện ép L3).
* **Tích hợp trọn vòng đời**: Công cụ đo GSD 2 điểm trực tiếp trên ảnh; API tái phân loại không cần suy luận lại (`POST /api/severity`).

## 3. Đang triển khai (Hiện tại)
* **Đa bề mặt & Đưa lại nhóm mặt đường**:
  * Đưa lại các bộ mặt đường (Crack500, 3DCrack, GAPs, CFD, CrackTree, RDD2022) và mở rộng tường sơn, gạch masonry, đá, kính, thép, gỗ để nâng tổng kho dữ liệu lên **60.000+ ảnh**.
* **Xử lý vết mảnh & Vân đá cho Phase 1 v3**:
  * Tiled training $640\text{px}$ ở độ phân giải gốc cho Volker / Rissbilder kết hợp SAHI inference + WBF.
  * Đưa hard-negative vân đá vào tập train để giảm FP xuống $<10\%$.
  * Huấn luyện v3 fine-tune từ v1 ở độ phân giải $960\text{px}$.
* **Chuẩn bị bài báo khoa học (CrackSieve)**: Hoàn thiện bảng đối chứng SOTA với framework GT-CrackSeg của Georgia Tech.

## 4. Kế hoạch tiếp theo — Khởi động Phase 3: Spalling & Lộ kết cấu (Tái khởi công công trình)
* **Bối cảnh ứng dụng**: Kiểm định đánh giá an toàn chịu lực cho các **tòa nhà bị đình trệ / đắp chiếu nhiều năm** trước khi tái khởi công xây dựng tiếp (theo Nghị định 06/2021/NĐ-CP, TCVN 9381:2012, ACI 562-19).
* **Nhiệm vụ trọng tâm**:
  1. **Dữ liệu**: Tích hợp các bộ `CrSpEE`, `SegCODEBRIM`, `CUHK-USR Defect`, `UAV Façade` $\to$ Gán nhãn 3 lớp: `crack`, `spalling`, `exposed_rebar`.
  2. **Mô hình**: Huấn luyện YOLOv8-seg đa khuyết tật (Multi-class defect segmentation).
  3. **Module định lượng & Thang 4 cấp SP0–SP3**:
     * Đo diện tích bong tróc ($S_{\text{spall}}$), chiều sâu tương đối, tỷ lệ diện tích vỡ trên cấu kiện dầm/cột.
     * Đo chiều dài và diện tích thanh thép kết cấu bị lộ ($L_{\text{rebar}}$), nhận diện mức độ gỉ sét.
     * Xếp loại từ `SP0` (an toàn thi công tiếp) đến `SP3` (cấm tái khởi công, nguy cơ mất an toàn chịu lực, bắt buộc chống đỡ tạm và gia cố).
  4. **Tích hợp Web App**: Bổ sung phân hệ "Kiểm định công trình tái khởi công" và xuất Báo cáo An toàn Kết cấu tổng hợp in PDF.
  5. Xem tài liệu thiết kế chi tiết tại [docs/standards/SPALLING_PHASE.md](file:///d:/crack_severity_ai/docs/standards/SPALLING_PHASE.md).
