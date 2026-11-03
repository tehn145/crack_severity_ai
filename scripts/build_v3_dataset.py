#!/usr/bin/env python3
"""
build_v3_dataset.py — Lắp ráp dataset v3 cho Kaggle:
  primary (14.594, val/test bất biến)
  + tiled 3.146 tile Volker/Rissbilder @độ phân giải gốc (train-only)
  + vân đá: 150 negative (nhãn rỗng) + 100 positive (GT) — train-only, seed=42
  + v1_best.pt (fine-tune khởi đầu)
  + data.yaml @960
Xuất: outputs/kaggle/phase1_v3/ + zip
Chạy: python scripts/build_v3_dataset.py
"""

from __future__ import annotations

import random
import shutil
from pathlib import Path

PRIMARY = Path("data/processed/phase1/primary")
TILED = Path("data/processed/phase1/tiled")
HARD = Path("data/processed/phase1/hard_cases")
W1 = Path("weights/phase1/best.pt")
OUT = Path("outputs/kaggle/phase1_v3")
N_STONE_NEG, N_STONE_POS = 150, 100

DATA_YAML = """\
# Phase 1 v3 - tiled + stone hard-negative/positive
path: /kaggle/working/phase1_v3
train: images/train
val: images/val
test: images/test

nc: 1
names:
  0: crack
"""


def copy_into(src: Path, dst_img: Path, dst_lbl: Path, new_stem: str) -> None:
    shutil.copy2(src, dst_img)
    lbl_src = PRIMARY / "labels" / "train" / f"{src.stem}.txt" if False else None
    shutil.copy2(dst_lbl.parent / "placeholder", dst_lbl) if False else None


def main() -> None:
    random.seed(42)
    if OUT.exists():
        shutil.rmtree(OUT)
    for sp in ("train", "val", "test"):
        (OUT / "images" / sp).mkdir(parents=True)
        (OUT / "labels" / sp).mkdir(parents=True)

    # 1) primary (image + label khớp sẵn)
    n1 = 0
    for sp in ("train", "val", "test"):
        for img in (PRIMARY / "images" / sp).iterdir():
            shutil.copy2(img, OUT / "images" / sp / img.name)
            shutil.copy2(PRIMARY / "labels" / sp / f"{img.stem}.txt",
                         OUT / "labels" / sp / f"{img.stem}.txt")
            n1 += 1
    print("primary:", n1)

    # 2) tiled (train-only)
    n2 = 0
    for img in (TILED / "images").iterdir():
        shutil.copy2(img, OUT / "images" / "train" / img.name)
        shutil.copy2(TILED / "labels" / f"{img.stem}.txt",
                     OUT / "labels" / "train" / f"{img.stem}.txt")
        n2 += 1
    print("tiled:", n2)

    # 3) vân đá: negative (nhãn rỗng) + positive (GT) — train-only, không giao nhau
    imgs = sorted((HARD / "images").iterdir())
    imgs = [p for p in imgs if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    order = imgs[:]
    random.shuffle(order)
    negs = order[:N_STONE_NEG]
    poss = order[N_STONE_NEG:N_STONE_NEG + N_STONE_POS]
    n3n = n3p = 0
    for img in negs:
        stem = f"am_stone_{img.stem}"
        shutil.copy2(img, OUT / "images" / "train" / f"{stem}{img.suffix.lower()}")
        (OUT / "labels" / "train" / f"{stem}.txt").write_text("", encoding="utf-8")
        n3n += 1
    for img in poss:
        stem = f"stone_pos_{img.stem}"
        shutil.copy2(img, OUT / "images" / "train" / f"{stem}{img.suffix.lower()}")
        shutil.copy2(HARD / "labels" / f"{img.stem}.txt",
                     OUT / "labels" / "train" / f"{stem}.txt")
        n3p += 1
    print(f"stone negative: {n3n} | stone positive: {n3p}")

    # 4) weight v1 + data.yaml
    if W1.exists():
        (OUT / "v1_best.pt").write_bytes(W1.read_bytes())
    (OUT / "data.yaml").write_text(DATA_YAML, encoding="utf-8")

    n_train = len(list((OUT / "images" / "train").iterdir()))
    n_val = len(list((OUT / "images" / "val").iterdir()))
    n_test = len(list((OUT / "images" / "test").iterdir()))
    print(f"TỔNG: train={n_train} val={n_val} test={n_test}")

    # 5) zip
    import zipfile

    zp = Path("outputs/kaggle/phase1_v3_20261029.zip")
    with zipfile.ZipFile(zp, "w", compression=zipfile.ZIP_STORED) as zf:
        for f in sorted(OUT.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(OUT.parent))
    print(f"Zip: {zp.resolve()} ({zp.stat().st_size / 1e9:.2f} GB)")


if __name__ == "__main__":
    main()
