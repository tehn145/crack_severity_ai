"""Phase 2 — Phân loại mức độ nghiêm trọng ĐA YẾU TỐ (rule-based).

Nguồn: docs/standards/severity_definition.md — ACI 224R-01 + TCVN 9381:2012.

Nguyên tắc thiết kế (giải thích được với hội đồng):
  1. **Bề rộng LỚN NHẤT là neo chuẩn ACI** — tra thang L0–L3 theo width_max × GSD.
  2. Bề rộng một mình KHÔNG ĐỦ: vết dài nhưng mảnh, hoặc vết mảnh nhưng đậm/sâu
     vẫn đáng lo. Vì vậy các yếu tố sau MỖI YẾU TỐ góp +1 mức (tối đa +2, trừ
     through_member mà đẩy thẳng L3):
       - CHIỀU DÀI: length_mm ≥ LENGTH_BUMP_MM (vết lan dài — extent của hư hỏng)
       - ĐỘ ĐẬM: contrast_ratio ≥ CONTRAST_BUMP (vết tối hơn nền rõ rệt —
         proxy cho độ sâu; vết cạn/hairline bề mặt thường mờ)
       - LỚP B: branching / multi_plane (mạng lưới nứt, giao cắt)
  3. through_member (kỹ sư đánh dấu) → L3 tuyệt đối.
  4. Mọi yếu tố làm tăng mức đều được trả về trong `factors` để hiển thị lý do.
  5. Thiếu GSD → KHÔNG phân loại (không đoán mò).
"""

from __future__ import annotations

from typing import Any

PROPOSAL = True  # False khi team nghiệm thu chính thức thang

# Ngưỡng yếu tố bổ sung (đề xuất, chỉnh tại đây khi có dữ liệu thực đo)
LENGTH_BUMP_MM = 300.0   # vết dài từ 300mm coi là lan rộng
CONTRAST_BUMP = 0.30     # vết tối hơn nền 30% coi là đậm (nghi sâu)

LEVELS: list[dict[str, Any]] = [
    {"level": 0, "name": "Hairline", "vi": "Nứt tóc — vô hại", "color": "#94a3b8", "max_mm": 0.1},
    {"level": 1, "name": "Minor", "vi": "Nhẹ — theo dõi định kỳ", "color": "#16a34a", "max_mm": 0.3},
    {"level": 2, "name": "Moderate", "vi": "Trung bình — cần đánh giá", "color": "#d97706", "max_mm": 1.0},
    {"level": 3, "name": "Severe", "vi": "Nghiêm trọng — kiểm tra kết cấu ngay", "color": "#dc2626", "max_mm": None},
]

SCALE_META = {
    "proposal": PROPOSAL,
    "reference": "ACI 224R-01 / TCVN 9381:2012 (đã chốt đề xuất 2026-10-23)",
    "width_basis": "max",
    "factors": {
        "length_bump_mm": LENGTH_BUMP_MM,
        "contrast_bump": CONTRAST_BUMP,
        "max_adjust": 2,
    },
    "levels": [
        {"level": lv["level"], "name": lv["name"], "vi": lv["vi"],
         "color": lv["color"], "range": (
             f"< {lv['max_mm']} mm" if lv["max_mm"] is not None else "≥ 1.0 mm")}
        for lv in LEVELS
    ],
}


def _level_of(width_mm: float) -> dict[str, Any]:
    return next(
        (lv for lv in LEVELS if lv["max_mm"] is None or width_mm < lv["max_mm"]),
        LEVELS[-1],
    )


def classify(
    width_mean_px: float | None,
    gsd_mm_per_px: float | None,
    width_max_px: float | None = None,
    length_px: float | None = None,
    branching: bool = False,
    multi_plane: bool = False,
    through_member: bool = False,
    contrast_ratio: float | None = None,
) -> dict | None:
    """Phân loại đa yếu tố. Trả None nếu thiếu GSD / thiếu bề rộng."""
    if gsd_mm_per_px is None or gsd_mm_per_px <= 0:
        return None
    if width_mean_px is None and width_max_px is None:
        return None

    w_mean_mm = (width_mean_px or 0.0) * gsd_mm_per_px
    w_max_mm = (width_max_px if width_max_px is not None else width_mean_px or 0.0) * gsd_mm_per_px
    length_mm = (length_px or 0.0) * gsd_mm_per_px

    if through_member:
        lv = LEVELS[3]
        basis = "through_member"
        factors = ["nứt xuyên cấu kiện (kỹ sư đánh dấu)"]
        bumps = 0
    else:
        lv = _level_of(w_max_mm)
        base_idx = lv["level"]
        basis = "mm_max"
        factors = []
        bumps = 0
        if length_mm >= LENGTH_BUMP_MM:
            factors.append(f"vết dài {length_mm:.0f} mm ≥ {LENGTH_BUMP_MM:.0f} mm")
            bumps += 1
        if contrast_ratio is not None and contrast_ratio >= CONTRAST_BUMP:
            factors.append(f"vết đậm (nền tối hơn {contrast_ratio:.0%}) — nghi sâu")
            bumps += 1
        if branching or multi_plane:
            which = "rẽ nhánh" if branching and not multi_plane else (
                "đa mặt phẳng" if multi_plane and not branching else "rẽ nhánh + đa mặt phẳng")
            factors.append(which)
            bumps += 1
        bumps = min(bumps, 2)  # tối đa +2 mức từ yếu tố bổ sung
        lv = LEVELS[min(3, base_idx + bumps)]

    return {
        "proposal": PROPOSAL,
        "level": lv["level"],
        "name": lv["name"],
        "vi": lv["vi"],
        "color": lv["color"],
        "width_mm": round(w_max_mm, 3),
        "width_mean_mm": round(w_mean_mm, 3),
        "length_mm": round(length_mm, 1) if length_px else None,
        "contrast": round(contrast_ratio, 3) if contrast_ratio is not None else None,
        "gsd_mm_per_px": gsd_mm_per_px,
        "bumps": bumps,
        "factors": factors,
        "through_member": through_member,
        "branching": branching,
        "multi_plane": multi_plane,
        "basis": basis,
    }
