#!/usr/bin/env python3
"""
eval_hard_cases.py — Đo ĐỘ NHẦM LẪN của model trên bộ vân đá (hard cases).

Vết nứt trên ĐÁ có vân là out-of-domain (không có trong train). Bộ này đo 2 chiều:
  1. NHẦM TEXTURE: model báo "nứt" ở chỗ GT không có (FP) — nhầm vân đá thành vết nứt.
     -> FP instances, FP image rate (%, số ảnh bị báo nhầm ít nhất 1 vết).
  2. RECALL vật liệu lạ: model còn tìm được vết nứt ĐÁ thật không (FN).
     -> P/R/F1 instance (IoU>=0.5, sweep conf) + pixel Dice.

Chạy:
  python scripts/eval_hard_cases.py --weights weights/phase1/best.pt --imgsz 640
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO

HARD = Path("data/processed/phase1/hard_cases")
OUT_DIR = Path("outputs/reports")
IOU_MATCH = 0.5
CONF_SWEEP = (0.25, 0.35, 0.45, 0.55)

def iou_xyxy(a: np.ndarray, b: np.ndarray) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    aa = (a[2] - a[0]) * (a[3] - a[1])
    ab = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (aa + ab - inter + 1e-9)


def parse_gt(txt: Path, w: int, h: int) -> list[np.ndarray]:
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


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default="weights/phase1/best.pt")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--tag", default="", help="nhãn đính tên báo cáo (vd v1/v2)")
    ap.add_argument("--images-dir", default=str(HARD / "images"))
    ap.add_argument("--labels-dir", default=str(HARD / "labels"))
    args = ap.parse_args()

    model = YOLO(args.weights)
    IMG_DIR = Path(args.images_dir); LBL_DIR = Path(args.labels_dir)
    images = sorted(p for p in IMG_DIR.iterdir()
                    if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    print(f"Hard cases: {len(images)} ảnh | weights={args.weights} | imgsz={args.imgsz}")

    agg = defaultdict(lambda: {"img": 0, "gt": 0, "pred": 0, "tp": 0, "fp": 0, "fn": 0,
                               "fp_img": 0, "px": np.zeros(3, dtype=np.int64)})
    sweep = {t: np.zeros(3, dtype=np.int64) for t in CONF_SWEEP}
    sweep_src: dict[str, dict[float, np.ndarray]] = defaultdict(
        lambda: {t: np.zeros(3, dtype=np.int64) for t in CONF_SWEEP})
    rows = []

    for img_path in tqdm(images, desc="hard cases"):
        src = "forest" if img_path.stem.lower().startswith("forest") else "sylvie"
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        h, w = img.shape[:2]
        lbl = LBL_DIR / f"{img_path.stem}.txt"
        gt = parse_gt(lbl, w, h)
        res = model.predict(img, conf=0.05, imgsz=args.imgsz, verbose=False)[0]
        pb = res.boxes.xyxy.cpu().numpy() if len(res.boxes) else np.zeros((0, 4))
        pc = res.boxes.conf.cpu().numpy() if len(res.boxes) else np.zeros(0)

        order = np.argsort(-pc)
        matched: set[int] = set()
        plist: list[tuple[float, bool]] = []
        for i in order:
            best_j, best_iou = -1, IOU_MATCH
            for j, g in enumerate(gt):
                if j in matched:
                    continue
                v = iou_xyxy(pb[i], g)
                if v >= best_iou:
                    best_iou, best_j = v, j
            if best_j >= 0:
                matched.add(best_j)
                plist.append((float(pc[i]), True))
            else:
                plist.append((float(pc[i]), False))
        tp = sum(1 for _, ok in plist if ok)
        fp = len(plist) - tp
        fn = len(gt) - len(matched)

        for t in CONF_SWEEP:
            t_tp = sum(1 for c, ok in plist if ok and c >= t)
            t_fp = sum(1 for c, ok in plist if not ok and c >= t)
            t_fn = max(0, len(gt) - t_tp)
            sweep[t] += np.array([t_tp, t_fp, t_fn], dtype=np.int64)
            sweep_src[src][t] += np.array([t_tp, t_fp, t_fn], dtype=np.int64)

        # pixel dice
        gmask = np.zeros((h, w), np.uint8)
        for ln in (lbl.read_text().splitlines() if lbl.exists() else []):
            p = ln.split()
            if len(p) >= 7:
                v = np.array([float(x) for x in p[1:]])
                cv2.fillPoly(gmask, [np.stack([v[0::2] * w, v[1::2] * h], 1).astype(np.int32)], 1)
        pmask = np.zeros((h, w), np.uint8)
        if res.masks is not None:
            for poly in res.masks.xy:
                cv2.fillPoly(pmask, [np.asarray(poly, np.int32)], 1)
        px_tp = int(np.logical_and(gmask, pmask).sum())
        px_fp = int(np.logical_and(gmask == 0, pmask).sum())
        px_fn = int(np.logical_and(gmask, pmask == 0).sum())

        a = agg[src]
        a["img"] += 1; a["gt"] += len(gt); a["pred"] += len(pb)
        a["tp"] += tp; a["fp"] += fp; a["fn"] += fn
        a["fp_img"] += int(fp > 0)
        a["px"] += np.array([px_tp, px_fp, px_fn])
        t = agg["TONG"]
        t["img"] += 1; t["gt"] += len(gt); t["pred"] += len(pb)
        t["tp"] += tp; t["fp"] += fp; t["fn"] += fn
        t["fp_img"] += int(fp > 0)
        t["px"] += np.array([px_tp, px_fp, px_fn])
        rows.append({"anh": img_path.name, "nguon": src, "gt": len(gt),
                     "pred": len(pb), "tp": tp, "fp": fp, "fn": fn,
                     "conf_list": plist})

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = args.tag or Path(args.weights).stem
    gt_total = agg["TONG"]["gt"]
    lines = [
        f"# Hard cases (vân đá) — {tag}",
        (f"- weights: `{args.weights}` | imgsz: {args.imgsz} | {len(images)} ảnh "
         f"(118 forest + 185 sylvie), GT {gt_total} vết"),
        "",
        "## 1. Theo nguồn — IoU≥0.5 @conf tối ưu F1 riêng từng nguồn",
        "| Nguồn | Ảnh | GT | P | R | F1 | best conf |",
        "|---|---|---|---|---|---|---|",
    ]
    for src in ("forest", "sylvie", "TONG"):
        a = agg[src]
        sw = sweep if src == "TONG" else sweep_src[src]
        best = max(CONF_SWEEP, key=lambda t: prf(*sw[t])[2])
        p, r, f = prf(*sw[best])
        lines.append(f"| {src} | {a['img']} | {a['gt']} | {p:.3f} | {r:.3f} | {f:.3f} | ≥{best} |")

    lines += ["", "## 2. Độ NHẦM LẪN texture vân đá (FP vết / FP ảnh)",
              "| conf ≥ | FP vết | FP ảnh có ≥1 FP |", "|---|---|---|"]
    tot_img = max(1, agg["TONG"]["img"])
    # FP ảnh chính xác theo từng ngưỡng: mỗi ảnh lưu danh sách (conf, có khớp GT?)
    for t in CONF_SWEEP:
        fp_vet = int(sweep[t][1])
        fp_img = sum(1 for r in rows if any(c >= t and not ok for c, ok in r["conf_list"]))
        lines.append(f"| {t} | {fp_vet} | {fp_img} / {tot_img} | {100 * fp_img / tot_img:.1f}% |")

    lines += [
        "",
        "## 3. Pixel Dice trên đá (vật liệu lạ)",
        "| Nguồn | TP px | FP px | FN px | Dice |", "|---|---|---|---|---|",
    ]
    for src in ("forest", "sylvie", "TONG"):
        tp, fp, fn = (int(x) for x in agg[src]["px"])
        dice = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
        lines.append(f"| {src} | {tp} | {fp} | {fn} | {dice:.3f} |")

    lines += [
        "",
        "## Đọc kết quả",
        "- **FP vết** = số lần model báo 'nứt' ở chỗ GT không có → NHẦM vân đá/texture thành nứt.",
        "- **Recall trên đá** thấp là BÌNH THƯỜNG (vật liệu lạ, out-of-domain, không có trong train).",
        "- Mục tiêu production: FP thấp ở conf vận hành (≥0.35–0.5) — texture đá ít bị báo nhầm.",
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = OUT_DIR / f"hard_cases_{tag}_{stamp}.md"
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    csv_rows = [{k: v for k, v in r.items() if k != "conf_list"} for r in rows]
    with open(OUT_DIR / f"hard_cases_{tag}_{stamp}_per_image.csv", "w", newline="", encoding="utf-8-sig") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()))
        wcsv.writeheader(); wcsv.writerows(csv_rows)

    print("\n".join(lines))
    print(f"\nBáo cáo: {md.resolve()}")


if __name__ == "__main__":
    main()
