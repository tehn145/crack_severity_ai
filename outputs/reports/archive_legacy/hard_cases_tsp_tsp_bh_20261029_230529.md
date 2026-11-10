# Hard cases (vân đá) — tsp_tsp_bh
- weights: `weights/phase1/best.pt` | imgsz: 640 | 303 ảnh (118 forest + 185 sylvie), GT 509 vết

## 1. Theo nguồn — IoU≥0.5 @conf tối ưu F1 riêng từng nguồn
| Nguồn | Ảnh | GT | P | R | F1 | best conf |
|---|---|---|---|---|---|---|
| forest | 118 | 281 | 0.500 | 0.110 | 0.181 | ≥0.25 |
| sylvie | 185 | 228 | 0.506 | 0.197 | 0.284 | ≥0.25 |
| TONG | 303 | 509 | 0.503 | 0.149 | 0.230 | ≥0.25 |

## 2. Độ NHẦM LẪN texture vân đá (FP vết / FP ảnh)
| conf ≥ | FP vết | FP ảnh có ≥1 FP |
|---|---|---|
| 0.25 | 75 | 68 / 303 | 22.4% |
| 0.35 | 53 | 50 / 303 | 16.5% |
| 0.45 | 43 | 41 / 303 | 13.5% |
| 0.55 | 29 | 27 / 303 | 8.9% |

## 3. Pixel Dice trên đá (vật liệu lạ)
| Nguồn | TP px | FP px | FN px | Dice |
|---|---|---|---|---|
| forest | 153600 | 261784 | 422083 | 0.310 |
| sylvie | 495598 | 149458 | 3144631 | 0.231 |
| TONG | 649198 | 411242 | 3566714 | 0.246 |

## Đọc kết quả
- **FP vết** = số lần model báo 'nứt' ở chỗ GT không có → NHẦM vân đá/texture thành nứt.
- **Recall trên đá** thấp là BÌNH THƯỜNG (vật liệu lạ, out-of-domain, không có trong train).
- Mục tiêu production: FP thấp ở conf vận hành (≥0.35–0.5) — texture đá ít bị báo nhầm.
