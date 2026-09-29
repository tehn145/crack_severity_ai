#!/usr/bin/env python3
"""
build_clean_phase1.py
Đọc outputs/reports/dataset_inspection.json
Theo build_plan từng bộ:
  - mask_to_yolo_label
  - prefer_txt_else_mask_to_yolo
  - copy_normalize_yolo
  - skip_*
In kế hoạch + overall → user duyệt mới ghi train/val/test
"""

import json
import re
import shutil
import hashlib
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm

REPORT_JSON = Path("outputs/reports/dataset_inspection.json")
OUT_DIR = Path("data/processed/phase1/primary")
ERROR_JSON = Path("outputs/reports/build_errors.json")
MATCH_JSON = Path("outputs/reports/split_name_match.json")

TRAIN_RATIO = 0.80
VAL_RATIO = 0.10
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
MASK_NAME_TOKENS = ("_mask", "mask_", "-mask", "_lab", "_gt", "_annot")


# --------------------- tiện ích ---------------------
def get_split(name: str) -> str:
    h = int(hashlib.md5(name.encode()).hexdigest(), 16) % 100
    if h < int(TRAIN_RATIO * 100):
        return "train"
    if h < int((TRAIN_RATIO + VAL_RATIO) * 100):
        return "val"
    return "test"


