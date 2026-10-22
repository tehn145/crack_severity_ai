#!/usr/bin/env python3
"""
download_public_datasets.py
Tải dataset công khai theo 3 tầng — miền công trình xây dựng
(bê tông, tường, cầu/trụ kết cấu). KHÔNG tải mặt đường asphalt.

1. Clean      → mask/box tốt (Primary Phase 1)
2. Expanded   → tăng số lượng (class / pseudo-label)
3. Hard cases → vân đá, bề mặt khó, nứt trang trí (sau)
"""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

BASE_DIR = Path("data/raw/public")
BASE_DIR.mkdir(parents=True, exist_ok=True)

# ====================== DANH SÁCH THEO TẦNG ======================
# Đã loại: CFD, Crack500, Roads_and_Bridges (đường), Concrete_and_Pavement
DATASETS = {
    # ---------- TẦNG 1: CLEAN (Primary — ưu tiên mask / box) ----------
    "clean": [
        {
            "name": "DeepCrack",
            "kaggle": "rukiyeaydn/deepcrack-dataset",
            "direct_url": "https://github.com/yhlleo/DeepCrack/archive/refs/heads/master.zip",
            "description": "DeepCrack — bê tông + mask (Primary)",
        },
        {
            "name": "CConCrack",
            "kaggle": "stmlen/cconcrack",
            "description": "CConCrack — bê tông crack/spall + mask",
        },
        {
            "name": "Ultralytics_CrackSeg",
            "kaggle": None,
            "direct_url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/crack-seg.zip",
            "description": "Ultralytics Crack-Seg — YOLO sẵn (lọc tường/bê tông khi build)",
        },
        {
            "name": "Bridge_Crack_Library",
            "kaggle": None,
            "direct_url": None,
            "manual": "https://doi.org/10.7910/DVN/RURXSH",
            "description": "BCL — cầu in-service + mask (tải tay Dataverse)",
        },
    ],

    # ---------- TẦNG 2: EXPANDED (class / tăng số lượng) ----------
    "expanded": [
        {
            "name": "SDNET2018",
            "kaggle": "aniruddhsharma/structural-defects-network-concrete-crack-images",
            "description": "SDNET2018 — dùng D (deck)+W (wall); bỏ P (pavement) khi build",
        },
        {
            "name": "METU",
            "kaggle": "arunrk7/surface-crack-detection",
            "description": "METU / Surface Crack — tường & bê tông (pos/neg)",
        },
        {
            "name": "Concrete_Bridge_Crack",
            "kaggle": None,
            "manual": "https://github.com/MCBDD-ZRE/Concrete-Bridge-Crack-Dataset-",
            "description": "MCBDD — cầu/culvert class (tải tay GitHub)",
        },
        {
            "name": "RC_Structure_10519",
            "kaggle": None,
            "manual": "https://data.mendeley.com/datasets/3ghxck2wd5",
            "description": "RC structure ~10.5k+10.5k (tải tay Mendeley)",
        },
    ],

    # ---------- TẦNG 3: HARD CASES (sau — vân đá / trang trí) ----------
    "hard_cases": [
        # Bổ sung khi có nguồn: stone texture, decorative cracks, thermal design joints
    ],
}


class DownloadProgressBar(tqdm if tqdm else object):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tqdm is None:
            return
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def is_already_downloaded(target_dir: Path, min_images: int = 5) -> bool:
    """Đủ ảnh thì coi như đã tải — không tải lại từ đầu."""
    if not target_dir.exists():
        return False
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
    count = sum(1 for p in target_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts)
    return count >= min_images


def download_via_kaggle(slug: str, target_dir: Path) -> bool:
    print(f"   → Kaggle: {slug}")
    target_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "kaggle", "datasets", "download",
        "-d", slug,
        "--unzip",
        "-p", str(target_dir),
    ]
    try:
        # Không capture → Kaggle tự in tiến độ trên terminal
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("   [ERROR] Kaggle thất bại (returncode ≠ 0)")
            return False
        return True
    except FileNotFoundError:
        print("   [ERROR] Chưa cài kaggle CLI (pip install kaggle + ~/.kaggle/kaggle.json)")
        return False
    except Exception as e:
        print(f"   [ERROR] Kaggle: {e}")
        return False


