# RESEARCH_ROADMAP.md — Lộ trình dữ liệu, model & hướng bài báo

> Cập nhật 2026-10-29 (v2 — sau khi đọc 22 bài trong sheet `crack_severity_ai reference.xlsx`
> + 23 PDF trong `docs/paper/`). Nguồn nền: Awesome-Crack-Detection, khanhha/crack_segmentation,
> arXiv:2508.10256 (Georgia Tech benchmark).

## 0. Vị trí hiện tại so với 2 bài "mục tiêu"

| Đối tượng | Số của họ | Số của ta (v1 @640) | Nhận định |
|---|---|---|---|
| khanhha/crack_segmentation | Dice tốt nhất **0.603** (UNet-VGG16); tự nhận yếu với nhiễu, rêu, vân gạch | Dice tổng **0.749** · DeepCrack **0.819** | **Đã vượt xa** — đây là nguồn dữ liệu của ta, không phải đối thủ |
| arXiv:2508.10256 (Georgia Tech) | ResUNet: DeepCrack 0.833 · 3DCrack 0.795; CrackSAM/UniMatch v2 cao hơn | 0.819 (98.3%) · 0.708 (89.2%) | Mục tiêu vượt: DeepCrack ≥ 0.84, 3DCrack ≥ 0.80 (v3/v4) |
| Awesome list (30+ dataset, 50+ method) | CrackFormer, Crack-SAM, TOPO-Loss, Syncrack… | — | **Khoảng trống: chưa ai có pipeline triệt tiêu texture cho đá + severity theo chuẩn ACI/TCVN có kiểm chứng ±1px** |

**Khoảng trống nghiên cứu (novelty gap) đã xác nhận:**
1. Không phương án nào trong Awesome list xử lý riêng texture vân đá trước khi detect.
2. Không bài CV crack nào gắn severity với tiêu chuẩn kiểm định (ACI 224R-01/TCVN 9381) kèm
   kiểm chứng sai số đo lường — toàn bộ chỉ dừng ở segmentation.
3. Ít bài có benchmark out-of-domain có kiểm soát (ta có: 303 ảnh vân đá + 4.048 negatives,
   val/test bất biến, mọi số tái lập bằng script).

## 1. VÂN ĐÁ — xử lý RIÊNG trước khi gộp train (ưu tiên 1)

Hiện trạng đã kiểm tra: **primary có 0 ảnh vân đá** (forest/sylvie bị loại đúng chính sách);
306 ảnh vân đá có GT đang nằm ở hard_cases (dùng test). Kế hoạch 4 bước:

### B1. Tiền xử lý chuyên biệt vân đá — 6 kỹ thuật (khác làm mờ thường)
| Kỹ thuật | Nguyên lý vì sao hợp vân đá | Đề xuất tham số |
|---|---|---|
| **Guided filter / Bilateral** (edge-preserving) | Làm phẳng texture hạt đá nhưng GIỮ biên rãnh nứt (làm mờ Gaussian làm mờ luôn nứt) | r=8–15, eps=1e-3 |
| **Frangi/Sato vesselness** (mượn từ y tế — phát hiện mạch) | Vết nứt = cấu trúc "ống" thẳng dài tối màu; vân đá = lượn sóng không tubular → lọc được vân, giữ nứt | multi-scale σ=1..5 |
| **Black-hat morphology** | Chiết xuất cấu trúc tối MẢNH tuyến tính trên nền sáng | kernel 15×45 (từ dài) |
| **DoG bandpass** | Nứt nằm dải tần số trung bình; vân đá tần số thấp → cắt dải | σ1/σ2 = 1:2 |
| **CLAHE** (đã có từ lần 11) | Tăng tương phản cục bộ | clip=2.0, tile 8×8 |
| **Background subtraction** (closing/median kernel lớn − ảnh gốc) | Residual = chỉ còn nứt + nhiễu tần số cao | kernel 51 |

→ Thí nghiệm A/B trên chính 306 ảnh hard-case: mỗi kỹ thuật + tổ hợp, đo FP ảnh @conf 0.45
hiện 24.1% → mục tiêu <10%. Kịch bản thắng sẽ thành **module TSP (Texture-Suppression
Preprocessing)** — ứng viên đóng góp chính của bài báo.

### B2. Sinh dữ liệu tổng hợp kiểu Syncrack trên nền đá
Paste mask vết nứt thật (từ GT bê tông) lên nền vân đá sạch (phần ảnh forest không nứt) →
sinh thêm positive vân đá CÓ nhãn không cần gán tay (nghiên cứu Syncrack trong Awesome list
đã chứng minh hiệu quả). Mục tiêu: +300–500 ảnh tổng hợp.

