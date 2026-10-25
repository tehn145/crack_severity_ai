"""Phân loại mức độ nghiêm trọng — RULE-BASED theo bản ĐỀ XUẤT thang 4 mức.

Nguồn: docs/severity_definition.md (ACI 224R-01 + TCVN 9381:2012).
TRẠNG THÁI: bản đề xuất chờ team chốt — mọi output đều gắn cờ `proposal: True`
và UI hiển thị disclaimer. Khi team chốt, chỉ sửa bảng THRESHOLDS_MM tại đây.

Bề rộng dùng để phân loại: bề rộng TRUNG BÌNH (area_px / length_px × GSD).
Không có GSD (mm/px) → KHÔNG phân loại (trả None, không đoán mò).
"""

from __future__ import annotations

from typing import Any

PROPOSAL = True  # cờ toàn cục: thang chưa được team phê duyệt chính thức

# (level, tên hiển thị, màu UI, ngưỡng trên [mm, lấy mức <])
LEVELS: list[dict[str, Any]] = [
    {"level": 0, "name": "Hairline", "vi": "Nứt tóc — vô hại", "color": "#7f8c8d", "max_mm": 0.1},
    {"level": 1, "name": "Minor", "vi": "Nhẹ — theo dõi định kỳ", "color": "#27ae60", "max_mm": 0.3},
    {"level": 2, "name": "Moderate", "vi": "Trung bình — cần đánh giá", "color": "#f39c12", "max_mm": 1.0},
    {"level": 3, "name": "Severe", "vi": "Nghiêm trọng — kiểm tra kết cấu ngay", "color": "#c0392b", "max_mm": None},
]

SCALE_META = {
    "proposal": PROPOSAL,
    "reference": "ACI 224R-01 / TCVN 9381:2012 (bản đề xuất — chờ team chốt)",
    "levels": [
        {"level": lv["level"], "name": lv["name"], "vi": lv["vi"],
         "color": lv["color"], "range": (
             f"< {lv['max_mm']} mm" if lv["max_mm"] is not None else "≥ 1.0 mm")}
        for lv in LEVELS
    ],
}


def classify(
    width_mean_px: float | None,
    gsd_mm_per_px: float | None,
    length_px: float | None = None,
    multi_plane: bool = False,
    branching: bool = False,
) -> dict | None:
    """Trả về kết quả phân loại hoặc None nếu chưa đủ dữ liệu định lượng."""
    if width_mean_px is None or gsd_mm_per_px is None or gsd_mm_per_px <= 0:
        return None
    width_mm = width_mean_px * gsd_mm_per_px
    level = next((lv for lv in LEVELS if lv["max_mm"] is None or width_mm < lv["max_mm"]), LEVELS[-1])
    bumped = False
    # Điều chỉnh +1 mức theo Lớp B / mật độ (theo mục 4 severity_definition.md)
    if (multi_plane or branching) and level["level"] < 3:
        level = LEVELS[level["level"] + 1]
        bumped = True
    return {
        "proposal": PROPOSAL,
        "level": level["level"],
        "name": level["name"],
        "vi": level["vi"],
        "color": level["color"],
        "width_mm": round(width_mm, 3),
        "length_mm": round(length_px * gsd_mm_per_px, 1) if length_px else None,
        "gsd_mm_per_px": gsd_mm_per_px,
        "adjusted_up": bumped,
        "basis": "mm",
    }
