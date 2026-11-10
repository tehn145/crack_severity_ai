# Hard cases (vân đá) — tsp_dog
- weights: `weights/phase1/best.pt` | imgsz: 640 | 303 ảnh (118 forest + 185 sylvie), GT 509 vết

## 1. Theo nguồn — IoU≥0.5 @conf tối ưu F1 riêng từng nguồn
| Nguồn | Ảnh | GT | P | R | F1 | best conf |
|---|---|---|---|---|---|---|
| forest | 118 | 281 | 0.677 | 0.374 | 0.482 | ≥0.35 |
| sylvie | 185 | 228 | 0.688 | 0.531 | 0.599 | ≥0.45 |
| TONG | 303 | 509 | 0.631 | 0.464 | 0.535 | ≥0.35 |

## 2. Độ NHẦM LẪN texture vân đá (FP vết / FP ảnh)
| conf ≥ | FP vết | FP ảnh có ≥1 FP |
|---|---|---|
| 0.25 | 212 | 135 / 303 | 44.6% |
| 0.35 | 138 | 101 / 303 | 33.3% |
| 0.45 | 91 | 75 / 303 | 24.8% |
| 0.55 | 58 | 49 / 303 | 16.2% |

## 3. Pixel Dice trên đá (vật liệu lạ)
| Nguồn | TP px | FP px | FN px | Dice |
|---|---|---|---|---|
| forest | 392040 | 593699 | 183643 | 0.502 |
| sylvie | 1158233 | 137370 | 2481996 | 0.469 |
| TONG | 1550273 | 731069 | 2665639 | 0.477 |

## Đọc kết quả
- **FP vết** = số lần model báo 'nứt' ở chỗ GT không có → NHẦM vân đá/texture thành nứt.
- **Recall trên đá** thấp là BÌNH THƯỜNG (vật liệu lạ, out-of-domain, không có trong train).
- Mục tiêu production: FP thấp ở conf vận hành (≥0.35–0.5) — texture đá ít bị báo nhầm.
