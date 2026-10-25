# Nhật ký thí nghiệm — crack_severity_ai

## Cải thiện mẫu v2 (2026-10-23, scripts/improve_v2_data.py)

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
