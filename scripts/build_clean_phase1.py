#!/usr/bin/env python3
"""
build_clean_phase1.py
Phase 1 — làm sạch dữ liệu
  CFD | Crack500 | DeepCrack | Roads_and_Bridges | Ultralytics_CrackSeg

Luồng:
  1) Scan/convert tất cả bộ (không hỏi từng bộ)
  2) OVERVIEW + file báo cáo
  3) Gõ yes một lần → xuất primary/{train,val,test}
"""

import hashlib
import shutil
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime

# ================== CẤU HÌNH ==================
OUT_BASE = Path("data/processed/phase1/primary")
TRAIN_RATIO = 0.80
VAL_RATIO = 0.10
# test = phần còn lại (0.10)

IMG_EXTS_ALL = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

REPORT_DIR = Path("outputs/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FILE = REPORT_DIR / f"bao_cao_du_lieu_phase1_{datetime.now():%Y%m%d_%H%M%S}.txt"

THESIS_TITLE_VI = (
    "Phát hiện và phân loại vết nứt bề mặt công trình xây dựng "
    "từ ảnh hai chiều sử dụng mô hình học sâu"
)
THESIS_TITLE_EN = (
    "Detection and classification of surface cracks on civil infrastructure "
    "from two-dimensional images using deep learning models"
)
ADVISOR = "TS. Phan Xuân Thiện"
STUDENTS = [
    "Ngô Kim Thành - 23521447",
    "Trần Công Thành - 23521463",
]
SCHOOL = "Trường Đại học Công nghệ Thông tin — ĐHQG-HCM"


def log(msg: str = "", also_print: bool = True):
    if also_print:
        print(msg)
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def write_report_header():
    lines = [
        "=" * 72,
        "BÁO CÁO XỬ LÝ DỮ LIỆU ĐẦU VÀO — PHASE 1 (PRIMARY)",
        "KHÓA LUẬN TỐT NGHIỆP",
        "=" * 72,
        "",
        f"Trường / đơn vị : {SCHOOL}",
        f"Giảng viên hướng dẫn : {ADVISOR}",
        "Sinh viên thực hiện :",
    ]
    for s in STUDENTS:
        lines.append(f"  - {s}")
    lines += [
        "",
        "Tên đề tài (VI):",
        f"  {THESIS_TITLE_VI}",
        "Tên đề tài (EN):",
        f"  {THESIS_TITLE_EN}",
        "",
        f"Thời điểm chạy script : {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"File báo cáo          : {REPORT_FILE.resolve()}",
        "",
        "Mục tiêu bước này:",
        "  - Quét và khớp ảnh / mask / label theo từng bộ dữ liệu công khai",
        "  - Chuyển mask → nhãn YOLO (class 0) khi chưa có file .txt hợp lệ",
        "  - Chia train/val/test (80/10/10) theo hash ổn định",
        "  - Tổng hợp overview, xác nhận một lần rồi xuất primary",
        "",
        "Các bộ xử lý: CFD | Crack500 | DeepCrack | Roads_and_Bridges | Ultralytics_CrackSeg",
        "Bỏ qua (classification, không có box/mask): METU | SDNET2018 | Concrete_and_Pavement",
        "=" * 72,
        "",
    ]
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Báo cáo: {REPORT_FILE.resolve()}")


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


def convert_mask_pair(img_path: Path, mask_path: Path) -> str | None:
    img = cv2.imread(str(img_path))
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if img is None or mask is None:
        return None
    h, w = img.shape[:2]
    if mask.shape[:2] != (h, w):
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
    return mask_to_yolo(mask, w, h)


def normalize_yolo_txt(text: str) -> str | None:
    lines = []
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        try:
            cls = int(float(parts[0]))
            vals = [min(max(float(x), 0.0), 1.0) for x in parts[1:5]]
        except ValueError:
            continue
        lines.append(f"{cls} {vals[0]:.6f} {vals[1]:.6f} {vals[2]:.6f} {vals[3]:.6f}")
    return "\n".join(lines) if lines else None


def get_split(name: str) -> str:
    """Chia train/val/test ổn định theo hash tên file."""
    h = int(hashlib.md5(name.encode()).hexdigest(), 16) % 100
    if h < TRAIN_RATIO * 100:
        return "train"
    if h < (TRAIN_RATIO + VAL_RATIO) * 100:
        return "val"
    return "test"


def write_pairs(pairs: list[dict], prefix: str) -> dict:
    """
    Ghi ảnh+label vào images/{train,val,test} và labels/{train,val,test}.
    Trả về {"train": n, "val": n, "test": n}.
    """
    counts = {"train": 0, "val": 0, "test": 0}
    for item in pairs:
        src = item["img_path"]
        stem = f"{prefix}_{item['stem']}"
        split = get_split(stem)

        out_img = OUT_BASE / "images" / split
        out_lbl = OUT_BASE / "labels" / split
        out_img.mkdir(parents=True, exist_ok=True)
        out_lbl.mkdir(parents=True, exist_ok=True)

        dst_img = out_img / f"{stem}{src.suffix.lower()}"
        dst_lbl = out_lbl / f"{stem}.txt"
        shutil.copy2(src, dst_img)
        dst_lbl.write_text(item["label"] + "\n", encoding="utf-8")
        counts[split] += 1
    return counts


# ================== CFD ==================
CFD_ROOT = Path("data/raw/public/CFD")
MASK_SUFFIXES = ("_label", "_labels", "_mask", "_masks", "_lab", "_gt", "_annot")


def cfd_normalize_stem(stem: str) -> str:
    s = stem.lower()
    for suffix in MASK_SUFFIXES:
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            break
    return s.strip("_")


def cfd_is_mask_name(stem: str) -> bool:
    low = stem.lower()
    return any(low.endswith(sfx) or sfx in low for sfx in MASK_SUFFIXES)


def cfd_find_dir(root: Path, default_name: str, aliases: tuple) -> Path:
    d = root / default_name
    if d.exists():
        return d
    for p in root.rglob("*"):
        if p.is_dir() and p.name.lower() in aliases:
            return p
    return d


def process_cfd() -> list[dict]:
    print("\n" + "=" * 60)
    print("1) CFD — ảnh + mask (001 / 001_label) → label YOLO")
    print("=" * 60)
    log("\n" + "=" * 60, also_print=False)
    log("1) CFD", also_print=False)

    if not CFD_ROOT.exists():
        print("[ERROR] Không thấy", CFD_ROOT)
        log(f"[ERROR] Không thấy {CFD_ROOT}", also_print=False)
        return []

    img_dir = cfd_find_dir(CFD_ROOT, "Images", ("images", "image", "img"))
    mask_dir = cfd_find_dir(CFD_ROOT, "Masks", ("masks", "mask", "lab", "labels"))
    print(f"Images: {img_dir} exists={img_dir.exists()}")
    print(f"Masks : {mask_dir} exists={mask_dir.exists()}")
    log(f"Images: {img_dir}", also_print=False)
    log(f"Masks : {mask_dir}", also_print=False)

    if not img_dir.exists() or not mask_dir.exists():
        return []

    images, masks = {}, {}
    for p in img_dir.iterdir():
        if p.is_file() and p.suffix.lower() in IMG_EXTS_ALL and not cfd_is_mask_name(p.stem):
            images[cfd_normalize_stem(p.stem)] = p
    for p in mask_dir.iterdir():
        if p.is_file() and p.suffix.lower() in IMG_EXTS_ALL:
            masks[cfd_normalize_stem(p.stem)] = p

    all_keys = sorted(set(images) | set(masks))
    matched_keys = sorted(set(images) & set(masks))
    only_img = sorted(set(images) - set(masks))
    only_mask = sorted(set(masks) - set(images))

    log(
        f"{'STT':>4} | {'Tên ảnh':<40} | {'Tên mask':<40} | {'Khớp':<6} | {'Convert':<8}",
        also_print=False,
    )
    log("-" * 110, also_print=False)

    ok_pairs = []
    fail_read = fail_empty = 0
    for i, key in enumerate(all_keys, start=1):
        img_p, mask_p = images.get(key), masks.get(key)
        matched = img_p is not None and mask_p is not None
        converted = False
        if matched:
            img = cv2.imread(str(img_p))
            mask = cv2.imread(str(mask_p), cv2.IMREAD_GRAYSCALE)
            if img is None or mask is None:
                fail_read += 1
            else:
                h, w = img.shape[:2]
                if mask.shape[:2] != (h, w):
                    mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
                yolo = mask_to_yolo(mask, w, h)
                if not yolo:
                    fail_empty += 1
                else:
                    converted = True
                    ok_pairs.append({"stem": img_p.stem, "img_path": img_p, "label": yolo})
        khop = "YES" if matched else "NO"
        conv = "-" if not matched else ("YES" if converted else "NO")
        log(
            f"{i:>4} | {(img_p.name if img_p else ''):<40} | "
            f"{(mask_p.name if mask_p else ''):<40} | {khop:<6} | {conv:<8}",
            also_print=False,
        )

    log(
        f"Khớp={len(matched_keys)} thiếu_mask={len(only_img)} thiếu_ảnh={len(only_mask)}",
        also_print=False,
    )
    log(
        f"Convert OK={len(ok_pairs)} đọc_lỗi={fail_read} mask_trống={fail_empty}",
        also_print=False,
    )

    print(f"Số ảnh: {len(images)} | mask: {len(masks)} | khớp: {len(matched_keys)}")
    print(f"Convert OK: {len(ok_pairs)} | đọc lỗi: {fail_read} | mask trống: {fail_empty}")
    return ok_pairs


# ================== CRACK500 ==================
CRACK500_ROOT = Path("data/raw/public/Crack500/CRACK500")
if not CRACK500_ROOT.exists():
    CRACK500_ROOT = Path("data/raw/public/Crack500")

FOLDERS_DATA_TXT = ("traindata", "testdata")
FOLDERS_CROP = ("traincrop", "testcrop", "valcrop")
FOLDERS_VALDATA = ("valdata",)
IMG_EXTS = {".jpg", ".jpeg"}
MASK_EXTS = {".png", ".bmp", ".tif", ".tiff"}


def c500_find_dir(root: Path, key: str) -> Path | None:
    cands = [p for p in root.rglob(key) if p.is_dir()]
    if not cands:
        return None
    return max(cands, key=lambda d: sum(1 for x in d.rglob("*") if x.is_file()))


def c500_list_files(folder: Path) -> list[Path]:
    if not folder or not folder.exists():
        return []
    files = [p for p in folder.iterdir() if p.is_file()]
    if len(files) < 3:
        for sub in folder.iterdir():
            if sub.is_dir():
                files.extend(p for p in sub.iterdir() if p.is_file())
    return files


def strip_mask_suffix(stem: str) -> str:
    return stem[: -len("_mask")] if stem.lower().endswith("_mask") else stem


def collect_files(folder: Path):
    images, masks, labels = {}, {}, {}
    for p in c500_list_files(folder):
        ext, stem = p.suffix.lower(), p.stem
        if ext in IMG_EXTS and not stem.lower().endswith("_mask"):
            images[stem] = p
        elif ext in MASK_EXTS:
            masks[strip_mask_suffix(stem)] = p
        elif ext == ".txt":
            labels[strip_mask_suffix(stem)] = p
    return images, masks, labels


def process_crack500() -> list[dict]:
    print("\n" + "=" * 60)
    print("2) CRACK500")
    print("=" * 60)
    log("\n" + "=" * 60, also_print=False)
    log("2) CRACK500", also_print=False)
    print(f"Root: {CRACK500_ROOT} exists={CRACK500_ROOT.exists()}")
    if not CRACK500_ROOT.exists():
        return []

    all_ok = []

    # traindata / testdata: txt YOLO nếu được, không thì mask
    for key in FOLDERS_DATA_TXT:
        folder = c500_find_dir(CRACK500_ROOT, key)
        print(f"\n[{key}] DATA — txt YOLO nếu được, không thì mask→label")
        log(f"\n[{key}] DATA", also_print=False)
        if folder is None:
            print("  [SKIP]")
            continue
        images, masks, labels = collect_files(folder)
        img_l = {k.lower(): v for k, v in images.items()}
        lbl_l = {k.lower(): v for k, v in labels.items()}
        mask_l = {k.lower(): v for k, v in masks.items()}
        candidates = sorted(set(img_l) & (set(lbl_l) | set(mask_l)))
        print(f"  img={len(images)} mask={len(masks)} txt={len(labels)} candidates={len(candidates)}")
        log(f"  img={len(images)} mask={len(masks)} txt={len(labels)}", also_print=False)
        log(f"{'STT':>4} | {'Ảnh':<36} | {'Nguồn':<10} | OK", also_print=False)

        ok = n_txt = n_mask = 0
        for i, lk in enumerate(candidates, start=1):
            img_p, lbl_p, mask_p = img_l[lk], lbl_l.get(lk), mask_l.get(lk)
            yolo, source = None, "-"
            if lbl_p is not None:
                yolo = normalize_yolo_txt(lbl_p.read_text(encoding="utf-8", errors="ignore"))
                if yolo:
                    source = "txt"
            if yolo is None and mask_p is not None:
                yolo = convert_mask_pair(img_p, mask_p)
                if yolo:
                    source = "mask"
            log(
                f"{i:>4} | {img_p.name:<36} | {source:<10} | {'YES' if yolo else 'NO'}",
                also_print=False,
            )
            if yolo:
                all_ok.append({"stem": f"{key}_{img_p.stem}", "img_path": img_p, "label": yolo})
                ok += 1
                n_txt += source == "txt"
                n_mask += source == "mask"
        print(f"  → OK={ok} (txt={n_txt}, mask={n_mask})")

    # crop + valdata: ảnh ∩ mask
    for key, mode in [(k, "CROP") for k in FOLDERS_CROP] + [(k, "VALDATA") for k in FOLDERS_VALDATA]:
        folder = c500_find_dir(CRACK500_ROOT, key)
        print(f"\n[{key}] {mode} — ảnh + mask khớp → convert")
        log(f"\n[{key}] {mode}", also_print=False)
        if folder is None:
            print("  [SKIP]")
            continue
        images, masks, _ = collect_files(folder)
        img_l = {k.lower(): v for k, v in images.items()}
        mask_l = {k.lower(): v for k, v in masks.items()}
        matched = sorted(set(img_l) & set(mask_l))
        print(f"  img={len(images)} mask={len(masks)} khớp={len(matched)}")
        log(f"{'STT':>4} | {'Ảnh':<40} | {'Mask':<40} | Convert", also_print=False)
        ok = 0
        for i, lk in enumerate(matched, start=1):
            img_p, mask_p = img_l[lk], mask_l[lk]
            yolo = convert_mask_pair(img_p, mask_p)
            log(
                f"{i:>4} | {img_p.name:<40} | {mask_p.name:<40} | {'YES' if yolo else 'NO'}",
                also_print=False,
            )
            if yolo:
                all_ok.append({"stem": f"{key}_{img_p.stem}", "img_path": img_p, "label": yolo})
                ok += 1
        print(f"  → Convert OK={ok}")

    print(f"\nCrack500 tổng: {len(all_ok)}")
    return all_ok


# ================== DEEPCRACK ==================
DEEPCRACK_ROOT = Path("data/raw/public/DeepCrack")
DC_PAIRS = [("train_img", "train_lab"), ("test_img", "test_lab")]


def deepcrack_find_root(root: Path) -> Path:
    if (root / "train_img").exists():
        return root
    for p in root.rglob("train_img"):
        if p.is_dir():
            return p.parent
    return root


def deepcrack_collect(folder: Path) -> dict:
    out = {}
    if not folder.exists():
        return out
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in IMG_EXTS_ALL:
            out[p.stem.lower()] = p
    return out


def process_deepcrack() -> list[dict]:
    print("\n" + "=" * 60)
    print("3) DEEPCRACK — train/test_img + train/test_lab")
    print("=" * 60)
    log("\n" + "=" * 60, also_print=False)
    log("3) DEEPCRACK", also_print=False)

    if not DEEPCRACK_ROOT.exists():
        print("[ERROR] Không thấy", DEEPCRACK_ROOT)
        return []

    root = deepcrack_find_root(DEEPCRACK_ROOT)
    print(f"Root: {root}")
    log(f"Root: {root}", also_print=False)
    all_ok = []

    for img_name, lab_name in DC_PAIRS:
        img_dir, lab_dir = root / img_name, root / lab_name
        print(f"\n[{img_name} ↔ {lab_name}]")
        if not img_dir.exists() or not lab_dir.exists():
            print("  [SKIP]")
            continue
        images, masks = deepcrack_collect(img_dir), deepcrack_collect(lab_dir)
        all_keys = sorted(set(images) | set(masks))
        print(f"  img={len(images)} mask={len(masks)}")
        log(f"\n[{img_name}]", also_print=False)
        log(f"{'STT':>4} | {'Ảnh':<40} | {'Mask':<40} | Khớp | Convert", also_print=False)

        ok = fail = 0
        for i, key in enumerate(all_keys, start=1):
            img_p, mask_p = images.get(key), masks.get(key)
            matched = img_p is not None and mask_p is not None
            converted = False
            if matched:
                yolo = convert_mask_pair(img_p, mask_p)
                if yolo:
                    converted = True
                    all_ok.append({
                        "stem": f"{img_name}_{img_p.stem}",
                        "img_path": img_p,
                        "label": yolo,
                    })
                    ok += 1
                else:
                    fail += 1
            else:
                fail += 1
            log(
                f"{i:>4} | {(img_p.name if img_p else ''):<40} | "
                f"{(mask_p.name if mask_p else ''):<40} | "
                f"{'YES' if matched else 'NO':<4} | "
                f"{'-' if not matched else ('YES' if converted else 'NO')}",
                also_print=False,
            )
        print(f"  → Convert OK={ok} | lỗi={fail}")

    print(f"\nDeepCrack tổng: {len(all_ok)}")
    return all_ok


# ================== ROADS AND BRIDGES ==================
ROADS_ROOT = Path("data/raw/public/Roads_and_Bridges")
ROADS_SPLITS = ("train", "valid", "test")


def process_roads_and_bridges() -> list[dict]:
    print("\n" + "=" * 60)
    print("4) ROADS_AND_BRIDGES — images + labels (.txt)")
    print("=" * 60)
    log("\n" + "=" * 60, also_print=False)
    log("4) ROADS_AND_BRIDGES", also_print=False)

    if not ROADS_ROOT.exists():
        print("[ERROR] Không thấy", ROADS_ROOT)
        log(f"[ERROR] Không thấy {ROADS_ROOT}", also_print=False)
        return []

    all_ok = []
    total_img = total_lbl = 0

    for split in ROADS_SPLITS:
        img_dir = ROADS_ROOT / split / "images"
        lbl_dir = ROADS_ROOT / split / "labels"
        if not img_dir.exists() and split == "valid":
            img_dir = ROADS_ROOT / "val" / "images"
            lbl_dir = ROADS_ROOT / "val" / "labels"

        print(f"\n[{split}]")
        print(f"  images: {img_dir} exists={img_dir.exists()}")
        print(f"  labels: {lbl_dir} exists={lbl_dir.exists()}")
        log(f"\n[{split}] img={img_dir} lbl={lbl_dir}", also_print=False)

        if not img_dir.exists() or not lbl_dir.exists():
            print("  [SKIP]")
            continue

        images = {
            p.stem.lower(): p
            for p in img_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMG_EXTS_ALL
        }
        labels = {
            p.stem.lower(): p
            for p in lbl_dir.iterdir()
            if p.is_file() and p.suffix.lower() == ".txt"
        }

        total_img += len(images)
        total_lbl += len(labels)
        all_keys = sorted(set(images) | set(labels))
        matched = sorted(set(images) & set(labels))
        only_img = sorted(set(images) - set(labels))
        only_lbl = sorted(set(labels) - set(images))

        print(f"  img={len(images)} txt={len(labels)} khớp={len(matched)}")
        print(f"  thiếu label={len(only_img)} | thiếu ảnh={len(only_lbl)}")
        log(
            f"  img={len(images)} txt={len(labels)} match={len(matched)} "
            f"only_img={len(only_img)} only_lbl={len(only_lbl)}",
            also_print=False,
        )
        log(
            f"{'STT':>4} | {'Ảnh':<40} | {'Label':<40} | {'Khớp':<6} | {'TXT OK':<6}",
            also_print=False,
        )
        log("-" * 110, also_print=False)

        ok = fail_txt = 0
        for i, key in enumerate(all_keys, start=1):
            img_p = images.get(key)
            lbl_p = labels.get(key)
            matched_row = img_p is not None and lbl_p is not None
            txt_ok = False
            if matched_row:
                yolo = normalize_yolo_txt(lbl_p.read_text(encoding="utf-8", errors="ignore"))
                if yolo:
                    txt_ok = True
                    all_ok.append({
                        "stem": f"{split}_{img_p.stem}",
                        "img_path": img_p,
                        "label": yolo,
                    })
                    ok += 1
                else:
                    fail_txt += 1
            log(
                f"{i:>4} | {(img_p.name if img_p else ''):<40} | "
                f"{(lbl_p.name if lbl_p else ''):<40} | "
                f"{'YES' if matched_row else 'NO':<6} | "
                f"{'YES' if txt_ok else ('NO' if matched_row else '-'):<6}",
                also_print=False,
            )

        print(f"  → Lấy được={ok} | txt không hợp lệ={fail_txt}")
        log(f"  → OK={ok} fail_txt={fail_txt}", also_print=False)

    print(f"\nRoads_and_Bridges raw img≈{total_img} lbl≈{total_lbl} | lấy={len(all_ok)}")
    return all_ok


# ================== ULTRALYTICS CRACKSEG ==================
ULTRA_ROOT = Path("data/raw/public/Ultralytics_CrackSeg")
ULTRA_SPLITS = ("train", "val", "test")


def process_ultralytics_crackseg() -> list[dict]:
    print("\n" + "=" * 60)
    print("5) ULTRALYTICS_CRACKSEG — images + labels (.txt)")
    print("=" * 60)
    log("\n" + "=" * 60, also_print=False)
    log("5) ULTRALYTICS_CRACKSEG", also_print=False)

    if not ULTRA_ROOT.exists():
        print("[ERROR] Không thấy", ULTRA_ROOT)
        log(f"[ERROR] Không thấy {ULTRA_ROOT}", also_print=False)
        return []

    all_ok = []

    for split in ULTRA_SPLITS:
        img_dir = ULTRA_ROOT / "images" / split
        lbl_dir = ULTRA_ROOT / "labels" / split

        print(f"\n[{split}]")
        print(f"  images: {img_dir} exists={img_dir.exists()}")
        print(f"  labels: {lbl_dir} exists={lbl_dir.exists()}")
        log(f"\n[{split}] {img_dir} | {lbl_dir}", also_print=False)

        if not img_dir.exists() or not lbl_dir.exists():
            print("  [SKIP]")
            continue

        images = {
            p.stem.lower(): p
            for p in img_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMG_EXTS_ALL
        }
        labels = {
            p.stem.lower(): p
            for p in lbl_dir.iterdir()
            if p.is_file() and p.suffix.lower() == ".txt"
        }

        all_keys = sorted(set(images) | set(labels))
        matched = sorted(set(images) & set(labels))
        only_img = sorted(set(images) - set(labels))
        only_lbl = sorted(set(labels) - set(images))

        print(f"  img={len(images)} txt={len(labels)} khớp={len(matched)}")
        print(f"  thiếu label={len(only_img)} | thiếu ảnh={len(only_lbl)}")
        log(
            f"  img={len(images)} txt={len(labels)} match={len(matched)} "
            f"only_img={len(only_img)} only_lbl={len(only_lbl)}",
            also_print=False,
        )
        log(
            f"{'STT':>4} | {'Ảnh':<40} | {'Label':<40} | {'Khớp':<6} | {'TXT OK':<6}",
            also_print=False,
        )
        log("-" * 110, also_print=False)

        ok = fail_txt = 0
        for i, key in enumerate(all_keys, start=1):
            img_p = images.get(key)
            lbl_p = labels.get(key)
            matched_row = img_p is not None and lbl_p is not None
            txt_ok = False
            if matched_row:
                yolo = normalize_yolo_txt(lbl_p.read_text(encoding="utf-8", errors="ignore"))
                if yolo:
                    txt_ok = True
                    all_ok.append({
                        "stem": f"{split}_{img_p.stem}",
                        "img_path": img_p,
                        "label": yolo,
                    })
                    ok += 1
                else:
                    fail_txt += 1
            log(
                f"{i:>4} | {(img_p.name if img_p else ''):<40} | "
                f"{(lbl_p.name if lbl_p else ''):<40} | "
                f"{'YES' if matched_row else 'NO':<6} | "
                f"{'YES' if txt_ok else ('NO' if matched_row else '-'):<6}",
                also_print=False,
            )

        print(f"  → Lấy được={ok} | txt không hợp lệ={fail_txt}")
        log(f"  → OK={ok} fail_txt={fail_txt}", also_print=False)

    print(f"\nUltralytics_CrackSeg tổng: {len(all_ok)}")
    return all_ok


# ================== MAIN ==================
def main():
    write_report_header()
    print("=" * 60)
    print("BUILD CLEAN PHASE 1")
    print("Scan tất cả → OVERVIEW → yes một lần → primary train/val/test")
    print("=" * 60)

    approved: list[tuple[str, list]] = [
        ("CFD", process_cfd()),
        ("Crack500", process_crack500()),
        ("DeepCrack", process_deepcrack()),
        ("Roads_and_Bridges", process_roads_and_bridges()),
        ("Ultralytics_CrackSeg", process_ultralytics_crackseg()),
    ]
    approved = [(p, pairs) for p, pairs in approved if pairs]

    print("\n" + "=" * 60)
    print("OVERVIEW — ĐỌC KỸ TRƯỚC KHI GHI PRIMARY")
    print("=" * 60)
    log("\n" + "=" * 60, also_print=False)
    log("OVERVIEW — TỔNG HỢP TRƯỚC KHI XUẤT PRIMARY", also_print=False)
    log("=" * 60, also_print=False)

    total = 0
    log(f"{'Bộ dữ liệu':<22} | {'Số mẫu':>8} | Ghi chú", also_print=False)
    log("-" * 55, also_print=False)
    for prefix, pairs in approved:
        n = len(pairs)
        total += n
        print(f"  {prefix:22s} : {n:5d} mẫu")
        log(f"{prefix:<22} | {n:>8} | mask→YOLO / txt sẵn", also_print=False)

    print(f"\n  TỔNG sẽ ghi primary     : {total}")
    print(f"  Tỷ lệ chia              : train={TRAIN_RATIO:.0%} val={VAL_RATIO:.0%} test={1-TRAIN_RATIO-VAL_RATIO:.0%}")
    print(f"  Output                 : {OUT_BASE}")
    print(f"  Báo cáo                : {REPORT_FILE.resolve()}")
    log(f"\nTỔNG: {total}", also_print=False)
    log(f"Split: train={TRAIN_RATIO} val={VAL_RATIO} test={1-TRAIN_RATIO-VAL_RATIO}", also_print=False)
    log(f"Output: {OUT_BASE.resolve()}", also_print=False)

    if total == 0:
        print("\nKhông có dữ liệu. Dừng.")
        log("Không có dữ liệu — dừng.", also_print=False)
        return

    ans = input("\n>>> Gõ yes để XUẤT toàn bộ vào primary (train/val/test): ").strip().lower()
    if ans != "yes":
        print("Đã hủy. Không ghi primary.")
        log("User hủy — không ghi primary.", also_print=False)
        return

    written = {"train": 0, "val": 0, "test": 0}
    for prefix, pairs in approved:
        counts = write_pairs(pairs, prefix)
        for k in written:
            written[k] += counts[k]
        print(
            f"  Đã ghi {prefix}: "
            f"train={counts['train']} val={counts['val']} test={counts['test']}"
        )
        log(
            f"Đã ghi {prefix}: train={counts['train']} val={counts['val']} test={counts['test']}",
            also_print=False,
        )

    total_w = sum(written.values())
    print(f"\n✅ HOÀN TẤT — {total_w} mẫu")
    print(f"   train={written['train']} | val={written['val']} | test={written['test']}")
    print(f"   {OUT_BASE.resolve()}")
    print(f"   Báo cáo: {REPORT_FILE.resolve()}")
    log(
        f"\n✅ HOÀN TẤT — train={written['train']} val={written['val']} test={written['test']}",
        also_print=False,
    )

    # Tạo data.yaml sẵn cho YOLO / Kaggle
    yaml_path = OUT_BASE / "data.yaml"
    yaml_path.write_text(
        "\n".join([
            f"path: {OUT_BASE.resolve().as_posix()}",
            "train: images/train",
            "val: images/val",
            "test: images/test",
            "",
            "names:",
            "  0: crack",
            "",
        ]),
        encoding="utf-8",
    )
    print(f"   data.yaml: {yaml_path.resolve()}")
    log(f"data.yaml: {yaml_path.resolve()}", also_print=False)


if __name__ == "__main__":
    main()