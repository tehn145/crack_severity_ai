#!/usr/bin/env python3
"""
build_clean_phase1.py
Phase 1 — YOLO-Seg (polygon thống nhất 1 type)
  CFD | Crack500 | DeepCrack | Roads_and_Bridges | Ultralytics_CrackSeg

Mọi label đầu ra cùng 1 format:
  cls x1 y1 x2 y2 x3 y3 ...  (YOLO-seg polygon)

Nguồn:
  - Có mask (CFD, Crack500, DeepCrack): LUÔN convert mask → polygon dày
  - Chỉ có txt (Roads, Ultralytics): chuẩn hóa về cùng polygon
      (seg giữ; bbox → polygon 4 điểm)

Luồng: Scan → OVERVIEW → yes → primary/{train,val,test}
Train: YOLO("yolov8s-seg.pt")
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

IMG_EXTS_ALL = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

REPORT_DIR = Path("outputs/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FILE = REPORT_DIR / f"bao_cao_du_lieu_phase1_seg_{datetime.now():%Y%m%d_%H%M%S}.txt"

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

# Polygon dày (bám pixel hơn)
APPROX_EPS = 0.0001
MAX_POINTS = 400
MIN_AREA = 8
MIN_POINTS = 3


def log(msg: str = "", also_print: bool = True):
    if also_print:
        print(msg)
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def write_report_header():
    lines = [
        "=" * 72,
        "BÁO CÁO XỬ LÝ DỮ LIỆU — PHASE 1 PRIMARY (YOLO-SEG THỐNG NHẤT)",
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
        f"Tên đề tài (VI): {THESIS_TITLE_VI}",
        f"Tên đề tài (EN): {THESIS_TITLE_EN}",
        "",
        f"Thời điểm chạy : {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"File báo cáo   : {REPORT_FILE.resolve()}",
        "",
        "Quy ước label (1 type duy nhất):",
        "  YOLO-Seg polygon: cls x1 y1 x2 y2 x3 y3 ...",
        "  - Có mask → convert mask (polygon dày)",
        "  - Có txt  → chuẩn hóa seg; bbox → polygon 4 điểm",
        "",
        "Bộ xử lý: CFD | Crack500 | DeepCrack | Roads_and_Bridges | Ultralytics_CrackSeg",
        "Bỏ qua  : METU | SDNET2018 | Concrete_and_Pavement",
        "=" * 72,
        "",
    ]
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Báo cáo: {REPORT_FILE.resolve()}")


# ================== CONVERT THỐNG NHẤT ==================
def mask_to_yolo_seg(
    mask: np.ndarray,
    w: int,
    h: int,
    min_area: int = MIN_AREA,
    approx_eps: float = APPROX_EPS,
    min_points: int = MIN_POINTS,
    max_points: int = MAX_POINTS,
) -> str | None:
    """Mask → YOLO-seg polygon dày (bám pixel)."""
    if mask is None:
        return None
    if len(mask.shape) == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

    _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    lines = []
    for cnt in contours:
        if cv2.contourArea(cnt) < min_area:
            continue

        if approx_eps <= 0:
            pts = cnt.reshape(-1, 2)
        else:
            epsilon = max(approx_eps * cv2.arcLength(cnt, True), 0.3)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            pts = approx.reshape(-1, 2)

        if len(pts) < min_points:
            continue

        # Giới hạn số điểm (tránh label quá nặng)
        if len(pts) > max_points:
            idx = np.linspace(0, len(pts) - 1, max_points, dtype=int)
            pts = pts[idx]

        parts = ["0"]
        for p in pts:
            x = min(max(float(p[0]) / w, 0.0), 1.0)
            y = min(max(float(p[1]) / h, 0.0), 1.0)
            parts.append(f"{x:.6f}")
            parts.append(f"{y:.6f}")
        lines.append(" ".join(parts))

    return "\n".join(lines) if lines else None


def convert_mask_pair_seg(img_path: Path, mask_path: Path) -> str | None:
    img = cv2.imread(str(img_path))
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if img is None or mask is None:
        return None
    h, w = img.shape[:2]
    if mask.shape[:2] != (h, w):
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
    return mask_to_yolo_seg(mask, w, h)


def bbox_line_to_seg_polygon(parts: list[str]) -> str | None:
    """cls xc yc w h → polygon 4 điểm (cùng type seg)."""
    if len(parts) < 5:
        return None
    try:
        cls = int(float(parts[0]))
        xc, yc, bw, bh = [float(x) for x in parts[1:5]]
    except ValueError:
        return None
    x1 = min(max(xc - bw / 2, 0.0), 1.0)
    y1 = min(max(yc - bh / 2, 0.0), 1.0)
    x2 = min(max(xc + bw / 2, 0.0), 1.0)
    y2 = min(max(yc + bh / 2, 0.0), 1.0)
    return (
        f"{cls} {x1:.6f} {y1:.6f} {x2:.6f} {y1:.6f} "
        f"{x2:.6f} {y2:.6f} {x1:.6f} {y2:.6f}"
    )


def normalize_label_to_seg(text: str) -> str | None:
    """
    Mọi txt → cùng type polygon seg:
      - Đã là seg (>= 3 điểm) → chuẩn hóa số
      - Bbox (5 số) → polygon 4 điểm
    """
    lines = []
    for line in text.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        # Polygon seg
        if len(parts) >= 7:
            try:
                cls = int(float(parts[0]))
                coords = [min(max(float(x), 0.0), 1.0) for x in parts[1:]]
            except ValueError:
                continue
            if len(coords) >= 6 and len(coords) % 2 == 0:
                body = " ".join(f"{v:.6f}" for v in coords)
                lines.append(f"{cls} {body}")
                continue
        # Bbox → polygon
        if len(parts) >= 5:
            poly = bbox_line_to_seg_polygon(parts)
            if poly:
                lines.append(poly)
    return "\n".join(lines) if lines else None


def get_split(name: str) -> str:
    h = int(hashlib.md5(name.encode()).hexdigest(), 16) % 100
    if h < TRAIN_RATIO * 100:
        return "train"
    if h < (TRAIN_RATIO + VAL_RATIO) * 100:
        return "val"
    return "test"


def write_pairs(pairs: list[dict], prefix: str) -> dict:
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
        dst_lbl.write_text(item["label"].rstrip() + "\n", encoding="utf-8")
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
    print("1) CFD — mask → polygon seg (thống nhất)")
    print("=" * 60)
    log("\n" + "=" * 60, also_print=False)
    log("1) CFD mask→seg", also_print=False)

    if not CFD_ROOT.exists():
        print("[ERROR] Không thấy", CFD_ROOT)
        return []

    img_dir = cfd_find_dir(CFD_ROOT, "Images", ("images", "image", "img"))
    mask_dir = cfd_find_dir(CFD_ROOT, "Masks", ("masks", "mask", "lab", "labels"))
    print(f"Images: {img_dir} exists={img_dir.exists()}")
    print(f"Masks : {mask_dir} exists={mask_dir.exists()}")
    if not img_dir.exists() or not mask_dir.exists():
        return []

    images, masks = {}, {}
    for p in img_dir.iterdir():
        if p.is_file() and p.suffix.lower() in IMG_EXTS_ALL and not cfd_is_mask_name(p.stem):
            images[cfd_normalize_stem(p.stem)] = p
    for p in mask_dir.iterdir():
        if p.is_file() and p.suffix.lower() in IMG_EXTS_ALL:
            masks[cfd_normalize_stem(p.stem)] = p

    matched = sorted(set(images) & set(masks))
    ok_pairs, fail = [], 0
    log(f"{'STT':>4} | {'Ảnh':<40} | {'Mask':<40} | OK", also_print=False)

    for i, key in enumerate(matched, start=1):
        img_p, mask_p = images[key], masks[key]
        yolo = convert_mask_pair_seg(img_p, mask_p)
        log(
            f"{i:>4} | {img_p.name:<40} | {mask_p.name:<40} | {'YES' if yolo else 'NO'}",
            also_print=False,
        )
        if yolo:
            ok_pairs.append({"stem": img_p.stem, "img_path": img_p, "label": yolo})
        else:
            fail += 1

    print(f"Khớp={len(matched)} | SEG OK={len(ok_pairs)} | lỗi={fail}")
    return ok_pairs


# ================== CRACK500 ==================
CRACK500_ROOT = Path("data/raw/public/Crack500/CRACK500")
if not CRACK500_ROOT.exists():
    CRACK500_ROOT = Path("data/raw/public/Crack500")

FOLDERS_ALL = (
    [("traindata", "DATA"), ("testdata", "DATA")]
    + [(k, "CROP") for k in ("traincrop", "testcrop", "valcrop")]
    + [("valdata", "VALDATA")]
)
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
    """Chỉ lấy ảnh + mask (bỏ txt hỏng Crack500)."""
    images, masks = {}, {}
    for p in c500_list_files(folder):
        ext, stem = p.suffix.lower(), p.stem
        if ext in IMG_EXTS and not stem.lower().endswith("_mask"):
            images[stem] = p
        elif ext in MASK_EXTS:
            masks[strip_mask_suffix(stem)] = p
    return images, masks


def process_crack500() -> list[dict]:
    print("\n" + "=" * 60)
    print("2) CRACK500 — mask → polygon seg (bỏ txt, thống nhất)")
    print("=" * 60)
    log("\n" + "=" * 60, also_print=False)
    log("2) CRACK500 mask→seg", also_print=False)
    if not CRACK500_ROOT.exists():
        print("[ERROR] Không thấy", CRACK500_ROOT)
        return []

    all_ok = []
    for key, mode in FOLDERS_ALL:
        folder = c500_find_dir(CRACK500_ROOT, key)
        print(f"\n[{key}] {mode}")
        if folder is None:
            print("  [SKIP]")
            continue
        images, masks = collect_files(folder)
        img_l = {k.lower(): v for k, v in images.items()}
        mask_l = {k.lower(): v for k, v in masks.items()}
        matched = sorted(set(img_l) & set(mask_l))
        print(f"  img={len(images)} mask={len(masks)} khớp={len(matched)}")

        ok = fail = 0
        for lk in matched:
            img_p, mask_p = img_l[lk], mask_l[lk]
            yolo = convert_mask_pair_seg(img_p, mask_p)
            if yolo:
                all_ok.append({
                    "stem": f"{key}_{img_p.stem}",
                    "img_path": img_p,
                    "label": yolo,
                })
                ok += 1
            else:
                fail += 1
        print(f"  → SEG OK={ok} | lỗi={fail}")

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
    print("3) DEEPCRACK — mask → polygon seg (thống nhất)")
    print("=" * 60)
    log("\n" + "=" * 60, also_print=False)
    log("3) DEEPCRACK mask→seg", also_print=False)

    if not DEEPCRACK_ROOT.exists():
        print("[ERROR] Không thấy", DEEPCRACK_ROOT)
        return []

    root = deepcrack_find_root(DEEPCRACK_ROOT)
    print(f"Root: {root}")
    all_ok = []

    for img_name, lab_name in DC_PAIRS:
        img_dir, lab_dir = root / img_name, root / lab_name
        print(f"\n[{img_name} ↔ {lab_name}]")
        if not img_dir.exists() or not lab_dir.exists():
            print("  [SKIP]")
            continue
        images, masks = deepcrack_collect(img_dir), deepcrack_collect(lab_dir)
        matched = sorted(set(images) & set(masks))
        print(f"  img={len(images)} mask={len(masks)} khớp={len(matched)}")

        ok = fail = 0
        for key in matched:
            img_p, mask_p = images[key], masks[key]
            yolo = convert_mask_pair_seg(img_p, mask_p)
            if yolo:
                all_ok.append({
                    "stem": f"{img_name}_{img_p.stem}",
                    "img_path": img_p,
                    "label": yolo,
                })
                ok += 1
            else:
                fail += 1
        print(f"  → SEG OK={ok} | lỗi={fail}")

    print(f"\nDeepCrack tổng: {len(all_ok)}")
    return all_ok


# ================== ROADS AND BRIDGES ==================
ROADS_ROOT = Path("data/raw/public/Roads_and_Bridges")
ROADS_SPLITS = ("train", "valid", "test")


def process_roads_and_bridges() -> list[dict]:
    print("\n" + "=" * 60)
    print("4) ROADS — txt → polygon seg thống nhất (seg giữ / bbox→poly)")
    print("=" * 60)
    log("\n" + "=" * 60, also_print=False)
    log("4) ROADS txt→seg", also_print=False)

    if not ROADS_ROOT.exists():
        print("[ERROR] Không thấy", ROADS_ROOT)
        return []

    all_ok = []
    for split in ROADS_SPLITS:
        img_dir = ROADS_ROOT / split / "images"
        lbl_dir = ROADS_ROOT / split / "labels"
        if not img_dir.exists() and split == "valid":
            img_dir = ROADS_ROOT / "val" / "images"
            lbl_dir = ROADS_ROOT / "val" / "labels"

        print(f"\n[{split}]")
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
        matched = sorted(set(images) & set(labels))
        print(f"  img={len(images)} txt={len(labels)} khớp={len(matched)}")

        ok = fail = 0
        for key in matched:
            img_p, lbl_p = images[key], labels[key]
            # LUÔN chạy qua normalize → cùng type
            yolo = normalize_label_to_seg(
                lbl_p.read_text(encoding="utf-8", errors="ignore")
            )
            if yolo:
                all_ok.append({
                    "stem": f"{split}_{img_p.stem}",
                    "img_path": img_p,
                    "label": yolo,
                })
                ok += 1
            else:
                fail += 1
        print(f"  → SEG OK={ok} | lỗi={fail}")

    print(f"\nRoads_and_Bridges tổng: {len(all_ok)}")
    return all_ok


# ================== ULTRALYTICS ==================
ULTRA_ROOT = Path("data/raw/public/Ultralytics_CrackSeg")
ULTRA_SPLITS = ("train", "val", "test")


def process_ultralytics_crackseg() -> list[dict]:
    print("\n" + "=" * 60)
    print("5) ULTRALYTICS — txt → polygon seg thống nhất (re-normalize)")
    print("=" * 60)
    log("\n" + "=" * 60, also_print=False)
    log("5) ULTRALYTICS txt→seg", also_print=False)

    if not ULTRA_ROOT.exists():
        print("[ERROR] Không thấy", ULTRA_ROOT)
        return []

    all_ok = []
    for split in ULTRA_SPLITS:
        img_dir = ULTRA_ROOT / "images" / split
        lbl_dir = ULTRA_ROOT / "labels" / split
        print(f"\n[{split}]")
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
        matched = sorted(set(images) & set(labels))
        print(f"  img={len(images)} txt={len(labels)} khớp={len(matched)}")

        ok = fail = 0
        for key in matched:
            img_p, lbl_p = images[key], labels[key]
            # LUÔN convert/chuẩn hóa cùng type (không copy thô)
            yolo = normalize_label_to_seg(
                lbl_p.read_text(encoding="utf-8", errors="ignore")
            )
            if yolo:
                all_ok.append({
                    "stem": f"{split}_{img_p.stem}",
                    "img_path": img_p,
                    "label": yolo,
                })
                ok += 1
            else:
                fail += 1
        print(f"  → SEG OK={ok} | lỗi={fail}")

    print(f"\nUltralytics_CrackSeg tổng: {len(all_ok)}")
    return all_ok


# ================== MAIN ==================
def main():
    write_report_header()
    print("=" * 60)
    print("BUILD CLEAN PHASE 1 — YOLO-SEG 1 TYPE")
    print("Mọi label → polygon seg thống nhất")
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
    print("OVERVIEW")
    print("=" * 60)
    total = 0
    for prefix, pairs in approved:
        n = len(pairs)
        total += n
        print(f"  {prefix:22s} : {n:5d} mẫu")
        log(f"{prefix}: {n} mẫu (YOLO-seg polygon)", also_print=False)

    print(f"\n  TỔNG     : {total}")
    print(f"  Split    : train={TRAIN_RATIO:.0%} val={VAL_RATIO:.0%} test={1-TRAIN_RATIO-VAL_RATIO:.0%}")
    print(f"  Output   : {OUT_BASE}")
    print(f"  Báo cáo  : {REPORT_FILE.resolve()}")

    if total == 0:
        print("Không có dữ liệu. Dừng.")
        return

    ans = input("\n>>> Gõ yes để XUẤT primary SEG: ").strip().lower()
    if ans != "yes":
        print("Đã hủy.")
        return

    if OUT_BASE.exists():
        shutil.rmtree(OUT_BASE)
        print("  Đã xóa primary cũ.")

    written = {"train": 0, "val": 0, "test": 0}
    for prefix, pairs in approved:
        counts = write_pairs(pairs, prefix)
        for k in written:
            written[k] += counts[k]
        print(
            f"  Đã ghi {prefix}: "
            f"train={counts['train']} val={counts['val']} test={counts['test']}"
        )

    print(
        f"\n✅ HOÀN TẤT — "
        f"train={written['train']} val={written['val']} test={written['test']}"
    )
    print(f"   {OUT_BASE.resolve()}")

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
    print('   Train: YOLO("yolov8s-seg.pt")')


if __name__ == "__main__":
    main()