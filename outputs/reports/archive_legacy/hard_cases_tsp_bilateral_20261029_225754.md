# Hard cases (vân đá) — tsp_bilateral
- weights: `weights/phase1/best.pt` | imgsz: 640 | 303 ảnh (118 forest + 185 sylvie), GT 509 vết

## 1. Theo nguồn — IoU≥0.5 @conf tối ưu F1 riêng từng nguồn
| Nguồn | Ảnh | GT | P | R | F1 | best conf |
|---|---|---|---|---|---|---|
| forest | 118 | 281 | 0.631 | 0.292 | 0.399 | ≥0.35 |
| sylvie | 185 | 228 | 0.800 | 0.614 | 0.695 | ≥0.35 |
| TONG | 303 | 509 | 0.728 | 0.436 | 0.545 | ≥0.35 |

## 2. Độ NHẦM LẪN texture vân đá (FP vết / FP ảnh)
| conf ≥ | FP vết | FP ảnh có ≥1 FP |
|---|---|---|
| 0.25 | 110 | 90 / 303 | 29.7% |
| 0.35 | 83 | 74 / 303 | 24.4% |
| 0.45 | 70 | 66 / 303 | 21.8% |
| 0.55 | 51 | 51 / 303 | 16.8% |

## 3. Pixel Dice trên đá (vật liệu lạ)
| Nguồn | TP px | FP px | FN px | Dice |
|---|---|---|---|---|
| forest | 545658 | 3857302 | 30025 | 0.219 |
| sylvie | 2807771 | 2430370 | 832458 | 0.632 |
| TONG | 3353429 | 6287672 | 862483 | 0.484 |

## Đọc kết quả
- **FP vết** = số lần model báo 'nứt' ở chỗ GT không có → NHẦM vân đá/texture thành nứt.
- **Recall trên đá** thấp là BÌNH THƯỜNG (vật liệu lạ, out-of-domain, không có trong train).
- Mục tiêu production: FP thấp ở conf vận hành (≥0.35–0.5) — texture đá ít bị báo nhầm.
