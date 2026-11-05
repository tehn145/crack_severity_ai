#!/usr/bin/env python3
"""
compare_with_sota.py — Đánh giá Phase 1 theo ĐÚNG metric của bài SOTA
(arXiv:2508.10256, Georgia Tech): semantic segmentation pixel-level
IoU / Precision / Recall / Dice.

So sánh trực tiếp với benchmark của bài trên 2 bộ mà ta cùng dùng:
  - DeepCrack  (bài: ResUNet Dice 0.833, IoU ~0.725; CrackSAM cao hơn)
  - 3DCrack    (bài: ResUNet Dice 0.795, IoU ~0.703; CrackSAM cao hơn)

Cách tính: gộp mask dự đoán của mọi vết trong 1 ảnh thành 1 mask nhị phân,
rasterize GT polygon tương tự, cộng dồn TP/FP/FN pixel toàn bộ ảnh của từng
nguồn rồi tính P/R/IoU/Dice (cách "micro" — giống chuẩn đánh giá seg).

Chạy:  python scripts/compare_with_sota.py [--conf 0.25] [--imgsz 640]
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO

WEIGHTS = Path("weights/phase1/best.pt")
DATA_ROOT = Path("data/processed/phase1/primary")
SPLIT = "test"
OUT_DIR = Path("outputs/reports")

# Số liệu trích từ arXiv:2508.10256 (train 100% data, bảng narrative)
SOTA = {
    "DeepCrack": [("ResUNet", 0.725, 0.833), ("CrackSAM", None, None)],
    "3DCrack": [("ResUNet", 0.703, 0.795), ("CrackSAM", None, None)],
}


def source_of(stem: str) -> str:
    for p in ("3DCrack_v1_", "DeepCrack_"):
        if stem.startswith(p):
            return "3DCrack" if p.startswith("3DCrack") else "DeepCrack"
    if stem.startswith("crack_segmentation_dataset_DeepCrack"):
        return "crack_seg/DeepCrack"
    return ""


def gt_mask(txt: Path, w: int, h: int) -> np.ndarray:
    m = np.zeros((h, w), dtype=np.uint8)
    if not txt.exists() or txt.stat().st_size == 0:
        return m
    for ln in txt.read_text().splitlines():
        p = ln.split()
        if len(p) < 7:
            continue
        v = np.array([float(x) for x in p[1:]], dtype=np.float64)
        pts = np.stack([v[0::2] * w, v[1::2] * h], axis=1).astype(np.int32)
        cv2.fillPoly(m, [pts], 1)
    return m


def pred_mask(res, w: int, h: int) -> np.ndarray:
    m = np.zeros((h, w), dtype=np.uint8)
    if res.masks is None:
        return m
    # masks.data: (N, H', W') ở kích thước gốc của ultralytics (letterbox)
    for poly in res.masks.xy:
        cv2.fillPoly(m, [np.asarray(poly, dtype=np.int32)], 1)
    return m


def prf_dice(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    iou = tp / (tp + fp + fn) if tp + fp + fn else 0.0
    dice = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    return {"P": p, "R": r, "IoU": iou, "Dice": dice}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--imgsz", type=int, default=640)
    args = ap.parse_args()

    model = YOLO(str(WEIGHTS))
    img_dir = DATA_ROOT / "images" / SPLIT
    lbl_dir = DATA_ROOT / "labels" / SPLIT
    images = sorted(
        p for p in img_dir.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"} and source_of(p.stem)
    )
    print(f"Ảnh đánh giá (DeepCrack + 3DCrack + crack_seg/DeepCrack): {len(images)}")
    print(f"conf={args.conf} | imgsz={args.imgsz}")

    acc = defaultdict(lambda: np.zeros(3, dtype=np.int64))  # tp, fp, fn

    for img_path in tqdm(images, desc="Đánh giá pixel"):
        stem = img_path.stem
        src = source_of(stem)
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        h, w = img.shape[:2]
        g = gt_mask(lbl_dir / f"{stem}.txt", w, h)
        res = model.predict(img, conf=args.conf, imgsz=args.imgsz, verbose=False)[0]
        pr = pred_mask(res, w, h)

        tp = int(np.logical_and(g == 1, pr == 1).sum())
        fp = int(np.logical_and(g == 0, pr == 1).sum())
        fn = int(np.logical_and(g == 1, pr == 0).sum())
        acc[src] += np.array([tp, fp, fn])
        acc["TAT_CA"] += np.array([tp, fp, fn])

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    lines = [
        "# So sánh với SOTA (arXiv:2508.10256) — metric segmentation pixel-level",
        f"- Model: `{WEIGHTS}` | conf={args.conf} | imgsz={args.imgsz} | split={SPLIT}",
        "",
        "| Nguồn | Ảnh | Precision | Recall | IoU | Dice |",
        "|---|---|---|---|---|---|",
    ]
    counts = defaultdict(int)
    for p in images:
        counts[source_of(p.stem)] += 1
    for src, (tp, fp, fn) in sorted(acc.items()):
        m = prf_dice(int(tp), int(fp), int(fn))
        lines.append(
            f"| {src} | {counts.get(src, 0)} | {m['P']:.3f} | {m['R']:.3f} | "
            f"{m['IoU']:.3f} | {m['Dice']:.3f} |"
        )
    lines += [
        "",
        "## Tham chiếu từ bài báo (train 100% data)",
        "- DeepCrack: ResUNet Dice 0.833, IoU ~0.725; CrackSAM/UniMatch v2 cao hơn nữa.",
        "- 3DCrack:  ResUNet Dice 0.795, IoU ~0.703; CrackSAM/UniMatch v2 cao hơn nữa.",
        "- Lưu ý: split của ta khác split của bài (ta chia trên primary gộp nguồn);",
        "  số mang tính tham chiếu tương đối, cùng loại metric pixel-level.",
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"compare_sota_{stamp}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nĐã ghi: {out.resolve()}")


if __name__ == "__main__":
    main()