def is_img(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in IMG_EXTS


def is_mask_name(p: Path) -> bool:
    n = p.name.lower()
    return is_img(p) and any(t in n for t in MASK_NAME_TOKENS)


def is_plain_image(p: Path) -> bool:
    return is_img(p) and not is_mask_name(p)


def stem_key(name: str) -> str:
    s = Path(name).stem.lower()
    for t in MASK_NAME_TOKENS:
        s = s.replace(t.strip("_"), "")
    return re.sub(r"[_\-\s]+", "", s)


def mask_to_yolo(mask: np.ndarray, w: int, h: int) -> str | None:
    if mask is None:
        return None
    if len(mask.shape) == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    coords = cv2.findNonZero(binary)
    if coords is None:
        return None
    x, y, bw, bh = cv2.boundingRect(coords)
    if bw < 3 or bh < 3:
        return None
    xc = min(max((x + bw / 2) / w, 0.0), 1.0)
    yc = min(max((y + bh / 2) / h, 0.0), 1.0)
    nw = min(max(bw / w, 0.0), 1.0)
    nh = min(max(bh / h, 0.0), 1.0)
    return f"0 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}"


def normalize_yolo_line(line: str) -> str | None:
    parts = line.strip().split()
    if len(parts) < 5:
        return None
    try:
        cls = int(float(parts[0]))
        vals = [min(max(float(x), 0.0), 1.0) for x in parts[1:5]]
    except ValueError:
        return None
    return f"{cls} {vals[0]:.6f} {vals[1]:.6f} {vals[2]:.6f} {vals[3]:.6f}"


def normalize_label_text(text: str) -> str | None:
    lines = []
    for line in text.splitlines():
        n = normalize_yolo_line(line)
        if n:
            lines.append(n)
    return "\n".join(lines) if lines else None


def save_pair(buffer: dict, img_path: Path, label_str: str, prefix: str):
    stem = f"{prefix}_{img_path.stem}"
    buffer[stem] = {"img_path": img_path, "label_str": label_str.strip()}


# --------------------- xử lý theo plan ---------------------
def process_mask_to_yolo(ds: dict) -> tuple[dict, list]:
    """CFD / DeepCrack: ảnh + mask → txt"""
    buffer, errors = {}, []
    root = Path(ds["path"])
    name = ds["name"]
    locs = ds.get("locations") or {}
    name_l = name.lower()

    pairs = []  # (img_dir, mask_dir)

    if "cfd" in name_l:
        img_dir = Path(locs["images_dir"]) if locs.get("images_dir") else root / "Images"
        mask_dir = Path(locs["masks_dir"]) if locs.get("masks_dir") else root / "Masks"
        if not img_dir.exists():
            for d in root.rglob("*"):
                if d.is_dir() and d.name.lower() == "images":
                    img_dir = d
                    break
        if not mask_dir.exists():
            for d in root.rglob("*"):
                if d.is_dir() and d.name.lower() == "masks":
                    mask_dir = d
                    break
        pairs.append((img_dir, mask_dir))
    else:
        # DeepCrack style
        mapping = [
            (locs.get("train_img"), locs.get("train_lab")),
            (locs.get("test_img"), locs.get("test_lab")),
        ]
        for a, b in mapping:
            if a and b:
                pairs.append((Path(a), Path(b)))
        if not pairs:
            root_dc = root
            for p in root.rglob("train_img"):
                if p.is_dir():
                    root_dc = p.parent
                    break
            pairs = [
                (root_dc / "train_img", root_dc / "train_lab"),
                (root_dc / "test_img", root_dc / "test_lab"),
            ]

    for img_dir, mask_dir in pairs:
        if not img_dir.exists() or not mask_dir.exists():
            errors.append({"reason": "missing_folder", "img_dir": str(img_dir), "mask_dir": str(mask_dir)})
            continue
        mask_index = {}
        for p in mask_dir.iterdir():
            if is_img(p):
                mask_index[stem_key(p.name)] = p
                mask_index[p.stem.lower()] = p

        imgs = [p for p in img_dir.iterdir() if is_plain_image(p) or (is_img(p) and not is_mask_name(p))]
        for img_path in tqdm(imgs, desc=f"    {name}/{img_dir.name}", leave=False):
            mk = mask_index.get(stem_key(img_path.name)) or mask_index.get(img_path.stem.lower())
            if mk is None:
                errors.append({"reason": "no_mask", "image": str(img_path)})
                continue
            img = cv2.imread(str(img_path))
            mask = cv2.imread(str(mk), cv2.IMREAD_GRAYSCALE)
            if img is None or mask is None:
                errors.append({"reason": "read_fail", "image": str(img_path)})
                continue
            h, w = img.shape[:2]
            if mask.shape[0] != h or mask.shape[1] != w:
                mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
            yolo = mask_to_yolo(mask, w, h)
            if not yolo:
                errors.append({"reason": "empty_mask", "image": str(img_path)})
                continue
            save_pair(buffer, img_path, yolo, name)

    return buffer, errors


def process_prefer_txt_else_mask(ds: dict) -> tuple[dict, list]:
    """Crack500: mixed folder — ưu tiên txt, không có thì mask→txt"""
    buffer, errors = {}, []
    root = Path(ds["path"])
    name = ds["name"]
    groups = (ds.get("locations") or {}).get("groups") or {}

    # ưu tiên full data, không lấy crop trừ khi không có gì
    prefer_keys = ["traindata", "testdata", "valdata"]
    dirs = []
    for k in prefer_keys:
        if k in groups:
            for d in groups[k].get("dirs", []):
                dirs.append(Path(d))
    if not dirs:
        for k, g in groups.items():
            for d in g.get("dirs", []):
                dirs.append(Path(d))
    if not dirs:
        dirs = [root]

    for folder in dirs:
        if not folder.exists():
            continue
        candidates = []
        for p in folder.rglob("*"):
            if p.is_file() and p.parent == folder or p.parent.parent == folder:
                candidates.append(p)
        # nới: mọi file dưới folder depth <= 2
        candidates = [p for p in folder.rglob("*") if p.is_file() and len(p.relative_to(folder).parts) <= 2]

        images, masks, labels = {}, {}, {}
        for f in candidates:
            if f.suffix.lower() == ".txt":
                labels[f.stem.lower()] = f
                labels[stem_key(f.name)] = f
            elif is_mask_name(f):
                masks[f.stem.lower().replace("_mask", "")] = f
                masks[stem_key(f.name)] = f
            elif is_plain_image(f):
                images[f.stem.lower()] = f

        for stem, img_path in images.items():
            label_str = None
            sk = stem_key(img_path.name)
            for key in (stem, sk, img_path.stem.lower()):
                if key in labels:
                    label_str = normalize_label_text(
                        labels[key].read_text(encoding="utf-8", errors="ignore")
                    )
                    if label_str:
                        break
            if not label_str:
                for key in (stem, sk, img_path.stem.lower()):
                    if key in masks:
                        img = cv2.imread(str(img_path))
                        mask = cv2.imread(str(masks[key]), cv2.IMREAD_GRAYSCALE)
                        if img is not None and mask is not None:
                            h, w = img.shape[:2]
                            if mask.shape[:2] != (h, w):
                                mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
                            label_str = mask_to_yolo(mask, w, h)
                        break
            if label_str:
                save_pair(buffer, img_path, label_str, name)
            else:
                errors.append({"reason": "no_txt_no_mask", "image": str(img_path)})

    return buffer, errors


def process_copy_yolo(ds: dict) -> tuple[dict, list]:
    """Roads / Ultralytics: có sẵn txt"""
    buffer, errors = {}, []
    root = Path(ds["path"])
    name = ds["name"]
    imgs = [p for p in root.rglob("*") if is_plain_image(p)]
    for img_path in tqdm(imgs, desc=f"    {name}", leave=False):
        lbl = img_path.with_suffix(".txt")
        if not lbl.exists():
            cands = list(root.rglob(img_path.stem + ".txt"))
            lbl = cands[0] if cands else None
        if not lbl or not lbl.exists():
            errors.append({"reason": "missing_label", "image": str(img_path)})
            continue
        label_str = normalize_label_text(lbl.read_text(encoding="utf-8", errors="ignore"))
        if not label_str:
            errors.append({"reason": "invalid_label", "image": str(img_path), "label": str(lbl)})
            continue
        save_pair(buffer, img_path, label_str, name)
    return buffer, errors


def process_dataset(ds: dict) -> tuple[dict, list]:
    plan = ds.get("build_plan", "")
    print(f"\n📦 {ds['name']}")
    print(f"   kind     : {ds.get('kind')}")
    print(f"   plan     : {ds.get('build_plan_vi') or plan}")
    c = ds.get("counts") or {}
    print(f"   inspect  : img={c.get('images')} mask={c.get('masks')} lbl={c.get('labels')}")

    if plan in ("skip_phase1", "skip_or_weak_label_later"):
        print("   → SKIP")
        return {}, []
    if plan == "mask_to_yolo_label":
        return process_mask_to_yolo(ds)
    if plan == "prefer_txt_else_mask_to_yolo":
        return process_prefer_txt_else_mask(ds)
    if plan == "copy_normalize_yolo":
        return process_copy_yolo(ds)
    # fallback theo tier
    if ds.get("recommended_tier") == "clean" and ds.get("ready_for_yolo"):
        return process_copy_yolo(ds)
    print("   → SKIP (plan không hỗ trợ)")
    return {}, []


# --------------------- ghi đĩa + kiểm tra ---------------------
def flush_buffer(buffer: dict) -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    for s in ["train", "val", "test"]:
        (OUT_DIR / "images" / s).mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "labels" / s).mkdir(parents=True, exist_ok=True)
    n = 0
    for stem, item in buffer.items():
        split = get_split(stem)
        src = Path(item["img_path"])
        dst_img = OUT_DIR / "images" / split / f"{stem}{src.suffix.lower()}"
        dst_lbl = OUT_DIR / "labels" / split / f"{stem}.txt"
        try:
            shutil.copy2(src, dst_img)
            dst_lbl.write_text(item["label_str"] + "\n", encoding="utf-8")
            n += 1
        except Exception as e:
            print(f"   [COPY FAIL] {stem}: {e}")
    return n


