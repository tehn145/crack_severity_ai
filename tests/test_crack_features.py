"""Unit test đặc trưng Lớp A v2 (app/crack_features.py)."""

from __future__ import annotations

import numpy as np
import pytest

from app.crack_features import contrast_ratio, crack_features


def test_rectangle_basic():
    rect = np.array([[0, 0], [100, 0], [100, 20], [0, 20]], dtype=np.float64)
    f = crack_features(rect)
    assert f["length_px"] == pytest.approx(100, abs=1)
    assert f["width_mean_px"] == pytest.approx(20, abs=1)
    assert f["width_max_px"] == pytest.approx(20, abs=2)
    assert f["area_px"] == pytest.approx(2000, abs=5)
    assert f["branching"] is False


def test_thin_line_no_branch():
    diag = np.array([[0, 0], [60, 60]], dtype=np.float64)
    f = crack_features(diag)
    assert f["n_branches"] == 0
    assert f["n_endpoints"] >= 1
    assert f["angle_deg"] == pytest.approx(45, abs=1.5)


def test_y_shape_has_branch():
    """Vết hình chữ Y phải phát hiện rẽ nhánh (Phase 2: branching)."""
    # thân dọc + 2 nhánh trên
    pts = []
    for y in range(60):                      # thân dọc
        pts += [(50 + dx, y) for dx in (-1, 0, 1)]
    for t in range(40):                      # nhánh trái đi lên
        pts += [(50 - t, 60 - t) for _ in range(1)]
    for t in range(40):                      # nhánh phải đi lên
        pts += [(50 + t, 60 - t) for _ in range(1)]
    f = crack_features(np.array(pts, dtype=np.float64))
    assert f["branching"] is True
    assert f["n_branches"] >= 1


def test_density_ratio_bounds():
    rect = np.array([[0, 0], [100, 0], [100, 20], [0, 20]], dtype=np.float64)
    f = crack_features(rect)
    assert 0 < f["density_ratio"] <= 1.0


def test_keys_present():
    rng = np.random.default_rng(1)
    pts = rng.uniform(0, 300, size=(60, 2))
    f = crack_features(pts)
    for key in ("length_px", "width_px", "width_mean_px", "width_max_px",
                "area_px", "angle_deg", "branching", "n_branches",
                "n_endpoints", "density_ratio"):
        assert key in f


def test_contrast_ratio_dark_vs_faint():
    """Vết ĐẬM (đen trên nền sáng) contrast cao; vết NHẠT contrast thấp."""
    img = np.full((200, 200, 3), 180, dtype=np.uint8)  # nền xám 180
    img[100:103, 40:160] = 10                          # vết đen đậm
    poly_dark = np.array([[40, 100], [160, 100], [160, 102], [40, 102]], dtype=np.float64)
    r_dark = contrast_ratio(img, poly_dark)
    assert r_dark is not None and r_dark > 0.5

    img2 = np.full((200, 200, 3), 180, dtype=np.uint8)
    img2[100:103, 40:160] = 170                        # vết nhạt (chỉ tối hơn 10)
    poly_faint = np.array([[40, 100], [160, 100], [160, 102], [40, 102]], dtype=np.float64)
    r_faint = contrast_ratio(img2, poly_faint)
    assert r_faint is not None and r_faint < 0.15

    assert r_dark > r_faint + 0.3


def test_contrast_ratio_edge_cases():
    img = np.full((100, 100, 3), 180, dtype=np.uint8)
    assert contrast_ratio(img, None) is None           # không có mask
    assert contrast_ratio(None, np.array([[0, 0], [1, 1]])) is None
    # vết sáng hơn nền -> clamp về 0
    img[50:53, 20:80] = 255
    poly = np.array([[20, 50], [80, 50], [80, 52], [20, 52]], dtype=np.float64)
    assert contrast_ratio(img, poly) == 0.0
