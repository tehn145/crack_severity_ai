#!/usr/bin/env python3
"""
build_clean_phase1.py

Quét dữ liệu Phase 1, khớp tên ảnh–mask/txt, xuất 1 file Excel / 1 sheet (tiếng Việt).

KEEP (đúng miền khóa luận: bê tông, tường, đường, cầu):
  - 3DCrack_v1: mọi cặp ảnh + anno (mask)
  - crack_segmentation_dataset theo tiền tố:
        GIỮ : Eugen_Muller, noncrack, Rissbilder, Volker,
              DeepCrack, CFD, CRACK500, CrackTree, GAPS384
        LOẠI: forest, Sylvie (đá), 1 crop Volker đá
  - DeepCrack độc lập (train_img/test_img + lab)
  - Roads_and_Bridges, Ultralytics_CrackSeg: YOLO txt

DROP / không nhét vào primary:
  - CConCrack (trùng Khanh, Khanh đủ hơn)
  - METU / SDNET / Concrete_and_Pavement: chỉ class, không box/mask
    → ghi số liệu vào báo cáo, không ghi từng file (tránh phá 0.95)

Mục tiêu: ~40k ảnh, độ chính xác ~0.95 — xem khối TÌNH HÌNH 40K trong Excel.
"""

from __future__ import annotations

import hashlib
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm

