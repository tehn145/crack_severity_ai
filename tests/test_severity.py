"""Unit test rule-based severity (thang ĐỀ XUẤT — app/severity.py)."""

from __future__ import annotations

import pytest

from app.severity import SCALE_META, classify


def test_levels_cover_full_range():
    """Mọi giá trị width_mm dương phải rơi vào đúng 1 mức."""
    for mm in (0.01, 0.05, 0.099, 0.1, 0.15, 0.299, 0.3, 0.5, 0.99, 1.0, 5.0):
        r = classify(width_mean_px=100.0, gsd_mm_per_px=mm / 100.0)
        assert r is not None and 0 <= r["level"] <= 3


def test_thresholds():
    assert classify(50.0, 0.001)["level"] == 0      # 0.05 mm -> Hairline
    assert classify(100.0, 0.002)["level"] == 1     # 0.20 mm -> Minor
    assert classify(100.0, 0.005)["level"] == 2     # 0.50 mm -> Moderate
    assert classify(100.0, 0.012)["level"] == 3     # 1.20 mm -> Severe


def test_no_gsd_returns_none():
    assert classify(100.0, None) is None
    assert classify(100.0, 0.0) is None
    assert classify(None, 0.01) is None


def test_adjust_up():
    base = classify(100.0, 0.002)  # Minor
    bumped = classify(100.0, 0.002, multi_plane=True)
    assert bumped["level"] == base["level"] + 1
    assert bumped["bumps"] == 1
    assert any("đa mặt phẳng" in f for f in bumped["factors"])
    # Severe không vượt quá L3
    assert classify(100.0, 0.02, multi_plane=True)["level"] == 3


def test_long_thin_crack_escalates():
    """Vết DÀI 750mm nhưng MẢNH 0.15mm: width-only = L1, đa yếu tố phải lên L3.

    Case thực tế: bề rộng một mình không đánh giá được vết dài mảnh.
    """
    base = classify(15.0, 0.01, width_max_px=15.0, length_px=1500.0)  # dài 15mm < 300
    assert base["level"] == 1
    # dài 75000px × 0.01 = 750mm -> +1; contrast 0.5 đậm -> +1 => L3
    r = classify(15.0, 0.01, width_max_px=15.0, length_px=75000.0, contrast_ratio=0.5)
    assert r["level"] == 3
    assert r["bumps"] == 2
    assert any("dài" in f for f in r["factors"])
    assert any("đậm" in f for f in r["factors"])


def test_long_thin_not_dark_moderate():
    """Dài 750mm nhưng nhạt (contrast thấp): chỉ +1 vì dài -> L2."""
    r = classify(15.0, 0.01, width_max_px=15.0, length_px=75000.0, contrast_ratio=0.1)
    assert r["level"] == 2
    assert r["bumps"] == 1


def test_contrast_alone_bumps():
    r = classify(10.0, 0.05, contrast_ratio=0.6)  # 0.5mm -> L2, đậm -> L3
    assert r["level"] == 3


def test_bumps_capped_at_two():
    # đủ cả length + contrast + branching nhưng chỉ +2, chặn tại L3
    r = classify(15.0, 0.01, width_max_px=15.0, length_px=75000.0,
                 contrast_ratio=0.5, branching=True)
    assert r["level"] == 3
    assert r["bumps"] == 2


def test_scale_meta_is_proposal():
    assert SCALE_META["proposal"] is True
    assert SCALE_META["width_basis"] == "max"
    assert len(SCALE_META["levels"]) == 4


def test_length_mm():
    r = classify(10.0, 0.05, length_px=200.0)
    assert r["width_mm"] == pytest.approx(0.5)
    assert r["length_mm"] == pytest.approx(10.0)


def test_classify_by_max_width():
    """Chỉ số phân loại là bề rộng MAX (chuẩn ACI): mean nhỏ, max lớn → mức cao hơn."""
    r = classify(5.0, 0.1, width_max_px=80.0)  # max = 8mm → Severe dù mean 0.5mm
    assert r["level"] == 3
    assert r["basis"] == "mm_max"


def test_through_member_forces_l3():
    r = classify(1.0, 0.01, through_member=True)  # 0.01mm nhưng xuyên cấu kiện
    assert r["level"] == 3
    assert r["basis"] == "through_member"


def test_branching_adjust_up_once():
    plain = classify(50.0, 0.002)                      # 0.1mm -> Minor (L1)
    branched = classify(50.0, 0.002, branching=True)   # +1 -> Moderate (L2)
    assert plain["level"] == 1
    assert branched["level"] == 2
    assert branched["bumps"] == 1
    assert any("rẽ nhánh" in f for f in branched["factors"])
    # branching + multi_plane không cộng dồn 2 lần
    both = classify(50.0, 0.002, branching=True, multi_plane=True)
    assert both["level"] == 2
