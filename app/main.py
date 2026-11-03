"""FastAPI — Hệ thống phát hiện vết nứt Phase 1 (crack_severity_ai).

Endpoint:
  GET  /                      → giao diện kỹ sư kiểm định (static/index.html)
  GET  /api/health            → trạng thái model
  POST /api/predict           → ảnh → phát hiện vết nứt + đặc trưng Lớp A (px)
  POST /api/inspections       → lưu hồ sơ kiểm định (ảnh + meta + detections)
  GET  /api/inspections       → danh sách hồ sơ
  GET  /api/inspections/export.csv → xuất CSV toàn bộ (báo cáo kiểm định)
  GET  /api/inspections/{id}/report.html → báo cáo in được (in ra PDF từ trình duyệt)

Chạy local:  uvicorn app.main:app --host 0.0.0.0 --port 7860
"""

from __future__ import annotations

import base64
import csv
import io
from collections import Counter
from pathlib import Path
from typing import Annotated

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from . import db
from .model_service import DEFAULT_IMGSZ, detect, get_model
from .severity import SCALE_META

APP_VERSION = "3.1.0-phase1+2"
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Crack Severity AI — Phase 1", version=APP_VERSION)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

COMPONENTS = ["cột", "tường", "sàn", "dầm", "cầu thang", "ban công", "khác"]


INFRA_DIR = Path(__file__).parent / "static" / "infra"


def _infra(name: str) -> Response:
    return HTMLResponse(
        (INFRA_DIR / name).read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@app.get("/", response_class=HTMLResponse)
def index() -> Response:
    """INFRA-GUARD gateway — template gốc 100%."""
    return _infra("infra_guard_3d_interactive_welcome_gateway.html")


@app.get("/registry", response_class=HTMLResponse)
def registry() -> Response:
    """Operational Console — template Building Infrastructure Registry 100%."""
    return _infra("building_infrastructure_registry.html")


@app.get("/console", response_class=HTMLResponse)
def console() -> Response:
    """Console đa-tab: ghép verbatim Registry + PE Review + Marketplace."""
    return _infra("console.html")


@app.get("/review", response_class=HTMLResponse)
def review() -> Response:
    return _infra("structural_evaluation_pe_sign_off_review.html")


@app.get("/marketplace", response_class=HTMLResponse)
def marketplace() -> Response:
    return _infra("engineering_services_marketplace.html")


@app.get("/api/health")
def health() -> dict:
    loaded = True
    detail = "ok"
    try:
        get_model()
    except Exception as exc:  # noqa: BLE001 — health phải luôn trả về, không crash
        loaded, detail = False, str(exc)
    return {"status": "ok" if loaded else "degraded", "model_loaded": loaded,
            "detail": detail, "version": APP_VERSION}


@app.post("/api/predict")
async def predict(
    file: Annotated[UploadFile, File()],
    conf: Annotated[float, Form()] = 0.25,
    imgsz: Annotated[int, Form()] = DEFAULT_IMGSZ,
    gsd_mm_per_px: Annotated[float, Form()] = 0.0,
) -> JSONResponse:
    raw = await file.read()
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "File không đọc được ảnh (jpg/png/...).")

    gsd = gsd_mm_per_px if gsd_mm_per_px > 0 else None
    detections, annotated, elapsed_ms = detect(img, conf=conf, imgsz=imgsz, gsd_mm_per_px=gsd)
    ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 88])
    if not ok:
        raise HTTPException(500, "Không encode được ảnh kết quả.")
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")

    sev_counts = Counter(
        f"L{d['severity']['level']}" for d in detections if d.get("severity")
    )
    return JSONResponse({
        "n_cracks": len(detections),
        "elapsed_ms": round(elapsed_ms, 1),
        "image_wh": [img.shape[1], img.shape[0]],
        "gsd_mm_per_px": gsd,
        "severity_summary": dict(sev_counts),
        "detections": detections,
        "annotated_jpg_b64": b64,
    })


