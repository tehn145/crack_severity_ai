# DATASETS.md — Kho dữ liệu bổ sung để đạt 40k+ đa bề mặt

> Cập nhật 2026-10-29. Mục tiêu: 21k hiện tại → **40k+ đa bề mặt** (bê tông, tường, gạch
> trang trí, đá, sàn cầu, thép). Ưu tiên building domain, license nghiên cứu.

## Hiện trạng
| Kho | Số lượng | Trạng thái |
|---|---|---|
| primary (v1–v3) | 17.594 | train+val+test bất biến |
| tiled Volker/Rissbilder | 3.146 | train-only (v3) |
| pseudo-label (METU 8k + SDNET CD/CW 5.9k) | ~8–12k giữ | script đang chạy (conf ≥ 0.5) |
| hard-case vân đá | 306 | test OOD (KHÔNG train) — trừ 250 đã vào v3 train |

## 1. OmniCrack30K — 30k đa vật liệu (MỤC TIÊU LỚN NHẤT)
- CVPRW 2024 benchmark; tổng hợp 20+ dataset (9 tỷ px); vật liệu: asphalt, **ceramic**,
  concrete, **masonry**, steel…
- **KHÔNG mở công khai** (license trộn nguồn) → **ACTION: gửi email từ tài khoản trường
  UIT** tới zneb_naitsirhc@web.de, tiêu đề "Access OmniCrack30k Dataset", nêu phi thương mại.
- Thay thế tức thời: tải trực tiếp các **nguồn gốc mở** của nó (mục 2–5 dưới).

## 2. Nguồn gốc mở của OmniCrack30K (tải được ngay)
| Dataset | Nội dung | Link | Ước lượng |
|---|---|---|---|
| **BCL** | 11.000 ảnh 256×256, 50+ cây cầu | (ref trong README OmniCrack30k) | +11k |
| **TopoDS** | Building post-earthquake (kết cấu nhà!) | (ref README) | +khang |
| **UAV75** | 75 ảnh UAV 512×512 | (ref README) | nhỏ |
| **Ceramic** | gạch men — bề mặt "trang trí" | (ref README) | nhỏ |
| **AEL** | synthetic + real, 5 hệ thu | (ref README) | +vài trăm |
→ Việc: mở README https://github.com/ben-z-original/omnicrack30k mục References, lấy link
từng nguồn (đa số GitHub/Zenodo/Harvard Dataverse — curl được).

## 3. Masonry / gạch trang trí (đúng yêu cầu "bề mặt trang trí nhà cao tầng")
- **MCrack1300** — 1.300 ảnh instance segmentation 3 lớp (**bricks, broken bricks, crack**)
  — có luôn nhãn gạch cho Phase 2 Lớp B:
  - GitHub: https://github.com/zxy239/LoRA-SAM-for-damage-detection
  - Roboflow (format sẵn): https://universe.roboflow.com/uni-of-birmingham/masonry
  - Paper: arXiv:2401.15266 (Ye 2024, Adv. Eng. Informatics)
- **Zenodo Masonry** (semantic seg, lab brick walls): https://zenodo.org/records/5108846

## 4. Component (cột/dầm) — cho v5 Lớp B
- **CODEBRIM** (multi-label: crack, spalling, exposed bars, corrosion, efflorescence —
  1.590 ảnh): https://zenodo.org/records/2620293 (mở)
- **SegCODEBRIM** (segmentation masks): Zenodo, code https://github.com/achrefjaziri/SimCrack
  (một số record cần request access)

## 5. Industrial / đa bề mặt khác
- **KolektorSDD2** — 3.335 ảnh (356 defect, pixel-level), license nghiên cứu, cần đăng ký:
  https://www.vicos.si/resources/kolektorsdd2
- **Syncrack** — generator synthetic có nhiễu kiểm soát (GitHub) — sinh không giới hạn
- **S2DS** (743 đa loại khuyết tật) — ref Awesome list

## 6. Kế hoạch tích hợp về số
| Bước | Thêm vào train | Tổng ước tính |
|---|---|---|
| Hiện tại (v3) | 18.015 (+pseudo 8–12k) | 26–30k |
| + MCrack1300 + Zenodo masonry | +1.5k (gạch — bề mặt trang trí) | ~31k |
| + BCL + TopoDS + Ceramic (nguồn mở OmniCrack) | +8–12k | **40k+** |
| + OmniCrack30K (sau khi duyệt email) | +30k nếu duyệt | 60k+ |

Quy tắc tích hợp: (1) convert về YOLO polygon, (2) prefix nguồn trong tên file,
(3) test set giữ bất biến — chỉ thêm train, (4) mỗi nguồn ghi license vào file này.

