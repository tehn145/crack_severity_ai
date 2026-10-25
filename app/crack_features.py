"""Đặc trưng Lớp A của 1 vết nứt (Phase 2) — đo từ mask polygon, đơn vị pixel.

Bao trọn vẹn morphology theo ARCHITECTURE.md:
  - length_px / width_px     : minAreaRect (chiều dài / bề rộng bao)
  - width_mean_px            : area / length (bề rộng trung bình)
  - width_max_px             : 2 × max distance-transform bên trong mask
                               (bề rộng lớn nhất — đúng cách kỹ sư dùng ke đo)
  - branching                : có điểm rẽ nhánh trên skeleton (Zhang-Suen)
  - n_branches / n_endpoints : số điểm nhánh / đầu mút của skeleton
  - density_ratio            : diện tích vết / diện tích bbox (mức đặc)
"""

from __future__ import annotations

import cv2
import numpy as np


def _crop_mask(poly: np.ndarray) -> tuple[np.ndarray, int, int]:
    """Rasterize polygon và trả (mask crop theo bbox, offset_x, offset_y)."""
    pts = np.asarray(poly, dtype=np.float32).reshape(-1, 1, 2)
    x, y, w, h = cv2.boundingRect(pts.astype(np.int32))
    m = np.zeros((h + 2, w + 2), dtype=np.uint8)
    shifted = pts - [x - 1, y - 1]
    cv2.fillPoly(m, [shifted.astype(np.int32)], 1)
    return m, x - 1, y - 1


def _thin_zhang_suen(img: np.ndarray) -> np.ndarray:
    """Làm mảnh nhị phân (Zhang-Suen) — không cần scikit-image."""
    img = (img > 0).astype(np.uint8)
    changed = True
    while changed:
        changed = False
        for step in (0, 1):
            p = np.pad(img, 1)
            p2, p3, p4, p5 = p[0:-2, 1:-1], p[0:-2, 2:], p[1:-1, 2:], p[2:, 2:]
            p6, p7, p8, p9 = p[2:, 1:-1], p[2:, 0:-2], p[1:-1, 0:-2], p[0:-2, 0:-2]
            neigh = [p2, p3, p4, p5, p6, p7, p8, p9]
            b = sum(neigh)
            seq = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
            a = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(np.uint8) for i in range(8))
            if step == 0:
                cond = (p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)
            else:
                cond = (p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0)
            remove = (img == 1) & (b >= 2) & (b <= 6) & (a == 1) & cond
            if remove.any():
                img[remove] = 0
                changed = True
    return img


def _skeleton_stats(mask: np.ndarray) -> tuple[int, int]:
    """Số điểm rẽ nhánh (>=3 láng giềng) và đầu mút (==1) trên skeleton."""
    sk = _thin_zhang_suen(mask)
    p = np.pad(sk, 1)
    n = (
        p[0:-2, 1:-1] + p[0:-2, 2:] + p[1:-1, 2:] + p[2:, 2:]
        + p[2:, 1:-1] + p[2:, 0:-2] + p[1:-1, 0:-2] + p[0:-2, 0:-2]
    )
    branch_pts = int(((sk == 1) & (n >= 3)).sum())
    endpoints = int(((sk == 1) & (n == 1)).sum())
    return branch_pts, endpoints


def crack_features(mask_xy: np.ndarray) -> dict:
    """Đặc trưng đầy đủ của 1 vết nứt từ polygon pixel coords (N,2)."""
    pts = np.asarray(mask_xy, dtype=np.float32).reshape(-1, 1, 2)
    (_, _), (rw, rh), angle = cv2.minAreaRect(pts)
    length, width = float(max(rw, rh)), float(min(rw, rh))
    area = float(cv2.contourArea(pts.astype(np.float32)))

    mask, _, _ = _crop_mask(mask_xy)
    dist = cv2.distanceTransform((mask > 0).astype(np.uint8), cv2.DIST_L2, 3)
    width_max = float(dist.max()) * 2.0 if dist.size else 0.0

    n_branch, n_end = _skeleton_stats(mask)

    bbox_area = max(1.0, length * width)
    angle_norm = abs(angle) if abs(angle) <= 90 else 180 - abs(angle)
    return {
        "length_px": round(length, 1),
        "width_px": round(width, 1),
        "width_mean_px": round(area / max(length, 1e-6), 2),
        "width_max_px": round(width_max, 2),
        "area_px": round(area, 1),
        "angle_deg": round(float(angle_norm), 1),
        "branching": n_branch >= 1,
        "n_branches": n_branch,
        "n_endpoints": n_end,
        "density_ratio": round(area / bbox_area, 4),
    }
