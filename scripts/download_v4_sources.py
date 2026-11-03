#!/usr/bin/env python3
"""
download_v4_sources.py — Tải các nguồn dataset mới cho v4 (đa bề mặt + đa defects).

Nguồn:
  1. CrackSeg9k (HuggingFace parquet ~4.2GB) — 9.2k ảnh 10 dataset, lọc nguồn mới
  2. CUHK-USR Defect-Dataset (GitHub) — crack/spalling/delamination/corrosion/efflorescence
  3. MCrack1300 (GitHub zxy239) — masonry instance segmentation

Chạy: python scripts/download_v4_sources.py
Xuất: data/raw/public/v4_sources/
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

RAW = Path("data/raw/public/v4_sources")


def hf_files(repo: str) -> list[dict]:
    with urllib.request.urlopen(f"https://huggingface.co/api/datasets/{repo}", timeout=60) as r:
        import json
        d = json.load(r)
    return d.get("siblings", [])


def download(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    done = dst.stat().st_size if dst.exists() else 0
    req = urllib.request.Request(url)
    if done:
        req.add_header("Range", f"bytes={done}-")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            total = done + int(resp.headers.get("Content-Length", 0) or 0)
            if total and done >= total:
                print(f"  [đủ] {dst.name} ({done/1e9:.2f} GB)")
                return
            print(f"  tải {dst.name}...")
            with open(dst, "ab" if done else "wb") as f:
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        print(f"\r  {done/1e9:.2f}/{total/1e9:.2f} GB", end="")
        print(f"  [xong] {dst.name}")
    except Exception as e:  # noqa: BLE001
        print(f"  [lỗi] {dst.name}: {e}")


def git_clone_zip(repo: str, dst: Path) -> None:
    if dst.exists():
        print(f"  [bỏ qua] {dst.name} đã có")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    branch = "main"
    url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"
    print(f"  tải {repo}...")
    download(url, dst)
    if not dst.exists() or dst.stat().st_size < 1000:
        # thử master
        download(f"https://github.com/{repo}/archive/refs/heads/master.zip", dst)


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)

    # 1) CrackSeg9k (HuggingFace parquet)
    print("== 1. CrackSeg9k ==")
    for f in hf_files("rimvydasrub/crackseg9k"):
        name = f["rfilename"]
        if name.endswith(".parquet"):
            download(
                f"https://huggingface.co/datasets/rimvydasrub/crackseg9k/resolve/main/{name}",
                RAW / "crackseg9k" / name,
            )

    # 2) CUHK-USR Defect-Dataset (GitHub zip)
    print("== 2. CUHK-USR Defect-Dataset ==")
    git_clone_zip("CUHK-USR-Group/Defect-Dataset", RAW / "cuhk_usr_defect.zip")

    # 3) MCrack1300 (GitHub zxy239)
    print("== 3. MCrack1300 ==")
    git_clone_zip("zxy239/LoRA-SAM-for-damage-detection", RAW / "mcrack1300.zip")

    print("\nXong tải nguồn v4. Giải nén + convert ở bước build_v4.")


if __name__ == "__main__":
    main()
