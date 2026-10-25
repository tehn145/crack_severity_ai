#!/usr/bin/env python3
"""
evaluate_phase1.py — Chẩn đoán Phase 1 v1 trên tập test theo NGUỒN DỮ LIỆU.

Trả lời các câu hỏi:
  1. Độ chính xác mức ảnh (ảnh có nứt / không nứt) — đối chiếu kỳ vọng 0.95.
  2. Model hay sai ở nguồn dữ liệu nào (P/R/F1 mức instance, IoU>=0.5).
  3. Ảnh âm (noncrack, txt rỗng) bị báo nhầm (FP) bao nhiêu.
  4. Vết nứt bị bỏ sót (FN) có đặc điểm gì (kích thước nhỏ?).
  5. Hướng xử lý đề xuất từ số liệu.

Output: console + outputs/reports/evaluate_phase1_<stamp>.md + .csv
Chạy từ thư mục gốc:  python scripts/evaluate_phase1.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO

# ================== CONFIG ==================
WEIGHTS = Path("weights/phase1/best.pt")
DATA_ROOT = Path("data/processed/phase1/primary")
SPLIT = "test"
CONF = 0.25          # ngưỡng confidence khi dự đoán
IOU_MATCH = 0.5      # ngưỡng IoU khớp GT <-> dự đoán
IMGSZ = 640
SMALL_PX = 32        # cạnh box < 32px coi là vết nhỏ
TARGET_ACC = 0.95
OUT_DIR = Path("outputs/reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Tiền tố dataset trong tên file primary (do build_clean_phase1.py đặt)
DATASET_PREFIXES = [
    "3DCrack_v1_",
    "crack_segmentation_dataset_",
    "DeepCrack_",
    "Roads_and_Bridges_",
    "Ultralytics_CrackSeg_",
]


def source_of(stem: str, has_label: bool) -> str:
    """Gộp nguồn: dataset (+ tap con với crack_segmentation_dataset); ảnh âm riêng."""
    if not has_label:
        if "noncrack" in stem.lower():
            return "AM_noncrack (ảnh âm trang trí)"
        return "AM_txt_rong (ảnh âm)"
    for p in DATASET_PREFIXES:
        if stem.startswith(p):
            rest = stem[len(p):]
            if p == "crack_segmentation_dataset_":
                return f"crack_seg/{rest.split('_')[0]}"
            return p.rstrip("_")
    return "khac"


def iou_xyxy(a: np.ndarray, b: np.ndarray) -> float:
    xa1, ya1, xa2, ya2 = a
    xb1, yb1, xb2, yb2 = b
    ix1, iy1 = max(xa1, xb1), max(ya1, yb1)
    ix2, iy2 = min(xa2, xb2), min(ya2, yb2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, (xa2 - xa1)) * max(0.0, (ya2 - ya1))
    area_b = max(0.0, (xb2 - xb1)) * max(0.0, (yb2 - yb1))
    return inter / (area_a + area_b - inter + 1e-9)


def parse_gt(txt_path: Path, w: int, h: int) -> list[np.ndarray]:
    """Nhãn polygon/box YOLO -> list box xyxy pixel."""
    boxes = []
    for ln in txt_path.read_text().splitlines():
        p = ln.split()
        if len(p) < 5:
            continue
        v = np.array([float(x) for x in p[1:]], dtype=np.float64)
        xs, ys = v[0::2], v[1::2]
        x1, x2 = xs.min() * w, xs.max() * w
        y1, y2 = ys.min() * h, ys.max() * h
        if x2 - x1 < 1 or y2 - y1 < 1:
            continue
        boxes.append(np.array([x1, y1, x2, y2]))
    return boxes


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def main() -> None:
    print("=" * 70)
    print(f"CHẨN ĐOÁN PHASE 1 — weights={WEIGHTS} | split={SPLIT}")
    print(f"conf={CONF} | IoU khớp={IOU_MATCH} | imgsz={IMGSZ}")
    print("=" * 70)

    model = YOLO(str(WEIGHTS))
    img_dir = DATA_ROOT / "images" / SPLIT
    lbl_dir = DATA_ROOT / "labels" / SPLIT
    images = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    print(f"Số ảnh test: {len(images)}")

    agg = defaultdict(lambda: {"img": 0, "gt": 0, "pred": 0, "tp": 0, "fp": 0, "fn": 0,
                               "img_ok": 0, "fn_small": 0, "fn_area": 0.0, "tp_area": 0.0})
    rows_csv: list[dict] = []

    for img_path in tqdm(images, desc="Đánh giá"):
        stem = img_path.stem
        lbl = lbl_dir / f"{stem}.txt"
        has_label = lbl.exists() and lbl.stat().st_size > 0
        src = source_of(stem, has_label)

        img = cv2.imread(str(img_path))
        if img is None:
            continue
        h, w = img.shape[:2]
        gt_boxes = parse_gt(lbl, w, h) if has_label else []
        res = model.predict(img, conf=CONF, imgsz=IMGSZ, verbose=False)[0]
        pred_boxes = res.boxes.xyxy.cpu().numpy() if len(res.boxes) else np.zeros((0, 4))
        pred_confs = res.boxes.conf.cpu().numpy() if len(res.boxes) else np.zeros(0)

        # khớp tham lam theo conf giảm dần
        order = np.argsort(-pred_confs)
        matched_gt: set[int] = set()
        tp = fp = 0
        for i in order:
            box = pred_boxes[i]
            best_j, best_iou = -1, IOU_MATCH
            for j, g in enumerate(gt_boxes):
                if j in matched_gt:
                    continue
                v = iou_xyxy(box, g)
                if v >= best_iou:
                    best_iou, best_j = v, j
            if best_j >= 0:
                matched_gt.add(best_j)
                tp += 1
            else:
                fp += 1
        fn = len(gt_boxes) - len(matched_gt)

        a = agg[src]
        a["img"] += 1
        a["gt"] += len(gt_boxes)
        a["pred"] += len(pred_boxes)
        a["tp"] += tp
        a["fp"] += fp
        a["fn"] += fn
        img_ok = (len(gt_boxes) > 0) == (len(pred_boxes) > 0)
        a["img_ok"] += int(img_ok)
        for j, g in enumerate(gt_boxes):
            if j not in matched_gt:
                side = max(g[2] - g[0], g[3] - g[1])
                a["fn_area"] += float((g[2] - g[0]) * (g[3] - g[1]))
                if side < SMALL_PX:
                    a["fn_small"] += 1
        for j in matched_gt:
            g = gt_boxes[j]
            a["tp_area"] += float((g[2] - g[0]) * (g[3] - g[1]))

        rows_csv.append({
            "anh": img_path.name, "nguon": src, "co_gt": len(gt_boxes),
            "co_pred": len(pred_boxes), "tp": tp, "fp": fp, "fn": fn,
            "img_level_dung": int(img_ok),
        })

    # ---------- tổng hợp ----------
    total = defaultdict(float)
    for a in agg.values():
        for k in ("img", "gt", "pred", "tp", "fp", "fn", "img_ok", "fn_small",
                  "fn_area", "tp_area"):
            total[k] += a[k]
    pos_img = sum(a["img"] for s, a in agg.items() if not s.startswith("AM_"))
    neg_img = sum(a["img"] for s, a in agg.items() if s.startswith("AM_"))
    neg_fp_img = sum(1 for r in rows_csv if r["nguon"].startswith("AM_") and r["co_pred"] > 0)
    img_acc = total["img_ok"] / max(1, total["img"])

    lines = [
        "# Báo cáo chẩn đoán Phase 1 v1",
        f"- Thời điểm: {STAMP} | weights: `{WEIGHTS}` | split: `{SPLIT}`",
        f"- Tham số: conf={CONF}, IoU khớp={IOU_MATCH}, imgsz={IMGSZ}",
        "",
        "## 1. Đối chiếu kỳ vọng",
        f"- Độ chính xác mức ảnh (có nứt/không nứt): **{img_acc:.3f}** (kỳ vọng {TARGET_ACC}) "
        + ("→ ĐẠT" if img_acc >= TARGET_ACC else f"→ CHƯA ĐẠT (thiếu {TARGET_ACC - img_acc:.3f})"),
        (f"- Ảnh dương: {pos_img} | Ảnh âm: {neg_img} | Ảnh âm bị báo nhầm: {neg_fp_img} "
        f"({100 * neg_fp_img / max(1, neg_img):.1f}%)"),
        f"- Instance tổng: TP={total['tp']}, FP={total['fp']}, FN={total['fn']}",
        "",
        "## 2. Hiệu năng theo nguồn dữ liệu (IoU>=0.5, conf>=0.25)",
        "| Nguồn | Ảnh | GT | Pred | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    order_src = sorted(agg.items(), key=lambda kv: -kv[1]["gt"])
    for s, a in order_src:
        p, r, f = prf(a["tp"], a["fp"], a["fn"])
        lines.append(
            f"| {s} | {a['img']} | {a['gt']} | {a['pred']} | {a['tp']} | {a['fp']} | {a['fn']} "
            f"| {p:.3f} | {r:.3f} | {f:.3f} |"
        )
    p, r, f = prf(total["tp"], total["fp"], total["fn"])
    lines += [
        (f"| **TỔNG** | {total['img']} | {total['gt']} | {total['pred']} | {total['tp']} | "
        f"{total['fp']} | {total['fn']} | **{p:.3f}** | **{r:.3f}** | **{f:.3f}** |"),
        "",
    ]

    lines += ["## 3. Đặc điểm các vết bị bỏ sót (FN)"]
    fn_tot = total["fn"]
    if fn_tot:
        share_small = total["fn_small"] / fn_tot
        lines += [
            (f"- Tổng FN: {fn_tot}; vết nhỏ (cạnh < {SMALL_PX}px): "
            f"**{total['fn_small']} ({100 * share_small:.1f}%)**"),
            (f"- Diện tích GT trung bình: FN={total['fn_area'] / fn_tot:.0f}px², "
            f"TP={total['tp_area'] / max(1, total['tp']):.0f}px²"),
        ]
    else:
        lines.append("- Không có FN.")

    # ---------- khuyến nghị ----------
    recs: list[str] = []
    if img_acc < TARGET_ACC:
        recs.append(f"Độ chính xác mức ảnh {img_acc:.3f} < {TARGET_ACC} — cần vòng cải thiện v2.")
    if neg_img and neg_fp_img / neg_img > 0.05:
        recs.append(f"Ảnh âm bị báo nhầm {100 * neg_fp_img / neg_img:.1f}% (>5%) → bổ sung ảnh âm/hard-negative mining, tăng weight background.")
    if fn_tot and total["fn_small"] / fn_tot > 0.4:
        recs.append(f"{100 * total['fn_small'] / fn_tot:.0f}% FN là vết nhỏ → tăng imgsz (960/1280) hoặc tiling/SAHI cho ảnh lớn.")
    weak = [(s, a) for s, a in order_src if not s.startswith("AM_") and a["gt"] >= 50
            and prf(a["tp"], a["fp"], a["fn"])[1] < 0.45]
    for s, a in weak:
        recs.append(f"Nguồn `{s}` recall thấp ({prf(a['tp'], a['fp'], a['fn'])[1]:.2f}) → rà chất lượng nhãn/đặc thù ảnh của nguồn này.")
    if not recs:
        recs.append("Không có vấn đề nổi bật vượt ngưỡng — tiếp tục fine-tune và mở rộng dữ liệu.")
    lines += ["## 4. Hướng xử lý đề xuất", *[f"- {x}" for x in recs]]

    md_path = OUT_DIR / f"evaluate_phase1_{STAMP}.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    csv_path = OUT_DIR / f"evaluate_phase1_{STAMP}_per_image.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows_csv[0].keys()))
        writer.writeheader()
        writer.writerows(rows_csv)

    print("\n".join(lines))
    print(f"\nĐã ghi: {md_path.resolve()}")
    print(f"Đã ghi: {csv_path.resolve()}")


if __name__ == "__main__":
    main()
