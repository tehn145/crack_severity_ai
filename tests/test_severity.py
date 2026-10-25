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
    assert bumped["adjusted_up"] is True
    # Severe không vượt quá L3
    assert classify(100.0, 0.02, multi_plane=True)["level"] == 3


def test_scale_meta_is_proposal():
    assert SCALE_META["proposal"] is True
    assert len(SCALE_META["levels"]) == 4


def test_length_mm():
    r = classify(10.0, 0.05, length_px=200.0)
    assert r["width_mm"] == pytest.approx(0.5)
    assert r["length_mm"] == pytest.approx(10.0)