# ================== CONFIG ==================
RAW_ROOT = Path("data/raw/public")
OUT_PRIMARY = Path("data/processed/phase1/primary")
OUT_NEG = Path("data/processed/phase1/negatives")
REPORT_DIR = Path("outputs/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT_XLSX = REPORT_DIR / f"build_clean_phase1_{STAMP}.xlsx"
SHEET_NAME = "Bao_cao_quet"

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
MASK_EXTS = IMG_EXTS
LBL_EXTS = {".txt"}

LABEL_MODE = "polygon"  # "box" | "polygon"
MIN_BOX_PX = 2
TRAIN_RATIO, VAL_RATIO = 0.80, 0.10
TARGET_N = 40_000
TARGET_ACC = 0.95

KHANH_KEEP_PREFIXES = (
    "eugen_muller",
    "eugen-muller",
    "eugenmuller",
    "noncrack",
    "rissbilder",
    "volker",
    "deepcrack",
)
# Bộ mặt đường: KHÔNG lấy theo chính sách mới (chỉ giữ bê tông/tường)
KHANH_REJECT_PREFIXES = (
    "forest",
    "sylvie_chambon",
    "sylvie",
    "cfd",
    "crack500",
    "cracktree",
    "gaps384",
    "gaps_",
)
KHANH_REJECT_STEMS = (
    "volker_dsc01625_578_1211_1171_1382",
)

FOLDER_ROADS = "Roads_and_Bridges"
FOLDER_ULTRA = "Ultralytics_CrackSeg"

DATASET_ORDER = [
    "3DCrack_v1",
    "crack_segmentation_dataset",
    "DeepCrack",
    "Roads_and_Bridges",
    "Ultralytics_CrackSeg",
]

POLICY_NOTES = [
    "Mục tiêu: ~40.000 ảnh, độ chính xác ~0.95 (train detection YOLOv8).",
    "CConCrack BỎ (trùng crack_segmentation_dataset, bộ kia đủ hơn).",
    "3DCrack_v1: giữ cặp ảnh–mask; mask toàn đen = không có vết nứt trên nhãn, không phải lỗi khớp tên.",
    "Khanh GIỮ tiền tố: Eugen_Muller, noncrack, Rissbilder, Volker, DeepCrack (bê tông/tường).",
    "KHÔNG lấy bộ mặt đường: CFD, CRACK500, CrackTree200, GAPS384 (theo chính sách mới).",
    "Khanh LOẠI: forest, Sylvie (đá), bộ mặt đường, 1 ảnh Volker đá.",
    "DeepCrack độc lập: quét train_img/test_img + lab.",
    "Roads_and_Bridges / Ultralytics: giữ txt hợp lệ; txt rỗng → ảnh âm (không nứt).",
    "METU / SDNET / Concrete_and_Pavement: chỉ class, không box → không đưa vào primary (sẽ phá 0.95 nếu gắn box cả ảnh).",
]

CSV_FIELDS = [
    "row_type",
    "stt",
    "dataset",
    "sub_source",
    "split_src",
    "image_name",
    "mask_name",
    "label_name",
    "has_mask",
    "has_label",
    "match",
    "convert",
    "include",
    "note",
]

# Cột tiếng Việt khi ghi Excel
COL_VI = {
    "row_type": "loai_dong",
    "stt": "stt",
    "dataset": "bo",
    "sub_source": "tap_con",
    "split_src": "tap_goc",
    "image_name": "ten_anh",
    "mask_name": "ten_mask",
    "label_name": "ten_nhan_txt",
    "has_mask": "co_mask",
    "has_label": "co_nhan_txt",
    "match": "khop_ten",
    "convert": "chuyen_doi",
    "include": "ket_luan",
    "note": "ghi_chu",
}

ROW_TYPE_VI = {
    "file": "file",
    "summary": "tom_tat",
    "overall": "tong",
    "blank": "",
    "goal": "muc_tieu",
}
INCLUDE_VI = {
    "primary": "lay_primary",
    "negative": "lay_anh_am",
    "exclude": "loai",
}
MATCH_VI = {
    "exact": "khop_chinh_xac",
    "partial": "khop_mot_phan",
    "none": "khong_khop",
}
YESNO_VI = {"yes": "co", "no": "khong"}

NOTE_VI = {
    "noncrack_to_negative": "noncrack → ảnh âm (nứt trang trí/gạch, phân biệt nứt nguy hại)",
    "mask_no_instance": "mask trống hoặc vết quá nhỏ, không tạo được box/polygon",
    "mask_empty": "mask toàn đen — nhãn gốc không có pixel nứt (không phải lỗi quét)",
    "invalid_txt": "file txt không đọc được / sai định dạng",
    "empty_txt": "file txt rỗng → ảnh âm (không nứt)",
    "txt_rong": "file txt rỗng → ảnh âm (không nứt)",
    "no_mask_or_label": "không có mask và không có txt",
    "name_mismatch": "tên ảnh không khớp mask/txt",
    "orphan_mask": "mask mồ côi (không có ảnh)",
    "orphan_label": "txt mồ côi (không có ảnh)",
    "folder_not_found": "không tìm thấy thư mục bộ dữ liệu",
    "rejected_stone_volker": "loại: crop Volker là nứt đá lớn",
    "not_in_whitelist": "không thuộc tiền tố được giữ",
    "invalid_txt_fallback_mask": "txt lỗi, đã chuyển từ mask",
}

POLICY_EXCLUDE_PREFIXES = ("rejected_prefix", "loai_theo_tien_to")
POLICY_EXCLUDE_NOTES = {
    "not_in_whitelist",
    "rejected_stone_volker",
    "loai: crop Volker là nứt đá lớn",
    "không thuộc tiền tố được giữ",
}


# ================== UTILS ==================
def list_files(root: Path | None, exts: set[str]) -> list[Path]:
    if not root or not root.exists():
        return []
    return sorted(
        p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in exts
    )


def child_dir(root: Path | None, *names: str) -> Path | None:
    if not root or not root.exists():
        return None
    want = {n.lower() for n in names}
    for p in root.iterdir():
        if p.is_dir() and p.name.lower() in want:
            return p
    return None


def resolve_dataset_root(root: Path) -> Path:
    cur = root
    markers = {
        "train", "val", "valid", "test",
        "images", "img", "masks", "mask", "anno",
        "labels", "label",
        "train_img", "test_img", "train_lab", "test_lab",
    }
    for _ in range(6):
        kids = [p for p in cur.iterdir() if p.is_dir()]
        if not kids:
            return cur
        names = {p.name.lower() for p in kids}
        if names & markers:
            return cur
        same = [
            p
            for p in kids
            if p.name.lower() in {root.name.lower(), cur.name.lower()}
        ]
        if len(same) == 1:
            cur = same[0]
            continue
        if len(kids) == 1:
            cur = kids[0]
            continue
        return cur
    return cur


def stem_norm(name: str) -> str:
    s = Path(name).stem.lower()
    s = re.sub(
        r"(_mask|-mask|mask_|_lab|-lab|_gt|-gt|_anno|-anno|_label|-label)$",
        "",
        s,
    )
    s = re.sub(r"(_seg|-seg|_poly)$", "", s)
    return s


def is_noncrack(name: str) -> bool:
    return Path(name).name.lower().startswith("noncrack") or "noncrack" in name.lower()


def find_raw_dir(keyword: str) -> Path | None:
    if not RAW_ROOT.exists():
        return None
    hits = [
        p
        for p in RAW_ROOT.iterdir()
        if p.is_dir() and keyword.lower() in p.name.lower()
    ]
    if not hits:
        return None
    return resolve_dataset_root(hits[0])


def detect_sub_source(filename: str) -> str:
    n = filename.lower()
    rules = [
        ("noncrack", "noncrack"),
        ("eugen_muller", "Eugen_Muller"),
        ("eugen-muller", "Eugen_Muller"),
        ("eugenmuller", "Eugen_Muller"),
        ("rissbilder", "Rissbilder"),
        ("volker", "Volker"),
        ("deepcrack", "DeepCrack"),
        ("crack500", "CRACK500"),
        ("cracktree", "CrackTree"),
        ("gaps384", "GAPS384"),
        ("gaps", "GAPS"),
        ("cfd", "CFD"),
        ("forest", "forest"),
        ("sylvie", "Sylvie_Chambon"),
    ]
    for key, label in rules:
        if n.startswith(key) or key in n:
            return label
    m = re.match(r"^([a-zA-Z]+(?:[_-][a-zA-Z]+)*)", Path(filename).stem)
    return m.group(1) if m else "unknown"


def _startswith_any(name: str, prefixes: tuple[str, ...]) -> str | None:
    n = Path(name).name.lower()
    for p in prefixes:
        if n.startswith(p):
            return p
    return None


def khanh_allowed(filename: str) -> tuple[bool, str]:
    stem = Path(filename).stem.lower()
    n = Path(filename).name.lower()
    if stem in KHANH_REJECT_STEMS or any(s in stem for s in KHANH_REJECT_STEMS):
        return False, "rejected_stone_volker"
    keep = _startswith_any(n, KHANH_KEEP_PREFIXES)
    if keep:
        return True, f"keep_prefix:{keep}"
    rej = _startswith_any(n, KHANH_REJECT_PREFIXES)
    if rej:
        return False, f"rejected_prefix:{rej}"
    return False, "not_in_whitelist"


def note_vi(note: str) -> str:
    if not note:
        return ""
    if note in NOTE_VI:
        return NOTE_VI[note]
    if note.startswith("rejected_prefix:"):
        return "loại theo tiền tố: " + note.split(":", 1)[1]
    if note.startswith("keep_prefix:"):
        return "giữ theo tiền tố: " + note.split(":", 1)[1]
    if note.startswith("error_detail:"):
        return "chi tiết lỗi: " + note_vi(note.split(":", 1)[1])
    if note.startswith("policy_exclude:"):
        return "loại theo chính sách: " + note_vi(note.split(":", 1)[1])
    return note


def is_policy_exclude(note: str) -> bool:
    n = note or ""
    return (
        n.startswith("rejected_prefix")
        or n.startswith("loại theo tiền tố")
        or n in {"not_in_whitelist", "rejected_stone_volker"}
    )


def partial_match(stem: str, candidates: dict[str, Path]) -> tuple[Path | None, str]:
    if stem in candidates:
        return candidates[stem], "exact"
    best, best_score = None, 0.0
    for cs, path in candidates.items():
        if stem in cs or cs in stem:
            score = min(len(stem), len(cs)) / max(len(stem), len(cs))
            if score > best_score:
                best_score, best = score, path
    if best is not None and best_score >= 0.55:
        return best, "partial"
    return None, "none"


def get_split(key: str) -> str:
    h = int(hashlib.md5(key.encode()).hexdigest(), 16) % 100
    if h < int(TRAIN_RATIO * 100):
        return "train"
    if h < int((TRAIN_RATIO + VAL_RATIO) * 100):
        return "val"
    return "test"


def file_md5(path: Path, chunk: int = 1 << 20) -> str:
    m = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            m.update(b)
    return m.hexdigest()


def _contours_to_lines(binary: np.ndarray, mode: str) -> list[str]:
    h, w = binary.shape[:2]
    lines: list[str] = []
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    for cnt in contours:
        if cv2.contourArea(cnt) < MIN_BOX_PX * MIN_BOX_PX:
            continue
        if mode == "box":
            x, y, bw, bh = cv2.boundingRect(cnt)
            if bw < MIN_BOX_PX or bh < MIN_BOX_PX:
                continue
            xc, yc = (x + bw / 2) / w, (y + bh / 2) / h
            nw, nh = bw / w, bh / h
            lines.append(f"0 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}")
        else:
            eps = 0.002 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, eps, True)
            pts_src = approx if len(approx) >= 3 else cnt
            if len(pts_src) < 3:
                x, y, bw, bh = cv2.boundingRect(cnt)
                if bw < MIN_BOX_PX or bh < MIN_BOX_PX:
                    continue
                xc, yc = (x + bw / 2) / w, (y + bh / 2) / h
                nw, nh = bw / w, bh / h
                lines.append(f"0 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}")
                continue
            pts: list[str] = []
            for p in np.asarray(pts_src).reshape(-1, 2):
                pts.extend([f"{p[0] / w:.6f}", f"{p[1] / h:.6f}"])
            lines.append("0 " + " ".join(pts))
    return lines


