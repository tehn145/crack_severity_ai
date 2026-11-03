#!/usr/bin/env python3
"""
stone_preprocess.py — TSP (Texture-Suppression Preprocessing): 6 kỹ thuật tiền xử lý
chuyên biệt cho bề mặt ĐÁ/VÂN ĐÁ, A/B đo FP trên hard-case để chọn tổ hợp thắng.

Kỹ thuật (tác dụng với texture đá):
  clahe     : tăng tương phản cục bộ (từ lần 11)
  bilateral : lọc giữ biên — phẳng hạt đá, giữ rãnh nứt
  guided    : guided filter (cần opencv-contrib; fallback bilateral)
  blackhat  : morphology black-hat kernel tuyến tính 15×45 — chiết cấu trúc tối mảnh
  dog       : DoG bandpass σ1/σ2=1:2 — nứt ở tần số TB, vân đá tần số thấp
  bgsub     : closing kernel lớn − ảnh gốc (background subtraction)
  tsp_full  : bilateral → dog → clahe (tổ hợp đề xuất)
  tsp_bh    : blackhat → clahe

A/B: mỗi biến thể xuất ảnh vào outputs/tsp/<tên>/{images,labels} rồi gọi
eval_hard_cases.py đo FP @conf sweep trên chính model đang dùng.

Chạy:  python scripts/stone_preprocess.py            # tạo + đánh giá tất cả
       python scripts/stone_preprocess.py --variants clahe,tsp_full
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

HARD = Path("data/processed/phase1/hard_cases")
OUT = Path("outputs/tsp")
WEIGHTS = "weights/phase1/best.pt"
IMGSZ = "640"

HAS_XIMG = hasattr(cv2, "ximgproc")


def t_clahe(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    out = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(g)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)


def t_bilateral(img):
    return cv2.bilateralFilter(img, d=9, sigmaColor=50, sigmaSpace=50)


def t_guided(img):
    if HAS_XIMG:
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.ximgproc.guidedFilter(g, g, radius=10, eps=1e-3)
    return t_bilateral(img)  # fallback


def t_blackhat(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 45))
    out = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, kernel)
    out = cv2.normalize(out, None, 0, 255, cv2.NORM_MINMAX)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)


def t_dog(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    dog = cv2.GaussianBlur(g, (0, 0), 1.0) - cv2.GaussianBlur(g, (0, 0), 2.0)
    out = cv2.normalize(dog, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)


def t_bgsub(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bg = cv2.morphologyEx(g, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51)))
    out = cv2.subtract(bg, g)
    out = cv2.normalize(out, None, 0, 255, cv2.NORM_MINMAX)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)


def t_tsp_full(img):
    return t_clahe(t_dog(t_bilateral(img)))


def t_tsp_bh(img):
    return t_clahe(t_blackhat(img))


TECHS = {
    "clahe": t_clahe, "bilateral": t_bilateral, "guided": t_guided,
    "blackhat": t_blackhat, "dog": t_dog, "bgsub": t_bgsub,
    "tsp_full": t_tsp_full, "tsp_bh": t_tsp_bh,
}


def build_variant(name: str, fn) -> Path:
    dst = OUT / name
    (dst / "images").mkdir(parents=True, exist_ok=True)
    lbl_dst = dst / "labels"
    if not lbl_dst.exists():
        shutil.copytree(HARD / "labels", lbl_dst)
    for img in sorted((HARD / "images").iterdir()):
        im = cv2.imread(str(img))
        if im is None:
            continue
        out = fn(im)
        cv2.imwrite(str(dst / "images" / img.name), out, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return dst


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default="clahe,bilateral,guided,blackhat,dog,bgsub,tsp_full,tsp_bh")
    ap.add_argument("--weights", default=WEIGHTS)
    args = ap.parse_args()
    variants = [v.strip() for v in args.variants.split(",") if v.strip()]

    summary = []
    for name in variants:
        if name not in TECHS:
            print(f"[BỎ] không biết biến thể {name}")
            continue
        d = build_variant(name, TECHS[name])
        tag = f"tsp_{name}"
        cmd = [sys.executable, "scripts/eval_hard_cases.py",
               "--weights", args.weights, "--imgsz", IMGSZ,
               "--images-dir", str(d / "images"), "--labels-dir", str(d / "labels"),
               "--tag", tag]
        print(f"\n>>> [{name}] đánh giá trên model {args.weights} ...")
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        log = Path(f"outputs/reports/tsp_{name}.log")
        log.write_text(r.stdout + "\n" + r.stderr, encoding="utf-8")
        # bấm FP @conf 0.45 từ markdown
        fp45 = fp_vet = "?"
        for ln in r.stdout.splitlines():
            if ln.startswith("| 0.45 |"):
                parts = [x.strip() for x in ln.split("|")]
                fp_vet, fp45 = parts[2], parts[4]
        summary.append((name, fp_vet, fp45))
        print(f"    FP@0.45: {fp45} ảnh | FP vết: {fp_vet} | log: {log}")

    print("\n" + "=" * 64)
    print("TỔNG KẾT TSP A/B (FP ảnh bị báo nhầm @conf 0.45 — càng thấp càng tốt)")
    print("=" * 64)
    print(f"  baseline (không TSP):          24.1%   (74 FP vết)")
    for name, fp_vet, fp45 in sorted(summary, key=lambda x: x[2] if str(x[2]).replace('%','').isdigit() else 999):
        print(f"  {name:<12} {fp45:>7}   ({fp_vet} FP vết)")
    best = min(summary, key=lambda x: x[2] if str(x[2]).replace('%','').isdigit() else 999)
    print(f"\n→ Tổ hợp thắng: {best[0]}")


if __name__ == "__main__":
    main()
