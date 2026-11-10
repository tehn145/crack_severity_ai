# 📑 TỔNG MỤC LỤC BÁO CÁO DỰ ÁN CRACK SEVERITY AI

Cấu trúc thư mục báo cáo chuẩn hóa theo Phase và Ngày/Phiên bản:

```
outputs/reports/
├── phase1a_crack_detection/
│   ├── evaluations/     # Báo cáo đánh giá mô hình (PDF/MD/CSV)
│   │   ├── 2026-11-09_v2.0_phase1a_uit_model_evaluation.pdf (Báo cáo chính thức ĐHQG-UIT)
│   │   ├── 2026-11-08_v1.0_phase1a_model_evaluation.pdf
│   │   └── 2026-11-09_v2.0_phase1a_test_inference_cache.csv
│   ├── datasets/        # Kiểm kê, phân tích dữ liệu & audit nứt
│   │   ├── 2026-11-09_v1.1_phase1a_bfdd_review.xlsx
│   │   ├── 2026-11-07_v1.0_phase1a_phase2_data_plan.xlsx
│   │   ├── 2026-11-07_v1.0_phase1a_image_audit.xlsx
│   │   └── 2026-11-09_v2.0_phase1a_omnicrack30k_deduplication.xlsx (Khử trùng OmniCrack30k)
│   └── legacy_logs/     # File log huấn luyện cũ
├── phase1b_multitemporal/   # Theo dõi vết nứt theo chuỗi thời gian
├── phase2a_crack_severity/  # Đánh giá cấp độ vết nứt (Micro / Minor / Severe)
├── phase2b_spalling_corrosion/ # Kiểm kê dữ liệu bong tróc bê tông
│   └── 2026-11-05_v1.0_phase2b_spalling_inventory.xlsx
├── phase3_shm_system/       # Kiến trúc hệ thống giám sát kết cấu SHM
│   └── 2026-11-06_v1.0_phase3_shm_architecture.pdf
└── archive_legacy/          # Lưu trữ lịch sử các bản nháp tháng 10/2026
```

### Quy ước đặt tên file (Naming Convention):
`YYYY-MM-DD_v<Major>.<Minor>_<phase>_<topic>.<extension>`
Ví dụ: `2026-11-09_v2.0_phase1a_omnicrack30k_deduplication.xlsx`
