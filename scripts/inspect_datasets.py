#!/usr/bin/env python3
"""
inspect_datasets.py
Kiểm tra và báo cáo cấu trúc các dataset công khai đã tải về.
Dùng cho khóa luận Crack Severity AI.
"""

import os
from pathlib import Path
from collections import defaultdict
import json

# ==================== CẤU HÌNH ====================
RAW_PUBLIC_DIR = Path("data/raw/public")

# Các phần mở rộng ảnh phổ biến
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
LABEL_EXTENSIONS = {".txt", ".json", ".xml", ".png", ".jpg"}  # mask cũng có thể là png/jpg


def is_image(file_path: Path) -> bool:
    return file_path.suffix.lower() in IMAGE_EXTENSIONS


def count_files(directory: Path, extensions: set = None) -> int:
    """Đếm số file theo extension (None = đếm tất cả file)"""
    count = 0
    if not directory.exists():
        return 0
    for root, _, files in os.walk(directory):
        for f in files:
            if extensions is None or Path(f).suffix.lower() in extensions:
                count += 1
    return count


def get_subdirs(path: Path, max_depth: int = 2) -> list:
    """Lấy danh sách thư mục con (giới hạn độ sâu)"""
    result = []
    if not path.exists():
        return result

    def _walk(current: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for item in sorted(current.iterdir()):
                if item.is_dir():
                    rel = item.relative_to(path)
                    result.append(str(rel))
                    _walk(item, depth + 1)
        except PermissionError:
            pass

    _walk(path, 1)
    return result


def analyze_dataset(dataset_dir: Path) -> dict:
    """Phân tích một dataset"""
    info = {
        "name": dataset_dir.name,
        "exists": dataset_dir.exists(),
        "total_images": 0,
        "total_files": 0,
        "subdirs": [],
        "has_labels": False,
        "possible_type": "Unknown",
        "notes": []
    }

    if not dataset_dir.exists():
        info["notes"].append("Thư mục không tồn tại")
        return info

    # Đếm ảnh và tổng file
    info["total_images"] = count_files(dataset_dir, IMAGE_EXTENSIONS)
    info["total_files"] = count_files(dataset_dir)

    # Lấy cấu trúc thư mục
    info["subdirs"] = get_subdirs(dataset_dir, max_depth=3)

    # Đoán loại annotation
    lower_subdirs = [s.lower() for s in info["subdirs"]]
    all_text = " ".join(lower_subdirs)

    if any(x in all_text for x in ["cd", "ud", "cracked", "uncracked", "positive", "negative"]):
        info["possible_type"] = "Classification (folder-based)"
        info["notes"].append("Thường dùng cho binary classification (có nứt / không nứt)")
    elif any(x in all_text for x in ["images", "masks", "labels", "annotations"]):
        info["possible_type"] = "Segmentation hoặc Detection"
        info["has_labels"] = True
    elif any(x in all_text for x in ["train", "val", "test"]):
        info["possible_type"] = "Đã chia sẵn train/val/test"
        info["has_labels"] = True
    elif any(x in all_text for x in ["yolo", "labels"]):
        info["possible_type"] = "YOLO format"
        info["has_labels"] = True

    # Kiểm tra có file label không
    label_count = count_files(dataset_dir, {".txt", ".json", ".xml"})
    if label_count > 0:
        info["has_labels"] = True
        info["notes"].append(f"Tìm thấy khoảng {label_count} file label (.txt/.json/.xml)")

    if info["total_images"] == 0:
        info["notes"].append("⚠ Không tìm thấy ảnh nào (có thể cấu trúc lồng sâu hoặc chưa giải nén hết)")

    return info


def print_report(results: list):
    """In báo cáo đẹp"""
    print("\n" + "="*70)
    print("BÁO CÁO KIỂM TRA DATASET CÔNG KHAI")
    print("Crack Severity AI – Khóa luận tốt nghiệp")
    print("="*70)

    total_images = 0
    success_count = 0

    for info in results:
        print(f"\n📦 {info['name']}")
        print("-" * 50)
        if not info["exists"]:
            print("   ❌ Thư mục không tồn tại")
            continue

        success_count += 1
        total_images += info["total_images"]

        print(f"   Số ảnh ước tính     : {info['total_images']:,}")
        print(f"   Tổng số file        : {info['total_files']:,}")
        print(f"   Loại dự đoán        : {info['possible_type']}")
        print(f"   Có label            : {'Có' if info['has_labels'] else 'Chưa rõ / Không'}")

        if info["subdirs"]:
            print(f"   Cấu trúc thư mục (một phần):")
            for sub in info["subdirs"][:12]:  # chỉ hiện 12 dòng đầu
                print(f"      └─ {sub}")
            if len(info["subdirs"]) > 12:
                print(f"      └─ ... và {len(info['subdirs']) - 12} thư mục khác")

        if info["notes"]:
            print("   Ghi chú:")
            for note in info["notes"]:
                print(f"      • {note}")

    print("\n" + "="*70)
    print("TỔNG KẾT")
    print("="*70)
    print(f"Số dataset tồn tại     : {success_count}/{len(results)}")
    print(f"Tổng số ảnh ước tính   : {total_images:,}")
    print(f"Thư mục gốc            : {RAW_PUBLIC_DIR.resolve()}")
    print("\nGợi ý tiếp theo:")
    print("  → Nếu dataset có cấu trúc Classification (folder CD/UD hoặc Positive/Negative)")
    print("    thì cần viết script chuyển sang YOLO format cho Phase 1.")
    print("  → Ưu tiên xử lý SDNET2018 trước vì có đầy đủ Bridge + Wall + Pavement.")


def main():
    print("Đang quét thư mục data/raw/public ...")

    if not RAW_PUBLIC_DIR.exists():
        print(f"[ERROR] Không tìm thấy thư mục: {RAW_PUBLIC_DIR}")
        print("Hãy chạy scripts/download_public_datasets.py trước.")
        return

    # Lấy tất cả thư mục con trực tiếp
    dataset_dirs = sorted([d for d in RAW_PUBLIC_DIR.iterdir() if d.is_dir()])

    if not dataset_dirs:
        print("[WARNING] Chưa có dataset nào trong data/raw/public/")
        return

    results = []
    for ds_dir in dataset_dirs:
        print(f"  Đang phân tích: {ds_dir.name} ...")
        results.append(analyze_dataset(ds_dir))

    print_report(results)

    # Lưu báo cáo ra file json (tiện cho luận văn)
    report_path = Path("outputs/reports/dataset_inspection.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nĐã lưu báo cáo chi tiết tại: {report_path}")


if __name__ == "__main__":
    main()