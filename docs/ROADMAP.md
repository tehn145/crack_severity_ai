# ROADMAP.md

## Đã xong
- Thu thập dataset công khai
- Xây pipeline download / inspect / convert
- Build được primary (image-label khớp)
- Nghiên cứu hướng Phase 2 (đặc trưng vết nứt + ngữ cảnh single/multi plane)
- Khảo sát ACI 224R-01 và TCVN 9381:2012

## Đang làm
- Rà soát và làm sạch dữ liệu sau khi merge (~66k ảnh)
- Chuẩn bị / đang train Phase 1 trên primary

## Tiếp theo
- Hoàn tất đánh giá Phase 1 (metrics + nhận xét false positive)
- Chốt thang mức độ nghiêm trọng
- Xây dựng dữ liệu và prototype Phase 2
- Tích hợp cascade Phase 1 → Phase 2