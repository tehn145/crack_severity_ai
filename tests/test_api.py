"""Smoke test API. Test cần model (/api/predict) tự bỏ qua nếu chưa có weight."""

from __future__ import annotations

import base64
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
WEIGHT_EXISTS = Path("weights/phase1/best.pt").exists()


def _png_bytes(w: int = 320, h: int = 240) -> bytes:
    img = np.full((h, w, 3), 128, dtype=np.uint8)
    cv2.line(img, (10, 120), (300, 110), (255, 255, 255), 3)  # "vết nứt" trắng
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in {"ok", "degraded"}
    assert "version" in body


def test_meta_and_index():
    assert client.get("/api/meta").status_code == 200
    r = client.get("/")
    assert r.status_code == 200
    assert "Crack Severity AI" in r.text


@pytest.mark.skipif(not WEIGHT_EXISTS, reason="chưa có weights/phase1/best.pt")
def test_predict_schema():
    r = client.post(
        "/api/predict",
        files={"file": ("test.png", _png_bytes(), "image/png")},
        data={"conf": "0.25", "imgsz": "640"},
    )
    assert r.status_code == 200
    body = r.json()
    for key in ("n_cracks", "elapsed_ms", "image_wh", "detections", "annotated_jpg_b64"):
        assert key in body
    for det in body["detections"]:
        assert 0 <= det["conf"] <= 1
        assert len(det["bbox"]) == 4
    base64.b64decode(body["annotated_jpg_b64"])  # decode được


def test_inspection_roundtrip_without_model():
    """Lưu + đọc + export hồ sơ không cần chạy model."""
    r = client.post(
        "/api/inspections",
        files={"file": ("test.png", _png_bytes(), "image/png")},
        data={
            "detections_json": '[{"conf":0.9,"bbox":[1,2,3,4],"length_px":10.0,'
                               '"width_px":2.0,"area_px":20.0,"angle_deg":45.0}]',
            "building": "Tòa A", "floor": "T12", "component": "cột", "note": "demo",
        },
    )
    assert r.status_code == 200
    ins_id = r.json()["id"]

    lst = client.get("/api/inspections").json()
    assert any(x["id"] == ins_id for x in lst)

    detail = client.get(f"/api/inspections/{ins_id}/report.html")
    assert detail.status_code == 200
    assert "Tòa A" in detail.text

    csv = client.get("/api/inspections/export.csv")
    assert csv.status_code == 200
    assert "ma_ho_so" in csv.text and "Tòa A" in csv.text


def test_predict_rejects_non_image():
    if not WEIGHT_EXISTS:
        pytest.skip("cần weight để tới bước decode model")
    r = client.post(
        "/api/predict",
        files={"file": ("x.bin", b"not-an-image", "application/octet-stream")},
    )
    assert r.status_code == 400
