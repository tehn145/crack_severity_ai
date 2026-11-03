#!/usr/bin/env python3
"""
download_datasets.py — Tải các dataset mở bổ sung (Zenodo API).

Hiện tại: Masonry (record 5108846), CODEBRIM (record 2620293).
Xuất: data/raw/public/<tên>/
Chạy: python scripts/download_datasets.py [--only masonry,codebrim]
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

RECORDS = {
    "masonry_zenodo": 5108846,
    "codebrim": 2620293,
    "multi_temporal_crack": 15187675,
}
RAW = Path("data/raw/public")


def api_record(rid: int) -> dict:
    with urllib.request.urlopen(f"https://zenodo.org/api/records/{rid}", timeout=60) as r:
        return json.load(r)


def download(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, 4):
        # resume nếu file còn thiếu so với lần trước
        done = dst.stat().st_size if dst.exists() else 0
        req = urllib.request.Request(url)
        if done:
            req.add_header("Range", f"bytes={done}-")
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                total = done + int(resp.headers.get("Content-Length", 0) or 0)
                if total and done >= total and total > 0:
                    print(f"  [đủ] {dst.name} ({done/1e6:.0f} MB)")
                    return
                mode = f"resume {done / 1e6:.0f}MB" if done else "mới"
                print(f"  tải {dst.name} ({mode})...")
                with open(dst, "ab" if done else "wb") as f:
                    while True:
                        chunk = resp.read(1 << 20)
                        if not chunk:
                            break
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            print(f"\r  {done/1e6:.0f}/{total/1e6:.0f} MB", end="")
            print()
            if total and dst.stat().st_size >= total:
                print(f"  [xong] {dst.name} ({dst.stat().st_size/1e6:.0f} MB)")
                return
            print(f"  [thiếu] {dst.stat().st_size/1e6:.0f}/{total/1e6:.0f} MB — thử lại (lần {attempt})")
        except Exception as e:  # noqa: BLE001 — mạng rớt cần retry
            print(f"  [lỗi mạng] {e} — thử lại (lần {attempt})")
    print(f"  [THẤT BẠI sau 3 lần] {dst.name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=",".join(RECORDS))
    ap.add_argument("--ext-filter", default=".zip,.rar,.7z",
                    help="chỉ tải file có đuôi này (bỏ qua tài liệu)")
    args = ap.parse_args()
    only = {x.strip() for x in args.only.split(",")}

    for name, rid in RECORDS.items():
        if name not in only:
            continue
        print(f"== {name} (record {rid}) ==")
        try:
            rec = api_record(rid)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"  lỗi API: {e}")
            continue
        files = rec.get("files", [])
        if not files:
            print("  record không mở file (cần request access) — bỏ qua")
            continue
        exts = tuple(x.strip().lower() for x in args.ext_filter.split(","))
        for f in files:
            key = f.get("key", "")
            link = f.get("links", {}).get("self")
            if not link or not key.lower().endswith(exts):
                continue
            download(link, RAW / name / Path(key).name)
    print("Xong. Giải nén bằng tay (zip/rar) rồi convert về YOLO polygon.")


if __name__ == "__main__":
    main()
