"""Tầng model — load YOLO một lần, inference, trích đặc trưng Lớp A (Phase 2 slot).

Quy tắc dự án (AGENTS.md): KHÔNG hard-code mức độ nghiêm trọng ở đây.
Đặc trưng Lớp A chỉ là ĐO LƯỜNG (px) để Phase 2 tiêu thụ sau khi chốt thang
ACI 224R-01 / TCVN 9381:2012.
"""

from __future__ import annotations

import os
from pathlib import Path

import cv2
import numpy as np

MODEL_PATH = Path(os.environ.get("MODEL_PATH", "weights/phase1/best.pt"))
MODEL_REPO = os.environ.get("MODEL_REPO", "")  # vd "tehn145/crack-phase1" trên HF
DEFAULT_CONf = float(os.environ.get("DEFAULT_CONF", "0.25"))
DEFAULT_IMGSZ = int(os.environ.get("DEFAULT_IMGSZ", "640"))

_model = None


def get_model():
    """Lazy-load model (app khởi động nhanh cả khi chưa có weight)."""
    global _model
    if _model is not None:
        return _model
    if not MODEL_PATH.exists() and MODEL_REPO:
        # Deploy (HF Spaces): tải weight từ Hugging Face model repo khi runtime
        from huggingface_hub import hf_hub_download

        local = hf_hub_download(
            repo_id=MODEL_REPO, filename="best.pt",
            token=os.environ.get("HF_TOKEN") or None,
        )
        target = Path("weights_runtime/best.pt")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(Path(local).read_bytes())
        MODEL_PATH_local = target
    else:
        MODEL_PATH_local = MODEL_PATH
    if not MODEL_PATH_local.exists():
        raise FileNotFoundError(
            f"Không tìm thấy weight {MODEL_PATH_local}. "
            "Đặt MODEL_PATH hoặc MODEL_REPO (HF) trong env."
        )
    from ultralytics import YOLO

    _model = YOLO(str(MODEL_PATH_local))
    return _model


def crack_features(mask_xy: np.ndarray) -> dict:
    """Đặc trưng Lớp A từ polygon mask của 1 vết nứt (đơn vị pixel).

    - length_px / width_px: từ minAreaRect (chiều dài = cạnh lớn).
    - angle_deg: hướng chính của vết nứt (0 = ngang, 90 = dọc).
    - area_px: diện tích trù polygon.
    - width_mean_px: ước lượng bề rộng trung bình = area / length.
    """
    pts = np.asarray(mask_xy, dtype=np.float32).reshape(-1, 1, 2)
    (_, _), (wh), angle = cv2.minAreaRect(pts)
    length, width = max(wh), min(wh)
    area = float(cv2.contourArea(pts.astype(np.float32)))
    # minAreaRect trả góc [-90, 0): chuẩn hóa về [0, 90]
    angle_norm = abs(angle) if abs(angle) <= 90 else 180 - abs(angle)
    return {
        "length_px": round(float(length), 1),
        "width_px": round(float(width), 1),
        "width_mean_px": round(area / max(length, 1e-6), 2),
        "area_px": round(area, 1),
        "angle_deg": round(float(angle_norm), 1),
    }


def detect(
    img_bgr: np.ndarray,
    conf: float | None = None,
    imgsz: int | None = None,
    gsd_mm_per_px: float | None = None,
) -> tuple[list[dict], np.ndarray, float]:
    """Chạy Phase 1 trên 1 ảnh BGR. Trả về (detections, ảnh chú thích, thời gian ms).

    gsd_mm_per_px: thang đo ảnh (mm/pixel) — có thì gắn phân loại severity đề xuất.
    """
    import time

    from .severity import classify

    model = get_model()
    t0 = time.perf_counter()
    res = model.predict(
        img_bgr,
        conf=conf or DEFAULT_CONf,
        imgsz=imgsz or DEFAULT_IMGSZ,
        verbose=False,
    )[0]
    elapsed_ms = (time.perf_counter() - t0) * 1000

    detections: list[dict] = []
    n_masks = 0 if res.masks is None else len(res.masks)
    for i, box in enumerate(res.boxes):
        x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
        det = {
            "conf": round(float(box.conf[0]), 4),
            "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
        }
        if i < n_masks:
            poly = res.masks.xy[i]  # (N, 2) pixel coords
            feats = crack_features(poly)
            det.update(feats)
            det["mask_points"] = [[round(float(p[0]), 1), round(float(p[1]), 1)] for p in poly]
            det["severity"] = classify(
                feats.get("width_mean_px"), gsd_mm_per_px, feats.get("length_px")
            )
        else:
            det["severity"] = None
        detections.append(det)

    annotated = res.plot()  # BGR, đã vẽ mask + box + conf
    return detections, annotated, elapsed_ms
