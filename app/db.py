"""SQLite lưu hồ sơ kiểm định (không cần server DB — đủ cho khóa luận + demo).

2 bảng:
  inspections : 1 lần kiểm tra (vị trí tòa nhà/tầng/cấu kiện, ảnh, số vết)
  detections  : từng vết nứt thuộc 1 inspection (conf, bbox, đặc trưng Lớp A)
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "inspections.db"
IMG_DIR = Path(__file__).parent / "data" / "images"
IMG_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                address     TEXT,
                n_floors    INTEGER,
                created_at  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS inspections (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT NOT NULL,
                building    TEXT,
                floor       TEXT,
                component   TEXT,
                note        TEXT,
                image_name  TEXT,
                gsd_mm_per_px REAL,
                n_cracks    INTEGER NOT NULL DEFAULT 0,
                project_id  INTEGER,
                engineer    TEXT,
                status      TEXT NOT NULL DEFAULT 'submitted',
                approved_by TEXT,
                approved_at TEXT
            );
            CREATE TABLE IF NOT EXISTS detections (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_id INTEGER NOT NULL REFERENCES inspections(id),
                conf          REAL,
                x1 REAL, y1 REAL, x2 REAL, y2 REAL,
                length_px REAL, width_px REAL, area_px REAL, angle_deg REAL,
                severity      TEXT DEFAULT NULL   -- Phase 2 điền sau
            );
            """
        )
        # Migration nhẹ cho DB cũ (trước khi có các cột mới)
        cols = {r[1] for r in c.execute("PRAGMA table_info(inspections)")}
        for col, typ in (
            ("gsd_mm_per_px", "REAL"),
            ("project_id", "INTEGER"),
            ("engineer", "TEXT"),
            ("status", "TEXT DEFAULT 'submitted'"),
            ("approved_by", "TEXT"),
            ("approved_at", "TEXT"),
        ):
            if col not in cols:
                c.execute(f"ALTER TABLE inspections ADD COLUMN {col} {typ}")
        if c.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
            c.execute(
                "INSERT INTO projects (name, address, n_floors, created_at)"
                " VALUES (?, ?, ?, datetime('now','localtime'))",
                ("Tòa nhà mẫu A", "Số 1 Đại Cồ Việt, Hà Nội", 15),
            )


STATUS_LABELS = {
    "draft": "Bản nháp",
    "submitted": "Chờ duyệt",
    "approved": "Đã duyệt",
}


def save_inspection(
    meta: dict, detections: list[dict], image_bgr_bytes: bytes, image_ext: str = ".jpg"
) -> int:
    """Lưu 1 hồ sơ + các vết nứt. Ảnh gốc lưu ra app/data/images/<id><ext>."""
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO inspections (created_at, building, floor, component, note,"
            " image_name, gsd_mm_per_px, n_cracks, project_id, engineer, status)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                now,
                meta.get("building", ""),
                meta.get("floor", ""),
                meta.get("component", ""),
                meta.get("note", ""),
                meta.get("image_name", ""),
                meta.get("gsd_mm_per_px"),
                len(detections),
                meta.get("project_id"),
                meta.get("engineer", ""),
                meta.get("status", "submitted"),
            ),
        )
        ins_id = cur.lastrowid
        for d in detections:
            b = d.get("bbox", [0, 0, 0, 0])
            sev = d.get("severity") or {}
            severity_label = (
                f"L{sev['level']} {sev['name']} ({sev['width_mm']}mm)"
                if isinstance(sev, dict) and "level" in sev else None
            )
            c.execute(
                "INSERT INTO detections (inspection_id, conf, x1, y1, x2, y2,"
                " length_px, width_px, area_px, angle_deg, severity) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    ins_id, d.get("conf"), b[0], b[1], b[2], b[3],
                    d.get("length_px"), d.get("width_px"), d.get("area_px"), d.get("angle_deg"),
                    severity_label,
                ),
            )
    (IMG_DIR / f"{ins_id}{image_ext}").write_bytes(image_bgr_bytes)
    return int(ins_id)


def list_inspections(limit: int = 100) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM inspections ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_inspection(ins_id: int) -> dict | None:
    with _conn() as c:
        ins = c.execute("SELECT * FROM inspections WHERE id=?", (ins_id,)).fetchone()
        if ins is None:
            return None
        dets = c.execute(
            "SELECT * FROM detections WHERE inspection_id=? ORDER BY conf DESC", (ins_id,)
        ).fetchall()
    out = dict(ins)
    out["detections"] = [dict(d) for d in dets]
    return out


def set_status(ins_id: int, status: str, by: str) -> dict | None:
    """Luồng phê duyệt: draft -> submitted -> approved (hoặc quay lại draft)."""
    if status not in STATUS_LABELS:
        raise ValueError(f"Trạng thái không hợp lệ: {status}")
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        if status == "approved":
            c.execute(
                "UPDATE inspections SET status=?, approved_by=?, approved_at=? WHERE id=?",
                (status, by, now, ins_id),
            )
        else:
            c.execute(
                "UPDATE inspections SET status=?, approved_by=NULL, approved_at=NULL WHERE id=?",
                (status, ins_id),
            )
    return get_inspection(ins_id)


def list_projects() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT p.*, COUNT(i.id) AS n_inspections FROM projects p"
            " LEFT JOIN inspections i ON i.project_id = p.id"
            " GROUP BY p.id ORDER BY p.id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def add_project(name: str, address: str = "", n_floors: int | None = None) -> int:
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO projects (name, address, n_floors, created_at) VALUES (?,?,?,?)",
            (name, address, n_floors, now),
        )
        return int(cur.lastrowid)


def export_csv_rows() -> tuple[list[str], list[list]]:
    """Toàn bộ hồ sơ dạng phẳng cho file CSV báo cáo kiểm định."""
    header = [
        "ma_ho_so", "thoi_gian", "toa_nha", "tang", "cau_kien",
        "so_vet", "stt_vet", "conf", "x1", "y1", "x2", "y2",
        "chieu_dai_px", "be_rong_px", "dien_tich_px", "goc_deg", "muc_do_nghiem_trong",
    ]
    rows: list[list] = []
    for ins in list_inspections(limit=10000):
        dets = get_inspection(ins["id"])["detections"]
        if not dets:
            rows.append([ins["id"], ins["created_at"], ins["building"], ins["floor"],
                         ins["component"], 0] + [""] * 11)
        for i, d in enumerate(dets, 1):
            rows.append([
                ins["id"], ins["created_at"], ins["building"], ins["floor"],
                ins["component"], len(dets), i, d["conf"],
                d["x1"], d["y1"], d["x2"], d["y2"],
                d["length_px"], d["width_px"], d["area_px"], d["angle_deg"],
                d["severity"] or "(chờ Phase 2)",
            ])
    return header, rows
