# Hard cases (vân đá) — tsp_clahe
- weights: `weights/phase1/best.pt` | imgsz: 640 | 303 ảnh (118 forest + 185 sylvie), GT 509 vết

## 1. Theo nguồn — IoU≥0.5 @conf tối ưu F1 riêng từng nguồn
| Nguồn | Ảnh | GT | P | R | F1 | best conf |
|---|---|---|---|---|---|---|
| forest | 118 | 281 | 0.618 | 0.299 | 0.403 | ≥0.25 |
| sylvie | 185 | 228 | 0.789 | 0.605 | 0.685 | ≥0.35 |
| TONG | 303 | 509 | 0.682 | 0.452 | 0.544 | ≥0.25 |

## 2. Độ NHẦM LẪN texture vân đá (FP vết / FP ảnh)
| conf ≥ | FP vết | FP ảnh có ≥1 FP |
|---|---|---|
| 0.25 | 107 | 96 / 303 | 31.7% |
| 0.35 | 84 | 78 / 303 | 25.7% |
| 0.45 | 72 | 70 / 303 | 23.1% |
| 0.55 | 60 | 59 / 303 | 19.5% |

## 3. Pixel Dice trên đá (vật liệu lạ)
| Nguồn | TP px | FP px | FN px | Dice |
|---|---|---|---|---|
| forest | 554535 | 4112471 | 21148 | 0.212 |
| sylvie | 2833648 | 2779304 | 806581 | 0.612 |
| TONG | 3388183 | 6891775 | 827729 | 0.467 |

## Đọc kết quả
- **FP vết** = số lần model báo 'nứt' ở chỗ GT không có → NHẦM vân đá/texture thành nứt.
- **Recall trên đá** thấp là BÌNH THƯỜNG (vật liệu lạ, out-of-domain, không có trong train).
- Mục tiêu production: FP thấp ở conf vận hành (≥0.35–0.5) — texture đá ít bị báo nhầm.