def mask_to_yolo_lines(mask_path: Path, mode: str = LABEL_MODE) -> tuple[list[str], str]:
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return [], "khong_doc_duoc_mask"
    if int(mask.max()) == 0:
        return [], "mask_empty"

    _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    if np.count_nonzero(binary) > binary.size * 0.5:
        binary = cv2.bitwise_not(binary)
    lines = _contours_to_lines(binary, mode)
    if lines:
        return lines, "ok"

    # mask xám mỏng: lấy mọi pixel > 0
    binary2 = np.where(mask > 0, 255, 0).astype(np.uint8)
    if np.count_nonzero(binary2) > binary2.size * 0.5:
        binary2 = cv2.bitwise_not(binary2)
    kernel = np.ones((3, 3), np.uint8)
    binary2 = cv2.morphologyEx(binary2, cv2.MORPH_CLOSE, kernel)
    lines = _contours_to_lines(binary2, mode)
    if lines:
        return lines, "ok"
    return [], "mask_no_instance"


def parse_yolo_txt(txt_path: Path) -> tuple[list[str], str]:
    try:
        text = txt_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return [], "invalid_txt"
    raw = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not raw:
        return [], "empty_txt"
    out: list[str] = []
    for line in raw:
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            vals = [float(x) for x in parts[1:]]
        except ValueError:
            continue
        vals = [min(1.0, max(0.0, v)) for v in vals]
        if len(vals) == 4:
            out.append(
                f"0 {vals[0]:.6f} {vals[1]:.6f} {vals[2]:.6f} {vals[3]:.6f}"
            )
        elif len(vals) >= 6 and len(vals) % 2 == 0:
            out.append("0 " + " ".join(f"{v:.6f}" for v in vals))
    if out:
        return out, "ok"
    return [], "invalid_txt"


def new_row(**kwargs) -> dict:
    base = {k: "" for k in CSV_FIELDS}
    base.update(kwargs)
    if not base.get("row_type"):
        base["row_type"] = "file"
    return base


