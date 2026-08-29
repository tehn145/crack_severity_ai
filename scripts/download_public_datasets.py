#!/usr/bin/env python3
"""
download_public_datasets.py
Script chuẩn tải dataset công khai - hỗ trợ nhiều bề mặt (tường, đường, cầu)
Có thanh tiến độ phần trăm
"""

import os
import subprocess
import zipfile
from pathlib import Path
from urllib.request import urlretrieve
from tqdm import tqdm

# ==================== CẤU HÌNH ====================
BASE_DIR = Path("data/raw/public")
BASE_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = [
    # ===== Bề mặt đa dạng (ưu tiên theo yêu cầu thầy) =====
    {
        "name": "SDNET2018",
        "kaggle": "atharv0919/sdnet2018-a-concrete-crack-image-dataset",
        "description": "SDNET2018 - Bridge Deck + Wall + Pavement (~56k ảnh)"
    },
    {
        "name": "Roads_and_Bridges",
        "kaggle": "danishghaffar786/roads-and-bridges-cracks-yolov8-format",
        "description": "Roads and Bridges Cracks (YOLOv8 format) - Đường + Cầu"
    },
    {
        "name": "CFD",
        "kaggle": "mahendrachouhanml/crackforest",
        "description": "Crack Forest Dataset (CFD) - Đường phố"
    },

    # ===== Các bộ trước đó =====
    {
        "name": "METU",
        "kaggle": "arnavr10880/concrete-crack-images-for-classification",
        "description": "METU Concrete Crack (tường bê tông, 40k ảnh)"
    },
    {
        "name": "Crack500",
        "kaggle": "pauldavid22/crack50020220509t090436z001",
        "description": "Crack500 - Đường asphalt"
    },
    {
        "name": "Ultralytics_CrackSeg",
        "kaggle": None,
        "direct_url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/crack-seg.zip",
        "description": "Ultralytics Crack-Seg (YOLO ready)"
    },
    {
        "name": "DeepCrack",
        "kaggle": None,
        "direct_url": "https://github.com/yhlleo/DeepCrack/archive/refs/heads/master.zip",
        "description": "DeepCrack dataset"
    },
]


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_via_kaggle(slug: str, target_dir: Path) -> bool:
    print(f"   → Đang tải bằng Kaggle CLI: {slug}")
    target_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "kaggle", "datasets", "download",
        "-d", slug,
        "--unzip",
        "-p", str(target_dir)
    ]

    try:
        # Không capture để hiện thanh tiến độ của Kaggle
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        print("   [ERROR] Kaggle tải thất bại")
        return False
    except FileNotFoundError:
        print("   [ERROR] Chưa cài kaggle. Chạy: pip install kaggle")
        return False


def download_direct(url: str, target_dir: Path, filename: str = "download.zip") -> bool:
    target_dir.mkdir(parents=True, exist_ok=True)
    zip_path = target_dir / filename

    if zip_path.exists():
        print(f"   [SKIP] File đã tồn tại: {zip_path.name}")
    else:
        print(f"   → Đang tải trực tiếp...")
        try:
            with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=f"   {filename}", ncols=80) as t:
                urlretrieve(url, filename=zip_path, reporthook=t.update_to)
            print(f"   [OK] Tải xong")
        except Exception as e:
            print(f"   [ERROR] Tải thất bại: {e}")
            return False

    try:
        print(f"   → Đang giải nén...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        print(f"   [OK] Giải nén thành công")
        return True
    except Exception as e:
        print(f"   [ERROR] Giải nén thất bại: {e}")
        return False


def download_dataset(ds: dict) -> bool:
    name = ds["name"]
    target_dir = BASE_DIR / name

    print("\n" + "="*60)
    print(f"📦 {name}")
    print(f"   {ds.get('description', '')}")
    print("="*60)

    if ds.get("kaggle"):
        success = download_via_kaggle(ds["kaggle"], target_dir)
        if success:
            return True
        print("   [WARN] Kaggle thất bại → thử tải trực tiếp...")

    if ds.get("direct_url"):
        return download_direct(ds["direct_url"], target_dir)

    print("   [ERROR] Không có cách tải nào thành công")
    return False


def main():
    print("="*60)
    print("DOWNLOAD PUBLIC DATASETS - Crack Severity AI")
    print("Hỗ trợ nhiều bề mặt: Tường + Đường + Cầu")
    print("="*60)

    results = {}
    for ds in DATASETS:
        results[ds["name"]] = download_dataset(ds)

    print("\n" + "="*60)
    print("KẾT QUẢ TẢI")
    print("="*60)
    for name, success in results.items():
        status = "✅ Thành công" if success else "❌ Thất bại"
        print(f"{name:25s} : {status}")

    print(f"\nThư mục dữ liệu: {BASE_DIR.resolve()}")
    print("\nGhi chú: SDNET2018 + Roads_and_Bridges + CFD giúp đáp ứng yêu cầu đa bề mặt của thầy.")


if __name__ == "__main__":
    main()