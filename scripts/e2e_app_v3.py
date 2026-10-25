"""Test E2E nhanh cho app v3: predict -> save -> approve -> report.

Chạy khi server đã bật tại 127.0.0.1:7860:
    python scripts/e2e_app_v3.py
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:7860"


def post_form(url: str, fields: dict, files: dict | None = None) -> dict:
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
        )
    for k, (fname, blob, ctype) in (files or {}).items():
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fname}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n".encode() + blob + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    req = Request(
        url,
        data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    return json.load(urlopen(req))


def get(url: str) -> str:
    return urlopen(url).read().decode("utf-8", "ignore")


def main() -> None:
    img_path = next(
        p for p in sorted(Path("data/processed/phase1/primary/images/test").glob("DeepCrack*"))
    )
    blob = img_path.read_bytes()

    # 1) predict với GSD
    pred = post_form(
        f"{BASE}/api/predict",
        {"conf": "0.25", "imgsz": "640", "gsd_mm_per_px": "0.25"},
        files={"file": ("t.jpg", blob, "image/jpeg")},
    )
    print("1) predict OK:", pred["n_cracks"], "vết | severity:", pred["severity_summary"])
    assert pred["n_cracks"] > 0 and pred["severity_summary"]

    # 2) lưu hồ sơ theo dự án + kỹ sư
    dets = [{k: v for k, v in x.items() if k != "mask_points"} for x in pred["detections"]]
    saved = post_form(
        f"{BASE}/api/inspections",
        {
            "building": "Tòa nhà mẫu A", "floor": "T12", "component": "Cột",
            "engineer": "Nguyễn Văn A", "gsd_mm_per_px": "0.25",
            "project_id": "1", "status": "submitted",
            "detections_json": json.dumps(dets),
            "annotated_jpg_b64": pred["annotated_jpg_b64"],
        },
        files={"file": ("t.jpg", blob, "image/jpeg")},
    )
    print("2) save OK: id =", saved["id"], "| n_cracks =", saved["n_cracks"])

    # 3) phê duyệt
    ap = post_form(
        f"{BASE}/api/inspections/{saved['id']}/status",
        {"status": "approved", "by": "Trần Quản Lý"},
    )
    print("3) approve OK:", ap["status"], "| by:", ap["approved_by"])

    # 4) báo cáo có trạng thái + chữ ký
    report = get(f"{BASE}/api/inspections/{saved['id']}/report.html")
    for needle in ("ĐÃ DUYỆT", "Trần Quản Lý", "KỸ SƯ KIỂM TRA"):
        assert needle in report, f"thiếu {needle} trong báo cáo"
    print("4) report OK: badge ĐÃ DUYỆT + 2 ô chữ ký")

    # 5) dashboard phản ánh số mới
    dash = json.loads(get(f"{BASE}/api/dashboard"))
    assert dash["kpi"]["inspections"] >= 1 and dash["kpi"]["pending"] >= 0
    print("5) dashboard OK:", dash["kpi"])
    print("\nE2E PASS ✓")


if __name__ == "__main__":
    main()
