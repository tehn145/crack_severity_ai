"""Unit test cho Phase 3 SHM Engine và Endpoints."""

from __future__ import annotations

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from scripts.evaluation.phase3_shm_engine import (
    RISK_MULTIPLIER,
    SCI_TIERS,
    SHMEngine,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_phase3_health(client):
    res = client.get("/api/phase3/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in {"ok", "degraded"}
    assert data["phase1_exists"] is True
    assert data["phase2_exists"] is True


def test_phase3_config(client):
    res = client.get("/api/phase3/config")
    assert res.status_code == 200
    data = res.json()
    assert "risk_multiplier" in data
    assert "column" in data["risk_multiplier"]
    assert len(data["sci_tiers"]) == 4


def test_phase3_shm_engine_logic():
    engine = SHMEngine()
    assert engine.phase1_weight is not None
    assert engine.phase2_weight is not None
    assert RISK_MULTIPLIER["beam_column_joint"] == 3.5
    assert len(SCI_TIERS) == 4


def test_phase3_analyze_endpoint(client):
    # Tạo một ảnh dummy xám
    img = np.full((300, 400, 3), 128, dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok

    files = {"file": ("test_wall.jpg", buf.tobytes(), "image/jpeg")}
    data = {"component_type": "column", "conf1": 0.25, "conf2": 0.25}

    res = client.post("/api/phase3/analyze", files=files, data=data)
    assert res.status_code == 200
    json_data = res.json()
    assert "sci_contribution" in json_data
    assert "component_type" in json_data
    assert json_data["component_type"] == "column"
    assert "annotated_b64" in json_data
    assert "fused_detections" in json_data