## 7. Script
- `scripts/download_datasets.py` — tải các nguồn mở (masonry, CODEBRIM, Syncrack…)
- Convert: mask→polygon tái dùng `build_clean_phase1.mask_to_yolo_lines`
EOF
echo OK
## 8. MA TRẬN ĐA BỀ MẶT cho kiểm định tòa nhà (2026-10-30)

| # | Bề mặt | Hiện có | Nguồn bổ sung | Trạng thái |
|---|---|---|---|---|
| 1 | Bê tông (tường/cột/sàn) | ✅ 17.6k primary + ~8-11k pseudo | OmniCrack30K (email) | ĐẠT |
| 2 | Sàn/dầm cầu | ✅ SDNET-D 2k + Roads 3.4k | **BCL 11k cầu** (50 cây cầu) | Cần tải |
| 3 | Tường trát/sơn | △ SDNET-W + Rissbilder/Volker | **TopoDS** (building post-earthquake) | Cần tải |
| 4 | Gạch masonry/trang trí | ✅ **masonry 1.3k đã tải** + noncrack 1.4k | MCrack1300 (RoboFlow/GitHub) | ĐẠT |
| 5 | Vân đá/đá | ✅ 306 hard-case | Stone331 (ref Awesome) | ĐẠT |
| 6 | **Thép corrosion** | ❌ | **Ameli 514 ảnh** (MDPI data statement) + **VT DeepLabV3+ corrosion** (data.lib.vt.edu) | Cần tải |
| 7 | **Kính facade** | ❌ | Khan hiếm public — chỉ RoboFlow community | Hạn chế |
| 8 | **Gỗ/timber** | ❌ | **Wood Defect 43k** (dataset-ninja) + Wooden Damages (RoboFlow) | Cần tải |
| 9 | **Ceramic** | ❌ | Ceramic subset (ref OmniCrack) | Cần tải |
| 10 | Component cột/dầm | △ CODEBRIM cls (đã tải) | SegCODEBRIM masks (request Zenodo) | v5 |

**Synthetic**: Syncrack generator + copy-paste đa bề mặt (paste vết GT lên mọi nền) — bù các bề mặt thiếu GT.

### Tải ngay (tuần này)
1. **BCL / TopoDS / UAV75 / Ceramic / AEL** — mở README https://github.com/ben-z-original/omnicrack30k mục References, từng nguồn có link GitHub/Zenodo/Dataverse riêng
2. **Corrosion**: MDPI paper #9 mục Data Availability + https://data.lib.vt.edu (Virginia Tech corrosion DeepLabV3+)
3. **Wood**: https://datasetninja.com/wood-defect-detection-dataset
4. **OmniCrack30K**: email trường UIT (zneb_naitsirhc@web.de) — CHỈ user làm được

### Lộ trình số đến 40k+ (bề mặt × nguồn)
21k (v3) + pseudo 8-11k + masonry 1.3k + BCL 5-11k + TopoDS/Ceramic 2-3k + corrosion 0.5k + wood subset 3-5k + synthetic 2-3k ≈ **42-51k đa bề mặt (9 loại)** — vượt mọi bài trong sheet (lớn nhất: Khanh 11.2k, OmniCrack 30k không public).

## 9. TIÊU CHÍ CHỌN/BỔ SUNG DỮ LIỆU (chốt 2026-10-31 — mục tiêu 50-55k)

### 9.1 Tiêu chí CHỌN (đưa vào train)
| Tiêu chí | Chi tiết |
|---|---|
| Domain | Bê tông, tường, gạch/masonry, sàn-dầm cầu, thép kết cấu — building inspection |
| Nhãn | Có mask/polygon (train chính) HOẶC pseudo-label conf ≥ 0.5 từ model v1 (semi-supervised) |
| Chất lượng nhãn | Polygon khớp vết nứt thật; audit 118 nhãn thiếu đã bổ sung |
| Ảnh âm | Nhãn rỗng — bắt buộc ≥ 20-25% tổng train để chống báo giả |
| Đa bề mặt | Mỗi bề mặt ≥ 1k ảnh; bề mặt khó (vân đá, gạch) có cả positive + negative |

### 9.2 Tiêu chí BỎ/LOẠI
| Tiêu chí | Ví dụ đã loại |
|---|---|
| Domain ngoài | Mặt đường (CFD, CRACK500, GAPS384, CrackTree), point cloud 3D |
| Chỉ classification không có mask + không pseudo được | CODEBRIM 12GB image-level (đã dừng tải) |
| Patch siêu nhỏ không dùng được cho YOLO 640 | Masonry Zenodo (946 patch 3.4KB) |
| Trùng lặp | CConCrack (trùng crack_seg), ảnh MD5 trùng |