def scan_image_label_match() -> dict:
    report = {"splits": {}, "all_match": True}
    for split in ["train", "val", "test"]:
        imgs = {p.stem for p in (OUT_DIR / "images" / split).glob("*") if p.suffix.lower() in IMG_EXTS}
        lbls = {p.stem for p in (OUT_DIR / "labels" / split).glob("*.txt")}
        only_img = sorted(imgs - lbls)
        only_lbl = sorted(lbls - imgs)
        ok = not only_img and not only_lbl
        if not ok:
            report["all_match"] = False
        report["splits"][split] = {
            "n_images": len(imgs),
            "n_labels": len(lbls),
            "match": ok,
            "only_image_stems": only_img,
            "only_label_stems": only_lbl,
        }
        print(f"  [{split}] img={len(imgs)} lbl={len(lbls)} {'✅' if ok else '❌'}")
        if only_img:
            print(f"       thiếu label: {only_img[:5]}")
        if only_lbl:
            print(f"       thiếu ảnh  : {only_lbl[:5]}")
    MATCH_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(MATCH_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  Chi tiết: {MATCH_JSON.resolve()}")
    return report


# --------------------- main ---------------------
def main():
    print("=" * 70)
    print("BUILD CLEAN PHASE 1")
    print("=" * 70)

    if not REPORT_JSON.exists():
        print(f"Chưa có {REPORT_JSON}")
        print("→ Chạy: python scripts/inspect_datasets.py")
        return

    with open(REPORT_JSON, encoding="utf-8") as f:
        report = json.load(f)

    datasets = report.get("datasets") or []
    all_buffer = {}
    all_errors = []
    per_ds = {}

    print("\n--- KẾ HOẠCH TỪNG BỘ (theo inspect) ---")
    for ds in datasets:
        buf, err = process_dataset(ds)
        all_errors.extend([{**e, "dataset": ds["name"]} for e in err])
        for k, v in buf.items():
            key = k if k not in all_buffer else k + "_dup"
            all_buffer[key] = v
        per_ds[ds["name"]] = {"kept": len(buf), "errors": len(err), "plan": ds.get("build_plan")}
        if ds.get("build_plan", "").startswith("skip"):
            continue
        print(f"   → Kết quả buffer: {len(buf)} cặp | lỗi: {len(err)}")

    # OVERALL trước split
    print("\n" + "=" * 70)
    print("OVERALL TRƯỚC KHI SPLIT — DUYỆT TAY")
    print("=" * 70)
    total = 0
    for name, info in per_ds.items():
        print(f"  {name:25s}  kept={info['kept']:5d}  errors={info['errors']:4d}  plan={info['plan']}")
        total += info["kept"]
    print(f"\n  TOTAL cặp image+label sẽ ghi: {total}")

    if all_errors:
        ERROR_JSON.parent.mkdir(parents=True, exist_ok=True)
        with open(ERROR_JSON, "w", encoding="utf-8") as f:
            json.dump(all_errors[:1000], f, indent=2, ensure_ascii=False)
        print(f"  ⚠️  {len(all_errors)} lỗi mẫu → {ERROR_JSON}")

    if total == 0:
        print("Không có dữ liệu. Dừng.")
        return

    ans = input("\nĐồng ý split train/val/test và ghi folder? [y/N]: ").strip().lower()
    if ans != "y":
        print("Đã hủy. Chưa ghi đĩa.")
        return

    written = flush_buffer(all_buffer)
    print(f"\nĐã ghi {written} mẫu → {OUT_DIR.resolve()}")

    print("\n" + "=" * 70)
    print("SCAN KHỚP TÊN IMAGE ↔ LABEL SAU SPLIT")
    print("=" * 70)
    rep = scan_image_label_match()
    if rep["all_match"]:
        print("\n✅ Khớp hết — có thể lên Kaggle")
    else:
        print("\n❌ Còn lệch — xem split_name_match.json / build_errors.json")


if __name__ == "__main__":
    main()