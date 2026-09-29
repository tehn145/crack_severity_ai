#!/usr/bin/env python3
"""Kiểm tra folder primary đã split trước khi lên Kaggle"""

from pathlib import Path

OUT_DIR = Path("data/processed/phase1/primary")
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def main():
    print("=" * 60)
    print("CHECK SPLIT FOLDER")
    print("=" * 60)
    if not OUT_DIR.exists():
        print(f"Không thấy {OUT_DIR}")
        return

    all_ok = True
    ti = tl = 0
    for split in ["train", "val", "test"]:
        idir = OUT_DIR / "images" / split
        ldir = OUT_DIR / "labels" / split
        imgs = {p.stem: p for p in idir.glob("*") if p.suffix.lower() in IMG_EXTS}
        lbls = {p.stem: p for p in ldir.glob("*.txt")}
        only_i = set(imgs) - set(lbls)
        only_l = set(lbls) - set(imgs)
        bad_lbl = []
        for stem, lp in lbls.items():
            if stem not in imgs:
                continue
            txt = lp.read_text(encoding="utf-8", errors="ignore").strip()
            if not txt:
                bad_lbl.append(stem)
                continue
            for line in txt.splitlines():
                parts = line.split()
                if len(parts) < 5:
                    bad_lbl.append(stem)
                    break
                try:
                    vals = [float(x) for x in parts[1:5]]
                    if any(v < 0 or v > 1 for v in vals):
                        bad_lbl.append(stem)
                        break
                except ValueError:
                    bad_lbl.append(stem)
                    break

        print(f"\n[{split}] img={len(imgs)} lbl={len(lbls)}")
        if only_i:
            all_ok = False
            print(f"  thiếu label: {len(only_i)} e.g. {list(only_i)[:3]}")
        if only_l:
            all_ok = False
            print(f"  thừa label: {len(only_l)} e.g. {list(only_l)[:3]}")
        if bad_lbl:
            all_ok = False
            print(f"  label lỗi (rỗng/out-of-bounds): {len(set(bad_lbl))} e.g. {bad_lbl[:3]}")
        if not only_i and not only_l and not bad_lbl:
            print("  ✅ OK")
        ti += len(imgs)
        tl += len(lbls)

    print(f"\nTOTAL img={ti} lbl={tl}")
    print("✅ PASS — có thể zip lên Kaggle" if all_ok and ti == tl else "❌ FAIL — sửa trước khi upload")


if __name__ == "__main__":
    main()