@app.post("/api/inspections")
async def save_inspection(
    file: Annotated[UploadFile, File()],
    annotated_jpg_b64: Annotated[str, Form()] = "",
    detections_json: Annotated[str, Form()] = "[]",
    building: Annotated[str, Form()] = "",
    floor: Annotated[str, Form()] = "",
    component: Annotated[str, Form()] = "",
    note: Annotated[str, Form()] = "",
    gsd_mm_per_px: Annotated[float, Form()] = 0.0,
    project_id: Annotated[int, Form()] = 0,
    engineer: Annotated[str, Form()] = "",
    status: Annotated[str, Form()] = "submitted",
) -> dict:
    import json as _json

    raw = await file.read()
    img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "File không đọc được ảnh.")
    try:
        detections = _json.loads(detections_json)
    except _json.JSONDecodeError:
        raise HTTPException(400, "detections_json sai định dạng.")

    ext = Path(file.filename or "upload.jpg").suffix.lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png"}:
        ext = ".jpg"

    ins_id = db.save_inspection(
        meta={"building": building, "floor": floor, "component": component,
              "note": note, "image_name": file.filename or "",
              "gsd_mm_per_px": gsd_mm_per_px if gsd_mm_per_px > 0 else None,
              "project_id": project_id or None, "engineer": engineer,
              "status": status if status in db.STATUS_LABELS else "submitted"},
        detections=detections,
        image_bgr_bytes=raw,
        image_ext=ext,
    )
    if annotated_jpg_b64:
        ann = base64.b64decode(annotated_jpg_b64)
        (db.IMG_DIR / f"{ins_id}_annotated.jpg").write_bytes(ann)
    return {"id": ins_id, "n_cracks": len(detections)}


@app.get("/api/inspections")
def inspections(limit: int = 100) -> list[dict]:
    return db.list_inspections(limit=limit)


@app.get("/api/projects")
def projects() -> list[dict]:
    return db.list_projects()


@app.post("/api/projects")
async def create_project(
    name: Annotated[str, Form()],
    address: Annotated[str, Form()] = "",
    n_floors: Annotated[int, Form()] = 0,
) -> dict:
    if not name.strip():
        raise HTTPException(400, "Tên dự án không được trống.")
    pid = db.add_project(name.strip(), address.strip(), n_floors or None)
    return {"id": pid, "name": name.strip()}


@app.get("/api/dashboard")
def dashboard() -> dict:
    """Dữ liệu 1 lần cho dashboard: KPI + phân bố + xu hướng + hồ sơ mới nhất."""
    from collections import Counter

    ins_list = db.list_inspections(limit=5000)
    n_cracks, confs = 0, []
    by_sev: Counter = Counter()
    by_comp: Counter = Counter()
    by_status: Counter = Counter()
    by_month: Counter = Counter()
    for ins in ins_list:
        by_status[ins["status"]] += 1
        by_comp[ins["component"] or "(không rõ)"] += 1
        ym = (ins["created_at"] or "")[:7]
        if ym:
            by_month[ym] += 1
        for d in db.get_inspection(ins["id"])["detections"]:
            n_cracks += 1
            confs.append(d["conf"] or 0)
            s = d["severity"] or ""
            if s.startswith("L"):
                by_sev[s.split()[0]] += 1  # "L2 Moderate (0.4mm)" -> "L2"
    months = sorted(by_month)[-6:]
    return {
        "kpi": {
            "projects": len(db.list_projects()),
            "inspections": len(ins_list),
            "cracks": n_cracks,
            "avg_conf": round(sum(confs) / len(confs), 3) if confs else None,
            "pending": by_status.get("submitted", 0),
        },
        "by_severity": dict(sorted(by_sev.items())),
        "by_component": dict(by_comp.most_common(8)),
        "by_status": dict(by_status),
        "trend": {"labels": months, "values": [by_month[m] for m in months]},
        "recent": ins_list[:8],
    }


