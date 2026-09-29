#!/usr/bin/env python3
"""
inspect_datasets.py
Nhận diện cấu trúc dataset như người đọc folder:
- Đếm image / mask / label
- Đoán kiểu + hướng xử lý bước build
- Overall trước khi ghi JSON (có xác nhận)
"""

import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

RAW_DIR = Path("data/raw/public")
OUTPUT_JSON = Path("outputs/reports/dataset_inspection.json")
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

MASK_NAME_TOKENS = ("_mask", "mask_", "-mask", "_lab", "_gt", "_annot")


def is_img(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in IMG_EXTS


def is_mask_name(p: Path) -> bool:
    n = p.name.lower()
    return is_img(p) and any(t in n for t in MASK_NAME_TOKENS)


def is_plain_image(p: Path) -> bool:
    return is_img(p) and not is_mask_name(p)


def is_label(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() == ".txt"


def stem_key(name: str) -> str:
    """Chuẩn hóa stem để so khớp một phần."""
    s = Path(name).stem.lower()
    for t in MASK_NAME_TOKENS:
        s = s.replace(t.strip("_"), "")
    s = re.sub(r"[_\-\s]+", "", s)
    return s


def list_files(folder: Path):
    if not folder.exists():
        return []
    return [p for p in folder.rglob("*") if p.is_file()]


def find_dirs_by_keywords(root: Path, keywords: tuple) -> list[Path]:
    found = []
    for d in root.rglob("*"):
        if d.is_dir() and d.name.lower() in keywords:
            found.append(d)
    return found


def match_score(stems_a: set, stems_b: set) -> dict:
    """Độ trùng khớp tên (full + partial)."""
    if not stems_a or not stems_b:
        return {"exact": 0, "partial": 0, "pct_exact": 0.0, "pct_partial": 0.0}
    exact = len(stems_a & stems_b)
    # partial: stem này nằm trong stem kia
    partial = 0
    for a in stems_a:
        for b in stems_b:
            if a == b or a in b or b in a:
                partial += 1
                break
    return {
        "exact": exact,
        "partial": partial,
        "pct_exact": round(100.0 * exact / max(len(stems_a), 1), 1),
        "pct_partial": round(100.0 * partial / max(len(stems_a), 1), 1),
    }


# ====================== TỪNG LOẠI BỘ ======================

def inspect_cfd(root: Path) -> dict:
    img_dirs = find_dirs_by_keywords(root, ("images", "image"))
    mask_dirs = find_dirs_by_keywords(root, ("masks", "mask"))
    img_dir = img_dirs[0] if img_dirs else root / "Images"
    mask_dir = mask_dirs[0] if mask_dirs else root / "Masks"

    images = [p for p in list_files(img_dir) if is_plain_image(p)] if img_dir.exists() else []
    masks = [p for p in list_files(mask_dir) if is_img(p)] if mask_dir.exists() else []

    img_stems = {stem_key(p.name) for p in images}
    mask_stems = {stem_key(p.name) for p in masks}
    match = match_score(img_stems, mask_stems)

    return {
        "kind": "image_mask_paired",
        "summary_vi": (
            f"Có folder ảnh ({img_dir.name if img_dir.exists() else '?'}) và mask "
            f"({mask_dir.name if mask_dir.exists() else '?'}). "
            f"{len(images)} ảnh + {len(masks)} mask (hình trắng đen). Chưa có .txt."
        ),
        "locations": {
            "images_dir": str(img_dir) if img_dir.exists() else None,
            "masks_dir": str(mask_dir) if mask_dir.exists() else None,
            "labels_dir": None,
        },
        "counts": {"images": len(images), "masks": len(masks), "labels": 0},
        "name_match_image_vs_mask": match,
        "build_plan": "mask_to_yolo_label",
        "build_plan_vi": "Bước build: ghép ảnh–mask theo tên → mask_to_yolo → tạo file .txt",
        "ready_for_yolo": False,
    }


def inspect_classification(root: Path, name: str) -> dict:
    """METU / Concrete: Positive-Negative hoặc tương tự, chỉ ảnh."""
    pos = neg = None
    for d in root.rglob("*"):
        if not d.is_dir():
            continue
        n = d.name.lower()
        if n == "positive":
            pos = d
        if n == "negative":
            neg = d

    n_pos = len([p for p in list_files(pos) if is_plain_image(p)]) if pos else 0
    n_neg = len([p for p in list_files(neg) if is_plain_image(p)]) if neg else 0

    return {
        "kind": "classification_images_only",
        "summary_vi": (
            f"Chỉ có ảnh phân lớp (Positive={n_pos}, Negative={n_neg}). "
            f"Không mask, không label. Phase1 detection: tạm bỏ hoặc weak-label sau."
        ),
        "locations": {
            "positive_dir": str(pos) if pos else None,
            "negative_dir": str(neg) if neg else None,
        },
        "counts": {"images": n_pos + n_neg, "positive": n_pos, "negative": n_neg, "masks": 0, "labels": 0},
        "name_match_image_vs_mask": None,
        "build_plan": "skip_or_weak_label_later",
        "build_plan_vi": "Bước build: SKIP phase1 (hoặc sau này weak box cho Positive)",
        "ready_for_yolo": False,
    }


def inspect_crack500(root: Path) -> dict:
    """
    traindata/testdata/valdata (+ crop): trong mỗi folder trộn
    image / *_mask / .txt cùng stem.
    """
    group_keys = ("traindata", "testdata", "valdata", "traincrop", "testcrop", "valcrop")
    groups = {}
    total_img = total_mask = total_lbl = 0
    match_details = {}

    for key in group_keys:
        dirs = [p for p in root.rglob(key) if p.is_dir()]
        if not dirs:
            continue
        images, masks, labels = [], [], []
        for d in dirs:
            # file nằm trực tiếp hoặc 1 tầng con
            candidates = list(d.iterdir()) if d.exists() else []
            for c in list(d.iterdir()) if d.exists() else []:
                if c.is_dir():
                    candidates.extend(c.iterdir())
            for f in candidates:
                if not f.is_file():
                    continue
                if is_label(f):
                    labels.append(f)
                elif is_mask_name(f):
                    masks.append(f)
                elif is_plain_image(f):
                    images.append(f)

        img_stems = {stem_key(p.name) for p in images}
        mask_stems = {stem_key(p.name) for p in masks}
        lbl_stems = {stem_key(p.name) for p in labels}
        m_im = match_score(img_stems, mask_stems)
        m_il = match_score(img_stems, lbl_stems)

        groups[key] = {
            "dirs": [str(d) for d in dirs],
            "images": len(images),
            "masks": len(masks),
            "labels": len(labels),
            "match_image_mask": m_im,
            "match_image_label": m_il,
        }
        total_img += len(images)
        total_mask += len(masks)
        total_lbl += len(labels)
        match_details[key] = {"image_mask": m_im, "image_label": m_il}

    return {
        "kind": "mixed_image_mask_label_per_folder",
        "summary_vi": (
            f"Có các nhóm train/val/test (+crop). Trong mỗi nhóm trộn image + mask + .txt. "
            f"Tổng đếm (cộng folder): img={total_img}, mask={total_mask}, lbl={total_lbl}. "
            f"Build: ưu tiên .txt nếu khớp tên; không có thì mask→txt; có thể chỉ lấy full data (không crop)."
        ),
        "locations": {"groups": groups},
        "counts": {"images": total_img, "masks": total_mask, "labels": total_lbl},
        "name_match_details": match_details,
        "build_plan": "prefer_txt_else_mask_to_yolo",
        "build_plan_vi": "Bước build: scan trùng tên → có .txt thì lấy; không thì mask→label; tách bộ sạch",
        "ready_for_yolo": total_lbl > 0,
    }


def inspect_deepcrack(root: Path) -> dict:
    train_img = test_img = train_lab = test_lab = None
    for d in root.rglob("*"):
        if not d.is_dir():
            continue
        n = d.name.lower()
        if n == "train_img":
            train_img = d
        elif n == "test_img":
            test_img = d
        elif n == "train_lab":
            train_lab = d
        elif n == "test_lab":
            test_lab = d

    def count_imgs(d):
        return len([p for p in list_files(d) if is_img(p)]) if d and d.exists() else 0

    n_ti, n_te = count_imgs(train_img), count_imgs(test_img)
    n_tl, n_el = count_imgs(train_lab), count_imgs(test_lab)

    # match train
    def stems(d):
        if not d or not d.exists():
            return set()
        return {stem_key(p.name) for p in d.iterdir() if p.is_file() and is_img(p)}

    m_train = match_score(stems(train_img), stems(train_lab))
    m_test = match_score(stems(test_img), stems(test_lab))

    return {
        "kind": "image_mask_split_folders",
        "summary_vi": (
            f"train_img={n_ti}, train_lab(mask)={n_tl}, test_img={n_te}, test_lab(mask)={n_el}. "
            f"Lab là ảnh mask, chưa có .txt."
        ),
        "locations": {
            "train_img": str(train_img) if train_img else None,
            "train_lab": str(train_lab) if train_lab else None,
            "test_img": str(test_img) if test_img else None,
            "test_lab": str(test_lab) if test_lab else None,
        },
        "counts": {
            "images": n_ti + n_te,
            "masks": n_tl + n_el,
            "labels": 0,
            "train_img": n_ti,
            "train_lab": n_tl,
            "test_img": n_te,
            "test_lab": n_el,
        },
        "name_match_image_vs_mask": {"train": m_train, "test": m_test},
        "build_plan": "mask_to_yolo_label",
        "build_plan_vi": "Bước build: ghép train_img↔train_lab, test_img↔test_lab theo tên → tạo .txt",
        "ready_for_yolo": False,
    }


def inspect_yolo_ready(root: Path) -> dict:
    """Roads_and_Bridges / Ultralytics: images + labels."""
    images = [p for p in root.rglob("*") if is_plain_image(p)]
    labels = [p for p in root.rglob("*") if is_label(p)]
    img_stems = {stem_key(p.name) for p in images}
    lbl_stems = {stem_key(p.name) for p in labels}
    match = match_score(img_stems, lbl_stems)

    # đoán layout
    layout = "images_and_labels_folders"
    for d in root.rglob("labels"):
        if d.is_dir():
            layout = "split_images_labels_dirs"
            break

    return {
        "kind": "yolo_ready",
        "summary_vi": (
            f"Đã có ảnh + file .txt. img={len(images)}, lbl={len(labels)}. "
            f"Khớp tên exact ~{match['pct_exact']}%."
        ),
        "locations": {"root": str(root), "layout": layout},
        "counts": {"images": len(images), "masks": 0, "labels": len(labels)},
        "name_match_image_vs_label": match,
        "build_plan": "copy_normalize_yolo",
        "build_plan_vi": "Bước build: copy ảnh + chuẩn hóa .txt (clip [0,1], bỏ segment)",
        "ready_for_yolo": True,
    }


def inspect_sdnet(root: Path) -> dict:
    folders = defaultdict(int)
    total = 0
    for d in root.rglob("*"):
        if not d.is_dir():
            continue
        n = d.name.upper()
        if n in ("CD", "UD", "CP", "UP", "CW", "UW"):
            c = len([p for p in d.iterdir() if is_plain_image(p)])
            folders[n] = c
            total += c
    return {
        "kind": "classification_by_folder",
        "summary_vi": (
            f"SDNET: chỉ ảnh theo thư mục CD/UD/CP/UP/CW/UW. Tổng ~{total}. "
            f"Không mask/label. Phase1: SKIP (hoặc chỉ lấy CD/CP/CW sau)."
        ),
        "locations": {"class_folders": dict(folders)},
        "counts": {"images": total, "masks": 0, "labels": 0, **{k.lower(): v for k, v in folders.items()}},
        "name_match_image_vs_mask": None,
        "build_plan": "skip_phase1",
        "build_plan_vi": "Bước build: SKIP",
        "ready_for_yolo": False,
    }


def inspect_generic(root: Path) -> dict:
    images = [p for p in root.rglob("*") if is_plain_image(p)]
    masks = [p for p in root.rglob("*") if is_mask_name(p)]
    labels = [p for p in root.rglob("*") if is_label(p)]
    return {
        "kind": "unknown",
        "summary_vi": f"Chưa nhận diện rõ. img={len(images)} mask={len(masks)} lbl={len(labels)}.",
        "locations": {"root": str(root)},
        "counts": {"images": len(images), "masks": len(masks), "labels": len(labels)},
        "name_match_image_vs_mask": match_score(
            {stem_key(p.name) for p in images}, {stem_key(p.name) for p in masks}
        ),
        "build_plan": "review_manual",
        "build_plan_vi": "Cần xem tay cấu trúc",
        "ready_for_yolo": len(labels) > 0 and len(labels) >= len(images) * 0.3,
    }


def inspect_one(ds_path: Path) -> dict:
    name = ds_path.name
    name_l = name.lower()
    print(f"\n  ▶ Đang đọc: {name}")

    if "cfd" in name_l:
        detail = inspect_cfd(ds_path)
    elif "concrete" in name_l:
        detail = inspect_classification(ds_path, name)
    elif "crack500" in name_l:
        detail = inspect_crack500(ds_path)
    elif "deepcrack" in name_l:
        detail = inspect_deepcrack(ds_path)
    elif "metu" in name_l:
        detail = inspect_classification(ds_path, name)
    elif "roads" in name_l or "ultralytics" in name_l:
        detail = inspect_yolo_ready(ds_path)
    elif "sdnet" in name_l:
        detail = inspect_sdnet(ds_path)
    else:
        detail = inspect_generic(ds_path)

    # tier gợi ý
    plan = detail["build_plan"]
    if plan in ("copy_normalize_yolo", "mask_to_yolo_label", "prefer_txt_else_mask_to_yolo"):
        tier = "clean"
    elif plan in ("skip_phase1", "skip_or_weak_label_later"):
        tier = "skip"
    else:
        tier = "review"

    return {
        "name": name,
        "path": str(ds_path.resolve()),
        "recommended_tier": tier,
        **detail,
    }


def print_overall(datasets: list):
    print("\n" + "=" * 70)
    print("OVERALL — ĐỌC NHƯ BÁO CÁO TRƯỚC KHI BUILD")
    print("=" * 70)
    total_img = total_mask = total_lbl = 0
    clean, skip, review = [], [], []

    for d in datasets:
        c = d.get("counts", {})
        total_img += c.get("images", 0)
        total_mask += c.get("masks", 0)
        total_lbl += c.get("labels", 0)
        print(f"\n📦 {d['name']}  [{d['recommended_tier']}]  kind={d['kind']}")
        print(f"   {d['summary_vi']}")
        print(f"   Hướng xử lý: {d['build_plan_vi']}")
        if d["recommended_tier"] == "clean":
            clean.append(d["name"])
        elif d["recommended_tier"] == "skip":
            skip.append(d["name"])
        else:
            review.append(d["name"])

    print("\n" + "-" * 70)
    print(f"Tổng ảnh (các bộ): {total_img}")
    print(f"Tổng mask        : {total_mask}")
    print(f"Tổng label .txt  : {total_lbl}")
    print(f"Clean (sẽ build) : {', '.join(clean) or 'None'}")
    print(f"Skip             : {', '.join(skip) or 'None'}")
    print(f"Review           : {', '.join(review) or 'None'}")
    print("-" * 70)
    print("Build sẽ: chỉ lấy tier=clean → tạo/chuẩn hóa label → bạn duyệt overall → mới split.")
    return {"total_images": total_img, "total_masks": total_mask, "total_labels": total_lbl,
            "clean": clean, "skip": skip, "review": review}


def main():
    print("=" * 70)
    print("INSPECT DATASETS — nhận diện thông tin (bước 1)")
    print("=" * 70)

    if not RAW_DIR.exists():
        print(f"[ERROR] Không thấy {RAW_DIR}")
        return

    datasets = []
    for item in sorted(RAW_DIR.iterdir()):
        if item.is_dir():
            datasets.append(inspect_one(item))

    overall = print_overall(datasets)

    ans = input("\nGhi file JSON để dùng cho build_clean? [y/N]: ").strip().lower()
    if ans != "y":
        print("Chưa ghi JSON. Chạy lại inspect khi sẵn sàng.")
        return

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "created_at": datetime.now().isoformat(),
        "raw_dir": str(RAW_DIR.resolve()),
        "overall": overall,
        "datasets": datasets,
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Đã lưu: {OUTPUT_JSON.resolve()}")
    print("Bước tiếp: viết/chạy build_clean_phase1.py đọc JSON này.")


if __name__ == "__main__":
    main()