# Nhật ký thí nghiệm — crack_severity_ai

## Hard-case vân đá — đo độ nhầm lẫn (2026-10-27)

- **Tách bộ hard cases** (`scripts/prepare_hard_cases.py`): 303 ảnh vân đá/nứt đá bị loại
  khỏi train — forest 118 ảnh (281 vết GT), sylvie 185 ảnh (228 vết GT); nhãn polygon từ
  mask GT bằng đúng thuật toán build. Mục đích: đo model có NHẦM texture vân đá thành vết
  nứt (FP) và recall trên vật liệu hoàn toàn lạ.
- **Kết quả** (IoU≥0.5, FP ảnh = ảnh bị báo nhầm ≥1 vết):

  | Model | conf | P | R | F1 | FP vết | FP ảnh |
  |---|---|---|---|---|---|---|
  | v1 @640 | 0.45 | **0.731** | **0.395** | **0.513** | 74 | **24.1%** (73/303) |
  | v1 @640 | 0.55 | 0.744* | — | — | 65 | 21.5% (65/303) |
  | v2 @1280 | 0.45 | 0.439 | 0.361 | 0.397 | 128 | 36.3% (110/303) |
  | v2 @1280 | 0.55 | — | — | — | 53 | 17.2% (52/303) |

  (*v1 P ở 0.55 từ sweep; chi tiết đầy đủ outputs/reports/hard_cases_v1_640_*.md, v2_1280_*.md)
- **Phân tách theo nguồn (v1)**: sylvie khá — P 0.843 / R 0.566 / F1 0.677; **forest tệ** —
  P 0.590 / R 0.256 / F1 0.357, pixel Dice chỉ **0.190** (4.7M px FP — vân đá forest dày
  đặc bị nhầm thành nứt ở mức pixel), sylvie Dice 0.606.
- **Kết luận**:
  1. CẢ HAI model vẫn nhầm vân đá (dự kiến — out-of-domain, không có trong train).
  2. v1 @conf 0.45: precision 73.1% trên vết đá, recall 39.5%, ~24% ảnh bị báo nhầm
     ít nhất 1 vết; nâng conf 0.55 còn 21.5%.
  3. v2 không khá hơn (F1 0.397) — nhất quán với quyết định giữ v1.
  4. **Hành động v3**: gộp một phần vân đá làm hard-negative (nhãn rỗng) vào train —
     đúng kế hoạch lần 11; giữ phần còn lại làm hard-case test; production dùng conf ≥ 0.45.

## Phase 2 v3 — Severity ĐA YẾU TỐ (2026-10-27)

- **Vấn đề**: bề rộng một mình không đánh giá được vết DÀI NHƯNG MẢNH (user nêu) —
  vết 0.15mm × 750mm width-only chỉ ra L1 trong khi thực tế đáng lo.
- **Giải pháp**: severity = neo ACI (width_max × GSD) + yếu tố bổ sung, mỗi yếu tố +1
  mức (tối đa +2, chặn L3), lý do hiển thị trên chip:
  - **Chiều dài**: length_mm ≥ 300mm → +1 (hư hỏng lan rộng)
  - **Độ đậm (contrast_ratio)**: ≥ 30% tối hơn nền cục bộ → +1 (proxy độ sâu;
    đo = (mean nền − mean vết)/mean nền, nền = vòng đệm 9px quanh mask)
  - **Lớp B**: branching / multi_plane → +1
  - through_member → L3 tuyệt đối; thiếu GSD → không phân loại
- **Đã test case user nêu**: 0.15mm + 750mm + contrast 50% → L1 → L3 (bumps=2,
  factors ["dài…", "đậm…"]); contrast thấp → L2; bump chặn ở +2.
- contrast_ratio có unit test (đậm vs nhạt vs sáng-hơn-nền clamp 0).
- pytest **28/28**, E2E 7/7, lint sạch. UI: cột "Đậm (%)" + tooltip factors +
  máy tính Phase 2 thêm input contrast. DB lưu contrast_ratio, reclassify-lưu dùng đủ yếu tố.