def print_and_build_summary(
    dataset: str,
    file_rows: list[dict],
    extra_header: str = "",
    verbose: bool = True,
) -> list[dict]:
    n = len(file_rows)
    n_primary = sum(1 for r in file_rows if r["include"] == "primary")
    n_neg = sum(1 for r in file_rows if r["include"] == "negative")
    n_excl = sum(1 for r in file_rows if r["include"] == "exclude")
    n_mask = sum(1 for r in file_rows if r.get("has_mask") == "yes")
    n_lbl = sum(1 for r in file_rows if r.get("has_label") == "yes")
    n_no_mask = sum(
        1
        for r in file_rows
        if r.get("image_name") and r.get("has_mask") != "yes"
    )
    n_no_lbl = sum(
        1
        for r in file_rows
        if r.get("image_name") and r.get("has_label") != "yes"
    )

    error_rows = [
        r
        for r in file_rows
        if r["include"] == "exclude" and not is_policy_exclude(str(r.get("note", "")))
    ]
    policy_excl = [
        r
        for r in file_rows
        if r["include"] == "exclude" and is_policy_exclude(str(r.get("note", "")))
    ]
    err_notes = Counter(r.get("note") or "unknown" for r in error_rows)
    pol_notes = Counter(r.get("note") or "unknown" for r in policy_excl)
    sub_counts = Counter(r.get("sub_source") or "?" for r in file_rows)
    match_counts = Counter(r.get("match") or "none" for r in file_rows)

    lines = [
        f"=== TÓM TẮT {dataset} ===",
        extra_header,
        f"  so_file_quet           = {n}",
        f"  hop_le_primary         = {n_primary}   (khớp tên + chuyển được nhãn)",
        f"  anh_am                 = {n_neg}",
        f"  loai_tong              = {n_excl}",
        f"  co_mask                = {n_mask}",
        f"  khong_co_mask          = {n_no_mask}",
        f"  co_nhan_txt            = {n_lbl}",
        f"  khong_co_nhan_txt      = {n_no_lbl}",
        f"  file_loi               = {len(error_rows)}",
        f"  loai_theo_chinh_sach   = {len(policy_excl)}",
    ]
    if sub_counts:
        lines.append("  theo_tap_con:")
        for k, v in sorted(sub_counts.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"      {k}: {v}")
    if match_counts:
        lines.append("  theo_khop_ten:")
        for k, v in sorted(match_counts.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"      {MATCH_VI.get(k, k)}: {v}")
    if err_notes:
        lines.append("  chi_tiet_loi:")
        for k, v in err_notes.most_common():
            lines.append(f"      {note_vi(k)}: {v}")
    else:
        lines.append("  chi_tiet_loi: (không)")
    if pol_notes:
        lines.append("  loai_chinh_sach:")
        for k, v in pol_notes.most_common():
            lines.append(f"      {note_vi(k)}: {v}")
    text = "\n".join(x for x in lines if x != "")
    if verbose:
        print(text)

    out: list[dict] = []
    out.append(
        new_row(
            row_type="summary",
            dataset=dataset,
            note=f"----- TÓM TẮT {dataset} -----",
        )
    )
    kv = [
        ("so_file_quet", n),
        ("hop_le_primary", n_primary),
        ("anh_am", n_neg),
        ("loai_tong", n_excl),
        ("co_mask", n_mask),
        ("khong_co_mask", n_no_mask),
        ("co_nhan_txt", n_lbl),
        ("khong_co_nhan_txt", n_no_lbl),
        ("file_loi", len(error_rows)),
        ("loai_theo_chinh_sach", len(policy_excl)),
    ]
    for item, val in kv:
        out.append(
            new_row(
                row_type="summary",
                dataset=dataset,
                sub_source=item,
                include=str(val),
                note=item,
            )
        )
    for k, v in sorted(sub_counts.items(), key=lambda x: (-x[1], x[0])):
        out.append(
            new_row(
                row_type="summary",
                dataset=dataset,
                sub_source=f"tap_con:{k}",
                include=str(v),
                note="theo_tap_con",
            )
        )
    for k, v in err_notes.most_common():
        out.append(
            new_row(
                row_type="summary",
                dataset=dataset,
                sub_source=note_vi(k),
                include=str(v),
                note=f"chi_tiet_loi:{note_vi(k)}",
            )
        )
    for k, v in pol_notes.most_common():
        out.append(
            new_row(
                row_type="summary",
                dataset=dataset,
                sub_source=note_vi(k),
                include=str(v),
                note=f"loai_chinh_sach:{note_vi(k)}",
            )
        )
    out.append(new_row(row_type="blank"))
    return out


# ================== PAIR PROCESSOR ==================
def process_pairs(
    dataset_name: str,
    pairs: list[dict],
    rows: list[dict],
    primary_buf: list[dict],
    neg_buf: list[dict],
) -> None:
    for it in pairs:
        img: Path | None = it.get("img")
        mask = it.get("mask")
        label = it.get("label")
        match = it.get("match", "none")
        split_src = it.get("split_src", "")
        sub = it.get("sub_source") or (
            detect_sub_source(img.name) if img is not None else ""
        )
        preset_note = it.get("note", "")
        preset_include = it.get("include", "")

        convert, include, note = "", "exclude", preset_note
        yolo_lines: list[str] = []

        if img is None:
            include = "exclude"
            note = preset_note or "orphan_mask"
        elif preset_include == "exclude" and preset_note:
            include = "exclude"
            note = preset_note
        elif is_noncrack(img.name):
            include = "negative"
            note = "noncrack_to_negative"
        elif label is not None:
            yolo_lines, why = parse_yolo_txt(label)
            if why == "ok":
                convert = "none"
                include = "primary"
                note = ""
            elif why == "empty_txt":
                include = "negative"
                note = "empty_txt"
            elif mask is not None:
                convert = f"mask2{LABEL_MODE}"
                yolo_lines, mwhy = mask_to_yolo_lines(mask, LABEL_MODE)
                include = "primary" if yolo_lines else "exclude"
                note = "" if yolo_lines else mwhy
            else:
                include = "exclude"
                note = why
        elif mask is not None:
            convert = f"mask2{LABEL_MODE}"
            yolo_lines, mwhy = mask_to_yolo_lines(mask, LABEL_MODE)
            include = "primary" if yolo_lines else "exclude"
            note = "" if yolo_lines else mwhy
        else:
            note = "no_mask_or_label"

        if img is not None and match == "none" and include == "primary":
            include = "exclude"
            note = "name_mismatch"

        rows.append(
            new_row(
                dataset=dataset_name,
                sub_source=sub,
                split_src=split_src,
                image_name=img.name if img is not None else "",
                mask_name=mask.name if mask else "",
                label_name=label.name if label else "",
                has_mask="yes" if mask is not None else "no",
                has_label="yes" if label is not None else "no",
                match=match,
                convert=convert,
                include=include,
                note=note,
            )
        )

        if img is None:
            continue
        rec = {
            "img": img,
            "lines": yolo_lines,
            "dataset": dataset_name,
            "sub_source": sub,
            "key": f"{dataset_name}_{sub}_{img.name}",
        }
        if include == "primary":
            primary_buf.append(rec)
        elif include == "negative":
            neg_buf.append(rec)


def _mark_used_and_orphans(
    dataset_name: str,
    pairs: list[dict],
    mask_map: dict[str, Path],
    rows: list[dict],
    primary_buf: list[dict],
    neg_buf: list[dict],
) -> None:
    used_masks: set[str] = set()
    for it in pairs:
        m = it.get("mask")
        if m is not None:
            used_masks.add(stem_norm(m.name))
    process_pairs(dataset_name, pairs, rows, primary_buf, neg_buf)
    orphans = []
    for stem, path in mask_map.items():
        if stem in used_masks:
            continue
        orphans.append(
            {
                "img": None,
                "mask": path,
                "label": None,
                "split_src": "",
                "match": "none",
                "sub_source": detect_sub_source(path.name),
                "note": "orphan_mask",
                "include": "exclude",
            }
        )
    if orphans:
        process_pairs(dataset_name, orphans, rows, primary_buf, neg_buf)


