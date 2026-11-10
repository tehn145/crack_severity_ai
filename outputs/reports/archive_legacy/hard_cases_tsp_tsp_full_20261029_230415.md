# Hard cases (vân đá) — tsp_tsp_full
- weights: `weights/phase1/best.pt` | imgsz: 640 | 303 ảnh (118 forest + 185 sylvie), GT 509 vết

## 1. Theo nguồn — IoU≥0.5 @conf tối ưu F1 riêng từng nguồn
| Nguồn | Ảnh | GT | P | R | F1 | best conf |
|---|---|---|---|---|---|---|
| forest | 118 | 281 | 0.608 | 0.391 | 0.476 | ≥0.35 |
| sylvie | 185 | 228 | 0.542 | 0.592 | 0.566 | ≥0.35 |
| TONG | 303 | 509 | 0.570 | 0.481 | 0.522 | ≥0.35 |

## 2. Độ NHẦM LẪN texture vân đá (FP vết / FP ảnh)
| conf ≥ | FP vết | FP ảnh có ≥1 FP |
|---|---|---|
| 0.25 | 307 | 173 / 303 | 57.1% |
| 0.35 | 185 | 120 / 303 | 39.6% |
| 0.45 | 126 | 88 / 303 | 29.0% |
| 0.55 | 81 | 65 / 303 | 21.5% |

## 3. Pixel Dice trên đá (vật liệu lạ)
| Nguồn | TP px | FP px | FN px | Dice |
|---|---|---|---|---|
| forest | 406378 | 470339 | 169305 | 0.560 |
| sylvie | 1085575 | 147518 | 2554654 | 0.446 |
| TONG | 1491953 | 617857 | 2723959 | 0.472 |

## Đọc kết quả
- **FP vết** = số lần model báo 'nứt' ở chỗ GT không có → NHẦM vân đá/texture thành nứt.
- **Recall trên đá** thấp là BÌNH THƯỜNG (vật liệu lạ, out-of-domain, không có trong train).
- Mục tiêu production: FP thấp ở conf vận hành (≥0.35–0.5) — texture đá ít bị báo nhầm.
