#!/usr/bin/env python3
"""
build_tiled_subset.py — Tiled training cho 2 bộ KHÓ NHẤT: Volker + Rissbilder.

Vấn đề: ảnh gốc lớn (Rissbilder ~4000×3000) bị resize về 640 → vết 2px biến mất.
Giải pháp: cắt tile 640×640 Ở ĐỘ PHÂN GIẢI GỐC (stride 512, overlap 128) — vết 2px
trong tile vẫn là 2px. Chỉ giữ tile CÓ vết nứt GT (positive mining); negative đã có
4.048 ảnh riêng.

Xuất: data/processed/phase1/tiled/{images,labels}/ (flat, prefix tiled_volker_/tiled_riss_)
Chạy: python scripts/build_tiled_subset.py [--tile 640] [--stride 512] [--min-gt-frac 0.02]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_clean_phase1 import (
    mask_to_yolo_lines,  # mask -> polygon (đúng thuật toán build)
)

RAW_IMG = Path("data/raw/public/crack_segmentation_dataset/crack_segmentation_dataset/images")
RAW_MASK = Path("data/raw/public/crack_segmentation_dataset/crack_segmentation_dataset/masks")
OUT = Path("data/processed/phase1/tiled")
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
SOURCES = {"volker": "Volker", "riss": "Rissbilder"}


def source_of(stem: str) -> str | None:
    low = stem.lower()
    if low.startswith("volker"):
        return "volker"
    if low.startswith("rissbilder"):
        return "riss"
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tile", type=int, default=640)
    ap.add_argument("--stride", type=int, default=512)
    ap.add_argument("--min-gt-frac", type=float, default=0.02, help="tối thiểu % pixel GT trong tile")
    args = ap.parse_args()
    T, S = args.tile, args.stride

    (OUT / "images").mkdir(parents=True, exist_ok=True)
    (OUT / "labels").mkdir(parents=True, exist_ok=True)

    stats: Counter = Counter()
    for img in sorted(RAW_IMG.iterdir()):
        if img.suffix.lower() not in IMG_EXTS:
            continue
        src = source_of(img.stem)
        if src is None:
            continue
        mask_path = next((RAW_MASK / f"{img.stem}{e}" for e in IMG_EXTS
                          if (RAW_MASK / f"{img.stem}{e}").exists()), None)
        img_full = cv2.imread(str(img))
        mask_full = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE) if mask_path else None
        if img_full is None or mask_full is None:
            stats[f"{src}/bo_qua"] += 1
            continue
        H, W = img_full.shape[:2]
        if mask_full.shape[:2] != (H, W):
            mask_full = cv2.resize(mask_full, (W, H), interpolation=cv2.INTER_NEAREST)
        gt = (mask_full > 127).astype(np.uint8)

        # pad để phủ đủ lưới tile
        pad_h = max(0, T - (H - T) % S if H > T else T - H)
        pad_w = max(0, T - (W - T) % S if W > T else T - W)
        img_p = cv2.copyMakeBorder(img_full, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
        gt_p = cv2.copyMakeBorder(gt, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)

        Path("outputs/tsp/_tmp_img.png")
        for ty in range(0, H + pad_h - T + 1, S):
            for tx in range(0, W + pad_w - T + 1, S):
                tile_gt = gt_p[ty:ty + T, tx:tx + T]
                frac = float(tile_gt.mean())
                if frac < args.min_gt_frac:
                    continue
                tile = img_p[ty:ty + T, tx:tx + T]
                # mask crop của tile -> file tạm -> polygon
                tile_mask = (tile_gt * 255)
                tmp_mask = Path("outputs/tsp/_tmp_mask.png")
                tmp_mask.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(tmp_mask), tile_mask)
                lines, _why = mask_to_yolo_lines(tmp_mask, mode="polygon")
                if not lines:
                    continue
                stem = f"tiled_{src}_{img.stem}_{ty}_{tx}"
                cv2.imwrite(str(OUT / "images" / f"{stem}{img.suffix.lower()}"), tile,
                            [cv2.IMWRITE_JPEG_QUALITY, 92])
                (OUT / "labels" / f"{stem}.txt").write_text(
                    "\n".join(lines) + "\n", encoding="utf-8")
                stats[f"{src}/tile"] += 1
                stats[f"{src}/vet"] += len(lines)

    print("=" * 60)
    print(f"TILED DATASET (tile={T}, stride={S}, min_gt_frac={args.min_gt_frac})")
    print("=" * 60)
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print(f"\nThư mục: {OUT.resolve()}")


if __name__ == "__main__":
    main()
