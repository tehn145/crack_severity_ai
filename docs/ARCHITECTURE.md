# ARCHITECTURE.md — Kiến trúc Hệ thống crack_severity_ai

## Tổng quan pipeline 3 Phase chuyên biệt (Multi-Expert Cascaded Architecture)

```
Ảnh 2D Hiện Trường / Quét Toàn Thư Mục Tầng / Di Sản (Tháp Bà Ponagar)
  │
  ├──► [TẦNG 1: DUAL SPECIALIST INFERENCE — CHẠY SONG SONG ĐỘC LẬP]
  │     │
  │     ├── Nhánh Phase 1: Chuyên gia Vết nứt (Crack Specialist)
  │     │     ├── Phase 1.A: Bề mặt dễ (Tường, Đường, Bê tông phẳng) -> Target mAP50 >93%
  │     │     │     └── Tiền xử lý: Bilateral Filter (d=5, σ=50) + Adaptive CLAHE (clip=2.5) + 12% Ảnh âm nền
  │     │     └── Phase 1.B: Bề mặt khó (Di sản gạch cổ, Gạch men bóng, Mạch vữa xây)
  │     │           └── Tiền xử lý: Multi-Scale Retinex khử bóng phản quang + Gabor filter
  │     │
  │     └── Nhánh Phase 2: Chuyên gia Kết cấu Phá hủy (Spalling & Rebar Specialist)
  │           ├── Triệt tiêu 100% nhãn 'crack' (không xung đột dữ liệu với Phase 1)
  │           ├── Class 0: spalling (Bong tróc bê tông thể tích)
  │           ├── Class 1: exposed_rebar (Lộ cốt thép chịu lực)
  │           └── Class 2: corrosion (Gỉ sét ăn mòn kim loại)
  │                 └── Tiền xử lý: CIE-Lab khuếch đại màu oxit sắt Fe2O3 đỏ nâu -> Target mAP50 >90%
  │
  ├──► [TẦNG 2: AI NHẬN DIỆN & BO KHUNG CẤU KIỆN (COMPONENT RECOGNITION)]
  │     ├── Tự động vẽ Bounding Box / Mask phân định cấu kiện:
  │     │     Cột (3.0x), Nút dầm-cột (3.5x), Dầm (2.5x), Bản sàn/Trần (1.5x), Tường (1.0x), Cổ cột móng (4.0x)
  │     └── Spatial Containment: Ánh xạ vết nứt / mảng vỡ thuộc về cấu kiện nào (IoU / Point-in-Box)
  │
  └──► [TẦNG 3: PHASE 3 SHM ENGINE — GIÁM ĐỊNH TOÀN DIỆN CÔNG TRÌNH]
        ├── Khử chồng lấn không gian (ORB Homography Matching) giữa các ảnh kề nhau khi quét cả tầng
        ├── Tính tỷ lệ diện tích hư hỏng thực tế so với toàn bộ không gian hình học
        ├── Bảng phân tích đa chiều (Sorting & Filtering):
        │     - Lọc theo từng cấu kiện (Cột, Dầm, Sàn, Tường)
        │     - Sắp xếp số vết nứt / spalling giảm dần (VD: Cột C12 có 7 vết nứt -> Ưu tiên xử lý)
        ├── Chỉ số nguy cơ sụp đổ Structural Collapse Index (SCI 0 - 100%): 4 cấp độ cảnh báo
        └── Báo cáo kỹ thuật in PDF chuẩn quy trình thẩm định PE Sign-off
```

---

## Cấu trúc dữ liệu huấn luyện

### 1. Dữ liệu Phase 1 (Crack Specialist)
`data/processed/phase1/`
* `v5_phase1_a_easy/`: Dữ liệu sạch bề mặt dễ (Tường, Đường nhựa, Bê tông phẳng tương phản cao) được tiền xử lý Bilateral + CLAHE + 12% ảnh âm nền (từ METU Negative và SDNET UD). Nhãn YOLO polygon 1 class: `0: crack`.
* `v5_phase1_b_hard/`: Dữ liệu bề mặt khó (Di sản gạch cổ, Gạch men bóng, Mạch vữa xây).
* `primary/`: Baseline 16k ảnh chuẩn (tham chiếu).
* `hard_cases/`: Tập kiểm thử vân đá OOD đo độ cứng báo giả.