# ================== COLLECTORS ==================
def collect_3dcrack(rows, primary_buf, neg_buf) -> None:
    root = find_raw_dir("3dcrack")
    name = "3DCrack_v1"
    if root is None:
        print("[BỎ QUA] Không thấy thư mục 3DCrack trong", RAW_ROOT)
        rows.append(
            new_row(
                dataset=name,
                include="exclude",
                note="folder_not_found",
                has_mask="no",
                has_label="no",
            )
        )
        return
    print(f"[3DCrack] thư mục gốc = {root}")
    pairs = []
    mask_map_all: dict[str, Path] = {}
    for split in ("train", "val", "test"):
        split_dir = child_dir(root, split)
        if split_dir is None:
            continue
        img_dir = child_dir(split_dir, "img", "images", "image")
        anno_dir = child_dir(split_dir, "anno", "mask", "masks")
        imgs = list_files(img_dir, IMG_EXTS)
        mask_map = {
            stem_norm(p.name): p for p in list_files(anno_dir, MASK_EXTS)
        }
        mask_map_all.update(mask_map)
        print(
            f"  tập={split_dir.name}: ảnh={len(imgs)} mask={len(mask_map)}"
        )
        for img in imgs:
            m, match = partial_match(stem_norm(img.name), mask_map)
            pairs.append(
                {
                    "img": img,
                    "mask": m,
                    "label": None,
                    "split_src": split,
                    "match": match,
                    "sub_source": "3DCrack",
                }
            )
    start = len(rows)
    _mark_used_and_orphans(
        name, pairs, mask_map_all, rows, primary_buf, neg_buf
    )
    print(f"[OK] {name} số cặp quét: {len(pairs)}")
    print_and_build_summary(name, rows[start:])


def collect_khanh(rows, primary_buf, neg_buf) -> None:
    root = find_raw_dir("crack_segmentation") or find_raw_dir("khanh")
    name = "crack_segmentation_dataset"
    if root is None:
        print("[BỎ QUA] Không thấy crack_segmentation_dataset trong", RAW_ROOT)
        rows.append(
            new_row(
                dataset=name,
                include="exclude",
                note="folder_not_found",
                has_mask="no",
                has_label="no",
            )
        )
        return
    print(f"[Khanh] thư mục gốc = {root}")

    img_slots: list[tuple[str, Path]] = []
    mask_dirs: list[Path] = []
    for split in ("train", "test", "val", "valid"):
        sd = child_dir(root, split)
        if sd is None:
            continue
        idir = child_dir(sd, "images", "img", "image")
        mdir = child_dir(sd, "masks", "mask", "anno")
        if idir:
            img_slots.append((split, idir))
        if mdir:
            mask_dirs.append(mdir)
    top_img = child_dir(root, "images", "img", "image")
    top_mask = child_dir(root, "masks", "mask", "anno")
    if top_img:
        img_slots.append(("", top_img))
    if top_mask:
        mask_dirs.append(top_mask)

    mask_map: dict[str, Path] = {}
    for d in mask_dirs:
        for p in list_files(d, MASK_EXTS):
            mask_map.setdefault(stem_norm(p.name), p)

    img_meta: dict[str, tuple[Path, str]] = {}
    for split, d in img_slots:
        for p in list_files(d, IMG_EXTS):
            key = p.name.lower()
            if key not in img_meta:
                img_meta[key] = (p, split)

    print(
        f"  ảnh unique={len(img_meta)} mask unique={len(mask_map)} "
        f"(đã unwrap + khử trùng train/test/images)"
    )

    pairs = []
    keep_n = 0
    for img, split in img_meta.values():
        ok, reason = khanh_allowed(img.name)
        sub = detect_sub_source(img.name)
        if not ok:
            pairs.append(
                {
                    "img": img,
                    "mask": None,
                    "label": None,
                    "split_src": split,
                    "match": "none",
                    "sub_source": sub,
                    "note": reason,
                    "include": "exclude",
                }
            )
            continue
        keep_n += 1
        m, match = partial_match(stem_norm(img.name), mask_map)
        pairs.append(
            {
                "img": img,
                "mask": m,
                "label": None,
                "split_src": split,
                "match": match,
                "sub_source": sub,
            }
        )

    start = len(rows)
    keep_mask_map = {
        s: p for s, p in mask_map.items() if khanh_allowed(p.name)[0]
    }
    _mark_used_and_orphans(
        name, pairs, keep_mask_map, rows, primary_buf, neg_buf
    )
    print(
        f"[OK] {name} ứng viên giữ theo tiền tố: {keep_n} / {len(img_meta)} ảnh unique"
    )
    print_and_build_summary(name, rows[start:])


def collect_deepcrack_standalone(rows, primary_buf, neg_buf) -> None:
    raw = find_raw_dir("deepcrack")
    name = "DeepCrack"
    if raw is None:
        print("[BỎ QUA] Không thấy DeepCrack độc lập")
        return
    # tìm cặp train_img/train_lab, test_img/test_lab dù lồng sâu
    pairs = []
    mask_map_all: dict[str, Path] = {}
    found = False
    for img_key, lab_key, split in (
        ("train_img", "train_lab", "train"),
        ("test_img", "test_lab", "test"),
    ):
        img_dirs = [p for p in raw.rglob("*") if p.is_dir() and p.name.lower() == img_key]
        lab_dirs = [p for p in raw.rglob("*") if p.is_dir() and p.name.lower() == lab_key]
        if not img_dirs:
            continue
        found = True
        img_dir, lab_dir = img_dirs[0], (lab_dirs[0] if lab_dirs else None)
        imgs = list_files(img_dir, IMG_EXTS)
        mask_map = {
            stem_norm(p.name): p for p in list_files(lab_dir, MASK_EXTS)
        }
        mask_map_all.update(mask_map)
        print(f"[DeepCrack] {split}: ảnh={len(imgs)} mask={len(mask_map)}")
        for img in imgs:
            m, match = partial_match(stem_norm(img.name), mask_map)
            pairs.append(
                {
                    "img": img,
                    "mask": m,
                    "label": None,
                    "split_src": split,
                    "match": match,
                    "sub_source": "DeepCrack",
                }
            )
    if not found:
        print("[BỎ QUA] DeepCrack không có train_img/test_img")
        return
    start = len(rows)
    _mark_used_and_orphans(
        name, pairs, mask_map_all, rows, primary_buf, neg_buf
    )
    print(f"[OK] {name} số cặp quét: {len(pairs)}")
    print_and_build_summary(name, rows[start:])


