#!/usr/bin/env python3
"""
package_kaggle_phase1.py

Đóng gói dữ liệu Phase 1 (primary + ảnh âm) thành 1 folder + 1 file zip
sẵn sàng upload lên Kaggle để train YOLOv8 (task=segment, nhãn polygon).

Cấu trúc bundle (giữ nguyên chuẩn YOLO):
  phase1_primary/
  ├── data.yaml          # path trỏ /kaggle/working/phase1_primary
  ├── README_KAGGLE.txt  # hướng dẫn unzip + lệnh train
  ├── images/{train,val,test}
  └── labels/{train,val,test}
      - primary  : nhãn polygon/box YOLO, class 0 = crack
      - ảnh âm   : label txt RỖNG → Ultralytics coi là background,
                   giúp giảm false positive (theo chiến lược 0.95)

Ảnh âm được chia split bằng cùng hàm hash md5 deterministic 80/10/10
như build_clean_phase1.py → chạy lại cho ra kết quả giống nhau.

Chạy từ thư mục gốc dự án:
  python scripts/package_kaggle_phase1.py
"""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

SRC_PRIMARY = Path("data/processed/phase1/primary")
SRC_NEG = Path("data/processed/phase1/negatives")
OUT_ROOT = Path("outputs/kaggle")
BUNDLE_NAME = "phase1_primary"
TRAIN_RATIO, VAL_RATIO = 0.80, 0.10  # phải khớp build_clean_phase1.py

DATA_YAML = """\
# Phase 1 - Crack Detection (Kaggle bundle)
# Nhãn dạng polygon, class 0 = crack -> train voi model YOLOv8 *-seg.pt
path: /kaggle/working/phase1_primary
train: images/train
val: images/val
test: images/test

nc: 1
names:
  0: crack
"""

README = """\
README - Bundle Kaggle Phase 1 (crack detection, YOLO format, polygon)

Cau truc:
  images/{train,val,test}  - anh
  labels/{train,val,test}  - nhan YOLO polygon (class 0 = crack);
                             anh am (background) co label txt RONG
  data.yaml                - path dang tro /kaggle/working/phase1_primary

Cach dung tren Kaggle notebook:
  1) Upload file zip nay nhu mot Kaggle Dataset (Private).
  2) Trong notebook:

     import zipfile
     zipfile.ZipFile("/kaggle/input/<ten-dataset>/phase1_primary.zip") \\
         .extractall("/kaggle/working")

     from ultralytics import YOLO
     model = YOLO("yolov8s-seg.pt")   # nhan polygon -> dung ban *-seg*
     model.train(
         data="/kaggle/working/phase1_primary/data.yaml",
         epochs=100, imgsz=640, batch=16,
     )

  3) Sau train: best.pt nam trong run moi nhat (runs/segment/train*/weights/best.pt).
     Tai ve va dat tai weights/phase1/best.pt cua du an.

Luu y:
  - Giai nen DUNG vao /kaggle/working/phase1_primary neu khong muon sua data.yaml.
  - Anh am co label rong la background: giup giam false positive (muc tieu 0.95).
  - Khong sua data.yaml truc tiep trong /kaggle/input (chi doc).
"""


def get_split(key: str) -> str:
    h = int(hashlib.md5(key.encode()).hexdigest(), 16) % 100
    if h < int(TRAIN_RATIO * 100):
        return "train"
    if h < int((TRAIN_RATIO + VAL_RATIO) * 100):
        return "val"
    return "test"


def link_or_copy(src: Path, dst: Path) -> None:
    try:
        dst.unlink(missing_ok=True)
    except OSError:
        pass
    try:
        import os

        os.link(src, dst)  # nhanh, khong ton dung dia (cung o dia)
    except OSError:
        shutil.copy2(src, dst)


def main() -> None:
    if not SRC_PRIMARY.exists():
        raise SystemExit(f"Không thấy {SRC_PRIMARY} — chạy build_clean_phase1.py trước.")

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    bundle = OUT_ROOT / BUNDLE_NAME
    if bundle.exists():
        shutil.rmtree(bundle)
    for sp in ("train", "val", "test"):
        (bundle / "images" / sp).mkdir(parents=True, exist_ok=True)
        (bundle / "labels" / sp).mkdir(parents=True, exist_ok=True)

    stats = {"train": 0, "val": 0, "test": 0}
    n_neg = {"train": 0, "val": 0, "test": 0}

    # 1) primary (da chuan hoa + chia split)
    for sp in ("train", "val", "test"):
        for img in sorted((SRC_PRIMARY / "images" / sp).iterdir()):
            lbl = SRC_PRIMARY / "labels" / sp / f"{img.stem}.txt"
            if not lbl.exists():
                raise SystemExit(f"Thiếu label cho {img} — dữ liệu primary chưa khớp.")
            link_or_copy(img, bundle / "images" / sp / img.name)
            link_or_copy(lbl, bundle / "labels" / sp / lbl.name)
            stats[sp] += 1

    # 2) anh am -> cung cau truc, label rong
    if SRC_NEG.exists():
        for img in sorted(SRC_NEG.iterdir()):
            if not img.is_file():
                continue
            sp = get_split(img.name)
            link_or_copy(img, bundle / "images" / sp / img.name)
            (bundle / "labels" / sp / f"{img.stem}.txt").write_text(
                "", encoding="utf-8"
            )
            n_neg[sp] += 1

    (bundle / "data.yaml").write_text(DATA_YAML, encoding="utf-8")
    (bundle / "README_KAGGLE.txt").write_text(README, encoding="utf-8")

    total_pos = sum(stats.values())
    total_neg = sum(n_neg.values())
    print(
        f"Primary : {total_pos} (train={stats['train']}, val={stats['val']}, test={stats['test']})"
    )
    print(
        f"Ảnh âm  : {total_neg} (train={n_neg['train']}, val={n_neg['val']}, test={n_neg['test']})"
    )
    print(f"Tổng    : {total_pos + total_neg}")

    # 3) zip (jpg/png da nen san -> ZIP_STORED cho nhanh)
    stamp = datetime.now().strftime("%Y%m%d")
    zip_path = OUT_ROOT / f"{BUNDLE_NAME}_{stamp}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        for p in sorted(bundle.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(bundle.parent))
    size_gb = zip_path.stat().st_size / 1e9
    print(f"Zip     : {zip_path.resolve()} ({size_gb:.2f} GB)")
    print("Xong. Upload zip này lên Kaggle Datasets (Private) rồi giải nén theo README.")


if __name__ == "__main__":
    main()
