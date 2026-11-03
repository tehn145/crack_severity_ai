# Bảng so sánh cho bài báo — CrackSieve (draft 2026-10-29)

> Mục tiêu "vượt bậc" phải chứng minh bằng số trên cùng benchmark + cùng metric.
> Cập nhật số "ta" sau khi v3 train xong. Đánh ⏳ = chờ kết quả.

## Bảng 1 — So sánh với các phương pháp (benchmark chung)

| Phương pháp | Venue/Year | Kiểu | DeepCrack Dice | 3DCrack Dice | Khanh11k Dice | Ghi chú |
|---|---|---|---|---|---|---|
| UNet-VGG16 (Khanh) | GitHub 2019 | seg | — | — | 0.603 | nguồn dữ liệu của ta |
| ResUNet | arXiv 2508.10256 | seg | 0.833 | 0.795 | — | baseline chính benchmark |
| CrackSAM | CBM 2024 | seg (SAM+LoRA) | >0.833* | >0.795* | — | số không công bố đủ trong text |
| UniMatch v2 | 2024 | semi-sup | >0.833* | >0.795* | — | mạnh khi thiếu nhãn |
| **Ta v1 (YOLOv8s-seg)** | — | det+seg | 0.819 | 0.708 | 0.749 (multi) | det + đo lường + severity |
| **Ta v3 (tiled+stone)** | — | det+seg | ⏳ ≥0.84 | ⏳ ≥0.80 | ⏳ | tiled + hard-negative vân đá |
| **Ta v3 trên vân đá (OOD)** | — | det+seg | FP ảnh: 24.1% → ⏳ <10% | — | — | benchmark OOD duy nhất |

## Bảng 2 — Năng lực pipeline (so 5 bài gần nhất từ sheet)

| Năng lực | #2 Zhang (CACAIE) | #7 Mayya (Sensors) | #9 Ameli (Infra) | #16 Inam (Sust.) | **TA** |
|---|---|---|---|---|---|
| Detection / localization | △ (cls) | ✓ | ✓ | ✓ | ✓ |
| Segmentation / đo kích thước | ✗ | ✗ | ✓ | ✓ | ✓ |
| **Kiểm chứng sai số đo lường** | ✗ | ✗ | ✗ | ✗ | **✓ ±1px / 0px / 0°** |
| Severity theo tiêu chuẩn | ✗ | △ (loại vết) | ✓ (corrosion, BIRM) | ✗ | **✓ ACI/TCVN L0–L3** |
| Đa bề mặt / benchmark OOD | △ | ✗ | ✗ | ✗ | **✓ vân đá 303 ảnh + 4.048 neg** |
| Số samples train | ~1.000 | 13k | 514 | ~2.000 | **20.990** |

## Bảng 3 — Ablation cho bài báo (đã có số)

| Thành phần | FP ảnh vân đá @0.45 | F1 vân đá | F1 test chính |
|---|---|---|---|
| v1 baseline | 24.1% | 0.513 | 0.655 |
| v1 + TSP suy luận (blackhat+clahe) | **13.5%** | 0.230 | — |
| v1 + TSP (bgsub) | 13.9% | 0.262 | — |
| v3 tiled + hard-negative | ⏳ | ⏳ | ⏳ |

→ Câu chuyện ablation: TSP suy luận chứng minh FP đến từ texture (giảm 44%) nhưng
phải xử ở TRAIN (hard-negative) — v3 chính là cách đúng. 2 bảng số đã đủ, chờ v3.

## Con số "vượt bậc" cần đạt trước 30/11 (viết bài)

1. DeepCrack Dice ≥ 0.84 (vượt ResUNet +1%) — khả thi với tiled @960
2. 3DCrack Dice ≥ 0.80 — khó nhất (mask head 1/4 res)
3. FP vân đá < 10% — khả thi với 150 hard-negative
4. Số samples: 20.990 — đã lớn nhất trong các bài so (Khanh 11.2k dùng được)
5. Severity: duy nhất có ±1px validation + ACI/TCVN — không ai cần thi, chỉ cần hoàn thiện E4/E5
