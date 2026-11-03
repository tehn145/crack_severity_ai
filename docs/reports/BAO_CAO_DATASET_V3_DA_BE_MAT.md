# BÁO CÁO TỔNG HỢP & PHÂN LOẠI DATASET ĐA BỀ MẶT (PHIÊN BẢN V3)
> **Ngày cập nhật**: 2026-11-03
> **Trạng thái**: Đã hoàn tất kiểm toán toàn bộ kho dữ liệu `data/raw/public` (18 bộ lớn, 45+ bộ nhỏ).
> **File Excel chi tiết phục vụ phê duyệt**: [`docs/dataset_v3_multi_surface_inventory.xlsx`](file:///d:/crack_severity_ai/docs/dataset_v3_multi_surface_inventory.xlsx)

---

## 1. Mục tiêu mở rộng & 4 Lĩnh vực kiểm định trọng tâm

Hệ thống được nâng cấp toàn diện từ bài toán nhận diện nứt bê tông đơn lẻ thành **Nền tảng kiểm định thị giác đa bề mặt**, bao phủ 4 lĩnh vực thực tế then chốt:

```
                            NỀN TẢNG KIỂM ĐỊNH THỊ GIÁC ĐA BỀ MẶT (V3)
                                               │
       ┌───────────────────────┬───────────────┴───────────────┬───────────────────────┐
       ▼                       ▼                               ▼                       ▼
1. CAO TẦNG KHÓ TIẾP CẬN   2. TÒA NHÀ ĐÌNH TRỆ / HOANG    3. CÔNG TRÌNH LỊCH SỬ / DI TÍCH  4. HẠ TẦNG GIAO THÔNG
• Chụp bằng flycam/UAV     • Công trình dở dang tái khởi  • Duy tu bảo tồn di sản cổ      • Mặt đường nhựa asphalt
• Tường ngoài façade       • Bong tróc bê tông (Spalling) • Tường thành cổ, vôi vữa cổ    • Mặt đường bê tông
• Ban công, kính mặt dựng  • Lộ cốt thép rỉ sét (Phase 3) • Đảm bảo an toàn khách tham quan • Sàn dầm cầu vượt
```

1. **Kiểm định các công trình cao tầng khó tiếp cận**: Sử dụng hình ảnh chụp từ flycam/drone khảo sát mặt đứng tòa nhà (*façade*), phát hiện nứt tường ngoài, bong tróc lớp hoàn thiện và nứt vỡ kính kiến trúc ở các vị trí nguy hiểm trên cao.
2. **Kiểm định các tòa nhà hoang, công trình bị dừng thi công để tái khởi công lại**: Đánh giá an toàn chịu lực cho các dự án đắp chiếu nhiều năm (theo **Nghị định 06/2021/NĐ-CP, TCVN 9381:2012, ACI 562-19**); phát hiện nứt kết cấu, **bong tróc bê tông (Spalling)** và **lộ cốt thép chịu lực bị gỉ sét (Phase 3)** để quyết định cho phép thi công tiếp hay bắt buộc gia cố kết cấu.
3. **Kiểm định các công trình lịch sử để duy tu bảo dưỡng và đảm bảo an toàn cho du khách tham quan**: Khảo sát hiện trạng nứt vỡ, phong hóa rêu mốc ẩm ướt trên các di tích kiến trúc cổ (như pháo đài Darbhanga Fort, tường gạch cổ, vách đá vôi), bảo tồn nguyên vẹn giá trị di sản và ngăn chặn nguy cơ đổ sập mất an toàn cho du khách.
4. **Kiểm định hạ tầng giao thông đường và cầu**: Bổ sung đầy đủ nhóm mặt đường nhựa (*asphalt*), đường bê tông xi măng, khe co giãn và bản mặt cầu.

---

## 2. Bảng tổng hợp các loại bề mặt vết nứt hiện có trong hệ thống

Kho dữ liệu hiện đã bao phủ **8 nhóm bề mặt kết cấu công trình**:

| STT | Loại bề mặt | Đặc điểm nhận diện & Thách thức | Dataset tiêu biểu | Số lượng ước tính |
|:---:|---|---|---|:---:|
| 1 | **Bê tông kết cấu** | Nền xám, vết nứt chân chim, nứt chịu lực dầm/cột/sàn | Ultralytics, Volker, Rissbilder, METU | ~55.000+ ảnh |
| 2 | **Mặt đường (Pavement)** | Mặt đường nhựa asphalt, đường bê tông, vạch sơn, khe co giãn | 3DCrack, CRACK500, GAPS384, Roads & Bridges | ~40.000+ ảnh |
| 3 | **Tường sơn & Vữa trát** | Lớp sơn phủ bong tróc (*peeling*), nứt chân chim mờ | DETR Crack, BD3, Wall Crack Plaster | ~5.500+ ảnh |
| 4 | **Tường gạch xây (Masonry)** | Nứt xiên, nứt bậc thang (*stairstep*), nhiễu ron mạch vữa | Darbhanga Fort, DETR Crack, Masonry Zenodo | ~6.500+ ảnh |
| 5 | **Mặt ngoài công trình (Façade)** | Chụp flycam drone góc nghiêng, ánh sáng chói, ban công, kính | BFDD Façade Drone, BD3, Façade subsets | ~5.000+ ảnh |
| 6 | **Công trình lịch sử / Di tích cổ** | Tường thành cổ, gạch nung cổ, vữa tam hợp, rêu mốc ẩm ướt | Darbhanga Fort, Historical Building Cracks | ~8.155 ảnh |
| 7 | **Ngói / Gạch men / Gốm sứ** | Bề mặt nhẵn tráng men, phản xạ gương, vết nứt sắc khúc xạ | Ceramics Defects, Ceramic Tiles subset | ~9.020 ảnh |
| 8 | **Đá tự nhiên / Vân đá** | Vân đá granite, đá dăm lồi lõm (Hard-cases chống báo giả) | Sylvie, Forest, Stone subsets | ~650 ảnh |

---

## 3. Báo cáo Tình trạng các bộ Dataset (Kiểm toán chất lượng & Tỷ lệ OK/Fail)

Tổng cộng đã kiểm toán **18 bộ dữ liệu lớn với hơn 45 bộ nhỏ** trong `data/raw/public`:

| STT | Bộ Dataset lớn | Bộ nhỏ tiêu biểu | Bề mặt | Tổng ảnh | Số ảnh OK | Số ảnh Fail | Tỷ lệ OK | Định dạng nhãn | Tình trạng kỹ thuật |
|:---:|---|---|---|:---:|:---:|:---:|:---:|---|---|
| 1 | **CrackSeg9k** | CRACK500, Rissbilder, noncrack, DeepCrack, Ceramic... (14 bộ nhỏ) | Đa bề mặt: đường, tường, gạch, ngói | 9.159 | 9.159 | 0 | 100% | Binary Mask | **HOÀN HẢO**: 100% ảnh có mask chuẩn pixel |
| 2 | **BFDD Façade** | Dataset_1x (Drone) | Mặt ngoài cao tầng | 838 | 838 | 0 | 100% | Semantic Mask | **HOÀN HẢO**: 100% ảnh drone có mask semantic |
| 3 | **Darbhanga Fort** | train, val, test | Di tích lịch sử | 4.259 | 4.046 | 213 (test) | 95.0% | YOLO BBox / Neg | **RẤT TỐT**: 3.843 ảnh có bbox, 203 ảnh âm |
| 4 | **DETR Crack** | train, valid, test | Tường sơn, gạch, ẩm mốc | 2.950 | 2.950 | 0 | 100% | YOLO BBox (5 cls) | **HOÀN HẢO**: 100% có nhãn nứt, rêu, tróc sơn |
| 5 | **Historical Building** | crack, non-crack | Di tích lịch sử | 3.896 | 3.896 | 0 | 100% | Classification | **TỐT**: 3.139 ảnh âm di tích chống báo giả |
| 6 | **Ceramics Defect** | amostra, amostra_proc | Ngói, gạch men | 8.920 | 8.920 | 0 | 100% | Classification | **TỐT**: Mẫu nứt ngói và ngói sạch |
| 7 | **BD3 Defect** | major/minor crack, spalling, peeling... | Mặt ngoài, đình trệ | 3.965 | 3.965 | 0 | 100% | Classification | **QUÝ GIÁ**: 500 spalling (Phase 3), 1.2k nứt |
| 8 | **Wall Crack Earthquake** | brick, plaster, concrete | Tường gạch, vữa | 526 | 526 | 0 | 100% | CSV Metadata | **TỐT**: Có nhãn loại vật liệu tường gạch/sơn |
| 9 | **3DCrack_v1** | Train, Val, Test | Mặt đường 3D | 1.634 | 1.634 | 0 | 100% | Binary Mask | **HOÀN HẢO**: Chuẩn SOTA Georgia Tech |
| 10 | **Khanh11k** | Rissbilder, CRACK500, Volker, DeepCrack... (11 bộ nhỏ) | Đa bề mặt | 11.298 | 11.298 | 0 | 100% | Binary Mask | **HOÀN HẢO**: 11.298 ảnh mask chuẩn |
| 11 | **DeepCrack (độc lập)**| train, test | Bê tông, đường | 537 | 537 | 0 | 100% | Binary Mask | **HOÀN HẢO**: 537 cặp ảnh mask |
| 12 | **Roads & Bridges** | train, valid, test | Mặt đường, sàn cầu | 3.458 | 3.458 | 0 | 100% | YOLO Polygon | **HOÀN HẢO**: 3.458 polygon chuẩn Ultralytics |
| 13 | **Ultralytics_CrackSeg**| train, val, test | Bê tông kết cấu | 4.029 | 4.029 | 0 | 100% | YOLO Polygon | **HOÀN HẢO**: 4.029 polygon chuẩn |
| 14 | **Masonry Zenodo** | real/0, real/1 | Tường gạch xây | 946 | 946 | 0 | 100% | Zip Classification | **TỐT**: Gạch phòng lab và ngoài trời |
| 15 | **METU** | Negative, Positive | Bê tông | 40.000 | 40.000 | 0 | 100% | Patch 227x227 | 20k ảnh âm sạch; 7.7k pseudo-label |
| 16 | **SDNET2018** | Decks, Pavements, Walls | Cầu, đường, tường | 56.092 | 56.092 | 0 | 100% | Patch 256x256 | Kho ảnh âm cực lớn (~47k) chống báo giả |
| 17 | **Concrete & Pavement** | Negative, Positive | Bê tông, đường | 30.000 | 30.000 | 0 | 100% | Patch 227x227 | 15k ảnh âm nền |
| 18 | **CConCrack** | Train, Test | Bê tông, đường | 10.995 | 10.995 | 0 | 100% | Binary Mask | Bộ gộp trùng Khanh11k |

---

## 4. Chiến lược Tiền xử lý Ảnh (Image Preprocessing) Nâng cao Độ chính xác

Dựa trên đặc thù của từng bề mặt mới (ngói tráng men bóng, tường thành cổ ẩm mốc, tường sơn tróc), hệ thống tích hợp quy trình tiền xử lý 5 bước:

```
[Ảnh Đầu Vào Đa Bề Mặt]
          │
          ├─► 1. Chuẩn hóa không gian màu CIE-Lab (Kênh L): Khử phản quang chói trên ngói/gạch men
          │
          ├─► 2. Cân bằng tương phản cục bộ CLAHE (clip=2.0, tile=8x8): Làm rõ nứt mờ trên tường vôi/sơn
          │
          ├─► 3. Lọc bảo toàn biên Bilateral Filter: Khử hạt cát thô trên gạch cổ mà không làm mờ nứt
          │
          ├─► 4. Hard-Negative Mining tích hợp: Đưa 3.139 ảnh âm di sản + 800 ngói sạch vào train
          │
          └─► 5. Tiled Training 640px ở độ phân giải gốc: Giữ nguyên vết nứt siêu mảnh 1-2px
```

1. **Khử phản xạ gương trên Ngói & Gạch men**: Bề mặt gạch men/ngói tráng men thường bị lóe sáng dưới ánh đèn hoặc mặt trời. Chuẩn hóa kênh độ sáng $L$ trong hệ màu CIE-Lab giúp ổn định vùng bóng chói.
2. **Tăng cường tương phản nứt chân chim trên Tường sơn (CLAHE)**: Vết nứt trên tường sơn trắng/xám thường rất mờ. CLAHE cục bộ giúp làm đậm rãnh nứt mà không làm vỡ hạt ảnh.
3. **Chống nhiễu ron mạch vữa trên Công trình cổ & Di tích**: Áp dụng Bilateral filtering và đưa tập ảnh âm di tích (Darbhanga Fort, Historical Building) vào train để mô hình phân biệt rõ ràng: đường ron vữa thẳng có trật tự $\neq$ rãnh nứt ngoằn ngoèo tự nhiên.
4. **Tiled Training & SAHI Inference**: Áp dụng cắt tile $640\times 640$ giữ nguyên độ phân giải cho các ảnh flycam độ phân giải cực cao (4K-8K) của BFDD và công trình cao tầng.

---

## 5. Kết luận & Đề xuất hành động

* **Dữ liệu đã sẵn sàng**: File Excel tổng hợp [`docs/dataset_v3_multi_surface_inventory.xlsx`](file:///d:/crack_severity_ai/docs/dataset_v3_multi_surface_inventory.xlsx) đã lập đầy đủ với hơn 48.000 dòng chi tiết từng ảnh (kèm số vết nứt, loại bề mặt, tên ảnh, tên mask, tên label) và bảng tổng kết cho từng bộ dataset.
* **Kính gửi bạn xem xét và phê duyệt file Excel**:
  1. Duyệt cấu trúc và cách gán loại bề mặt của các bộ dữ liệu.
  2. Sau khi bạn duyệt xong, tôi sẽ bắt tay vào viết script converter để chuẩn hóa toàn bộ các bộ này thành tập dữ liệu chuẩn YOLO polygon cho đợt train v3.