- Hạn chế: ngưỡng 300mm/30% là đề xuất — cần hiệu chuẩn trên ảnh thực có thước;
  contrast nhạy với ánh sáng chụp (đèn bóng tạo nền/vết lệch) — khuyến nghị chụp
  ánh sáng đều; Lớp B đúng (segmentation mặt phẳng) vẫn là việc giai đoạn sau.

## UI v4 — thiết kế lại toàn bộ (2026-10-27)

- **Theme sáng hiện đại** (tham chiếu SafetyCulture/Procore): top navbar trắng trong suốt
  (backdrop blur) thay cho sidebar tối, hero gradient xanh→cyan trên dashboard, card trắng
  bo góc mềm, bảng màu brand #2563eb → cyan #06b6d4.
- Bố cục theo luồng mới: Dashboard (hero + KPI icon + 3 biểu đồ + hồ sơ gần đây có thumbnail)
  → Wizard 4 bước (stepper pill gradient) → Hồ sơ (filter + thumbnail + duyệt) →
  **Phase 2 (mục nav riêng: thang + máy tính phân loại + quy tắc + kiểm chứng)** →
  Model (benchmark + so v1/v2 + SOTA progress + lộ trình) → Thiết lập (thang + tham số + vai trò + về hệ thống).
- Hoàn thiện thiếu sót: favicon SVG, skeleton loading, empty states có icon + CTA, toast trắng
  viền màu, focus ring, thời gian chào theo buổi, hero stats, cache-bust v=40 + no-cache index.
