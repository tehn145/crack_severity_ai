# Hard cases (vân đá) — tsp_bgsub
- weights: `weights/phase1/best.pt` | imgsz: 640 | 303 ảnh (118 forest + 185 sylvie), GT 509 vết

## 1. Theo nguồn — IoU≥0.5 @conf tối ưu F1 riêng từng nguồn
| Nguồn | Ảnh | GT | P | R | F1 | best conf |
|---|---|---|---|---|---|---|
| forest | 118 | 281 | 0.549 | 0.139 | 0.222 | ≥0.25 |
| sylvie | 185 | 228 | 0.500 | 0.219 | 0.305 | ≥0.25 |
| TONG | 303 | 509 | 0.520 | 0.175 | 0.262 | ≥0.25 |

## 2. Độ NHẦM LẪN texture vân đá (FP vết / FP ảnh)
| conf ≥ | FP vết | FP ảnh có ≥1 FP |
|---|---|---|
| 0.25 | 82 | 70 / 303 | 23.1% |
| 0.35 | 58 | 50 / 303 | 16.5% |
| 0.45 | 44 | 42 / 303 | 13.9% |
| 0.55 | 31 | 30 / 303 | 9.9% |

## 3. Pixel Dice trên đá (vật liệu lạ)
| Nguồn | TP px | FP px | FN px | Dice |
|---|---|---|---|---|
| forest | 180684 | 282558 | 394999 | 0.348 |
| sylvie | 531363 | 141826 | 3108866 | 0.246 |
| TONG | 712047 | 424384 | 3503865 | 0.266 |

## Đọc kết quả
- **FP vết** = số lần model báo 'nứt' ở chỗ GT không có → NHẦM vân đá/texture thành nứt.
- **Recall trên đá** thấp là BÌNH THƯỜNG (vật liệu lạ, out-of-domain, không có trong train).
- Mục tiêu production: FP thấp ở conf vận hành (≥0.35–0.5) — texture đá ít bị báo nhầm.
