# SPALLING_PHASE.md — Đánh giá Bong tróc Bê tông & Lộ cốt thép kết cấu (Phase 3)
> **Ứng dụng trọng tâm**: Hỗ trợ kiểm định an toàn chịu lực cho các tòa nhà bị đình trệ (dự án đắp chiếu, dừng thi công nhiều năm) trước khi tái khởi công xây dựng tiếp.

---

## 1. Bối cảnh kỹ thuật & Tính cấp thiết thực tế

### 1.1 Thực trạng các công trình đình trệ (Stalled / Abandoned Buildings)
Tại Việt Nam và nhiều quốc gia, có hàng loạt dự án bất động sản, cao ốc văn phòng, chung cư bị tạm dừng thi công hoặc đình trệ kéo dài (3–10 năm) do vướng mắc pháp lý, tài chính hoặc thay đổi chủ đầu tư. Khi các khối nhà đã hoàn thành phần kết cấu thô (móng, cột, dầm, sàn bê tông cốt thép) nhưng bị phơi mưa nắng ngoài trời không có mái che hoàn thiện hay lớp sơn bảo vệ:
1. **Xâm thực khí quyển & Cacbonat hóa (Carbonation)**: Khí $CO_2$ và độ ẩm thẩm thấu sâu làm giảm độ kiềm ($pH$) của bê tông từ $\sim 12.5$ xuống $<9.0$, phá hủy màng thụ động bảo vệ cốt thép.
2. **Gỉ sét trương nở thể tích cốt thép**: Cốt thép chịu lực và râu thép chờ (starter bars/dowels) bị oxy hóa rỉ sét, thể tích gỉ sắt tăng gấp $2\text{--}6$ lần thể tích thép ban đầu, tạo áp lực nở cực lớn từ bên trong lòng cấu kiện.
3. **Hiện tượng nứt dọc & Bong tróc (Delamination & Spalling)**: Áp lực trương nở làm bung vỡ lớp bê tông bảo vệ (cover concrete), dẫn đến **bong tróc mảng lớn (Spalling)** và làm **lộ cốt thép kết cấu (Exposed Rebar)** ra môi trường ngoài.
4. **Mất an toàn chịu lực**: Cốt thép lộ bị ăn mòn rỗ (pitting corrosion) làm suy giảm tiết diện chịu lực, đồng thời phá hủy lực bám dính (bond strength) giữa bê tông và cốt thép.

### 1.2 Yêu cầu bắt buộc khi tái khởi công (Resuming Construction)
Theo **Nghị định 06/2021/NĐ-CP** và **TCVN 9381:2012**, trước khi tái khởi công tiếp tục xây dựng các tầng trên hoặc hoàn thiện công trình đình trệ, chủ đầu tư và nhà thầu **bắt buộc phải thực hiện kiểm định đánh giá an toàn kết cấu**:
* Xác định các vị trí dầm, cột, nút khung bị bong tróc.
* Đo đạc diện tích bong tróc và tỷ lệ lộ cốt thép.
* Đánh giá mức độ suy giảm tiết diện thép và nứt vỡ bê tông lõi.
* Kết luận cấu kiện có đủ khả năng tiếp tục chịu tải khi thi công chồng tầng hay bắt buộc phải gia cường (chống đỡ tạm, bọc thép hình, dán sợi carbon CFRP).

$\implies$ **Hệ thống AI mở rộng thêm Phase 3 (Spalling & Exposed Rebar Assessment)** đóng vai trò công cụ kiểm định thị giác tự động hóa, cung cấp bằng chứng định lượng chính xác, minh bạch cho hội đồng thẩm định và kỹ sư tư vấn.

---

## 2. Mục tiêu kỹ thuật của Phase Spalling

1. **Phát hiện & Phân đoạn đa lớp (Multi-class Instance/Semantic Segmentation)**:
   * **Lớp 1 - Spalling**: Phân đoạn ranh giới mảng bê tông bị nứt vỡ, bong tróc, lõm sâu.
   * **Lớp 2 - Exposed Rebar**: Phát hiện và phân đoạn từng thanh cốt thép (thép chủ, thép đai) bị lộ ra ngoài.
   * **Lớp 3 - Rust Staining / Corrosion**: Phát hiện vùng ố vàng gỉ sét lan trên bề mặt bê tông (dấu hiệu cảnh báo ăn mòn ngầm).
2. **Đo lường & Định lượng hình học (Geometric Quantification)**:
   * Diện tích bong tróc thực tế ($S_{\text{spall}}$ theo $\text{cm}^2$ hoặc $\text{m}^2$ thông qua thang đo GSD).
   * Chiều dài và diện tích cốt thép bị phơi nhiễm ($L_{\text{rebar}}$, $A_{\text{rebar}}$).
   * Tỷ lệ diện tích hư hỏng so với diện tích bề mặt cấu kiện ($S_{\text{spall}} / S_{\text{member}}$).
3. **Phân cấp mức độ nguy hiểm kết cấu (Severity Grading)**:
   * Tự động xếp loại mức độ hư hỏng theo tiêu chuẩn **TCVN 9381:2012**, **ACI 562-19** và **ACI 318-19**.
   * Đưa ra khuyến nghị kỹ thuật: An toàn thi công tiếp / Sửa chữa trám vá cục bộ / Đình chỉ thi công để gia cố kết cấu.

