"""
Script sắp xếp và chuẩn hóa thư mục outputs/reports
Theo từng Phase (1a, 1b, 2a, 2b, 3) và phiên bản ngày tháng (YYYY-MM-DD_vX.Y_...)
"""
import os, sys, shutil
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT_REPORTS = Path(r"D:\crack_severity_ai\outputs\reports")

# Cấu trúc thư mục chuẩn hóa
DIRS = {
    "p1a_eval": ROOT_REPORTS / "phase1a_crack_detection" / "evaluations",
    "p1a_data": ROOT_REPORTS / "phase1a_crack_detection" / "datasets",
    "p1a_logs": ROOT_REPORTS / "phase1a_crack_detection" / "legacy_logs",
    "p1b":      ROOT_REPORTS / "phase1b_multitemporal",
    "p2a":      ROOT_REPORTS / "phase2a_crack_severity",
    "p2b":      ROOT_REPORTS / "phase2b_spalling_corrosion",
    "p3":       ROOT_REPORTS / "phase3_shm_system",
    "archive":  ROOT_REPORTS / "archive_legacy",
}

for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

print("=" * 70, flush=True)
print("📁 BẮT ĐẦU SẮP XẾP VÀ CHUẨN HÓA THƯ MỤC OUTPUTS/REPORTS", flush=True)
print("=" * 70, flush=True)

# Bản đồ ánh xạ các file quan trọng sang tên chuẩn hóa có ngày và version
MAPPINGS = {
    # ── Phase 1A Evaluations (Đánh giá mô hình) ──
    "UIT_Phase1A_Model_Evaluation_v2.pdf": (
        DIRS["p1a_eval"], "2026-11-09_v2.0_phase1a_uit_model_evaluation.pdf"
    ),
    "phase1a_model_evaluation_report.pdf": (
        DIRS["p1a_eval"], "2026-11-08_v1.0_phase1a_model_evaluation.pdf"
    ),
    "inference_cache_v2.csv": (
        DIRS["p1a_eval"], "2026-11-09_v2.0_phase1a_test_inference_cache.csv"
    ),

    # ── Phase 1A Datasets (Kiểm duyệt dữ liệu & Audit) ──
    "BFDD_Dataset_RGB_Kiem_Duyet_Nut.xlsx": (
        DIRS["p1a_data"], "2026-11-09_v1.1_phase1a_bfdd_review.xlsx"
    ),
    "Ke_Hoach_Du_Lieu_Phase1A_va_Phase2_Chi_Tiet.xlsx": (
        DIRS["p1a_data"], "2026-11-07_v1.0_phase1a_phase2_data_plan.xlsx"
    ),
    "Kiem_Toan_Chi_Tiet_Tung_Anh_Phase1A_va_Phase2.xlsx": (
        DIRS["p1a_data"], "2026-11-07_v1.0_phase1a_image_audit.xlsx"
    ),
    "dataset_v3_multi_surface_inventory.xlsx": (
        DIRS["p1a_data"], "2026-11-04_v1.0_phase1a_v3_surface_inventory.xlsx"
    ),
    "dataset_v3_inventory_updated.xlsx": (
        DIRS["p1a_data"], "2026-11-04_v1.1_phase1a_v3_inventory_updated.xlsx"
    ),

    # ── Phase 2B Spalling (Bong tróc bê tông) ──
    "dataset_phase2_spalling_inventory.xlsx": (
        DIRS["p2b"], "2026-11-05_v1.0_phase2b_spalling_inventory.xlsx"
    ),

    # ── Phase 3 SHM System ──
    "Kien_Truc_Phase_3_He_Thong_Giam_Dinh_Ket_Cau.pdf": (
        DIRS["p3"], "2026-11-06_v1.0_phase3_shm_architecture.pdf"
    ),
}

moved_count = 0
for src_name, (target_dir, target_name) in MAPPINGS.items():
    src_file = ROOT_REPORTS / src_name
    if src_file.exists():
        target_file = target_dir / target_name
        shutil.move(str(src_file), str(target_file))
        print(f"✅ Đã chuyển: {src_name} -> {target_file.relative_to(ROOT_REPORTS)}", flush=True)
        moved_count += 1

# Di chuyển toàn bộ các file log, test và báo cáo cũ (tháng 10/2026) vào archive_legacy hoặc legacy_logs
for item in ROOT_REPORTS.iterdir():
    if item.is_dir():
        continue
    name = item.name
    
    # Phân loại
    if name.endswith(".log"):
        dest = DIRS["p1a_logs"] / name
        shutil.move(str(item), str(dest))
    elif any(kw in name for kw in ["build_clean_phase1", "hard_cases_", "improve_v2", "pseudo_label", "validate_measurements", "compare_sota", "scan_data", "train_report"]):
        dest = DIRS["archive"] / name
        shutil.move(str(item), str(dest))
    elif name.startswith("evaluate_phase1_"):
        dest = DIRS["p1a_eval"] / name
        shutil.move(str(item), str(dest))
    else:
        # Nếu còn file thừa khác, đưa vào archive_legacy
        dest = DIRS["archive"] / name
        shutil.move(str(item), str(dest))

print(f"\nĐã sắp xếp xong toàn bộ các file.", flush=True)

# Tạo file README.md tổng mục lục
readme_content = """# 📑 TỔNG MỤC LỤC BÁO CÁO DỰ ÁN CRACK SEVERITY AI

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
"""

(ROOT_REPORTS / "README.md").write_text(readme_content, encoding="utf-8")
print(f"✅ Đã tạo mục lục README.md tại: {ROOT_REPORTS / 'README.md'}", flush=True)
print("=" * 70, flush=True)
