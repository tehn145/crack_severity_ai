#!/usr/bin/env python3
"""
download_public_datasets.py
Script chuẩn tải dataset công khai - hỗ trợ nhiều bề mặt
(Tường, Bê tông, Mặt đường, Mặt cầu)
Có thanh tiến độ phần trăm
→ Chỉ tải những bộ còn thiếu (không tải lại từ đầu)
"""

import subprocess
import zipfile
from pathlib import Path
from urllib.request import urlretrieve
from tqdm import tqdm

# ==================== CẤU HÌNH ====================
BASE_DIR = Path("data/raw/public")
BASE_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = [
    # ===== 1. ĐA BỀ MẶT (ưu tiên cao nhất) =====
    {
        "name": "SDNET2018",
        "kaggle": "atharv0919/sdnet2018-a-concrete-crack-image-dataset",
        "description": "SDNET2018 - Bridge Deck + Wall + Pavement (~56k ảnh) ★★★"
    },
    {
        "name": "Roads_and_Bridges",
        "kaggle": "danishghaffar786/roads-and-bridges-cracks-yolov8-format",
        "description": "Roads and Bridges Cracks (YOLOv8) - Đường + Cầu"
    },
    {
        "name": "Concrete_and_Pavement",
        "kaggle": "oluwaseunad/concrete-and-pavement-crack-images",
        "description": "Concrete & Pavement Crack Dataset (30k ảnh)"
    },

    # ===== 2. MẶT ĐƯỜNG =====
    {
        "name": "Crack500",
        "kaggle": "pauldavid22/crack50020220509t090436z001",
        "description": "Crack500 - Đường asphalt (Segmentation)"
    },
    {
        "name": "CFD",
        "kaggle": "mahendrachouhanml/crackforest",
        "description": "Crack Forest Dataset (CFD) - Đường phố / mặt đường asphalt"
    },

    # ===== 3. TƯỜNG / BÊ TÔNG =====
    {
        "name": "METU",
        "kaggle": "arnavr10880/concrete-crack-images-for-classification",
        "description": "METU Concrete Crack - Tường bê tông (40k ảnh)"
    },

    # ===== 4. BỘ BỔ SUNG (tải trực tiếp) =====
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


def is_already_downloaded(target_dir: Path) -> bool:
    """
    Kiểm tra xem dataset đã được tải chưa.
    Coi là đã tải nếu thư mục tồn tại và có ít nhất vài file ảnh bên trong.
    """
    if not target_dir.exists():
        return False

    # Đếm số file ảnh
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    image_count = 0
    for ext in image_exts:
        image_count += len(list(target_dir.rglob(f"*{ext}")))
        image_count += len(list(target_dir.rglob(f"*{ext.upper()}")))

    # Nếu có từ 5 ảnh trở lên thì coi như đã tải thành công
    return image_count >= 5


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
        print(f"   [SKIP] File zip đã tồn tại: {zip_path.name}")
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


def download_dataset(ds: dict) -> str:
    """
    Trả về:
        "skipped"  → đã có sẵn
        "success"  → tải thành công
        "failed"   → tải thất bại
    """
    name = ds["name"]
    target_dir = BASE_DIR / name

    print("\n" + "="*60)
    print(f"📦 {name}")
    print(f"   {ds.get('description', '')}")
    print("="*60)

    # === Kiểm tra đã tải chưa ===
    if is_already_downloaded(target_dir):
        print("   ✅ Đã có sẵn → Bỏ qua (không tải lại)")
        return "skipped"

    # === Tiến hành tải ===
    if ds.get("kaggle"):
        success = download_via_kaggle(ds["kaggle"], target_dir)
        if success:
            return "success"
        print("   [WARN] Kaggle thất bại → thử tải trực tiếp...")

    if ds.get("direct_url"):
        success = download_direct(ds["direct_url"], target_dir)
        return "success" if success else "failed"

    print("   [ERROR] Không có cách tải nào thành công")
    return "failed"


def main():
    print("="*60)
    print("DOWNLOAD PUBLIC DATASETS - Crack Severity AI")
    print("Hỗ trợ nhiều bề mặt: Tường • Bê tông • Mặt đường • Mặt cầu")
    print("Chỉ tải những bộ còn thiếu")
    print("="*60)

    results = {"success": [], "skipped": [], "failed": []}

    for ds in DATASETS:
        status = download_dataset(ds)
        results[status].append(ds["name"])

    # ===== Tổng kết =====
    print("\n" + "="*60)
    print("KẾT QUẢ TẢI")
    print("="*60)

    if results["skipped"]:
        print("\n✅ Đã có sẵn (bỏ qua):")
        for name in results["skipped"]:
            print(f"   • {name}")

    if results["success"]:
        print("\n⬇️  Tải mới thành công:")
        for name in results["success"]:
            print(f"   • {name}")

    if results["failed"]:
        print("\n❌ Tải thất bại:")
        for name in results["failed"]:
            print(f"   • {name}")

    print(f"\nThư mục dữ liệu: {BASE_DIR.resolve()}")
    print(f"Tổng cộng: {len(results['skipped'])} bỏ qua | "
          f"{len(results['success'])} tải mới | "
          f"{len(results['failed'])} thất bại")


if __name__ == "__main__":
    main()