#!/usr/bin/env python3
"""
prepare_hard_cases.py — Tách bộ HARD CASES (vân đá) để test độ nhầm lẫn.

Nguồn: crack_segmentation_dataset/images — các tiền tố bị LOẠI khỏi train
  - forest_*  : nứt trên bề mặt đá có vân (118 ảnh)
  - sylvie*   : nứt đá Sylvie_Chambon (185 ảnh)
Vì sao là hard cases: texture vân đá trông giống vết nứt; dataset này KHÔNG
xuất hiện trong train (chính sách chỉ lấy bê tông/tường) → dùng để đo model
có nhầm vân đá/texture thành vết nứt hay không, và recall trên vật liệu lạ.

Xuất: data/processed/phase1/hard_cases/{images,labels}/ (flat, không split)
  - labels: YOLO polygon từ mask GT (dùng đúng thuật toán build_clean_phase1)
Chạy: python scripts/prepare_hard_cases.py
"""

from __future__ import annotations

import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_clean_phase1 import mask_to_yolo_lines  # tái dùng đúng thuật toán

RAW_IMG = Path("data/raw/public/crack_segmentation_dataset/crack_segmentation_dataset/images")
RAW_MASK = Path("data/raw/public/crack_segmentation_dataset/crack_segmentation_dataset/masks")
OUT = Path("data/processed/phase1/hard_cases")
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

HARD_PREFIXES = ("forest", "sylvie")  # vân đá / nứt đá — bị loại khỏi train


def source_of(name: str) -> str:
    low = name.lower()
    if low.startswith("forest"):
        return "forest"
    if low.startswith("sylvie"):
        return "sylvie"
    return "khac"


def main() -> None:
    if not RAW_IMG.exists():
        raise SystemExit(f"Không thấy {RAW_IMG}")
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    (OUT / "labels").mkdir(parents=True, exist_ok=True)

    stats: Counter = Counter()
    skipped_mask = 0
    for img in sorted(RAW_IMG.iterdir()):
        if img.suffix.lower() not in IMG_EXTS:
            continue
        src = source_of(img.name)
        if src not in HARD_PREFIXES:
            continue
        # mask cùng stem (đuôi có thể khác)
        mask = next((RAW_MASK / f"{img.stem}{e}" for e in IMG_EXTS
                     if (RAW_MASK / f"{img.stem}{e}").exists()), None)

        dst_img = OUT / "images" / img.name
        shutil.copy2(img, dst_img)

        lines: list[str] = []
        if mask is not None:
            lines, _why = mask_to_yolo_lines(mask, mode="polygon")
        else:
            skipped_mask += 1
        (OUT / "labels" / f"{img.stem}.txt").write_text(
            "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
        )
        stats[f"{src}/anh"] += 1
        stats[f"{src}/vet_gt"] += len(lines)
        if not lines:
            stats[f"{src}/khong_gt"] += 1

    print("=" * 60)
    print("HARD CASES (vân đá) — tách xong")
    print("=" * 60)
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    if skipped_mask:
        print(f"  (ảnh không tìm thấy mask: {skipped_mask} — vẫn copy, label rỗng)")
    print(f"\nThư mục: {OUT.resolve()}")


if __name__ == "__main__":
    main()