---

## 3. Tiêu chuẩn kỹ thuật tham chiếu & Thang phân loại 4 cấp (SP0 – SP3)

### 3.1 Cơ sở tiêu chuẩn
* **TCVN 9381:2012**: Hướng dẫn đánh giá mức độ nguy hiểm của kết cấu nhà — Phân loại cấu kiện bê tông cốt thép theo tình trạng nứt, bong tróc và lộ cốt thép.
* **ACI 562-19**: Code for Assessment, Repair, and Rehabilitation of Existing Concrete Structures and Commentary.
* **ACI 318-19**: Yêu cầu về chiều dày lớp bê tông bảo vệ cốt thép công trình nhà.
* **BIRM / AASHTO**: Thang đánh giá tình trạng ăn mòn cốt thép và hư hỏng kết cấu.

### 3.2 Thang đánh giá mức độ nghiêm trọng bong tróc (Spalling Severity Scale)

| Cấp độ | Tên gọi | Tiêu chí nhận diện thị giác | Ý nghĩa an toàn chịu lực | Khuyến nghị cho công trình tái khởi công |
|:---:|---|---|---|---|
| **SP0** | **Bề mặt (Surface Flaking / Delamination)** | • Vết bong tróc rất nông ($<10\text{mm}$).<br>• Chưa chạm tới cốt thép.<br>• Chủ yếu bong lớp sơn lót hoặc vữa trát mỏng. | **An toàn chịu lực**.<br>Chưa ảnh hưởng đến kết cấu bê tông cốt thép bên trong. | Cho phép tiếp tục thi công. Chỉ cần cạo sạch lớp bong tróc và vệ sinh bề mặt trước khi hoàn thiện. |
| **SP1** | **Bong tróc bê tông bảo vệ (Minor Concrete Spalling)** | • Vỡ mảng bê tông bảo vệ sâu $10\text{--}25\text{mm}$.<br>• Chưa lộ thanh thép chịu lực chính.<br>• Diện tích vỡ cục bộ nhỏ ($<0.05\text{m}^2$). | **Suy giảm độ bền lâu (Durability Risk)**.<br>Nước và khí $CO_2$ bắt đầu tiếp cận gần cốt thép. | Bắt buộc trám bù bằng vữa sửa chữa cường độ cao không co ngót (non-shrink grout) trước khi tải trọng thi công tăng lên. |
| **SP2** | **Lộ cốt thép kết cấu (Severe Spalling / Exposed Rebar)** | • Vỡ hoàn toàn lớp bê tông bảo vệ, **lộ rõ thanh thép chịu lực**.<br>• Thép có dấu hiệu gỉ vàng bề mặt nhưng chưa bong vảy lớn.<br>• Giảm tiết diện thép ước tính $<5\%$. | **Nguy hiểm trung bình (Moderate Structural Risk)**.<br>Lực bám dính bê tông - cốt thép bị suy giảm tại vùng lộ. | **Chưa được đổ thêm tải**. Phải đánh gỉ cốt thép đến cấp Sa 2.0, quét sơn lót chống gỉ gốc epoxy/kẽm, và trám vữa polymer biến tính kết dính cao. |
| **SP3** | **Nguy hại kết cấu cấp bách (Critical / Rebar Section Loss)** | • Lộ cốt thép diện rộng trên cấu kiện chịu lực chính (cột, chân vách, dầm nhịp lớn).<br>• Cốt thép bị gỉ phồng rộp, bong vảy dày, giảm đường kính $>10\text{--}15\%$.<br>• Biến dạng đứt gãy đai thép hoặc bê tông lõi bị nứt vỡ xuyên tâm. | **MẤT AN TOÀN CHỊU LỰC (Critical Failure Risk)**.<br>Nguy cơ sụp đổ cục bộ hoặc nứt gãy khi tiếp tục chất tải tầng trên. | **CẤM TÁI KHỞI CÔNG NGAY LẬP TỨC**. Bắt buộc lắp hệ thống cột chống đỡ tạm (shoring), kiểm định siêu âm/khoan lõi chuyên sâu và lập phương án gia cường kết cấu (bọc thép hình jacket hoặc dán tấm sợi carbon CFRP). |

---

## 4. Kiến trúc Pipeline tích hợp (Cascade: Crack + Spalling)

