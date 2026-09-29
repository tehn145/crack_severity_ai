#!/usr/bin/env python3
"""
convert_annotations.py
Chuyển đổi các dataset công khai về định dạng YOLO thống nhất cho Phase 1 (Detection)
Crack Severity AI - Khóa luận tốt nghiệp
"""

import os
import shutil
import random
from pathlib import Path
from tqdm import tqdm
from PIL import Image
import numpy as np

# ==================== CẤU HÌNH ====================
RAW_DIR = Path("data/raw/public")
PROCESSED_DIR = Path("data/processed/phase1")
IMAGES_DIR = PROCESSED_DIR / "images"
LABELS_DIR = PROCESSED_DIR / "labels"

# Tạo thư mục đích
for split in ["train", "val", "test"]:
    (IMAGES_DIR / split).mkdir(parents=True, exist_ok=True)
    (LABELS_DIR / split).mkdir(parents=True, exist_ok=True)

# Tỷ lệ chia
TRAIN_RATIO = 0.8
VAL_RATIO = 0.1
TEST_RATIO = 0.1

random.seed(42)


def get_split(filename: str) -> str:
    """Chia train/val/test theo hash tên file (ổn định)"""
    h = hash(filename) % 100
    if h < TRAIN_RATIO * 100:
        return "train"
    elif h < (TRAIN_RATIO + VAL_RATIO) * 100:
        return "val"
    else:
        return "test"


def create_full_image_label(img_path: Path, label_path: Path, class_id: int = 0):
    """
    Tạo YOLO label dạng full-image bounding box
    (dùng cho dataset Classification: coi toàn bộ ảnh là 1 object)
    Format YOLO: class x_center y_center width height (normalized)
    """
    try:
        with Image.open(img_path) as img:
            w, h = img.size
        # Full image box
        xc, yc, bw, bh = 0.5, 0.5, 1.0, 1.0
        with open(label_path, "w") as f:
            f.write(f"{class_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
    except Exception as e:
        print(f"   [ERROR] Không tạo được label cho {img_path.name}: {e}")


def convert_classification_folder(
    dataset_name: str,
    positive_dirs: list,
    negative_dirs: list,
    class_id_crack: int = 0
):
    """
    Chuyển dataset dạng folder Classification (Positive/Negative hoặc CD/UD)
    → YOLO format
    """
    print(f"\n{'='*60}")
    print(f"Đang convert: {dataset_name} (Classification → YOLO)")
    print(f"{'='*60}")

    all_images = []

    # Thu thập ảnh Positive (có nứt)
    for p_dir in positive_dirs:
        p_path = RAW_DIR / dataset_name / p_dir
        if p_path.exists():
            for img_path in p_path.rglob("*"):
                if img_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}:
                    all_images.append((img_path, True))  # True = có nứt

    # Thu thập ảnh Negative (không nứt)
    for n_dir in negative_dirs:
        n_path = RAW_DIR / dataset_name / n_dir
        if n_path.exists():
            for img_path in n_path.rglob("*"):
                if img_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}:
                    all_images.append((img_path, False))

    print(f"   Tổng số ảnh tìm thấy: {len(all_images)}")

    count = {"train": 0, "val": 0, "test": 0}

    for img_path, has_crack in tqdm(all_images, desc=f"   {dataset_name}"):
        split = get_split(img_path.name)
        stem = f"{dataset_name}_{img_path.stem}"

        # Copy ảnh
        dst_img = IMAGES_DIR / split / f"{stem}{img_path.suffix.lower()}"
        shutil.copy2(img_path, dst_img)

        # Tạo label
        dst_label = LABELS_DIR / split / f"{stem}.txt"
        if has_crack:
            create_full_image_label(img_path, dst_label, class_id=class_id_crack)
        else:
            # Không có nứt → file label rỗng
            dst_label.touch()

        count[split] += 1

    print(f"   → train: {count['train']} | val: {count['val']} | test: {count['test']}")