def collect_yolo_ready(
    name: str, root: Path, rows, primary_buf, neg_buf
) -> None:
    if not root.exists():
        print(f"[BỎ QUA] Không thấy {root}")
        rows.append(
            new_row(
                dataset=name,
                include="exclude",
                note="folder_not_found",
                has_mask="no",
                has_label="no",
            )
        )
        return
    root = resolve_dataset_root(root)
    print(f"[{name}] thư mục gốc = {root}")
    pairs, seen = [], set()
    splits: list[tuple[str, Path, Path]] = []
    seen_split_dirs: set[str] = set()
    images_root = child_dir(root, "images")
    labels_root = child_dir(root, "labels")
    for sp in ("train", "val", "valid", "test"):
        sp_dir = child_dir(root, sp)
        if sp_dir is not None:
            idir = child_dir(sp_dir, "images", "img")
            ldir = child_dir(sp_dir, "labels", "label")
            if idir:
                key = str(idir.resolve())
                if key not in seen_split_dirs:
                    seen_split_dirs.add(key)
                    splits.append((sp, idir, ldir or (sp_dir / "labels")))
        if images_root is not None:
            idir = child_dir(images_root, sp)
            ldir = child_dir(labels_root, sp) if labels_root else None
            if idir:
                key = str(idir.resolve())
                if key not in seen_split_dirs:
                    seen_split_dirs.add(key)
                    splits.append(
                        (
                            sp,
                            idir,
                            ldir
                            or (
                                labels_root / sp
                                if labels_root
                                else images_root
                            ),
                        )
                    )
    if not splits:
        images_root = child_dir(root, "images")
        labels_root = child_dir(root, "labels")
        if images_root:
            splits.append(("", images_root, labels_root or (root / "labels")))

    lbl_all: dict[str, Path] = {}
    for split, img_dir, lbl_dir in splits:
        lbl_map = {
            stem_norm(p.name): p for p in list_files(lbl_dir, LBL_EXTS)
        }
        lbl_all.update(lbl_map)
        n_img = 0
        for img in list_files(img_dir, IMG_EXTS):
            key = str(img.resolve())
            if key in seen:
                continue
            seen.add(key)
            n_img += 1
            lb, match = partial_match(stem_norm(img.name), lbl_map)
            pairs.append(
                {
                    "img": img,
                    "mask": None,
                    "label": lb,
                    "split_src": split,
                    "match": match,
                    "sub_source": name,
                }
            )
        print(f"  tập={split or '-'}: ảnh={n_img} txt={len(lbl_map)}")

    start = len(rows)
    used = {
        stem_norm(it["label"].name)
        for it in pairs
        if it.get("label") is not None
    }
    process_pairs(name, pairs, rows, primary_buf, neg_buf)
    orphans = []
    for stem, path in lbl_all.items():
        if stem in used:
            continue
        orphans.append(
            {
                "img": None,
                "mask": None,
                "label": path,
                "split_src": "",
                "match": "none",
                "sub_source": name,
                "note": "orphan_label",
                "include": "exclude",
            }
        )
    if orphans:
        process_pairs(name, orphans, rows, primary_buf, neg_buf)
    print(f"[OK] {name} số cặp quét: {len(pairs)}")
    print_and_build_summary(name, rows[start:])


def count_class_only() -> list[dict]:
    """Đếm bộ chỉ có class, không liệt kê từng file."""
    recs: list[dict] = []

    def n_img(p: Path) -> int:
        if not p.exists():
            return 0
        return sum(1 for x in p.iterdir() if x.is_file() and x.suffix.lower() in IMG_EXTS)

    metu = RAW_ROOT / "METU"
    recs.append(
        {
            "bo": "METU",
            "positive": n_img(metu / "Positive"),
            "negative": n_img(metu / "Negative"),
            "ghi_chu": "chỉ class crack/no-crack, không mask/box → không đưa primary",
        }
    )
    cap = RAW_ROOT / "Concrete_and_Pavement"
    recs.append(
        {
            "bo": "Concrete_and_Pavement",
            "positive": n_img(cap / "Positive"),
            "negative": n_img(cap / "Negative"),
            "ghi_chu": "chỉ class; Mixed đường+bê tông; không đưa primary",
        }
    )
    sd = RAW_ROOT / "SDNET2018"
    sd_root = None
    if sd.exists():
        hits = list(sd.rglob("SDNET2018"))
        sd_root = hits[-1] if hits else sd
    def sd_n(*parts: str) -> int:
        if sd_root is None:
            return 0
        p = sd_root
        for a in parts:
            nxt = child_dir(p, a)
            if nxt is None:
                return 0
            p = nxt
        return n_img(p)

    recs.append(
        {
            "bo": "SDNET2018",
            "positive": sd_n("D", "CD") + sd_n("W", "CW"),
            "negative": sd_n("D", "UD") + sd_n("W", "UW"),
            "ghi_chu": "chỉ class; giữ D (sàn cầu)+W (tường); bỏ P (pavement) theo chính sách tải",
        }
    )
    return recs


