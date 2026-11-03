# ARCHITECTURE.md — Kiến trúc Hệ thống crack_severity_ai

## Tổng quan pipeline đa giai đoạn (Multi-Stage Defect Cascade)

```
Ảnh 2D (Chụp cấu kiện dầm/cột/sàn/tường)
  │
  ├─► Multi-Defect Detection & Segmentation (YOLOv8-seg)
  │     ├── Nhánh Vết nứt (Crack)
  │     ├── Nhánh Bong tróc (Spalling)
  │     └── Nhánh Cốt thép lộ (Exposed Rebar)
  │
  ├─► Phase 2: Crack Severity Classification (Đánh giá Vết nứt)
  │     ├── Lớp A: Đặc trưng hình học (chiều dài, width_max, branching, diện tích, contrast_ratio)
  │     ├── Lớp B: Ngữ cảnh cấu kiện (single_plane / multi_plane, xuyên cấu kiện)
  │     └── Output: Mức độ nghiêm trọng nứt L0–L3 (ACI 224R-01 / TCVN 9381:2012)
  │
  └─► Phase 3: Spalling & Exposed Rebar Assessment (Đánh giá Bong tróc & Lộ cốt thép)
        ├── Đặc trưng Spalling: Diện tích vỡ ($S_{\text{spall}}$), chiều sâu tương đối, tỷ lệ diện tích
        ├── Đặc trưng Rebar: Số lượng thanh lộ, chiều dài lộ ($L_{\text{rebar}}$), mức độ rỉ sét
        ├── Đánh giá an toàn tái khởi công: Thang SP0–SP3 (TCVN 9381:2012, ACI 562-19)
        └── Output: Kết luận an toàn cho phép tiếp tục xây dựng hay đình chỉ gia cố kết cấu
```

---

## Cấu trúc dữ liệu huấn luyện

### 1. Dữ liệu Phase 1 (Crack Detection)
`data/processed/phase1/`
* `primary/`: Dữ liệu sạch chuẩn (bê tông, tường, đường, sàn cầu) $\to$ huấn luyện chính.
* `expanded/`: Dữ liệu mở rộng đa bề mặt (mặt đường, gạch masonry, đá).
* `hard_cases/`: Vân đá + họa tiết dễ gây báo giả (dùng đo độ cứng OOD / fine-tune).
* `full/`: Gộp tất cả các nguồn.

Mỗi tập gồm: `images/{train,val,test}` và `labels/{train,val,test}` (định dạng YOLO polygon class 0 = crack).

### 2. Dữ liệu Phase 3 (Spalling & Exposed Rebar)
`data/processed/phase3/` (chuẩn bị tích hợp từ CrSpEE, SegCODEBRIM, CUHK-USR, Roboflow):
* `class 0`: crack
* `class 1`: spalling
* `class 2`: exposed_rebar

---

## Trạng thái hiện tại của các Phase

### Phase 1 — Vết nứt (Đang active)
* **Dữ liệu**: primary v2 gồm 17.594 ảnh (train 14.619 / val 1.484 / test 1.491) + 4.048 ảnh âm train.
* **Mô hình active**: YOLOv8s-seg @640 (`weights/phase1/best.pt`), FP trên ảnh âm chỉ 2.2%, F1 instance 0.655, Dice DeepCrack 0.819.
* **Đang chuẩn bị v3/v4**: Tiled training cho vết mảnh (Volker/Rissbilder) + gộp hard-negative vân đá và đưa lại nhóm mặt đường.

### Phase 2 — Phân loại mức độ vết nứt (ĐÃ HOÀN THIỆN + KIỂM CHỨNG)
* **Lớp A**: `length`, `width_mean`, `width_max` (Distance Transform chính xác hiệu chỉnh nửa pixel, sai số $\le 1\text{px}$), `angle` (moments, $0^\circ$ ngang), `branching` (skeleton Zhang-Suen), `contrast_ratio` (proxy cho độ sâu vết nứt).
* **Kiểm chứng đo lường**: `scripts/validate_measurements.py` $\to$ ĐẠT NGHIỆM THU.
* **Lớp B**: Heuristic `multi_plane` + cờ `through_member` (kỹ sư đánh dấu UI, ép L3).
* **Quy tắc phân loại**: Bề rộng MAX $\times$ GSD theo thang 4 mức ACI 224R-01 / TCVN 9381:2012; điều chỉnh đa yếu tố (chiều dài $\ge 300\text{mm}$, độ đậm $\ge 30\%$).

### Phase 3 — Bong tróc & Lộ cốt thép cho công trình tái khởi công (ĐANG THIẾT KẾ & TÍCH HỢP)
* **Mục đích**: Chuyên dụng đánh giá an toàn cho các **tòa nhà đình trệ, công trình dở dang qua nhiều năm** trước khi tiếp tục thi công.
* **Thang 4 cấp SP0–SP3**:
  * `SP0`: Bong tróc nông lớp vữa ngoài $\to$ An toàn, thi công tiếp.
  * `SP1`: Vỡ bê tông bảo vệ ($10\text{--}25\text{mm}$), chưa lộ thép $\to$ Trám vữa không co ngót.
  * `SP2`: Lộ cốt thép kết cấu, gỉ bề mặt $\to$ Xử lý đánh gỉ + bù bê tông trước khi tăng tải.
  * `SP3`: Lộ cốt thép diện rộng, gỉ rộp giảm tiết diện $>10\%$, bê tông lõi vỡ dập $\to$ **CẤM TÁI KHỞI CÔNG**, bắt buộc chống đỡ tạm và gia cố kết cấu.
* **Chi tiết kỹ thuật**: Xem đầy đủ tại [docs/standards/SPALLING_PHASE.md](file:///d:/crack_severity_ai/docs/standards/SPALLING_PHASE.md).

---

## Serving & Demo System (v3.1)
* **Backend**: FastAPI (`app/main.py`) + SQLite lưu trữ hồ sơ kiểm định (`inspections`, `detections`).
* **Frontend**: SPA giao diện doanh nghiệp 6 phân hệ (Dashboard, Wizard kiểm định 4 bước, Hồ sơ & Duyệt, Phase 2, Model benchmark, Thiết lập).
* **Quy trình doanh nghiệp**: Dự án $\to$ Kiểm định $\to$ Chờ duyệt $\to$ Đã duyệt (phân vai Kỹ sư / Quản lý) $\to$ Xuất báo cáo in PDF chuẩn có 2 khung chữ ký.
* **Công cụ tương tác**: Đo GSD 2 điểm trực tiếp trên ảnh; API tái phân loại không cần inference lại (`POST /api/severity`).
* **DevOps**: Docker, docker-compose, CI/CD GitHub Actions deploy tự động lên Hugging Face Spaces (CPU).
* **Kiểm thử tự động**: 28/28 pytest unit test + 7/7 bước end-to-end pass.

---

## Quyết định kỹ thuật đã chốt
1. **Kiến trúc cốt lõi**: Mô hình học sâu thị giác 2D (YOLOv8-seg), không lệ thuộc sensor 3D hay ảnh nhiệt tốn kém.
2. **Nguyên tắc an toàn kết cấu**: Mọi thang phân cấp (Vết nứt L0–L3, Bong tróc SP0–SP3) phải có chỗ dựa tiêu chuẩn kỹ thuật (ACI 224R, TCVN 9381, ACI 562).
3. **Phân cấp độc lập**: Nhánh vết nứt và nhánh bong tróc có tiêu chí đánh giá riêng, sau đó tổng hợp thành Chỉ số An toàn Cấu kiện (Structural Safety Score) phục vụ nghiệm thu tái khởi công.