@app.get("/api/model-info")
def model_info() -> dict:
    """Thông tin model + benchmark (v1 active, v2 tham chiếu) cho view Phân tích."""
    return {
        "version": APP_VERSION,
        "model": "YOLOv8s-seg (Ultralytics)",
        "active": "v1 — imgsz 640, 100 epochs (chọn sau khi so sánh v2)",
        "trained_v1": "Kaggle T4, imgsz 640, 100 epochs, 15.947 ảnh",
        "trained_v2": "imgsz 1280 + multi_scale, +3.000 ảnh âm, +118 pseudo-GT (~76 epochs)",
        "test_metrics": {
            "box": {"P": 0.823, "R": 0.565, "mAP50": 0.599, "mAP50-95": 0.455},
            "mask": {"P": 0.794, "R": 0.492, "mAP50": 0.488, "mAP50-95": 0.145},
        },
        "test_metrics_note": "v1 (active). v2 @1280: instance F1 tối đa 0.514 < v1 0.655 → giữ v1",
        "image_level_acc": 0.999,
        "neg_fp_rate": 0.022,
        "neg_fp_rate_note": "v1 @640: 2.2% — v2 @1280: 1.5% (v2 tốt hơn ở mục này)",
        "model_compare": {
            "v1_640": {"inst_F1": 0.655, "inst_P": 0.797, "inst_R": 0.555,
                        "dice_3dcrack": 0.708, "dice_deepcrack": 0.819,
                        "neg_fp": 0.022, "verdict": "ACTIVE — F1 instance cao nhất"},
            "v2_1280": {"inst_F1": 0.514, "inst_P": 0.516, "inst_R": 0.511,
                         "dice_3dcrack": 0.718, "dice_deepcrack": 0.803,
                         "neg_fp": 0.015, "verdict": "Tham chiếu — FP thấp hơn nhưng precision sụp @IoU0.5"},
        },
        "sota_ref": {
            "paper": "arXiv:2508.10256 (Georgia Tech, 2025)",
            "deepcrack": {"ours_dice": 0.819, "resunet_dice": 0.833},
            "3dcrack": {"ours_dice": 0.708, "resunet_dice": 0.795},
            "note": "số của model active (v1)",
        },
        "data": {
            "train": 14619, "val": 1484, "test": 1491,
            "negatives_train": 4048,
            "sources": ["3DCrack_v1", "crack_segmentation_dataset", "DeepCrack",
                        "Roads_and_Bridges", "Ultralytics_CrackSeg", "METU Negative", "SDNET"],
        },
        "phase2": {
            "type": "rule-based (Lớp A morphology + Lớp B tín hiệu)",
            "scale": "4 mức L0–L3 theo ACI 224R-01 / TCVN 9381:2012",
            "inputs": ["width_max × GSD", "branching (skeleton)", "multi_plane", "through_member"],
        },
    }


@app.get("/api/inspections/export.csv")
def export_csv() -> Response:
    header, rows = db.export_csv_rows()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerows(rows)
    return Response(
        content="\ufeff" + buf.getvalue(),  # BOM để Excel mở UTF-8 đúng
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=bao_cao_kiem_dinh.csv"},
    )


@app.get("/api/inspections/{ins_id}")
def inspection_detail(ins_id: int) -> JSONResponse:
    ins = db.get_inspection(ins_id)
    if ins is None:
        raise HTTPException(404, "Không tìm thấy hồ sơ.")
    return JSONResponse(ins)


@app.post("/api/inspections/{ins_id}/status")
async def inspection_status(
    ins_id: int, status: Annotated[str, Form()], by: Annotated[str, Form()] = ""
) -> dict:
    """Luồng phê duyệt: draft -> submitted -> approved."""
    try:
        ins = db.set_status(ins_id, status, by)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if ins is None:
        raise HTTPException(404, "Không tìm thấy hồ sơ.")
    return ins


