"""Unit test đặc trưng Lớp A (Phase 2 slot) — không cần model."""

from __future__ import annotations

import numpy as np
import pytest

from app.model_service import crack_features


def test_rectangle_mask_features():
    """Polygon hình chữ nhật 100x20 phải cho đúng length/width/area."""
    rect = np.array([[0, 0], [100, 0], [100, 20], [0, 20]], dtype=np.float64)
    f = crack_features(rect)
    assert f["length_px"] == pytest.approx(100, abs=0.5)
    assert f["width_px"] == pytest.approx(20, abs=0.5)
    assert f["area_px"] == pytest.approx(2000, abs=1)
    assert f["width_mean_px"] == pytest.approx(20, abs=0.5)


def test_diagonal_line_features():
    """Vết nứt chéo 45°: góc ~45°, length theo đường chéo."""
    diag = np.array([[0, 0], [60, 60]], dtype=np.float64)  # đoạn thẳng mảnh
    f = crack_features(diag)
    assert f["angle_deg"] == pytest.approx(45, abs=1.5)
    assert f["length_px"] == pytest.approx(60 * 2**0.5, abs=2)


def test_features_are_numeric_and_nonnegative():
    rng = np.random.default_rng(0)
    pts = rng.uniform(0, 300, size=(40, 2))
    f = crack_features(pts)
    for key in ("length_px", "width_px", "area_px", "angle_deg"):
        assert isinstance(f[key], float) and f[key] >= 0
    assert f["length_px"] >= f["width_px"]
    assert 0 <= f["angle_deg"] <= 90