### B3. Gộp có kiểm soát vào train (không đụng test)
- 150–200 ảnh vân đá **nhãn rỗng (hard-negative)** — giảm FP.
- ~100 ảnh vân đá **có GT** (nứt đá thật) + 300 ảnh tổng hợp B2 — tăng tổng quát.
- **Giữ lại ~150 ảnh vân đá làm test OOD bất biến** (không bao giờ train) để so sánh công bằng v1→v4.

### B4. Chuẩn hóa đánh giá
Mọi lần train ghi lại: FP vân đá @0.45, F1 test, Dice 3DCrack — 3 chỉ số cố định này là
"bảng vàng" tiến bộ (slide/báo cáo dùng chung).

## 2. VOLKER + RISSBILDER — 2 bộ yếu nhất (F1 0.50 / 0.54)

Chẩn đoán đã xong (không phải nhãn thiếu — audit 3.810 ảnh chỉ 118 vết thiếu 0.9%):
vết mảnh dày + imgsz 640 nén mất chi tiết. Giải pháp:

1. **Tiled training**: cắt ảnh gốc thành tile 640px ở độ phân giải GỐC (không resize xuống)
   khi build dataset → vết 2px vẫn là 2px trong tile. Ưu tiên áp riêng 2 bộ này trước,
   toàn dataset sau nếu hiệu quả. (Đây cũng là lý giải vì sao v2 @1280 thất bại: nâng imgsz
   toàn ảnh ≠ tile — mosaic + letterbox vẫn hòa tan vết mảnh.)
2. **SAHI sliced inference**: suy luận theo lát + gộp (kèm WBF thay NMS cho box chồng nhau).
3. **Copy-paste augmentation** vết mảnh: dán vết mảnh thật vào ảnh bê tông sạch của cùng bộ.
4. Không loại 2 bộ này — chúng là nguồn khó nhất, giữ làm "đề thi" đo tiến bộ model.

## 3. LỘ TRÌNH MODEL v3 → v4 → v5

| Phiên bản | Nội dung | Mục tiêu số |
|---|---|---|
| **v3** (tuần tới) | Tiled training (Volker/Rissbilder trước) + hard-negative vân đá B3 + fine-tune từ weight v1 @960 + tải ĐÚNG best.pt + WBF inference | F1 ≥ 0.70 · FP vân đá < 10% · Dice DeepCrack ≥ 0.84 (vượt ResUNet) |
| **v4** | **Texture-conditioned model**: kênh đầu vào thêm texture-map (LBP) — 1 model đa bề mặt; hoặc MoE 2 expert (bê tông / đá) + router nhẹ | Dice 3DCrack ≥ 0.80 · giữ F1 bê tông |
| **v5** | **Multi-defect & Component: Spalling & Exposed Rebar** (cột/dầm/sàn + bong tróc lộ cốt thép từ CrSpEE / SegCODEBRIM / CUHK-USR) → Phase 3: Đánh giá an toàn kết cấu cho tòa nhà đình trệ tái khởi công theo TCVN 9381 / ACI 562-19 | Đột phá ứng dụng thực tế: Demo "Kiểm định an toàn tái khởi công" + bài báo hướng CACAIE / Automation in Construction |

## 4. HƯỚNG BÀI BÁO (mục tiêu: bài báo chuẩn, đăng hội thảo/tạp chí)

**Tựa đề xuất (EN):**
*CrackSieve: Texture-Suppression Preprocessing and Standards-Grounded Severity Grading
for Multi-Surface Crack Detection in Building Inspection*

**4 đóng góp (novelty) — mỗi cái đều có số liệu sẵn trong repo:**
1. **TSP module** — pipeline triệt tiêu texture (Frangi + guided filter + black-hat + bandpass)
   cho phát hiện vết nứt đa bề mặt, đánh giá trên benchmark OOD vân đá có kiểm soát
   (FP 24.1% → <10%). *Khoảng trống đã xác nhận chưa ai làm.*
2. **Benchmark đa bề mặt có kiểm soát**: 5 nguồn + 4.048 negatives + 306 vân đá OOD,
   split bất biến, mọi số tái lập bằng script công khai.
3. **Severity theo chuẩn kiểm định**: thang L0–L3 bám ACI 224R-01/TCVN 9381:2012,
   đo lường kiểm chứng ±1px, đa yếu tố (bề rộng–chiều dài–độ đậm–ngữ cảnh) —
   đóng cầu nối CV ↔ kỹ thuật xây dựng mà không bài crack-CV nào làm.
4. (v5) **Component-aware severity**: ngữ cảnh cấu kiện tự động.