- Báo cáo in PDF đồng bộ theme sáng (#2563eb), giữ khung chữ ký + badge trạng thái.
- Version **3.1.0-phase1+2**. Không đổi API — pytest 22/22 + E2E 7/7 pass ngay sau rewrite.

## Phase 2 — Kiểm chứng đo lường & hoàn thiện tích hợp (2026-10-27)

- **validate_measurements.py** (mask raster GT đúng chuẩn): width_max lệch tối đa **1px**
  (giới hạn lượng tử hóa — đã hiệu chỉnh DT nửa pixel: `width = 2×(d − 0.5)`), length 0px,
  angle 0° sau khi chuyển từ minAreaRect sang **moments** (quy ước 0°=ngang), branching đúng.
  → **ĐẠT NGHIỆM THU**. Báo cáo: outputs/reports/validate_measurements_*.md
- **Tích hợp trọn vòng đời**: DB lưu width_max/branching/multi_plane; POST
  `/api/inspections/{id}/severity` phân loại lại hồ sơ ĐÃ LƯU từ px (đổi GSD sau lưu,
  không cần ảnh/model); modal chi tiết có ô GSD + nút tính lại.
- E2E 7/7 (thêm bước reclassify-lưu), pytest 22/22, lint sạch.
- Hạn chế đã ghi nhận: vết <3px sai số tương đối lớn (lượng tử hóa) — khuyến nghị
  GSD ≤ 0.2 mm/px khi cần phân biệt Hairline/Minor; Lớp B đúng (segmentation mặt phẳng)
  để làm giai đoạn sau.

## Phase 1 v2 @1280 — đánh giá & QUYẾT ĐỊNH GIỮ v1 (2026-10-26/27)

- **Weight v2**: best.pt từ Kaggle (imgsz 1280, multi_scale, ~76 epochs, dữ liệu cải thiện
  +3.000 ảnh âm +118 pseudo-GT). Lưu: checkpoint trỏ nguồn "v2epoch74/last.pt" — nghi là
  last.pt của run resume, không phải best.pt thật của run.
- **Kết quả v2 @1280 (test 1.491 ảnh / 3.531 GT)**:
  - Ảnh âm: FP **1.5%** (v1: 2.2%) ✅
  - Pixel-level: 3DCrack Dice **0.718** (v1 0.708), DeepCrack **0.803** (v1 0.819), tổng ngang
  - Instance @conf 0.25: P=0.516, R=0.511, F1=0.513 — FP 498→1689 ⚠️
  - **Sweep conf (mới — sửa bug indent làm eval chỉ chạy 1 ảnh)**:

    | conf≥ | P | R | F1 |
    |---|---|---|---|
    | 0.25 | 0.516 | 0.511 | 0.513 |
    | 0.35 | 0.554 | 0.478 | 0.514 |
    | 0.45 | 0.608 | 0.445 | 0.514 |
    | 0.55 | 0.683 | 0.378 | 0.487 |
    | 0.65 | 0.744 | 0.244 | 0.368 |

- **KẾT LUẬN: F1 tối đa v2 = 0.514 < v1 = 0.655 trên toàn dải conf** → không tích hợp v2.
  - Giả thuyết nguyên nhân: (1) checkpoint là last.pt resume epoch ~74, không phải best;
    (2) multi_scale + 1280 làm đầu mỏng nhiều box trùng/lệch, IoU 0.5 phạt nặng;
    (3) thiếu WBF/merge box. Pixel Dice 3DCrack vẫn nhỉnh hơn (0.718) — hướng mask còn tốt.
- **Hành động**: best.pt = v1 (oldbest.pt, imgsz 640); v2 lưu `weights/phase1/best_v2_1280.pt`
  chỉ để tham chiếu. App model-info/view Phân tích hiển thị bảng so v1/v2 minh bạch.
- **Bài học cho v3**: train từ weight v1, imgsz 960 (không 1280), tải đúng best.pt của run,
  cân nhắc WBF cho box mảnh; giữ ảnh âm (đã chứng minh giảm FP).

## Phase 2 — HOÀN THIỆN rule-based (2026-10-26)

- **Lớp A đầy đủ** (app/crack_features.py): length/width_mean/**width_max** (distance-transform
  ×2), area, angle, **branching** (skeleton Zhang-Suen: n_branches/n_endpoints), density_ratio.
- **Lớp B**: multi_plane (heuristic: skeleton ≥2 điểm rẽ nhánh) + through_member (kỹ sư
  đánh dấu checkbox "Xuyên?" trên UI → ép L3).
- **Quy tắc** (app/severity.py): phân loại theo **bề rộng MAX × GSD** (đúng thực hành ACI
  đo max width); branching/multi_plane → +1 mức (không cộng dồn); xuyên cấu kiện → L3;
  thiếu GSD → không phân loại (không đoán).
- **Tích hợp app**: công cụ "📏 Đo GSD" (bấm 2 điểm vào vật chuẩn → GSD tự tính, tự phân
  loại lại toàn bộ vết), POST /api/severity tái phân loại không cần inference, cột mức độ
  màu trong bảng + báo cáo in, legend thang.
- Test: pytest 22/22 (thêm test_crack_features + severity v2), E2E 6/6 (có bước /api/severity).

- **Audit label miss** (Volker + Rissbilder, train only, conf≥0.6, IoU<0.3 với mọi GT):
  - Rissbilder: 106 vết / 99 ảnh (~0.9% GT nguồn) — Volker: 12 vết / 11 ảnh (~0.4%).
  - **Kết luận: recall thấp ở 2 nguồn KHÔNG phải do thiếu nhãn** → do model yếu với vết
    mảnh dày; tăng imgsz là đòn bẩy chính.
- Đã **ghép 118 pseudo-GT polygon** vào nhãn train (conf≥0.6, val/test giữ nguyên).
- Đã **thêm 3.000 ảnh âm train-only** (METU Negative + SDNET UD/UW, label rỗng, tiền tố
  am_v2_) — train=14.619 ảnh; val/test không đổi để so sánh công bằng với v1.
- Zip v2: outputs/kaggle/phase1_primary_20261023.zip (1.15 GB, 18.947 ảnh).
- Train v2: YOLOv8s-seg, imgsz 1280, batch 16 (T4 x2), multi_scale 0.5, epochs 100, patience 25.

## So sánh SOTA (arXiv:2508.10256) — metric pixel-level (2026-10-22)

- Metric cùng loại với bài: semantic segmentation, IoU/Precision/Recall/Dice (micro, cộng dồn pixel).
- **v1 của ta (YOLOv8s-seg @640) trên đúng 2 bộ benchmark của bài:**

  | Bộ | Ta: Dice / IoU | Bài (ResUNet 100% data): Dice / IoU | Gap Dice |
  |---|---|---|---|
  | DeepCrack | **0.819 / 0.694** | 0.833 / 0.725 | **−0.014 (≈1.7%)** |
  | 3DCrack | **0.708 / 0.548** | 0.795 / 0.703 | **−0.087 (≈11%)** |

- Nhận xét:
  - DeepCrack: đã **ngang tầm baseline ResUNet** của bài (chênh 1.4% Dice) dù ta train đa nguồn
    và split khác (ta chia hash 80/10/10 trên primary gộp; bài dùng split gốc của từng bộ).
  - 3DCrack là khoảng cách chính (−11% Dice): ảnh 512×624 với vết mảnh 1–2px, mask head của
    YOLO-seg decode ở 1/4 độ phân giải nên vết quá mảnh bị mất. CrackSAM/UniMatch v2 của bài
    còn cao hơn ResUNet nữa (mask decoder độ phân giải cao).
- Kế hoạch thu hẹp gap: v2 train imgsz 1280 (T4 x2, DDP) + multi_scale 0.5 + epochs 100 —
  tăng độ phân giải mask prototype; v3 pseudo-label mở rộng dữ liệu (METU/SDNET positive)
  sau khi v2 xác nhận image-level vẫn ≥0.99; cân nhắc fine-tune mask head hoặc model seg
  chuyên dụng nếu 3DCrack vẫn thấp.
- Báo cáo: outputs/reports/compare_sota_20261022_233105.md

## Phase 1 v1 — Chẩn đoán sai theo nguồn (2026-10-22, scripts/evaluate_phase1.py)

- Cài đặt: conf=0.25, IoU khớp=0.5, imgsz=640; test primary 1.491 ảnh + mẫu 400/1.353 ảnh âm.
- **Mức ảnh (có/không nứt): 0.999 → ĐẠT kỳ vọng 0.95.** Ảnh âm báo nhầm 2.2% (9/400, conf TB 0.45).
- **Mức instance: P=0.797, R=0.555, F1=0.655** (TP=1961, FP=498, FN=1570).
- **75.5% FN là vết nhỏ (cạnh <32px)** → nguyên nhân chính là độ phân giải 640.
- Recall theo nguồn: Ultralytics 0.84, Roads_and_Bridges 0.81, DeepCrack 0.76, 3DCrack 0.63,
  crack_seg/DeepCrack 0.56, **Volker 0.34, Rissbilder 0.41** (2 nguồn này nhiều vết mảnh/đông GT).
- Báo cáo: outputs/reports/evaluate_phase1_20261022_180022.md (+ per-image CSV).
- Kế hoạch v2: (1) imgsz 960/1280 hoặc tiling SAHI; (2) rà nhãn Volker/Rissbilder (nghi label miss);
  (3) giữ ảnh âm trong train; (4) nếu vẫn thấp → yolov8m-seg.

## Phase 1 v1 — YOLOv8s-seg (2026-10-22)

- **Dữ liệu**: primary 14.594 ảnh (bê tông/tường: 3DCrack_v1, crack_segmentation_dataset [Eugen_Muller, noncrack, Rissbilder, Volker, DeepCrack], DeepCrack độc lập, Roads_and_Bridges, Ultralytics_CrackSeg) + 1.353 ảnh âm (noncrack, txt rỗng) = 15.947 ảnh. Split 80/10/10 hash deterministic.
  - Bỏ bộ mặt đường (CFD, CRACK500, CrackTree200, GAPS384) theo chính sách mới — chỉ giữ bê tông/tường.
  - Nhãn: YOLO polygon thuần (class 0 = crack); dòng box được ép thành polygon 4 điểm; ảnh âm label rỗng (background).
- **Huấn luyện**: Kaggle T4, YOLOv8s-seg pretrained, epochs 100, imgsz 640, batch 16, patience 20, seed 42, workers 2. ~5 giờ.
- **Kết quả trên test (1.633 ảnh / 3.532 instance, 142 background)**:

  | Metric | Box | Mask |
  |---|---|---|
  | Precision | 0.823 | 0.794 |
  | Recall | 0.565 | 0.492 |
  | mAP50 | 0.599 | 0.488 |
  | mAP50-95 | 0.455 | 0.145 |

- **Speed**: 5.9ms inference (T4).
- **Weight**: `weights/phase1/best.pt` (yolov8s-seg, 11.78M params). Đã kiểm tra load + predict local OK.
- **Nhận xét**:
  - Precision khá (0.82) nhưng recall thấp (0.57) → bỏ sót nhiều vết nứt, đặc biệt vết mảnh/nhỏ ở imgsz 640.
  - Mask mAP50-95 thấp (0.145) → mask dự đoán chưa khớp chi tiết biên — cần imgsz lớn hơn / mask head tốt hơn.
  - Mục tiêu ~0.95 CHƯA đạt; đây là baseline v1 để so sánh.
- **Hướng cải thiện kế tiếp (ưu tiên)**:
  1. imgsz 960 hoặc 1280 (vết nứt mảnh, ảnh gốc lớn của CRACK500/Roads bị downsample mạnh).
  2. Xem results.csv + confusion matrix trên Kaggle: chốt đã chạy hết 100 epochs hay dừng sớm.
  3. Phân tích FP trên ảnh âm (noncrack) và FN theo từng nguồn dữ liệu local (infer_cascade.py).
  4. Nếu vẫn thấp: yolov8m-seg / l-seg, tăng epochs, cân nhắc close_mosaic, multi_scale.

## Thí nghiệm 6 — TSP texture-suppression: KẾT QUẢ ÂM có giá trị (2026-10-29)

- A/B 8 biến thể tiền xử lý trên 303 ảnh vân đá @conf 0.45 (scripts/stone_preprocess.py):
  | Biến thể | FP ảnh | FP vết | R trên đá | F1 đá |
  |---|---|---|---|---|
  | baseline | 24.1% | 74 | 0.395 | 0.513 |
  | **blackhat→clahe** | **13.5%** | **43** | **0.149** | **0.230** |
  | bgsub | 13.9% | 44 | 0.175 | 0.262 |
  | blackhat | 15.2% | 49 | — | — |
  | bilateral/guided | 21.8% | 70 | — | — |
  | dog / tsp_full | 24.8/29.0% | 91/126 | — | — |
- **Phát hiện**: TSP lúc suy luận giảm FP 42% nhưng ĐÁNH SẬP recall đá (0.395→0.149) —
  model học trên ảnh gốc, biến đổi mạnh lúc inference xóa luôn tín hiệu vết thật.
  F1 đá 0.513 → 0.230-0.262.
- **Kết luận kỹ thuật**: texture FP KHÔNG thể xử bằng preprocessing lúc suy luận;
  phải đưa texture (vân đá) vào TRAIN dạng hard-negative. TSP trở thành ablation
  chứng minh điều này trong bài báo.
- Thực hiện: scripts/stone_preprocess.py (8 biến thể, logs outputs/reports/tsp_*.log).

## Hard-case vân đá — đo độ nhầm lẫn (2026-10-27)
