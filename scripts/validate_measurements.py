#!/usr/bin/env python3
"""
validate_measurements.py — Kiểm chứng độ chính xác đo lường Lớp A (Phase 2).

Phương pháp: tạo ẢNH NHỊ PHÂN có vết nứt tổng hợp kích thước đã biết
(thanh các bề rộng 1–20px, các góc 0–90°, vết chữ Y) → lấy contour bằng
findContours (polygon khớp raster 100%) → chạy app/crack_features → so sánh.

Ngưỡng nghiệm thu (giới hạn lượng tử hóa pixel):
  - width_max: sai số tuyệt đối <= 1px
  - length:    sai số tuyệt đối <= 2px
  - angle:     lệch <= 1°
  - branching: Y phát hiện được, thẳng không báo nhầm

Chạy:  python scripts/validate_measurements.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np

from app.crack_features import crack_features

OUT = Path("outputs/reports")
OUT.mkdir(parents=True, exist_ok=True)
H, W = 600, 900


def strip_image(length: int, width: int, angle_deg: float = 0.0) -> np.ndarray:
    """Ảnh nhị phân thanh chữ nhật length × width (đúng w hàng raster), xoay."""
    img = np.zeros((H, W), np.uint8)
    box = cv2.boxPoints(((450, 300), (length, width), angle_deg)).astype(np.int32)
    cv2.fillPoly(img, [box], 255)
    return img


def y_image(arm: int, width: int, split_angle_deg: float = 45.0) -> np.ndarray:
    """Vết hình Y: thân dọc + 2 nhánh chéo."""
    img = np.zeros((H, W), np.uint8)
    cv2.rectangle(img, (450 - width // 2, 120), (450 + width // 2, 120 + arm), 255, -1)
    a = np.deg2rad(split_angle_deg)
    L = int(arm * 0.7)
    dx, dy = int(np.sin(a) * L), int(np.cos(a) * L)
    cv2.line(img, (450, 120 + arm), (450 - dx, 120 + arm + dy), 255, width)
    cv2.line(img, (450, 120 + arm), (450 + dx, 120 + arm + dy), 255, width)
    return img


def largest_contour_poly(img: np.ndarray) -> np.ndarray:
    cnts, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return max(cnts, key=cv2.contourArea).reshape(-1, 2)


def main() -> None:
    rows = []
    print("=" * 72)
    print("KIỂM CHỨNG ĐO LƯỜNG LỚP A (mask tổng hợp raster, GT đã biết)")
    print("=" * 72)

    # 1) Bề rộng: thanh ngang 200px, bề rộng 1..20px
    print("-- width_max --")
    for w_true in (1, 2, 3, 5, 8, 12, 20):
        poly = largest_contour_poly(strip_image(200, w_true))
        f = crack_features(poly.astype(np.float64))
        err = abs(f["width_max_px"] - w_true)
        rows.append(("width_max", w_true, f["width_max_px"], err, "px"))
        print(f"  width {w_true:>2}px -> đo {f['width_max_px']:>5.2f}  lệch {err:.2f}px")

    # 2) Chiều dài
    print("-- length --")
    for l_true in (50, 100, 200, 400):
        poly = largest_contour_poly(strip_image(l_true, 6))
        f = crack_features(poly.astype(np.float64))
        err = abs(f["length_px"] - l_true)
        rows.append(("length", l_true, f["length_px"], err, "px"))
        print(f"  length {l_true:>3}px -> đo {f['length_px']:>7.2f}  lệch {err:.2f}px")

    # 3) Góc trục chính (0 = ngang, 90 = dọc)
    print("-- angle --")
    for ang in (0, 30, 60, 90):
        poly = largest_contour_poly(strip_image(200, 4, ang))
        f = crack_features(poly.astype(np.float64))
        err = abs(f["angle_deg"] - ang)
        rows.append(("angle", ang, f["angle_deg"], err, "°"))
        print(f"  angle {ang:>2}° -> đo {f['angle_deg']:>5.1f}°  lệch {err:.2f}°")

    # 4) Branching
    print("-- branching --")
    f_y = crack_features(largest_contour_poly(y_image(80, 3)).astype(np.float64))
    f_line = crack_features(largest_contour_poly(strip_image(200, 3)).astype(np.float64))
    ok_y = f_y["branching"] and f_y["n_branches"] >= 1
    ok_line = not f_line["branching"]
    print(f"  vết Y  -> {'PHÁT HIỆN ✅' if ok_y else 'TRƯỢT ❌'} ({f_y['n_branches']} nhánh)")
    print(f"  thẳng  -> {'ổn (không nhánh) ✅' if ok_line else 'BÁO NHẦM ❌'}")

    # tổng kết theo ngưỡng
    wm_ok = all(r[3] <= 1.0 for r in rows if r[0] == "width_max")
    ln_ok = all(r[3] <= 2.0 for r in rows if r[0] == "length")
    an_ok = all(r[3] <= 1.0 for r in rows if r[0] == "angle")
    max_w = max(r[3] for r in rows if r[0] == "width_max")
    max_l = max(r[3] for r in rows if r[0] == "length")
    print("-" * 72)
    print(f"width_max: lệch tối đa {max_w:.2f}px  {'✅ ĐẠT (<=1px)' if wm_ok else '❌ VƯỢT'}")
    print(f"length:    lệch tối đa {max_l:.2f}px  {'✅ ĐẠT (<=2px)' if ln_ok else '❌ VƯỢT'}")
    print(f"angle:     {'✅ ĐẠT (<=1°)' if an_ok else '❌ VƯỢT'} | branching: {'✅' if ok_y and ok_line else '❌'}")
    verdict = wm_ok and ln_ok and an_ok and ok_y and ok_line
    print(f"\nKẾT LUẬN: {'✅ HỆ THỐNG ĐO ĐẠT NGHIỆM THU' if verdict else '❌ CẦN CHỈNH'}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md = OUT / f"validate_measurements_{stamp}.md"
    md.write_text(
        "# Kiểm chứng đo lường Lớp A (Phase 2)\n\n"
        f"- width_max: lệch tối đa **{max_w:.2f}px** (ngưỡng 1px — giới hạn lượng tử hóa)\n"
        f"- length: lệch tối đa **{max_l:.2f}px** (ngưỡng 2px)\n"
        f"- angle: {'đạt' if an_ok else 'trượt'} (<=1°) | branching: {'đạt' if ok_y and ok_line else 'trượt'}\n"
        f"- **Kết luận: {'ĐẠT NGHIỆM THU' if verdict else 'CHƯA ĐẠT'}**\n\n"
        "| Đại lượng | GT | Đo | Lệch |\n|---|---|---|---|\n"
        + "\n".join(f"| {n} | {gt}{u} | {meas:.2f}{u} | {err:.2f}{u} |" for n, gt, meas, err, u in rows)
        + "\n",
        encoding="utf-8",
    )
    print(f"\nBáo cáo: {md.resolve()}")


if __name__ == "__main__":
    main()