def convert_sdnet2018():
    """SDNET2018 có cấu trúc đặc biệt: D/P/W → bên trong có CD/UD"""
    print(f"\n{'='*60}")
    print("Đang convert: SDNET2018 (Bridge + Wall + Pavement)")
    print(f"{'='*60}")

    base = RAW_DIR / "SDNET2018"
    # Tìm đúng thư mục chứa D, P, W
    possible_roots = list(base.rglob("SDNET2018"))
    if not possible_roots:
        possible_roots = [base]

    root = possible_roots[0]
    print(f"   Root tìm thấy: {root}")

    all_images = []

    for surface in ["D", "P", "W"]:  # Deck, Pavement, Wall
        for crack_type in ["CD", "UD", "C", "U"]:  # một số bản dùng C/U
            folder = root / surface / crack_type
            if folder.exists():
                is_crack = crack_type in ["CD", "C"]
                for img_path in folder.rglob("*"):
                    if img_path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                        all_images.append((img_path, is_crack, surface))

    print(f"   Tổng số ảnh: {len(all_images)}")

    count = {"train": 0, "val": 0, "test": 0}

    for img_path, has_crack, surface in tqdm(all_images, desc="   SDNET2018"):
        split = get_split(img_path.name)
        stem = f"SDNET_{surface}_{img_path.stem}"

        dst_img = IMAGES_DIR / split / f"{stem}{img_path.suffix.lower()}"
        shutil.copy2(img_path, dst_img)

        dst_label = LABELS_DIR / split / f"{stem}.txt"
        if has_crack:
            create_full_image_label(img_path, dst_label, class_id=0)
        else:
            dst_label.touch()

        count[split] += 1

    print(f"   → train: {count['train']} | val: {count['val']} | test: {count['test']}")


def convert_cfd():
    """CFD: Images + Masks → YOLO (full box nếu mask có pixel trắng)"""
    print(f"\n{'='*60}")
    print("Đang convert: CFD (CrackForest)")
    print(f"{'='*60}")

    img_dir = RAW_DIR / "CFD" / "Images"
    mask_dir = RAW_DIR / "CFD" / "Masks"

    if not img_dir.exists():
        print("   [SKIP] Không tìm thấy CFD/Images")
        return

    images = list(img_dir.glob("*"))
    print(f"   Tổng số ảnh: {len(images)}")

    count = {"train": 0, "val": 0, "test": 0}

    for img_path in tqdm(images, desc="   CFD"):
        if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue

        split = get_split(img_path.name)
        stem = f"CFD_{img_path.stem}"

        # Copy ảnh
        dst_img = IMAGES_DIR / split / f"{stem}{img_path.suffix.lower()}"
        shutil.copy2(img_path, dst_img)

        # Xử lý mask
        mask_path = mask_dir / f"{img_path.stem}.png"
        if not mask_path.exists():
            mask_path = mask_dir / f"{img_path.stem}.jpg"

        dst_label = LABELS_DIR / split / f"{stem}.txt"

        has_crack = False
        if mask_path.exists():
            try:
                mask = np.array(Image.open(mask_path).convert("L"))
                if mask.max() > 127:  # có pixel sáng = có nứt
                    has_crack = True
            except:
                pass

        if has_crack:
            create_full_image_label(img_path, dst_label, class_id=0)
        else:
            dst_label.touch()

        count[split] += 1

    print(f"   → train: {count['train']} | val: {count['val']} | test: {count['test']}")


