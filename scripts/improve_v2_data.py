#!/usr/bin/env python3
"""
improve_v2_data.py — Cải thiện CHẤT LƯỢNG MẪU cho train v2 (không đụng val/test).

1) Audit nhãn Volker + Rissbilder (train split):
   - Chạy model hiện tại trên ảnh train của 2 nguồn này.
   - Vết dự đoán conf >= CONF_MERGE nhưng IoU < IOU_ORPHAN với mọi GT
     = "vết thật có khả năng bị thiếu nhãn" (label miss).
   - --merge: ghép polygon mask của các vết đó vào file nhãn train
     (pseudo-GT, có ghi chú trong báo cáo). Val/test KHÔNG BAO GIỜ bị sửa.

2) Bổ sung ảnh âm train-only:
   - METU/Negative + SDNET2018 D/UD + W/UW (class-only "không nứt").
   - Ảnh âm không cần box → label rỗng (background), đúng chính sách
     "METU Negative mẫu" trong báo cáo quét.
   - Idempotent: bỏ qua ảnh đã copy (theo tên đích).

Chạy:
  python scripts/improve_v2_data.py            # chỉ audit + thống kê
  python scripts/improve_v2_data.py --merge --add-negatives 3000
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import Counter
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO

WEIGHTS = Path("weights/phase1/best.pt")
PRIMARY = Path("data/processed/phase1/primary")
RAW = Path("data/raw/public")
CONF_MERGE = 0.60      # conf tối thiểu để coi là label miss đáng ghép
IOU_ORPHAN = 0.30      # IoU với GT thấp hơn ngưỡng này = không trùng GT nào
SOURCES = ("Volker", "Rissbilder")
REPORT_DIR = Path("outputs/reports")


def iou(a: np.ndarray, b: np.ndarray) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    aa = (a[2] - a[0]) * (a[3] - a[1])
    ab = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (aa + ab - inter + 1e-9)


def parse_gt_boxes(txt: Path, w: int, h: int) -> list[np.ndarray]:
    out = []
    if not txt.exists() or txt.stat().st_size == 0:
        return out
    for ln in txt.read_text().splitlines():
        p = ln.split()
        if len(p) < 5:
            continue
        v = np.array([float(x) for x in p[1:]])
        xs, ys = v[0::2] * w, v[1::2] * h
        out.append(np.array([xs.min(), ys.min(), xs.max(), ys.max()]))
    return out


def polygon_to_yolo_row(poly: np.ndarray, w: int, h: int) -> str:
    pts = np.asarray(poly).reshape(-1, 2)
    vals = []
    for x, y in pts:
        vals += [min(1.0, max(0.0, x / w)), min(1.0, max(0.0, y / h))]
    return "0 " + " ".join(f"{v:.6f}" for v in vals)


def audit_and_merge(model, merge: bool) -> dict:
    stats = Counter()
    report_rows = []
    for src in SOURCES:
        imgs = sorted((PRIMARY / "images" / "train").glob(f"crack_segmentation_dataset_{src}_*"))
        print(f"[{src}] ảnh train: {len(imgs)}")
        for img_path in tqdm(imgs, desc=f"audit {src}"):
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            h, w = img.shape[:2]
            lbl = PRIMARY / "labels" / "train" / f"{img_path.stem}.txt"
            gt = parse_gt_boxes(lbl, w, h)
            res = model.predict(img, conf=CONF_MERGE, imgsz=640, verbose=False)[0]
            if res.masks is None:
                continue
            added = 0
            for box, poly in zip(res.boxes, res.masks.xy):
                b = np.array([float(v) for v in box.xyxy[0]])
                if any(iou(b, g) >= IOU_ORPHAN for g in gt):
                    continue
                stats[f"{src}/label_miss"] += 1
                added += 1
                report_rows.append({
                    "nguon": src, "anh": img_path.name, "conf": round(float(box.conf[0]), 3),
                })
                if merge:
                    with open(lbl, "a", encoding="utf-8") as f:
                        f.write(polygon_to_yolo_row(np.asarray(poly), w, h) + "\n")
            if added:
                stats[f"{src}/anh_bi_them_nhan"] += 1
    return {"stats": stats, "rows": report_rows}


def add_negatives(n_total: int) -> dict:
    """Ảnh âm METU Negative + SDNET D/UD, W/UW → train-only, label rỗng."""
    pools: list[Path] = []
    metu = RAW / "METU" / "Negative"
    if metu.exists():
        pools += [p for p in metu.iterdir() if p.suffix.lower() in {".jpg", ".png", ".jpeg"}]
    sd = RAW / "SDNET2018" / "DATA_Maguire_20180517_ALL" / "SDNET2018"
    for sub in ("D", "W"):
        d = sd / f"U{sub}" if (sd / f"U{sub}").exists() else sd / sub / f"U{sub}"
        if d.exists():
            pools += [p for p in d.iterdir() if p.suffix.lower() in {".jpg", ".png", ".jpeg"}]
    print(f"Pool ảnh âm khả dụng: {len(pools)}")

    random.seed(42)
    random.shuffle(pools)
    added = skipped = 0
    for p in tqdm(pools[: n_total * 3], desc="add negatives"):
        if added >= n_total:
            break
        stem = f"am_v2_{p.stem}"
        dst_img = PRIMARY / "images" / "train" / f"{stem}{p.suffix.lower()}"
        dst_lbl = PRIMARY / "labels" / "train" / f"{stem}.txt"
        if dst_img.exists():
            skipped += 1
            continue
        import shutil

        shutil.copy2(p, dst_img)
        dst_lbl.write_text("", encoding="utf-8")
        added += 1
    return {"added": added, "skipped": skipped, "pool": len(pools)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--merge", action="store_true", help="ghép pseudo-GT vào nhãn train")
    ap.add_argument("--add-negatives", type=int, default=0, help="số ảnh âm thêm vào train")
    args = ap.parse_args()

    print("=" * 66)
    print(f"CẢI THIỆN MẪU V2 | merge={args.merge} | add_negatives={args.add_negatives}")
    print(f"CONF_MERGE={CONF_MERGE} IOU_ORPHAN={IOU_ORPHAN} (val/test không bị sửa)")
    print("=" * 66)

    out = {"stats": Counter(), "rows": []}
    if args.merge or True:  # audit luôn chạy; merge chỉ khi cờ bật
        model = YOLO(str(WEIGHTS))
        out = audit_and_merge(model, merge=args.merge)

    neg = {"added": 0, "skipped": 0, "pool": 0}
    if args.add_negatives:
        neg = add_negatives(args.add_negatives)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = REPORT_DIR / f"improve_v2_data_{stamp}.md"
    lines = [
        "# Cải thiện mẫu v2",
        f"- merge={args.merge}, add_negatives={args.add_negatives}",
        "",
        "## Audit label miss (Volker, Rissbilder — train only)",
    ]
    for k, v in sorted(out["stats"].items()):
        lines.append(f"- {k}: {v}")
    if neg["added"]:
        lines += ["", "## Ảnh âm bổ sung (train only)"]
        lines += [f"- added: {neg['added']} | skipped (đã có): {neg['skipped']} | pool: {neg['pool']}"]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    print(f"\nBáo cáo: {md.resolve()}")
    if out["rows"]:
        csv_path = REPORT_DIR / f"improve_v2_data_{stamp}_label_miss.csv"
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["nguon", "anh", "conf"])
            w.writeheader()
            w.writerows(out["rows"])
        print(f"CSV label miss: {csv_path.resolve()}")


if __name__ == "__main__":
    main()
