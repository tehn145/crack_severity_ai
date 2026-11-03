#!/usr/bin/env python3
"""parallel_download.py — Tải file lớn bằng N range song song (curl), ghép + verify."""
import subprocess, sys, os
from pathlib import Path

def head_size(url: str) -> int:
    r = subprocess.run(["curl", "-sIL", url], capture_output=True, text=True, timeout=60)
    size = 0
    for line in r.stdout.lower().splitlines():
        if line.startswith("content-length:"):
            size = int(line.split(":")[1].strip())
            if size > 0:
                break
    return size

def parallel(url: str, out: str, size: int, n: int = 8) -> None:
    chunk = size // n
    procs = []
    for i in range(n):
        start = i * chunk
        end = size - 1 if i == n - 1 else (i + 1) * chunk - 1
        part = f"{out}.part{i}"
        if os.path.exists(part) and os.path.getsize(part) == end - start + 1:
            print(f"  part{i}: đã có")
            continue
        procs.append((i, subprocess.Popen(
            ["curl", "-sL", "--retry", "5", "-C", "-", "-o", part,
             "-r", f"{start}-{end}", url],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)))
    for i, pr in procs:
        pr.wait()
        print(f"  part{i}: xong")
    # ghép
    with open(out, "wb") as f:
        for i in range(n):
            part = f"{out}.part{i}"
            with open(part, "rb") as pf:
                shutil_copyfileobj(pf, f)
            os.remove(part)

def shutil_copyfileobj(pf, f):
    while True:
        b = pf.read(1 << 22)
        if not b:
            break
        f.write(b)

if __name__ == "__main__":
    url, out = sys.argv[1], sys.argv[2]
    size = int(sys.argv[3])
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    parallel(url, out, size, n)
    actual = os.path.getsize(out)
    print(f"Kết quả: {out} {actual/1e6:.0f} MB (kỳ vọng {size/1e6:.0f} MB) — {'ĐÚNG' if actual == size else 'LỆCH'}")