### 2. Dữ liệu Phase 2 (Spalling & Rebar Specialist)
`data/processed/phase2/`
* `v2_clean_multidefect/`: Dữ liệu 3 lớp khuyết tật thể tích độc lập (không có nhãn `crack`):
  * `class 0`: `spalling` (Bong tróc bê tông)
  * `class 1`: `exposed_rebar` (Lộ cốt thép chịu lực)
  * `class 2`: `corrosion` (Ăn mòn gỉ sét)
  * Kèm 12% ảnh âm (bê tông lành lặn không bong tróc từ `spall nonAccepted`).

---

## Chi tiết kỹ thuật các Phase

### Phase 1.A — Vết nứt Bề mặt Dễ (Đột phá >93% mAP50)
* **Backbone**: `yolov8m-seg.pt` (25.9M params) @ `imgsz=1024`.
* **Tiền xử lý**: Bilateral Filter ($d=5, \sigma=50$) khử nhiễu hạt cát + Adaptive CLAHE ($clip=2.5, tile=8\times 8$) làm nổi vết nứt.
* **Quy mô sạch**: ~28,700 ảnh (bao gồm 3,500 ảnh âm chống ảo giác).

### Phase 2 — Bong tróc & Cốt thép (Đột phá >90% mAP50)
* **Backbone**: `yolov8m-seg.pt` @ `imgsz=1024`.
* **Tiền xử lý**: Không gian màu CIE-Lab khuếch đại kênh $a^*$ và $b^*$ cho gỉ sét đỏ nâu, triệt tiêu bóng tối dưới hốc vỡ bằng Retinex.
* **Quy mô sạch**: ~12,700 ảnh sạch đa khuyết tật (Rebar Exposure, RC Structure, HRCDS, spallSubImage).

### Phase 3 — Hệ thống Giám định Kết cấu (SHM Engine)
* **Khảo sát phân cấp**: Hỗ trợ quét theo Tầng (Tầng 1..N) hoặc Khối di sản kiến trúc (Tháp Bà Ponagar).
* **Khử trùng lặp ORB**: Tự động tính ma trận Homography giữa các góc chụp kề nhau, trừ hao diện tích chồng lấn trước khi tính phần trăm hư hỏng toàn không gian.
* **AI Bo khung cấu kiện**: Tự động nhận diện biên giới hạn của Cột, Dầm, Sàn, Nút khung, Móng và tính hệ số rủi ro chịu lực $W_c \in [1.0, 4.0]$.
* **Bộ lọc Sort/Filter**: Lọc theo cấu kiện và sắp xếp số lượng vết nứt/spalling giảm dần.
* **SCI Index**: Điểm số nguy cơ sụp đổ từ 0 - 100% kèm khuyến nghị kỹ thuật (bơm Epoxy, dán sợi carbon CFRP, bọc thép hình, hoặc sơ tán khẩn cấp).

---

## Serving & Web App Demo
* **Backend**: FastAPI (`app/main.py`), SQLite lưu trữ hồ sơ, module AI phân loại cấu kiện (`app/component_classifier.py`), router Phase 3 (`app/phase3_endpoints.py`).
* **Frontend**: SPA giao diện doanh nghiệp (`app/static/index.html`) tích hợp trực tiếp bảng điều khiển **Phase 3 SHM Console** (`app/static/phase3_demo.html`).
* **Quy trình thẩm định**: Tải ảnh đơn hoặc thư mục quét cả tầng $\to$ AI tự động nhận diện cấu kiện $\to$ Khử trùng lặp $\to$ Tính điểm SCI $\to$ Bảng phân tích lọc sort $\to$ Xuất báo cáo PE sign-off in PDF.