**Bảng thí nghiệm cho bài báo (đã có hạ tầng đo sẵn):**
| Thí nghiệm | Script có sẵn | Số hiện tại |
|---|---|---|
| So sánh preprocessing trên vân đá (6 kỹ thuật A/B) | eval_hard_cases.py | 24.1% FP |
| So SOTA cùng metric pixel | compare_with_sota.py | 0.819/0.708 Dice |
| Đối chứng kiến trúc/độ phân giảu | evaluate_phase1.py (sweep) | F1 0.655 |
| Kiểm chứng đo lường | validate_measurements.py | ±1px |
| Ablation đa yếu tố severity | pytest test_severity | 28/28 |

**Venue mục tiêu (thứ tự ưu tiên):**
1. Hội thảo quốc tế trong nước: **SoICT**, **KSE**, **ICCAIS** (IEEE, 2 cột) — phù hợp khối lượng.
2. Tạp chí: **VNU Journal of Science (JCSC)**, **Tạp chí Xây dựng** — hướng kỹ thuật xây dựng sẽ
   thích mảng ACI/TCVN + component-aware.

**Nguyên tắc "phấn đấu số 1" đo được:** vượt Khanh (xong), vượt ResUNet cả 2 benchmark (v3/v4),
số mẫu 16k→20k+ (đã > Khanh11k thực dụng), và duy nhất có severity chuẩn + benchmark OOD.

## 5. Việc ngay tuần này (theo thứ tự)

1. Viết `scripts/stone_preprocess.py`: 6 kỹ thuật B1, xuất ảnh đã xử lý + chạy
   `eval_hard_cases.py` trên 6 biến thể → chọn tổ hợp thắng (kỳ vọng Frangi+guided).
2. Build tiled dataset Volker/Rissbilder (`scripts/build_tiled_subset.py`).
3. Gộp hard-negative + positive vân đá B3 vào train v3, train Kaggle 960px.
4. Đối chiếu bảng tính Google Sheets của nhóm (link cần quyền truy cập — export CSV gửi vào
   repo nếu muốn tôi đồng bộ số liệu tự động).

## 6. NÂNG CẤP từ 22 bài tham chiếu của nhóm (sheet reference v2026-10-29)

### 6.1 Bảng định vị — 5 đối thủ gần nhất và cái họ THIẾU

| Bài (từ sheet) | Venue / IF | Họ có | Họ THIẾU (≈ là chỗ của ta) |
|---|---|---|---|
| #2 Zhang 2024 — Hierarchical 3-level (Structure→Component→Defect) | CACAIE, IF ~9.1 | Phân cấp 3 lớp, acc 96/92/81% | Chỉ classification — KHÔNG segmentation, KHÔNG đo kích thước, KHÔNG severity |
| #16 Inam 2023 — YOLOv5+U-Net đo kích thước | Sustainability | Detection→segmentation→đo width/length thực | Không kiểm chứng sai số đo, không bám chuẩn severity, innovation thấp |
| #9 Ameli 2024 — Corrosion + condition rating BIRM/AASHTO | Infrastructures | Condition rating theo TIÊU CHUẨN (ý tưởng giống ta) | Chỉ corrosion 514 ảnh; không crack, không đo mm |
| #7 Mayya 2024 — YOLOV10→ViT multi-stage | Sensors | Detect→classify type 2 tầng (F1 90.34%) | Phân loại LOẠI vết, không mức độ nghiêm trọng theo chuẩn; phụ thuộc crop |
| #10 Ren 2025 — LBA-YOLO micro-crack | PLOS One | Lightweight chuyên micro-crack (+3.5% recall YOLOv8n) | Chỉ detection, không severity; tiling của ta nhắm đúng bài toán này |

### 6.2 Kết luận định vị sau khi đọc full 22 bài

1. **Không bài nào trong 22 bài có đủ chuỗi**: segmentation → đo kích thước **kiểm chứng sai số**
   → severity theo **chuẩn kỹ thuật** (ACI/TCVN) → benchmark OOD đa bề mặt. Bài gần nhất là
   #16 (đo kích thước, không kiểm chứng, không chuẩn) và #9 (chuẩn nhưng corrosion, không đo).
2. **Ý tưởng hierarchical 3-level của bài #2 (IF 9.1) xác nhận hướng component-aware (v5) là
   hướng "đắt"** — nhưng họ dừng ở classification; ta có thể đi tiếp: component → **vết nứt
   trong component đó → severity có ngữ cảnh**. Đây là bước tiến tự nhiên của bài họ.