def convert_deepcrack():
    """Lấy đúng phần dataset của DeepCrack"""
    print(f"\n{'='*60}")
    print("Đang convert: DeepCrack")
    print(f"{'='*60}")

    base = RAW_DIR / "DeepCrack"
    # Tìm thư mục chứa ảnh thật
    possible = list(base.rglob("DeepCrack"))
    img_dirs = []

    for p in base.rglob("*"):
        if p.is_dir() and any(f.suffix.lower() in {".jpg", ".png"} for f in p.glob("*")):
            img_dirs.append(p)

    if not img_dirs:
        print("   [SKIP] Không tìm thấy ảnh DeepCrack")
        return

    print(f"   Tìm thấy các thư mục ảnh: {[str(d.relative_to(base)) for d in img_dirs[:5]]}")

    all_images = []
    for d in img_dirs:
        for img_path in d.glob("*"):
            if img_path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                all_images.append(img_path)

    print(f"   Tổng số ảnh: {len(all_images)}")

    count = {"train": 0, "val": 0, "test": 0}
    for img_path in tqdm(all_images, desc="   DeepCrack"):
        split = get_split(img_path.name)
        stem = f"DeepCrack_{img_path.stem}"

        dst_img = IMAGES_DIR / split / f"{stem}{img_path.suffix.lower()}"
        if not dst_img.exists():
            shutil.copy2(img_path, dst_img)

        # Tạm thời coi tất cả là có nứt (vì DeepCrack chủ yếu là ảnh nứt)
        dst_label = LABELS_DIR / split / f"{stem}.txt"
        create_full_image_label(img_path, dst_label, class_id=0)

        count[split] += 1

    print(f"   → train: {count['train']} | val: {count['val']} | test: {count['test']}")


def copy_yolo_ready(dataset_name: str, img_subdir="images", label_subdir="labels"):
    """Copy các bộ đã sẵn YOLO format"""
    print(f"\n{'='*60}")
    print(f"Đang copy bộ YOLO sẵn: {dataset_name}")
    print(f"{'='*60}")

    src = RAW_DIR / dataset_name
    if not src.exists():
        print("   [SKIP] Không tồn tại")
        return

    count = 0
    for split in ["train", "val", "test", "valid"]:
        img_src = src / split / "images"
        label_src = src / split / "labels"

        # Một số bộ dùng "valid" thay vì "val"
        target_split = "val" if split == "valid" else split

        if not img_src.exists():
            img_src = src / "images" / split
            label_src = src / "labels" / split

        if img_src.exists():
            for img_path in img_src.glob("*"):
                if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                    continue
                stem = f"{dataset_name}_{img_path.stem}"
                dst_img = IMAGES_DIR / target_split / f"{stem}{img_path.suffix.lower()}"
                shutil.copy2(img_path, dst_img)

                # Copy label nếu có
                label_path = label_src / f"{img_path.stem}.txt"
                dst_label = LABELS_DIR / target_split / f"{stem}.txt"
                if label_path.exists():
                    shutil.copy2(label_path, dst_label)
                else:
                    dst_label.touch()
                count += 1

    print(f"   → Đã copy khoảng {count} ảnh")


def main():
    print("="*60)
    print("CONVERT ANNOTATIONS → YOLO FORMAT")
    print("Phase 1 - Crack Detection")
    print("="*60)

    # 1. Các bộ Classification lớn
    convert_sdnet2018()

    convert_classification_folder(
        dataset_name="METU",
        positive_dirs=["Positive"],
        negative_dirs=["Negative"]
    )

    convert_classification_folder(
        dataset_name="Concrete_and_Pavement",
        positive_dirs=["Positive"],
        negative_dirs=["Negative"]
    )

    # 2. CFD
    convert_cfd()

    # 3. DeepCrack
    convert_deepcrack()

    # 4. Các bộ đã YOLO sẵn
    copy_yolo_ready("Roads_and_Bridges")
    copy_yolo_ready("Ultralytics_CrackSeg")

    # Tổng kết
    print("\n" + "="*60)
    print("HOÀN TẤT CONVERT")
    print("="*60)
    for split in ["train", "val", "test"]:
        n_img = len(list((IMAGES_DIR / split).glob("*")))
        n_lbl = len(list((LABELS_DIR / split).glob("*.txt")))
        print(f"{split:5s} : {n_img:6d} ảnh | {n_lbl:6d} label")

    print(f"\nDữ liệu đã sẵn sàng tại: {PROCESSED_DIR.resolve()}")
    print("Bước tiếp theo: tạo file data.yaml và bắt đầu train Phase 1")


if __name__ == "__main__":
    main()