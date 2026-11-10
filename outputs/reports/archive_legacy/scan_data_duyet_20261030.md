# BÁO CÁO SCAN DỮ LIỆU — PHỤC VỤ DUYỆT (2026-10-30)

> Trước khi qua v3: báo cáo này tổng hợp (1) trạng thái mọi nguồn đang tải/đã tải,
> (2) định giá từng nguồn sau khi scan cấu trúc thật, (3) phương án tiền xử lý cho
> bề mặt khó dựa trên thí nghiệm TSP đã chạy, (4) quyết định cần duyệt.

## 1. Trạng thái các nguồn

| Nguồn | Kích thước | Scan cấu trúc | Kết luận |
|---|---|---|---|
| **Pseudo-label** (METU 8k + SDNET CD/CW 5.9k) | đang chạy | 7.5k+/13.976 (54%) | Giữ ~8–10k ảnh conf ≥ 0.5 — polygon từ mask dự đoán v1 |
| **Masonry Zenodo** (Sensors 2021) | 2.7 MB | 946 ảnh, chia 0/1 theo thư mục, ảnh ~3.4KB, **KHÔNG mask** | **Giá trị THẤP** cho segmentation (patch siêu nhỏ, chỉ classification) — lưu tham chiếu |
| **CODEBRIM balanced** | ĐÃ DỪNG ở 706MB/12.2GB | Classification image-level, KHÔNG mask | **DỪNG** — 12GB đổi lại nhãn image-level không làm được YOLO polygon. SegCODEBRIM (có mask) cần request access Zenodo → chuyển sang mục cần duyệt |
| **Hard-case vân đá** | 306 ảnh / 509 vết | Đã scan, đã đo FP | ĐANG DÙNG: 250 vào v3 train, ~53 giữ test OOD |

## 2. Bài học tiền xử lý cho bề mặt khó (Thí nghiệm 6 — đã chạy đủ 8 biến thể)

Kết quả A/B TSP trên 303 ảnh vân đá @conf 0.45:

| Biến thể | FP ảnh | FP vết | Recall đá | F1 đá |
|---|---|---|---|---|
| baseline (không TSP) | 24.1% | 74 | 0.395 | **0.513** |
| **blackhat→clahe (thắng FP)** | **13.5%** | **43** | **0.149** | 0.230 |
| bgsub | 13.9% | 44 | 0.175 | 0.262 |
| blackhat đơn | 15.2% | 49 | — | — |
| bilateral / guided | 21.8% | 70 | — | — |
| dog / tsp_full | 24.8 / 29.0% | 91/126 | — | — |

**Kết luận quan trọng**: TSP lúc SUY LUẬN giảm FP 44% nhưng đánh sập recall đá
(0.395 → 0.149) — model học trên ảnh gốc, biến đổi mạnh lúc inference xóa cả tín hiệu
vết thật. F1 0.513 → 0.230.

**⇒ Phương án đúng cho bề mặt khó (đề xuất duyệt):**
1. **Train-time TSP augmentation**: ảnh vân đá/gạch trang trí trong train giữ CẢ 2 phiên
   bản (gốc + blackhat→clahe) → model học vết nứt ở cả hai "tọa độ texture", suy luận
   trên đá thật bền hơn mà không cần biết trước bề mặt.
2. **Tiled training** cho vết mảnh (đã build 3.146 tile @độ phân giải gốc).
3. **Hard-negative** vân đá nhãn rỗng (đã có 150 trong v3).
4. **Synthetic paste** (Syncrack-style): dán vết nứt GT lên nền gạch/đá sạch — dùng luôn
   90 ảnh "real/0" (không nứt) của masonry làm nền.

## 3. Dataset v3 — ĐÃ BUILD, CHỜ DUYỆT UPLOAD
`outputs/kaggle/phase1_v3_20261029.zip` (1.52 GB):
- train **18.015** = primary 14.594 + tiled 3.146 + vân đá negative 150 + vân đá positive 97
- val 1.484 / test 1.491 — BẤT BIẾN
- kèm v1_best.pt (fine-tune) + data.yaml @960
- Cell train: `outputs/kaggle/cell_v3_kaggle.py`

## 4. Những gì cần DUYỆT để tiếp tục

| # | Quyết định | Tác động |
|---|---|---|
| D1 | **Upload v3 zip lên Kaggle + train** theo cell kèm | F1 mục tiêu ≥ 0.70; FP vân đá đo lại |
| D2 | **Duyệt phương án train-time TSP** (mục 2.1) cho v4 | Xử lý bề mặt khó đúng cách |
| D3 | **Email xin OmniCrack30K** (từ mail UIT) + request SegCODEBRIM Zenodo | Mở 30k đa vật liệu + component masks |
| D4 | **MCrack1300**: tải từ GitHub zxy239/LoRA-SAM hoặc Roboflow (cần account) | +1.3k masonry có mask instance (bricks/crack) — cho Lớp B |
| D5 | **BCL / TopoDS / UAV75 / Ceramic / AEL**: lấy link từ README OmniCrack30K References | +8–12k đa nguồn |
| D6 | KolektorSDD2: đăng ký tài khoản ViCoS | +3.3k industrial (tuỳ) |

## 5. Lộ trình số sau duyệt
v3 (18k) + pseudo 8–10k + TSP-augmentation ×2 (vân đá/gạch) + MCrack1300 1.3k + BCL/TopoDS 8–12k
≈ **38–44k đa bề mặt** — đủ số và đủ bề mặt để viết bài so sánh với 22 bài tham chiếu.