3. Các bài "kém/loại" trong sheet (#1,8,9,16,17,18,19 cũ 2017–2021) → dùng cho phần
   related-work lịch sử, không phải đối thủ.

### 6.3 Nâng cấp đề tài & bài báo (v2)

**Đề tài nâng cấp (thuyết minh khóa luận):** từ "Phát hiện và phân loại vết nứt" →
*"Pipeline kiểm định vết nứt đa bề mặt: từ phân đoạn ảnh đến đánh giá mức độ theo chuẩn
ACI 224R-01/TCVN 9381:2012, kèm benchmark out-of-domain có kiểm soát"* — giữ khối lượng
hiện tại, nâng chất lượng đóng góp.

**Tựa bài báo (cập nhật):**
*From Pixels to Standards: A Two-Stage Pipeline with Validated Crack Measurement and
Standards-Grounded Severity Grading for Building Crack Inspection*

**4 đóng góp — tinh chỉnh sau khi đọc 22 bài:**
1. **Validated measurement** (mới nhấn mạnh): đo bề rộng/chiều dài/góc kiểm chứng ≤1px/0px/0°
   — 22 bài tham chiếu KHÔNG bài nào kiểm chứng sai số đo (bài #16 đo nhưng không validate).
   Đây là đóng góp mạnh nhất vì hiếm và dễ chứng minh.
2. **Standards-grounded severity đa yếu tố** (width neo ACI + length + contrast-độ sâu +
   Lớp B + through): bài #9 làm condition rating cho corrosion theo BIRM — ta làm tương tự
   cho CRACK theo ACI/TCVN nhưng có đo lường định lượng đầu vào.
3. **TSP texture-suppression + benchmark OOD vân đá** (giữ nguyên từ v1 roadmap).
4. **Hierarchical extension** (v5, optional): component-aware severity — bài #2 chứng minh
   venue IF 9.1 chấp nhận hướng này; ta làm sâu hơn bằng segmentation + severity.

**Baseline so sánh trong bài (chọn từ 22 bài, đủ mặt phủ):**
- Segmentation: ResUNet (bài SOTA), UNet-VGG16 (Khanhha), SAM (bài #8), CCTNet (bài #11)
- Detection/micro-crack: LBA-YOLO (bài #10), YOLOv8n gốc
- Cascade: YOLOV10-ViT (bài #7), Hierarchical (bài #2)
- Severity: bài #16 (đo kích thước), bài #9 (condition rating) — so về phương pháp, không so số

### 6.4 Thí nghiệm bổ sung cần làm (sau v3, trước khi viết bài)

| # | Thí nghiệm | Mục đích | Công cụ |
|---|---|---|---|
| E1 | TSP ablation: 6 kỹ thuật texture, từng cái + tổ hợp trên hard-case | Chứng minh mỗi thành phần TSP đóng góp | eval_hard_cases.py |
| E2 | So SAM zero-shot trên test set của ta | Baseline foundation model (bài #8 dùng SAM) | SAM + GT |
| E3 | Tiled vs full-image trên Volker/Rissbilder | Chứng minh tiling fix vết mảnh | build_tiled_subset.py |
| E4 | Measurement validation trên ảnh THỰC có thước (không chỉ synthetic) | Nâng độ tin cậy đóng góp #1 | cần chụp/ thu thập 20–50 ảnh |
| E5 | Human-study nhỏ: so mức độ kỹ sư tự đánh vs hệ thống trên 30 ảnh | Chứng minh severity khớp chuyên gia | bảng Google Sheets của nhóm |

### 6.5 Venue — nâng kỳ vọng theo sheet

- Sheet xác nhận CACAIE (IF ~9.1) nhận hướng hierarchical/system — **mục tiêu dài hạn:
  CACAIE** (pipeline đầy đủ sau v5). 
- Mục tiêu khóa luận: **SoICT / KSE / ICCAIS** (IEEE) với 4 đóng góp 1–3.
- Phương án dự phòng: JCSCE, VNU JCSC.

## 7. GT-CrackSeg (phát hiện 2026-10-30) — vũ khí tái lập baseline

GT-CrackSeg (github.com/GT-SCI/GT-CrackSeg) = framework PyTorch CHÍNH CHỦ của nhóm Georgia
Tech (tác giả bài SOTA 2508.10256), đóng gói sẵn: ResUNet, DeepLabV3, SegFormer, DPT,
CrackFormerII, SCSegamba, CrackSAM + metric Dice/P/R/IoU/ODS/OIS + loader cho DeepCrack/TUT/
Khanhha/CrackTree + Google Drive "all datasets".

**Dùng trong bài báo**: chạy chính các baseline của benchmark bằng framework của chính họ
trên SPLIT CỦA TA → bảng so sánh airtight, không ai chê "so khác điều kiện". Đây là cách
nhanh nhất đạt chuẩn "so sánh chính xác với các bài tốt nhất".