```
                              Ảnh chụp cấu kiện 2D
                                       │
                                       ▼
                     ┌───────────────────────────────────┐
                     │     DETECTION & SEGMENTATION      │
                     │  (YOLOv8x-seg / Multi-class Head) │
                     └─────────────────┬─────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
       [Nhánh Vết Nứt - Phase 1]                     [Nhánh Bong Tróc - Phase 3]
                │                                             │
                ▼                                             ▼
       Mask Vết Nứt Polygon                           Mask Spalling & Exposed Rebar
                │                                             │
                ▼                                             ▼
   Phase 2: Severity Vết Nứt                     Phase 3: Severity Bong Tróc & Cốt Thép
   • Bề rộng max (Distance Transform)            • Diện tích Spall ($S_{\text{spall}} = A \times \text{GSD}^2$)
   • Chiều dài, độ tương phản (độ sâu)           • Diện tích & Chiều dài thép lộ ($L_{\text{rebar}}$)
   • Thang ACI 224R (L0 - L3)                    • Tỷ lệ che phủ trên cấu kiện ($S_{\text{spall}} / S_{\text{col}}$)
                │                                • Thang TCVN 9381 (SP0 - SP3)
                │                                             │
                └──────────────────────┬──────────────────────┘
                                       │
                                       ▼
                   ┌───────────────────────────────────────┐
                   │   BÁO CÁO AN TOÀN TÁI KHỞI CÔNG       │
                   │   (Comprehensive Structural Safety)   │
                   │  • Điểm tổng hợp an toàn cấu kiện     │
                   │  • Kết luận: Đạt / Cần xử lý / Cấm đổ │
                   │  • Bản đồ trực quan vùng nguy hiểm    │
                   └───────────────────────────────────────┘
```

---

## 5. Danh mục Dataset huấn luyện cho Phase Spalling

Để triển khai Phase 3 mà không cần tự chụp và gán nhãn thủ công từ đầu, hệ thống sẽ tận dụng các bộ dữ liệu công khai hàng đầu chuyên về bong tróc và lộ cốt thép:

| STT | Dataset | Số lượng | Nhãn | Loại bề mặt & Hư hỏng | Nguồn & Link |
|:---:|---|:---:|---|---|---|
| 1 | **CrSpEE** (2021) | 2.229 ảnh | Pixel mask | Vết nứt (Crack) và Bong tróc (Spalling) trên kết cấu bê tông | Benchmark quốc tế chuyên đề Crack & Spalling |
| 2 | **SegCODEBRIM** (2024) | 420 ảnh ($1500\times 844$) | Polygon mask đa lớp | **Crack, Spalling, Exposed Bars, Corrosion, Efflorescence** trên cầu bê tông | [Zenodo / SimCrack](https://github.com/achrefjaziri/SimCrack) |
| 3 | **CODEBRIM** (2019) | 1.590 ảnh | Bounding box / Image-level | 6 lớp khuyết tật kết cấu bê tông cốt thép | [Zenodo 2620293](https://zenodo.org/records/2620293) |
| 4 | **CUHK-USR Defect-Dataset** | ~1.200 ảnh | Pixel mask | Crack, spalling, delamination, corrosion rỉ thép | [GitHub CUHK-USR-Group](https://github.com/CUHK-USR-Group/Defect-Dataset) |
| 5 | **UAV Façade Dataset** (Zhao 2023) | 6.996 ảnh | Bounding box & Mask (62k instances) | Nứt tường và bong tróc mặt đứng tòa nhà cao tầng | Zhao et al. (Khảo sát flycam) |
| 6 | **S2DS (Structural Defect)** | 743 ảnh | Bounding box / Mask | Đa khuyết tật: bê tông bong tróc, lộ cốt thép, rỉ sét | Benz et al. 2022 |
| 7 | **Roboflow Concrete Spalling** | ~1.500 ảnh | Polygon mask | Chuyên sâu về bê tông bong tróc và lộ cốt thép | Roboflow Universe Open Projects |

---

## 6. Lộ trình triển khai Phase Spalling

1. **Giai đoạn 1 — Thu thập & Thống nhất cấu trúc dữ liệu**:
   * Tải và chuyển đổi nhãn các bộ `CrSpEE`, `SegCODEBRIM`, `CUHK-USR Defect` về định dạng YOLO segmentation.
   * Gán quy ước ID lớp:
     * `class 0: crack`
     * `class 1: spalling`
     * `class 2: exposed_rebar`
2. **Giai đoạn 2 — Huấn luyện mô hình cơ sở**:
   * Huấn luyện mô hình YOLOv8-seg đa lớp (Multi-class defect model).
   * Đánh giá mAP50 và mAP50-95 riêng cho từng lớp khuyết tật.
3. **Giai đoạn 3 — Xây dựng Module trích xuất đặc trưng & Phân loại SP0–SP3**:
   * Viết module `app/spalling_features.py`: Tính toán diện tích vùng bong tróc, xác định tỷ lệ diện tích cốt thép lộ, trích xuất độ đậm gỉ sét (corrosion index).
   * Viết module `app/spalling_severity.py`: Phân cấp SP0–SP3 theo các quy tắc kiểm định của TCVN 9381:2012 và ACI 562-19.
4. **Giai đoạn 4 — Tích hợp hệ sinh thái Web App & Báo cáo kiểm định**:
   * Cập nhật giao diện Wizard kiểm tra trong `app/`: Hiển thị đồng thời overlay vết nứt (màu đỏ) và vùng bong tróc / cốt thép lộ (màu cam/vàng).
   * Bổ sung mục "Đánh giá an toàn tái khởi công công trình" vào Báo cáo in PDF (kèm khuyến nghị kỹ thuật: Trát vá / Chống đỡ tạm / Gia cố kết cấu).
