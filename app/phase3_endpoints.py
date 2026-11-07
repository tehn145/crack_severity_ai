"""FastAPI Router cho Phase 3 — Structural Health Monitoring (SHM).

Endpoints:
  GET  /api/phase3/health         → Kiểm tra trạng thái tải của 2 model Phase 1.2 & Phase 2
  GET  /api/phase3/config         → Trọng số cấu kiện (RISK_MULTIPLIER), thang phân cấp SCI
  POST /api/phase3/analyze        → Phân tích hư hỏng kết cấu từ 1 ảnh đơn (Dual inference)
  POST /api/phase3/analyze-folder → Phân tích toàn bộ tập ảnh tầng/công trình (Khử trùng lặp ORB + SCI)
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Annotated, List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from scripts.evaluation.phase3_shm_engine import (
    DEFAULT_PHASE1_WEIGHT,
    DEFAULT_PHASE2_WEIGHT,
    RISK_MULTIPLIER,
    SCI_TIERS,
    SHMEngine,
)

router = APIRouter(prefix="/api/phase3", tags=["Phase 3 SHM"])

_engine: Optional[SHMEngine] = None


def get_shm_engine() -> SHMEngine:
    """Khởi tạo lazy singleton cho SHMEngine."""
    global _engine
    if _engine is None:
        _engine = SHMEngine(
            phase1_weight=DEFAULT_PHASE1_WEIGHT,
            phase2_weight=DEFAULT_PHASE2_WEIGHT,
            conf1=0.25,
            conf2=0.25,
            device="cpu",
        )
    return _engine


@router.get("/health")
def phase3_health() -> dict:
    """Kiểm tra sự tồn tại của trọng số và trạng thái engine."""
    engine = get_shm_engine()
    p1_ok = Path(engine.phase1_weight).exists()
    p2_ok = Path(engine.phase2_weight).exists()
    status = "ok" if (p1_ok and p2_ok) else "degraded"
    return {
        "status": status,
        "phase1_weight": str(engine.phase1_weight),
        "phase1_exists": p1_ok,
        "phase2_weight": str(engine.phase2_weight),
        "phase2_exists": p2_ok,
        "models_cached": {
            "phase1": engine._model1 is not None,
            "phase2": engine._model2 is not None,
        },
    }


@router.get("/config")
def phase3_config() -> dict:
    """Trả về cấu hình hệ số rủi ro cấu kiện và bảng phân cấp SCI."""
    return {
        "risk_multiplier": RISK_MULTIPLIER,
        "sci_tiers": SCI_TIERS,
    }


@router.post("/classify-component")
async def phase3_classify_component(
    file: Annotated[UploadFile, File()],
) -> JSONResponse:
    """AI tự động nhận diện loại cấu kiện kết cấu từ ảnh (không cần chọn tay)."""
    from app.component_classifier import AIComponentClassifier

    raw = await file.read()
    arr = np.frombuffer(raw, dtype=np.uint8)
    img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise HTTPException(400, "File không đọc được ảnh.")

    res = AIComponentClassifier.classify(img_bgr)
    return JSONResponse(res)


@router.post("/analyze")
async def phase3_analyze_single(
    file: Annotated[UploadFile, File()],
    component_type: Annotated[str, Form()] = "auto",
    conf1: Annotated[float, Form()] = 0.25,
    conf2: Annotated[float, Form()] = 0.25,
) -> JSONResponse:
    """Phân tích ảnh đơn lẻ bằng dual inference Phase 1.2 + Phase 2."""
    raw = await file.read()
    arr = np.frombuffer(raw, dtype=np.uint8)
    img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise HTTPException(400, "File không đọc được ảnh (jpg/png/...).")

    engine = get_shm_engine()
    engine.conf1 = conf1
    engine.conf2 = conf2

    try:
        result = engine.analyze_image(
            img_bgr,
            component_type=component_type,
        )
    except Exception as e:
        raise HTTPException(500, f"Lỗi khi chạy phân tích Phase 3: {e}")

    return JSONResponse(result)


@router.post("/analyze-folder")
async def phase3_analyze_folder(
    files: List[UploadFile] = File(...),
    components_json: Annotated[str, Form()] = "[]",
    dedup_enabled: Annotated[bool, Form()] = True,
    conf1: Annotated[float, Form()] = 0.25,
    conf2: Annotated[float, Form()] = 0.25,
) -> JSONResponse:
    """Phân tích tập ảnh (quét tầng/công trình) có hỗ trợ khử trùng lặp (ORB Homography)."""
    if not files:
        raise HTTPException(400, "Danh sách file upload trống.")

    try:
        comp_list = json.loads(components_json) if components_json else []
    except json.JSONDecodeError:
        comp_list = []

    engine = get_shm_engine()
    engine.conf1 = conf1
    engine.conf2 = conf2

    temp_dir = Path(tempfile.mkdtemp(prefix="phase3_folder_"))
    try:
        image_paths = []
        for i, f in enumerate(files):
            ext = Path(f.filename or "img.jpg").suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png", ".bmp"}:
                ext = ".jpg"
            target_path = temp_dir / f"img_{i:04d}{ext}"
            content = await f.read()
            target_path.write_bytes(content)
            image_paths.append(str(target_path))

        component_types = []
        for i in range(len(image_paths)):
            if i < len(comp_list) and isinstance(comp_list[i], str):
                component_types.append(comp_list[i])
            else:
                component_types.append("auto")

        result = engine.analyze_folder(
            image_paths=image_paths,
            component_types=component_types,
            dedup_enabled=dedup_enabled,
        )
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(500, f"Lỗi khi phân tích tập ảnh Phase 3: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