# ================== EXCEL ==================
def row_to_vi(r: dict) -> dict:
    out = {}
    for eng, vie in COL_VI.items():
        val = r.get(eng, "")
        if eng == "row_type":
            val = ROW_TYPE_VI.get(val, val)
        elif eng == "include":
            val = INCLUDE_VI.get(val, val)
        elif eng == "match":
            val = MATCH_VI.get(val, val)
        elif eng in ("has_mask", "has_label"):
            val = YESNO_VI.get(val, val)
        elif eng == "note":
            val = note_vi(str(val)) if val else ""
        out[vie] = val
    return out


def goal_block(n_primary: int, n_neg: int, class_recs: list[dict]) -> list[dict]:
    thieu = max(0, TARGET_N - n_primary)
    pos_class = sum(r["positive"] for r in class_recs)
    neg_class = sum(r["negative"] for r in class_recs)
    notes = [
        f"MỤC TIÊU: {TARGET_N} ảnh, độ chính xác {TARGET_ACC:.2f}.",
        f"Hiện PRIMARY có mask/txt (detection): {n_primary} ảnh. Ảnh âm có nhãn: {n_neg}.",
        f"Còn thiếu so với 40k nếu chỉ đếm primary: {thieu}.",
        "KHÔNG gắn box cả khung cho METU/SDNET/Concrete Positive — localization kém, khó đạt 0.95.",
        f"Kho class-only (tham khảo, không primary): positive={pos_class}, negative={neg_class}.",
        "Hướng đạt 0.95: train YOLO trên primary sạch (~20k) + ảnh âm (noncrack, txt rỗng, METU Negative mẫu).",
        "Hướng đủ 40k sau này: bổ sung nguồn detection có mask/box mới, hoặc pseudo-label expanded SAU KHI model primary đã ≥0.95 — không trộn ẩu từ đầu.",
    ]
    out = [
        new_row(
            row_type="goal",
            dataset="MUC_TIEU_40K",
            note=notes[0],
        )
    ]
    for i, t in enumerate(notes, 1):
        out.append(
            new_row(
                row_type="goal",
                dataset="MUC_TIEU_40K",
                sub_source=f"y{i}",
                include=str(n_primary if i == 2 else thieu if i == 3 else ""),
                note=t,
            )
        )
    for r in class_recs:
        out.append(
            new_row(
                row_type="goal",
                dataset="CLASS_ONLY",
                sub_source=r["bo"],
                image_name=f"positive={r['positive']}",
                label_name=f"negative={r['negative']}",
                include=str(r["positive"] + r["negative"]),
                note=r["ghi_chu"],
            )
        )
    out.append(new_row(row_type="blank"))
    return out


