# severity_definition.md — Đề xuất thang mức độ nghiêm trọng vết nứt (Phase 2)

> TRẠNG THÁI: **BẢN ĐỀ XUẤT — chờ team chốt**. Chưa hard-code vào code (quy tắc AGENTS.md).
> Tham chiếu: ACI 224R-01 (bảng bề rộng nứt chấp nhận được), TCVN 9381:2012 (quy trình
> quản lý, duy tu, bảo trì công trình), kết hợp đặc trưng Lớp A/Lớp B trong ARCHITECTURE.md.

## 1. Cơ sở khoa học

**ACI 224R-01 — bề rộng vết nứt "hợp lý" theo điều kiện phơi nhiễm:**

| Điều kiện phơi nhiễm | Bề rộng nứt tham chiếu |
|---|---|
| Không khí khô | 0.41 mm |
| Độ ẩm cao / không khí ẩm | 0.30 mm |
| Tiếp xúc đất | 0.30 mm |
| Nước biển / nước bắn | 0.15 mm |
| Công trình chứa nước (chống thấm) | 0.10 mm |

**TCVN 9381:2012**: yêu cầu kiểm tra, phân loại hư hỏng và lập kế hoạch duy tu/bảo trì
theo định kỳ; vết nứt là một trong các hư hỏng phải theo dõi và đánh giá mức độ.

## 2. Thang 4 mức đề xuất (bê tông cốt thép — công trình nhà cao tầng)

| Level | Tên | Bề rộng w | Đặc điểm | Hành động đề xuất |
|---|---|---|---|---|
| 0 | Hairline (nứt tóc) | w < 0.1 mm | Vô hại, thường do co ngót | Theo dõi, ghi nhận |
| 1 | Minor (nhẹ) | 0.1 ≤ w < 0.3 mm | Ảnh hưởng thẩm mỹ/độ bền bề mặt nhẹ | Theo dõi định kỳ |
| 2 | Moderate (trung bình) | 0.3 ≤ w < 1.0 mm | Vượt ngưỡng phơi nhiễm phổ biến | Đánh giá chi tiết, lên kế hoạch xử lý |
| 3 | Severe (nghiêm trọng) | w ≥ 1.0 mm, hoặc nứt xuyên cấu kiện, hoặc tiến triển | Nguy cơ ảnh hưởng kết cấu/nước | Kiểm tra kết cấu ngay, xử lý khẩn |

Ghi chú: ngưỡng 0.3 mm nằm giữa "không khí khô 0.41" và "môi trường ẩm 0.30" của ACI —
chọn giá trị bảo thủ cho môi trường Việt Nam (ẩm). Team có thể chỉnh theo đối tượng công trình.

## 3. Từ đặc trưng pixel → mm (bắt buộc phải có để dùng thang trên)

Phase 2 cần **thang đo (GSD: mm/pixel)**:
- Cách đúng: `GSD = Kích thước vật chuẩn (mm) / số pixel của nó` — đặt thước/ruler hoặc
  dùng khoảng cách chụp + thông số camera (khoảng cách d × FOV).
- App đã lưu đặc trưng px (length/width/area). Bổ sung trường `gsd_mm_per_px` vào hồ sơ;
  khi thiếu → hiển thị severity **tương đối** (theo bề rộng tương đối và mật độ) kèm cảnh báo.

## 4. Quy tắc quyết định (skeleton — Phase 2 tiêu thụ)

```
inputs: Lớp A (width_px → width_mm = width_px × gsd),
        Lớp B (single/multi plane — tín hiệu hỗ trợ),
        tiến triển (nếu có ảnh lần trước tại cùng vị trí)

nếu nứt xuyên plane hoặc w ≥ 1.0mm            → Level 3
nếu 0.3 ≤ w < 1.0                              → Level 2
nếu 0.1 ≤ w < 0.3                              → Level 1
nếu w < 0.1                                    → Level 0
+ điều chỉnh +1 mức nếu: multi_plane, độ dày phát triển, mật độ nứt cao (branching)
```

## 5. Việc cần chốt trước khi code

1. Chốt thang 4 mức và ngưỡng (bảng mục 2) — có giữ 0.41mm cho môi trường khô?
2. Nguồn dữ liệu huấn luyện/kiểm chứng Level: gán nhãn tay ~200–500 vết có mm thực đo
   (ảnh có thước tham chiếu), hoặc rule-based trước (không cần train).
3. Ưu tiên giai đoạn 1: **rule-based** (dùng thang trên, không train) → demo được ngay;
   giai đoạn 2: học thống kê nếu có dữ liệu mm thực đo.