@app.post("/api/inspections/{ins_id}/severity")
async def inspection_reclassify(
    ins_id: int,
    gsd_mm_per_px: Annotated[float, Form()],
    through_flags: Annotated[str, Form()] = "[]",
) -> JSONResponse:
    """Phase 2: phân loại lại mức độ của hồ sơ ĐÃ LƯU (không cần ảnh/model).

    Dùng khi kỹ sư nhập/đổi GSD sau khi lưu, hoặc đánh dấu vết xuyên cấu kiện.
    """
    import json as _json

    from .severity import classify

    if gsd_mm_per_px <= 0:
        raise HTTPException(400, "Cần GSD (mm/pixel) > 0.")
    try:
        flags = _json.loads(through_flags) if through_flags else []
    except _json.JSONDecodeError:
        raise HTTPException(400, "through_flags sai định dạng.")

    def label_for(d: dict, through: bool) -> str | None:
        w_mean = d.get("width_px")
        if d.get("area_px") and d.get("length_px"):
            w_mean = d["area_px"] / d["length_px"]  # tái tạo width_mean từ px đã lưu
        sev = classify(
            w_mean,
            gsd_mm_per_px,
            width_max_px=d.get("width_max_px"),
            length_px=d.get("length_px"),
            branching=bool(d.get("branching")),
            multi_plane=bool(d.get("multi_plane")),
            through_member=through,
            contrast_ratio=d.get("contrast_ratio"),
        )
        if sev is None:
            return None
        return f"L{sev['level']} {sev['name']} ({sev['width_mm']}mm)"

    ins = db.reclassify_inspection(ins_id, gsd_mm_per_px, flags, label_for)
    if ins is None:
        raise HTTPException(404, "Không tìm thấy hồ sơ.")
    return JSONResponse(ins)