def write_excel_report(
    rows: list[dict],
    primary_buf: list[dict],
    neg_buf: list[dict],
    class_recs: list[dict] | None = None,
    write_stats: dict | None = None,
) -> Path:
    file_rows = [r for r in rows if r.get("row_type", "file") == "file"]
    class_recs = class_recs or []
    n_primary = sum(1 for r in file_rows if r["include"] == "primary")
    n_neg = sum(1 for r in file_rows if r["include"] == "negative")
    out_rows: list[dict] = []

    out_rows.append(
        new_row(
            row_type="summary",
            dataset="CHINH_SACH",
            note=" | ".join(POLICY_NOTES),
        )
    )
    out_rows.append(
        new_row(
            row_type="summary",
            dataset="CHINH_SACH",
            sub_source="che_do_nhan",
            include=LABEL_MODE,
            note=str(RAW_ROOT.resolve()),
        )
    )
    out_rows.append(
        new_row(
            row_type="summary",
            dataset="CHINH_SACH",
            sub_source="buffer_primary_truoc_khu_trung",
            include=str(len(primary_buf)),
        )
    )
    out_rows.append(
        new_row(
            row_type="summary",
            dataset="CHINH_SACH",
            sub_source="buffer_anh_am_truoc_khu_trung",
            include=str(len(neg_buf)),
        )
    )
    out_rows.extend(goal_block(n_primary, n_neg, class_recs))

    by_ds: dict[str, list[dict]] = defaultdict(list)
    for r in file_rows:
        by_ds[r.get("dataset") or "unknown"].append(r)

    order = [d for d in DATASET_ORDER if d in by_ds]
    order += sorted(k for k in by_ds if k not in DATASET_ORDER)

    stt = 1
    for ds in order:
        group = by_ds[ds]
        for r in group:
            r = dict(r)
            r["stt"] = stt
            r["row_type"] = "file"
            stt += 1
            out_rows.append(r)
        out_rows.extend(print_and_build_summary(ds, group, verbose=False))

    out_rows.append(
        new_row(
            row_type="overall",
            dataset="TONG",
            note="----- TỔNG TOÀN BỘ CÁC BỘ -----",
        )
    )
    overall_block = print_and_build_summary("TONG", file_rows, verbose=True)
    for r in overall_block:
        r["row_type"] = "overall"
        r["dataset"] = "TONG"
        out_rows.append(r)

    if write_stats is not None:
        out_rows.append(
            new_row(
                row_type="overall",
                dataset="GHI_RA_DIA",
                note="----- THỐNG KÊ GHI FILE -----",
            )
        )
        for k in ("train", "val", "test", "dup", "name_clash", "negatives"):
            out_rows.append(
                new_row(
                    row_type="overall",
                    dataset="GHI_RA_DIA",
                    sub_source=k,
                    include=str(write_stats.get(k, 0)),
                )
            )

    vi_rows = [row_to_vi(r) for r in out_rows]
    df = pd.DataFrame(vi_rows)
    cols = list(COL_VI.values())
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    df = df[cols]

    with pd.ExcelWriter(REPORT_XLSX, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
    return REPORT_XLSX


# ================== WRITE OUTPUT ==================
def clear_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def polygon_lines(lines: list[str]) -> list[str]:
    """Ép mọi dòng nhãn về polygon: dòng box (cls cx cy w h) -> polygon 4 điểm chữ nhật.
    Train *-seg* của Ultralytics yêu cầu dataset thuần segment, không được trộn box."""
    out: list[str] = []
    for ln in lines:
        p = ln.split()
        if len(p) == 5:
            cls = int(float(p[0]))
            cx, cy, w, h = (float(x) for x in p[1:])
            x1, y1, x2, y2 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
            out.append(
                f"{cls} "
                + " ".join(f"{v:.6f}" for v in (x1, y1, x2, y1, x2, y2, x1, y2))
            )
        else:
            out.append(ln)
    return out


def write_primary(primary_buf: list[dict]) -> dict:
    clear_dir(OUT_PRIMARY)
    for sp in ("train", "val", "test"):
        (OUT_PRIMARY / "images" / sp).mkdir(parents=True, exist_ok=True)
        (OUT_PRIMARY / "labels" / sp).mkdir(parents=True, exist_ok=True)

    seen_hash: set[str] = set()
    used_stems: set[str] = set()
    stats = {"train": 0, "val": 0, "test": 0, "dup": 0, "name_clash": 0}

    for rec in tqdm(primary_buf, desc="Ghi primary"):
        img: Path = rec["img"]
        try:
            h = file_md5(img)
        except Exception:
            h = rec["key"]
        if h in seen_hash:
            stats["dup"] += 1
            continue
        seen_hash.add(h)

        sp = get_split(rec["key"])
        stem = f'{rec["dataset"]}_{rec.get("sub_source", "x")}_{Path(img.name).stem}'
        stem = re.sub(r"[^\w\-]+", "_", stem)
        # Windows FS không phân biệt hoa/thường + chuẩn hóa ký tự có thể làm
        # 2 file gốc khác nhau ra cùng tên đầu ra → file sau đè file trước.
        # Thêm hậu tố _2, _3... để không mất ảnh.
        base = stem
        k = 2
        while stem.lower() in used_stems:
            stem = f"{base}_{k}"
            k += 1
        used_stems.add(stem.lower())
        if stem != base:
            stats["name_clash"] += 1
        out_img = OUT_PRIMARY / "images" / sp / f"{stem}{img.suffix.lower()}"
        out_lbl = OUT_PRIMARY / "labels" / sp / f"{stem}.txt"
        shutil.copy2(img, out_img)
        out_lbl.write_text(
            "\n".join(polygon_lines(rec["lines"])) + "\n", encoding="utf-8"
        )
        stats[sp] += 1
    return stats


def write_neg(neg_buf: list[dict]) -> int:
    clear_dir(OUT_NEG)
    n = 0
    seen: set[str] = set()
    for rec in neg_buf:
        img: Path = rec["img"]
        try:
            h = file_md5(img)
        except Exception:
            h = str(img)
        if h in seen:
            continue
        seen.add(h)
        stem = f'{rec["dataset"]}_{Path(img.name).stem}'
        stem = re.sub(r"[^\w\-]+", "_", stem)
        shutil.copy2(img, OUT_NEG / f"{stem}{img.suffix.lower()}")
        n += 1
    return n


def main() -> None:
    print("=" * 60)
    print("XÂY DỮ LIỆU SẠCH PHASE-1")
    print("Báo cáo tiếng Việt | 1 file Excel | 1 sheet")
    print(f"Mục tiêu: {TARGET_N} ảnh, độ chính xác {TARGET_ACC:.2f}")
    print("=" * 60)
    print(f"RAW_ROOT = {RAW_ROOT.resolve()}")
    print(f"BÁO CÁO  = {REPORT_XLSX.resolve()}")

    rows: list[dict] = []
    primary_buf: list[dict] = []
    neg_buf: list[dict] = []

    collect_3dcrack(rows, primary_buf, neg_buf)
    collect_khanh(rows, primary_buf, neg_buf)
    collect_deepcrack_standalone(rows, primary_buf, neg_buf)
    collect_yolo_ready(
        "Roads_and_Bridges", RAW_ROOT / FOLDER_ROADS, rows, primary_buf, neg_buf
    )
    collect_yolo_ready(
        "Ultralytics_CrackSeg",
        RAW_ROOT / FOLDER_ULTRA,
        rows,
        primary_buf,
        neg_buf,
    )
    class_recs = count_class_only()
    print("\n=== Bộ chỉ có class (không primary) ===")
    for r in class_recs:
        print(
            f"  {r['bo']}: positive={r['positive']} negative={r['negative']} | {r['ghi_chu']}"
        )

    print("\n" + "=" * 60)
    print("Đang ghi Excel (1 file, 1 sheet, tiếng Việt)...")
    xlsx_path = write_excel_report(rows, primary_buf, neg_buf, class_recs)
    print(f"\nĐã ghi báo cáo: {xlsx_path.resolve()}")
    print(f"Sheet: {SHEET_NAME}")
    print(f"Buffer primary (trước khử trùng): {len(primary_buf)}")
    print(f"Buffer ảnh âm (trước khử trùng): {len(neg_buf)}")

    ans = input("\nGõ yes để GHI primary + ảnh âm ra đĩa: ").strip().lower()
    if ans != "yes":
        print("Đã hủy ghi đĩa. Chỉ có file Excel.")
        return

    stats = write_primary(primary_buf)
    n_neg = write_neg(neg_buf)
    stats["negatives"] = n_neg
    write_excel_report(rows, primary_buf, neg_buf, class_recs, write_stats=stats)

    print("\nXong.")
    print(
        f"Primary: {stats['train'] + stats['val'] + stats['test']} "
        f"(train={stats['train']}, val={stats['val']}, test={stats['test']})"
    )
    print(f"Trùng bỏ (md5): {stats['dup']}")
    print(f"Đụng tên (đã thêm hậu tố): {stats['name_clash']}")
    print(f"Ảnh âm:   {n_neg}")
    print(f"Excel:    {REPORT_XLSX.resolve()}")


if __name__ == "__main__":
    main()
