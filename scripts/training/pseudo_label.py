#!/usr/bin/env python3
"""
pseudo_label.py v2 — Mở kho class-only bằng batch pseudo-labeling (nhanh 4x).

Pools (building domain):
  METU/Positive (8k mẫu)      — bê tông tường/sàn
  SDNET2018 D/CD + W/CW      — sàn cầu + tường (5.9k)
  CAP Positive (10k mẫu)     — bê tông tường (15k có sẵn)

Quy tắc: chỉ giữ ảnh có det conf >= 0.5; nhãn = polygon mask dự đoán.
Idempotent: bỏ qua ảnh đã xử lý. Xuất: data/processed/phase1/pseudo/

Chạy: python scripts/pseudo_label.py [--metu 8000] [--cap 10000] [--conf 0.5]
"""

from __future__ import annotations

import argparse
import random
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO

RAW = Path("data/raw/public")
SDNET = RAW / "SDNET2018" / "DATA_Maguire_20180517_ALL" / "SDNET2018"
CAP = RAW / "Concrete_and_Pavement"
OUT = Path("data/processed/phase1/pseudo")
REPORTS = Path("outputs/reports")
BATCH = 12  # CPU batch size


def pools(metu_n: int, cap_n: int) -> dict[str, list[Path]]:
    random.seed(42)
    metu = sorted((RAW / "METU" / "Positive").glob("*.jpg"))
    random.shuffle(metu)
    cap_pos = sorted((CAP / "Positive").glob("*.jpg"))
    random.shuffle(cap_pos)
    return {
        "metu_pos": metu[:metu_n],
        "sdnet_cd": sorted(SDNET.glob("D/CD/*.jpg")),
        "sdnet_cw": sorted(SDNET.glob("W/CW/*.jpg")),
        "cap_pos": cap_pos[:cap_n],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metu", type=int, default=8000)
    ap.add_argument("--cap", type=int, default=10000)
    ap.add_argument("--conf", type=float, default=0.5)
    ap.add_argument("--weights", default="weights/phase1/best.pt")
    args = ap.parse_args()

    (OUT / "images").mkdir(parents=True, exist_ok=True)
    (OUT / "labels").mkdir(parents=True, exist_ok=True)

    model = YOLO(args.weights)
    stats: Counter = Counter()
    src_map = pools(args.metu, args.cap)

    for src, files in src_map.items():
        todo = []
        for img_path in files:
            stem = f"pseudo_{src}_{img_path.stem}"
            if (OUT / "labels" / f"{stem}.txt").exists():
                stats[f"{src}/bo_qua"] += 1
                continue
            todo.append((stem, img_path))
        print(f"[{src}] cần xử lý: {len(todo)}/{len(files)}")

        # batch prediction
        for i in tqdm(range(0, len(todo), BATCH), desc=src):
            chunk = todo[i : i + BATCH]
            imgs = []
            valid = []
            for stem, p in chunk:
                im = cv2.imread(str(p))
                if im is None:
                    stats[f"{src}/loi_doc"] += 1
                    continue
                imgs.append(im)
                valid.append((stem, p))
            if not imgs:
                continue
            results = model.predict(imgs, conf=args.conf, imgsz=640, verbose=False)
            for (stem, img_path), res in zip(valid, results):
                h, w = res.orig_shape
                if res.masks is None or len(res.boxes) == 0:
                    stats[f"{src}/khong_dat_conf"] += 1
                    continue
                lines = []
                for poly in res.masks.xy:
                    if len(poly) < 3:
                        continue
                    vals = []
                    for px, py in poly:
                        vals += [f"{min(1.0, max(0.0, px / w)):.6f}",
                                 f"{min(1.0, max(0.0, py / h)):.6f}"]
                    lines.append("0 " + " ".join(vals))
                if not lines:
                    stats[f"{src}/khong_dat_conf"] += 1
                    continue
                shutil.copy2(img_path, OUT / "images" / f"{stem}{img_path.suffix.lower()}")
                (OUT / "labels" / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
                stats[f"{src}/giu"] += 1
                stats[f"{src}/vet"] += len(lines)

    print("=" * 60)
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / f"pseudo_label_{datetime.now():%Y%m%d_%H%M%S}.md").write_text(
        "# Pseudo-label batch v2 (conf ≥ %.2f)\n\n" % args.conf
        + "\n".join(f"- {k}: {v}" for k, v in sorted(stats.items())),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