### 9.3 Lộ trình số đến 50-55k (tối nay train v4)
| Thành phần | Số ảnh | Nguồn |
|---|---|---|
| v3 train (hiện có) | 18.015 | primary + tiled + vân đá |
| Pseudo METU (xong) | ~7.7k | conf ≥ 0.5 |
| Pseudo SDNET CD/CW (đang chạy) | ~2-3k | conf ≥ 0.5 |
| **Pseudo CAP Positive (mới)** | **~8-10k** | CAP Positive 15k, conf ≥ 0.5 |
| **CAP Negative (mới)** | **+5k** | nhãn rỗng |
| Masonry MCrack1300 | +1.3k | GitHub/RoboFlow (cần tải) |
| **TỔNG v4** | **≈ 45-50k** | train 40-45k + val/test bất biến |

### 9.4 Sau v4 (nếu chỉ số tốt): mở rộng loại hư hỏng — nâng cấp đề tài
| Loại hư hỏng | Dataset nguồn | Ghi chú |
|---|---|---|
| **Bong tróc (spalling)** | CrSpEE (2.229 ảnh crack/spalling), CSSC (UAV) | Gộp lớp spalling vào Phase 1 |
| **Corrosion cầu thép** | Ameli 514 (pixel-level, BIRM/AASHTO) | Đa material: thép |
| **Efflorescence / rêu** | CODEBRIM multi-label | Classification phụ |
| **Multi-damage (5 loại)** | Cha 2018 Faster R-CNN (2.366 ảnh) | Kinh điển đa loại |
→ Mỗi loại hư hỏng mới = +1 lớp đầu ra Phase 1 + 1 quy tắc severity Phase 2 → đề tài
nâng cấp từ "crack" sang "multi-defect inspection" — đúng hướng CACAIE (hierarchical).

## 10. NGUỒN MỚI ĐÃ KHẢO SÁT (2026-10-31) — tải trực tiếp được, không cần xin phép

### 10.1 Segmentation đa bề mặt (ưu tiên cao — có mask)
| Dataset | Số ảnh | Bề mặt | Tải | Ghi chú |
|---|---|---|---|---|
| **CrackSeg9k** | 9.255 | tổng hợp 10 dataset (gồm Ceramic, Stone331, masonry) | [HuggingFace](https://huggingface.co/datasets/rimvydasrub/crackseg9k) 4.2GB parquet · [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/JCTO4P) | Chuẩn hóa nhãn sẵn; nhiều nguồn TRÙNG với ta — lọc phần mới |
| **Multi-temporal Crack** | ~1k | bê tông đa thời điểm | [Zenodo 15187675](https://zenodo.org/records/15187675) | Có tiến triển vết nứt theo thời gian — vàng cho Phase 2 |
| **MCrack1300** | 1.300 | masonry (bricks/broken/crack instance) | [GitHub zxy239](https://github.com/zxy239/LoRA-SAM-for-damage-detection) · [RoboFlow](https://universe.roboflow.com/uni-of-birmingham/masonry) | Gạch masonry — bề mặt trang trí |
| **Masonry Zenodo** | 946 patch | gạch classification | Đã tải (chỉ classification, nhỏ) | Dùng làm nền negative |
| **Masonry Zhou 2025** | instance | masonry under loading | Structures (Mendeley Data) | Tìm link trong paper |

### 10.2 Multi-defect (nâng cấp đề tài: spalling, efflorescence, corrosion)
| Dataset | Số ảnh | Loại hư hỏng | Tải |
|---|---|---|---|
| **CUHK-USR Defect-Dataset** | ~1k+ | crack, spalling, delamination, corrosion, efflorescence | [GitHub CUHK-USR-Group/Defect-Dataset](https://github.com/CUHK-USR-Group/Defect-Dataset) |
| **Benz 743** | 743 | crack, spalling, corrosion, efflorescence, vegetation | Stitch ref |
| **ConViD** | lớn | concrete defects incl. spalling | (tìm link) |
| **CODEBRIM** | 1.590 | 6 lớp multi-label | Đã tải classification (đang dừng — image-level) |
| **UAV façade (Zhao)** | 6.996 ảnh / 62k instance | crack + spalling | Zhao et al. |

### 10.3 Tiêu chí lọc khi gộp CrackSeg9k (tránh trùng)
CrackSeg9k gộp 10 dataset — ĐỐI CHIỀU loại các nguồn đã có: DeepCrack, CRACK500,
GAPS384, CrackTree200… Giữ CHỈ các nguồn MỚI: **Ceramic-Cracks, Stone331, masonry,
EPVK, EZGCrack…** — ước tính phần mới ~2-3k ảnh có mask.

### 10.4 Kế hoạch tích hợp v4 (sau khi pseudo + các nguồn trên về)
| Bước | Hành động |
|---|---|
| 1 | Convert CrackSeg9k (parquet → polygon) — lọc nguồn mới |
| 2 | Convert MCrack1300 instance → polygon (lớp crack) |
| 3 | CUHK-USR Defect → polygon (mask có sẵn) — mở lớp spalling/efflorescence |
| 4 | Gộp vào v4 + đánh giá lại 3 chỉ số vàng |