def download_direct(url: str, target_dir: Path, filename: str = "download.zip") -> bool:
    target_dir.mkdir(parents=True, exist_ok=True)
    zip_path = target_dir / filename

    if not zip_path.exists():
        print("   → Đang tải trực tiếp...")
        try:
            if tqdm:
                with DownloadProgressBar(
                    unit="B", unit_scale=True, miniters=1, desc="   download", ncols=80
                ) as t:
                    urlretrieve(url, filename=zip_path, reporthook=t.update_to)
            else:
                urlretrieve(url, filename=zip_path)
        except Exception as e:
            print(f"   [ERROR] Tải thất bại: {e}")
            return False

    try:
        print("   → Đang giải nén...")
        if zipfile.is_zipfile(zip_path):
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(target_dir)
        return True
    except Exception as e:
        print(f"   [ERROR] Giải nén thất bại: {e}")
        return False


def download_dataset(ds: dict) -> str:
    name = ds["name"]
    target_dir = BASE_DIR / name

    print("\n" + "=" * 60)
    print(f"📦 {name}")
    print(f"   {ds.get('description', '')}")
    print("=" * 60)

    if is_already_downloaded(target_dir):
        print("   ✅ Đã có sẵn → Bỏ qua (không tải lại)")
        return "skipped"

    if ds.get("kaggle"):
        if download_via_kaggle(ds["kaggle"], target_dir):
            if is_already_downloaded(target_dir, min_images=1):
                return "success"
            print("   [WARN] Kaggle xong nhưng chưa thấy ảnh.")

    if ds.get("direct_url"):
        if download_direct(ds["direct_url"], target_dir):
            if is_already_downloaded(target_dir, min_images=1):
                return "success"

    if ds.get("manual"):
        print(f"   [MANUAL] Tải tay → giải nén vào: {target_dir.resolve()}")
        print(f"            {ds['manual']}")
        return "failed"

    return "failed"


def main():
    print("=" * 60)
    print("DOWNLOAD PUBLIC DATASETS — 3 tầng")
    print("Công trình xây dựng (bê tông / tường / cầu)")
    print("KHÔNG tải: CFD, Crack500, Roads đường, pavement-only")
    print("=" * 60)

    results = {"success": [], "skipped": [], "failed": []}

    for tier_name in ["clean", "expanded", "hard_cases"]:
        tier_list = DATASETS.get(tier_name, [])
        print(f"\n\n########## TẦNG: {tier_name.upper()} ({len(tier_list)} bộ) ##########")
        if not tier_list:
            print("   (trống — bổ sung sau cho hard cases)")
            continue
        for ds in tier_list:
            status = download_dataset(ds)
            results[status].append(f"{tier_name}/{ds['name']}")

    print("\n" + "=" * 60)
    print("KẾT QUẢ TẢI")
    print("=" * 60)
    print("\n✅ Đã có sẵn (skip):")
    for x in results["skipped"]:
        print(f"   • {x}")
    print("\n⬇️  Tải mới thành công:")
    for x in results["success"]:
        print(f"   • {x}")
    print("\n❌ Thất bại / cần tải tay:")
    for x in results["failed"]:
        print(f"   • {x}")

    print(f"\nThư mục: {BASE_DIR.resolve()}")
    print("\nGợi ý build:")
    print("  Clean  → Primary (mask/box): DeepCrack, CConCrack, BCL, CrackSeg đã lọc")
    print("  Expanded → class: SDNET D+W (bỏ P), METU, MCBDD, RC_10519")
    print("  Hard   → bổ sung sau (vân đá, nứt trang trí)")


if __name__ == "__main__":
    main()