# ROADMAP.md

## Đã xong
- Thu thập dataset công khai
- Xây pipeline download / inspect / convert
- Build được primary (image-label khớp)
- Chuẩn hóa toàn bộ nguồn (mask + txt) về YOLO polygon thuần, build primary 14.594 ảnh + 1.353 ảnh âm, chia split 80/10/10
- Đóng gói bundle Kaggle (data.yaml + README + zip)
- Train Phase 1 v1: YOLOv8s-seg, 100 epochs, imgsz 640, Kaggle T4 → weights/phase1/best.pt
  - Test set (1.633 ảnh / 3.532 instance): Box mAP50 = 0.599, mAP50-95 = 0.455; Mask mAP50 = 0.488, mAP50-95 = 0.145; Box P = 0.823, R = 0.565
- Chẩn đoán v1 (scripts/evaluate_phase1.py): mức ảnh 0.999 ĐẠT kỳ vọng 0.95; ảnh âm báo nhầm chỉ 2.2%; instance P/R/F1 = 0.80/0.56/0.66; 75.5% vết bỏ sót là vết nhỏ <32px; yếu nhất: Volker (R=0.34), Rissbilder (R=0.41)
- App serving demo (app/): FastAPI + SQLite + UI kỹ sư kiểm định, Docker, CI/CD GitHub Actions → HF Spaces (docs/DEVOPS.md); pytest 8/8; CPU warm ~160-200ms/ảnh
- Nghiên cứu hướng Phase 2 (đặc trưng vết nứt + ngữ cảnh single/multi plane)
- Khảo sát ACI 224R-01 và TCVN 9381:2012

## Đang làm
- Phase 1 v2: train lại Kaggle T4x2, imgsz 1280, multi_scale 0.5 (fix 75% FN vết nhỏ, thu hẹp gap 3DCrack vs SOTA) → so lại scripts/compare_with_sota.py
- Phase 1 v3 (sau v2): pseudo-label mở rộng dữ liệu (METU/SDNET positive, conf≥0.5) khi image-level vẫn ≥0.99
- Phase 2: chốt thang mức độ nghiêm trọng — bản đề xuất 4 mức theo ACI 224R-01/TCVN 9381 ở docs/severity_definition.md; giai đoạn 1 rule-based (GSD mm/px), cắm vào cột severity của app

## Tiếp theo
- Hoàn tất đánh giá Phase 1 (metrics + nhận xét false positive)
- Chốt thang mức độ nghiêm trọng
- Xây dựng dữ liệu và prototype Phase 2
- Tích hợp cascade Phase 1 → Phase 2