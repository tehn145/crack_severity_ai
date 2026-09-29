# CONVENTIONS.md

## Code
- Python 3.10+
- Ưu tiên dễ đọc, có type hint khi hợp lý
- Mỗi script phải chạy được từ thư mục gốc dự án
- Có log rõ ràng (print hoặc logging)

## Dữ liệu
- Không tự ý xóa hoặc ghi đè primary đã sạch
- Mọi script xử lý data phải hỗ trợ chạy lại (idempotent nếu có thể)
- Label Phase 1: YOLO format, class 0 = crack

## Đặt tên
- Script: snake_case
- Thư mục dữ liệu: giữ nguyên cấu trúc đã thống nhất
- Weights: weights/phase1/best.pt , weights/phase2/...

## Git
- Không commit dữ liệu thô lớn
- Không commit file weights nặng (trừ khi được yêu cầu rõ)