@app.get("/api/inspections/{ins_id}/report.html", response_class=HTMLResponse)
def inspection_report(ins_id: int) -> HTMLResponse:
    ins = db.get_inspection(ins_id)
    if ins is None:
        raise HTTPException(404, "Không tìm thấy hồ sơ.")
    ann_path = db.IMG_DIR / f"{ins_id}_annotated.jpg"
    img_tag = (
        f'<img src="/api/inspections/{ins_id}/image_annotated" style="max-width:100%">'
        if ann_path.exists()
        else "<i>(không có ảnh chú thích)</i>"
    )
    rows = "".join(
        f"<tr><td>{i + 1}</td><td>{d['conf']:.2f}</td><td>{d['length_px']}</td>"
        f"<td>{d['width_px']}</td><td>{d['area_px']}</td><td>{d['angle_deg']}</td>"
        f"<td>{d['severity'] or '(chờ Phase 2)'}</td></tr>"
        for i, d in enumerate(ins["detections"])
    ) or "<tr><td colspan='7'>Không phát hiện vết nứt</td></tr>"
    gsd_row = (
        f"<tr><td><b>Thang đo (GSD):</b></td><td colspan='3'>{ins['gsd_mm_per_px']} mm/pixel</td></tr>"
        if ins["gsd_mm_per_px"] else ""
    )
    status_map = {"draft": "BẢN NHÁP", "submitted": "CHỜ DUYỆT", "approved": "ĐÃ DUYỆT"}
    st_badge = status_map.get(ins["status"], ins["status"].upper())
    st_color = {"draft": "#64748b", "submitted": "#b9770e", "approved": "#1e8449"}.get(ins["status"], "#333")
    html = f"""<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8">
<title>Báo cáo kiểm định #{ins_id}</title>
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;margin:0;color:#0f172a;background:#f6f8fb}}
.page{{max-width:860px;margin:0 auto;padding:40px;background:#fff;min-height:100vh}}
.letterhead{{display:flex;justify-content:space-between;align-items:flex-end;
border-bottom:3px solid #2563eb;padding-bottom:12px;margin-bottom:20px}}
.letterhead .logo{{font-size:20px;font-weight:700;color:#2563eb}}
.letterhead .logo small{{display:block;font-weight:400;color:#64748b;font-size:12px}}
.letterhead .docno{{text-align:right;font-size:13px;color:#475569}}
.st-badge{{display:inline-block;padding:4px 14px;border-radius:99px;color:#fff;font-size:12px;font-weight:700;background:{st_color}}}
h1{{font-size:19px;color:#1d4ed8;margin:18px 0 8px}}
table{{border-collapse:collapse;width:100%;margin-top:10px}}
td,th{{border:1px solid #cbd5e1; padding:7px 10px;font-size:13.5px}}
th{{background:#eff6ff;text-align:left}}
.meta td{{border:none;padding:3px 12px 3px 0;font-size:14px}}
footer{{margin-top:26px;font-size:11.5px;color:#64748b;border-top:1px solid #e2e8f0;padding-top:8px}}
.signs{{display:flex;justify-content:space-between;margin-top:38px;gap:40px}}
.sign{{flex:1;text-align:center;font-size:13px}}
.sign .line{{margin-top:64px;border-top:1px solid #334155;padding-top:6px}}
@media print .noprint{{display:none}}
</style></head><body><div class="page">
<div class="letterhead">
  <div class="logo">🏗️ CRACK SEVERITY AI<small>Hệ thống hỗ trợ kiểm định vết nứt bề mặt công trình</small></div>
  <div class="docno"><b>Mã hồ sơ:</b> CSA-{ins_id:05d}<br><b>Phiên bản:</b> {APP_VERSION}<br>
  <span class="st-badge">{st_badge}</span></div>
</div>
<h1>PHIẾU KIỂM TRA VẾT NỨT BỀ MẶT — PHASE 1 (YOLOv8s-seg)</h1>
<p class="noprint"><button onclick="window.print()">🖨️ In / Lưu PDF</button></p>
<table class="meta">
<tr><td><b>Thời gian kiểm tra:</b></td><td>{ins['created_at'].replace('T', ' ')}</td></tr>
<tr><td><b>Tòa nhà / Công trình:</b></td><td>{ins['building']}</td>
    <td><b>Tầng:</b></td><td>{ins['floor']}</td></tr>
<tr><td><b>Cấu kiện:</b></td><td>{ins['component']}</td>
    <td><b>Số vết phát hiện:</b></td><td><b>{ins['n_cracks']}</b></td></tr>
<tr><td><b>Kỹ sư kiểm tra:</b></td><td>{ins['engineer'] or '—'}</td>
    <td><b>Người duyệt:</b></td><td>{ins['approved_by'] or '—'}</td></tr>
{gsd_row}
<tr><td><b>Ghi chú hiện trường:</b></td><td colspan="3">{ins['note']}</td></tr>
</table>
<h3>1. Ảnh phát hiện tự động</h3>
{img_tag}
<h3>2. Danh sách vết nứt — đặc trưng Lớp A (đơn vị pixel ảnh)</h3>
<table><tr><th>#</th><th>Conf</th><th>Chiều dài (px)</th><th>Bề rộng TB (px)</th>
<th>Diện tích (px²)</th><th>Góc (°)</th><th>Mức độ nghiêm trọng (đề xuất)</th></tr>
{rows}</table>
<div class="signs">
  <div class="sign">KỸ SƯ KIỂM TRA<div class="line">{ins['engineer'] or '(ký, ghi rõ họ tên)'}</div></div>
  <div class="sign">TRƯỞNG BỘ PHẬN DUYỆT<div class="line">{ins['approved_by'] or '(ký, ghi rõ họ tên)'}</div></div>
</div>
<footer>
Mức độ nghiêm trọng theo thang ĐỀ XUẤT 4 mức tham chiếu ACI 224R-01 / TCVN 9381:2012
(chờ phê duyệt — xem docs/standards/severity_definition.md). Kết quả máy hỗ trợ, không thay thế
kết luận của kỹ sư kiểm định. © crack_severity_ai — khóa luận tốt nghiệp.
</footer>
</div></body></html>"""
    return HTMLResponse(html)


