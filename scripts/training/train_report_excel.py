#!/usr/bin/env python3
"""
train_report_excel.py — Báo cáo Excel TẬP TRAIN theo format dự án đã thống nhất
(cùng phong cách báo cáo quét build_clean_phase1: tiếng Việt, 1 file, nhiều sheet).

Sheets:
  1. Tong_quan      : thống kê tổng theo nguồn × split + số vết GT
  2. Phan_bo_vet    : phân bố số vết/ảnh, độ dài nhãn theo nguồn
  3. Chi_tiet_train : từng ảnh train (tên, nguồn, loại, số vết, bbox lớn nhất)
  4. Negative_van_da: ảnh nền + vân đá trong train
Xuất: outputs/reports/train_report_<stamp>.xlsx
Chạy: python scripts/train_report_excel.py
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOTS = {
    "primary": Path("data/processed/phase1/primary"),
    "tiled": Path("data/processed/phase1/tiled"),
    "pseudo": Path("data/processed/phase1/pseudo"),
}
HARD = Path("data/processed/phase1/hard_cases")
OUT = Path("outputs/reports")

HEADER_FILL = PatternFill("solid", fgColor="0F172A")
HEADER_FONT = Font(color="FFFFFF", bold=True, name="Segoe UI", size=10)
SRC_FILL = PatternFill("solid", fgColor="E2E8F0")


def source_of(stem: str) -> str:
    low = stem.lower()
    for key, name in [
        ("tiled_riss", "tiled/Rissbilder"), ("tiled_volker", "tiled/Volker"),
        ("pseudo_metu", "pseudo/METU"), ("pseudo_sdnet_cd", "pseudo/SDNET-CD"),
        ("pseudo_sdnet_cw", "pseudo/SDNET-CW"), ("am_stone", "vân đá (âm)"),
        ("stone_pos", "vân đá (dương)"), ("am_v2_", "âm METU/SDNET"),
        ("am_", "âm khác"), ("3dcrack", "3DCrack_v1"),
        ("crack_segmentation_dataset", "crack_seg"), ("deepcrack", "DeepCrack"),
        ("roads_and_bridges", "Roads_and_Bridges"), ("ultralytics", "Ultralytics_CrackSeg"),
    ]:
        if low.startswith(key):
            return name
    return "khác"


def count_label(lbl: Path) -> tuple[int, float]:
    """Số vết + tỷ lệ diện tích GT lớn nhất (áp chừng bbox lớn nhất)."""
    n = 0
    max_frac = 0.0
    if not lbl.exists() or lbl.stat().st_size == 0:
        return 0, 0.0
    for ln in lbl.read_text().splitlines():
        p = ln.split()
        if len(p) < 5:
            continue
        n += 1
        v = [float(x) for x in p[1:]]
        xs, ys = v[0::2], v[1::2]
        frac = (max(xs) - min(xs)) * (max(ys) - min(ys))
        max_frac = max(max_frac, frac)
    return n, max_frac


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    wb = openpyxl.Workbook()

    def style_header(ws, ncols, row=1):
        for c in range(1, ncols + 1):
            cell = ws.cell(row=row, column=c)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")

    def autosize(ws, maxw=60):
        for col in ws.columns:
            best = 10
            for cell in col:
                if cell.value is not None:
                    best = max(best, min(maxw, len(str(cell.value)) + 2))
            ws.column_dimensions[get_column_letter(col[0].column)].width = best

    # ============ SHEET 1: TONG_QUAN ============
    ws = wb.active
    ws.title = "Tong_quan"
    ws.append(["BÁO CÁO TẬP TRAIN — CRACK SEVERITY AI", f"Xuất {datetime.now():%Y-%m-%d %H:%M}"])
    ws.append([])
    header = ["Nguồn", "Loại", "train", "val", "test", "Tổng vết GT (train)", "Ảnh không nhãn (train)"]
    ws.append(header)
    style_header(ws, len(header))

    agg: dict[str, dict] = defaultdict(lambda: {"train": 0, "val": 0, "test": 0, "vet": 0, "rong": 0})
    detail_rows = []
    for root_name, root in ROOTS.items():
        # tiled/pseudo là thư mục flat (tất cả tính là train)
        splits = ("train",) if root_name in ("tiled", "pseudo") else ("train", "val", "test")
        for sp in splits:
            idir = root / "images" / sp if (root / "images" / sp).exists() else root / "images"
            if not idir.exists():
                continue
            for img in sorted(idir.iterdir()):
                if img.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                    continue
                src = source_of(img.stem)
                kind = ("tiled" if root_name == "tiled" else
                        "pseudo" if root_name == "pseudo" else
                        "âm (nền)" if src.startswith("âm") else "dương có nhãn")
                lbl = root / "labels" / sp / f"{img.stem}.txt" if (root / "labels" / sp).exists() else root / "labels" / f"{img.stem}.txt"
                n_vet, max_frac = count_label(lbl)
                agg[f"{src} | {kind}"][sp] += 1
                agg[f"{src} | {kind}"]["vet"] += n_vet if sp == "train" else 0
                if not n_vet and sp == "train":
                    agg[f"{src} | {kind}"]["rong"] += 1
                if sp == "train":
                    detail_rows.append([img.name, src, kind, n_vet, round(max_frac, 4)])
    # Vân đá trong bundle v3 (outputs/kaggle/phase1_v3 — sẽ là tập train thực tế)
    v3_train = Path("outputs/kaggle/phase1_v3/images/train")
    v3_lbl = Path("outputs/kaggle/phase1_v3/labels/train")
    if v3_train.exists():
        for img in sorted(v3_train.glob("am_stone_*")):
            n, mf = count_label(v3_lbl / f"{img.stem}.txt")
            agg["vân đá | âm (nền)"] ["train"] += 1
            agg["vân đá | âm (nền)"]["rong"] += 1
            detail_rows.append([img.name, "vân đá", "âm (nền)", n, round(mf, 4)])
        for img in sorted(v3_train.glob("stone_pos_*")):
            n, mf = count_label(v3_lbl / f"{img.stem}.txt")
            agg["vân đá | dương có nhãn"]["train"] += 1
            agg["vân đá | dương có nhãn"]["vet"] += n
            detail_rows.append([img.name, "vân đá", "dương có nhãn", n, round(mf, 4)])

    for key, a in sorted(agg.items()):
        src, kind = key.split(" | ", 1)
        ws.append([src, kind, a["train"], a["val"], a["test"], a["vet"], a["rong"]])
    ws.append([])
    total = ["TỔNG", "", sum(a["train"] for a in agg.values()),
             sum(a["val"] for a in agg.values()), sum(a["test"] for a in agg.values()),
             sum(a["vet"] for a in agg.values()), sum(a["rong"] for a in agg.values())]
    ws.append(total)
    for c in range(1, 8):
        ws.cell(row=ws.max_row, column=c).font = Font(bold=True)
    autosize(ws)

    # ============ SHEET 2: PHAN_BO_VET ============
    ws2 = wb.create_sheet("Phan_bo_vet")
    ws2.append(["Số vết/ảnh (train)", "Số ảnh", "Tỉ lệ %"])
    style_header(ws2, 3)
    hist = Counter()
    for r in detail_rows:
        hist[min(r[3], 10)] += 1  # gộp >=10
    tot = sum(hist.values()) or 1
    for k in sorted(hist):
        ws2.append([k if k < 10 else "≥10", hist[k], round(100 * hist[k] / tot, 2)])
    autosize(ws2)

    # ============ SHEET 3: CHI_TIET_TRAIN ============
    ws3 = wb.create_sheet("Chi_tiet_train")
    ws3.append(["Tên ảnh", "Nguồn", "Loại", "Số vết GT", "Tỉ lệ diện tích GT lớn nhất"])
    style_header(ws3, 5)
    for r in detail_rows:
        ws3.append(r)
    ws3.freeze_panes = "A2"
    autosize(ws3)

    # ============ SHEET 4: NEGATIVE_VAN_DA ============
    ws4 = wb.create_sheet("Negative_van_da")
    ws4.append(["Ảnh vân đá / âm trong train", "Loại"])
    style_header(ws4, 2)
    for r in detail_rows:
        if "âm" in r[2] or "vân đá" in r[1]:
            ws4.append([r[0], r[2]])
    autosize(ws4)

    # ============ SHEET 5: HARD_CASE_TEST (OOD) ============
    ws5 = wb.create_sheet("Hard_case_test")
    ws5.append(["Ảnh vân đá hard-case (test OOD, không train)", "Số vết GT"])
    style_header(ws5, 2)
    if (HARD / "images").exists():
        for img in sorted((HARD / "images").iterdir()):
            n, _ = count_label(HARD / "labels" / f"{img.stem}.txt")
            ws5.append([img.name, n])
    autosize(ws5)

    OUT.mkdir(exist_ok=True)
    out = OUT / f"train_report_{stamp}.xlsx"
    wb.save(out)
    print(f"Đã ghi: {out.resolve()}")
    print(f"Chi tiết train: {len(detail_rows)} ảnh | tổng vết GT train: {total[5]}")


if __name__ == "__main__":
    main()
