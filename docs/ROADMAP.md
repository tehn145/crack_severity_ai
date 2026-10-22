# ROADMAP.md

## Đã xong
- Thu thập dataset công khai
- Xây pipeline download / inspect / convert
- Build được primary (image-label khớp)
- Chuẩn hóa toàn bộ nguồn (mask + txt) về YOLO polygon, build primary 18.790 ảnh + 1.353 ảnh âm, chia split 80/10/10
- Đóng gói bundle Kaggle (data.yaml + README + zip)
- Nghiên cứu hướng Phase 2 (đặc trưng vết nứt + ngữ cảnh single/multi plane)
- Khảo sát ACI 224R-01 và TCVN 9381:2012

## Đang làm
- Train Phase 1 trên Kaggle bằng bundle outputs/kaggle/phase1_primary.zip (18.790 ảnh primary + 1.353 ảnh âm)

## Tiếp theo
- Hoàn tất đánh giá Phase 1 (metrics + nhận xét false positive)
- Chốt thang mức độ nghiêm trọng
- Xây dựng dữ liệu và prototype Phase 2
- Tích hợp cascade Phase 1 → Phase 2