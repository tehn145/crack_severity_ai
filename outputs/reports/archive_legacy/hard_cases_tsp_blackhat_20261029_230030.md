# Hard cases (vân đá) — tsp_blackhat
- weights: `weights/phase1/best.pt` | imgsz: 640 | 303 ảnh (118 forest + 185 sylvie), GT 509 vết

## 1. Theo nguồn — IoU≥0.5 @conf tối ưu F1 riêng từng nguồn
| Nguồn | Ảnh | GT | P | R | F1 | best conf |
|---|---|---|---|---|---|---|
| forest | 118 | 281 | 0.575 | 0.149 | 0.237 | ≥0.25 |
| sylvie | 185 | 228 | 0.539 | 0.241 | 0.333 | ≥0.25 |
| TONG | 303 | 509 | 0.554 | 0.191 | 0.284 | ≥0.25 |

## 2. Độ NHẦM LẪN texture vân đá (FP vết / FP ảnh)
| conf ≥ | FP vết | FP ảnh có ≥1 FP |
|---|---|---|
| 0.25 | 78 | 71 / 303 | 23.4% |
| 0.35 | 60 | 56 / 303 | 18.5% |
| 0.45 | 49 | 46 / 303 | 15.2% |
| 0.55 | 38 | 36 / 303 | 11.9% |

## 3. Pixel Dice trên đá (vật liệu lạ)
| Nguồn | TP px | FP px | FN px | Dice |
|---|---|---|---|---|
| forest | 177008 | 286024 | 398675 | 0.341 |
| sylvie | 544051 | 132228 | 3096178 | 0.252 |
| TONG | 721059 | 418252 | 3494853 | 0.269 |

## Đọc kết quả
- **FP vết** = số lần model báo 'nứt' ở chỗ GT không có → NHẦM vân đá/texture thành nứt.
- **Recall trên đá** thấp là BÌNH THƯỜNG (vật liệu lạ, out-of-domain, không có trong train).
- Mục tiêu production: FP thấp ở conf vận hành (≥0.35–0.5) — texture đá ít bị báo nhầm.