@app.get("/api/inspections/{ins_id}/image_annotated")
def inspection_image(ins_id: int) -> Response:
    p = db.IMG_DIR / f"{ins_id}_annotated.jpg"
    if not p.exists():
        raise HTTPException(404, "Không có ảnh chú thích.")
    return Response(content=p.read_bytes(), media_type="image/jpeg")


@app.get("/api/stats")
def stats() -> dict:
    """Thống kê tổng quan cho dashboard."""
    ins_list = db.list_inspections(limit=10000)
    n_ins = len(ins_list)
    n_cracks = 0
    comps: Counter = Counter()
    sev: Counter = Counter()
    confs: list[float] = []
    for ins in ins_list:
        comps[ins["component"] or "(không rõ)"] += 1
        detail = db.get_inspection(ins["id"])
        for d in detail["detections"]:
            n_cracks += 1
            confs.append(d["conf"] or 0)
            s = d["severity"]
            if s:
                sev[f"L{s[1]}"] += 1  # "L2 Moderate (0.4mm)" -> "L2"
    return {
        "inspections": n_ins,
        "cracks": n_cracks,
        "avg_conf": round(sum(confs) / len(confs), 3) if confs else None,
        "by_component": dict(comps),
        "by_severity": dict(sev),
    }


@app.post("/api/severity")
async def reclassify_severity(
    detections_json: Annotated[str, Form()],
    gsd_mm_per_px: Annotated[float, Form()],
    through_flags: Annotated[str, Form()] = "[]",
) -> JSONResponse:
    """Phân loại lại Phase 2 KHÔNG cần chạy model lại.

    - detections_json: mảng detections từ /api/predict (có width/length px).
    - through_flags: mảng bool theo thứ tự vết — kỹ sư đánh dấu "nứt xuyên cấu kiện".
    Trả về detections đã cập nhật severity + summary.
    """
    import json as _json

    from .severity import classify

    if gsd_mm_per_px <= 0:
        raise HTTPException(400, "Cần GSD (mm/pixel) > 0 để phân loại.")
    try:
        dets = _json.loads(detections_json)
        flags = _json.loads(through_flags) if through_flags else []
    except _json.JSONDecodeError:
        raise HTTPException(400, "JSON sai định dạng.")

    out = []
    for i, d in enumerate(dets):
        d = dict(d)
        d.pop("severity", None)
        d["severity"] = classify(
            d.get("width_mean_px"), gsd_mm_per_px,
            width_max_px=d.get("width_max_px"),
            length_px=d.get("length_px"),
            branching=bool(d.get("branching")),
            multi_plane=bool(d.get("multi_plane")),
            through_member=bool(flags[i]) if i < len(flags) else False,
        )
        out.append(d)

    sev_counts = Counter(f"L{d['severity']['level']}" for d in out if d.get("severity"))
    return JSONResponse({
        "detections": out,
        "severity_summary": dict(sev_counts),
        "gsd_mm_per_px": gsd_mm_per_px,
    })


@app.get("/api/demo-image")
def demo_image() -> Response:
    """Ảnh mẫu từ tập test để dùng thử nhanh."""
    import random

    img_dir = Path("data/processed/phase1/primary/images/test")
    if not img_dir.exists():
        raise HTTPException(404, "Không có thư mục ảnh test trên server này.")
    imgs = [p for p in img_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    if not imgs:
        raise HTTPException(404, "Không có ảnh test.")
    p = random.choice(imgs)
    return Response(content=p.read_bytes(), media_type="image/jpeg")


@app.get("/api/meta")
def meta() -> dict:
    return {
        "components": COMPONENTS,
        "version": APP_VERSION,
        "severity_scale": SCALE_META,
    }
