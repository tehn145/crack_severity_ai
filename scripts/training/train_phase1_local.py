#!/usr/bin/env python3
"""
Train thử nhanh Phase 1 YOLO-Seg trên CPU.
Chỉ lấy một ít ảnh mỗi bộ (khớp image–label) → xong mới lên Kaggle.
"""

import random
import shutil
from pathlib import Path
from ultralytics import YOLO

# ===== CẤU HÌNH =====
PRIMARY = Path("data/processed/phase1/primary")
MINI = Path("data/processed/phase1/primary_mini")
YAML_PATH = Path("configs/phase1_local_mini.yaml")
PROJECT = Path("outputs/runs/phase1_local_mini")

MODEL = "yolov8n-seg.pt"
EPOCHS = 5
IMGSZ = 416
BATCH = 2
DEVICE = "cpu"
SEED = 42

# Mỗi prefix lấy tối đa N ảnh train / M ảnh val
PER_PREFIX_TRAIN = 40
PER_PREFIX_VAL = 10

PREFIXES = (
    "CFD_",
    "Crack500_",
    "DeepCrack_",
    "Roads_and_Bridges_",
    "Ultralytics_CrackSeg_",
)


def list_matched(split: str) -> list[tuple[Path, Path]]:
    """Trả về list (img_path, lbl_path) khớp stem."""
    img_dir = PRIMARY / "images" / split
    lbl_dir = PRIMARY / "labels" / split
    if not img_dir.exists() or not lbl_dir.exists():
        return []

    labels = {p.stem: p for p in lbl_dir.glob("*.txt")}
    pairs = []
    for img in img_dir.iterdir():
        if not img.is_file():
            continue
        if img.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".webp"}:
            continue
        lbl = labels.get(img.stem)
        if lbl is not None:
            pairs.append((img, lbl))
    return pairs


def filter_prefix(pairs: list[tuple[Path, Path]], prefix: str) -> list[tuple[Path, Path]]:
    return [p for p in pairs if p[0].stem.startswith(prefix)]


def build_mini():
    """Tạo primary_mini: mỗi bộ một ít, image–label khớp."""
    if MINI.exists():
        shutil.rmtree(MINI)

    rng = random.Random(SEED)
    total = {"train": 0, "val": 0}

    for split, n_per in (("train", PER_PREFIX_TRAIN), ("val", PER_PREFIX_VAL)):
        pairs_all = list_matched(split)
        if not pairs_all:
            print(f"[WARN] Không có dữ liệu matched ở {split}")
            continue

        out_img = MINI / "images" / split
        out_lbl = MINI / "labels" / split
        out_img.mkdir(parents=True, exist_ok=True)
        out_lbl.mkdir(parents=True, exist_ok=True)

        print(f"\n[{split}] lấy tối đa {n_per}/prefix")
        used = 0
        for prefix in PREFIXES:
            group = filter_prefix(pairs_all, prefix)
            if not group:
                # fallback: stem chứa tên bộ (phòng prefix khác)
                key = prefix.rstrip("_").lower()
                group = [p for p in pairs_all if key in p[0].stem.lower()]
            if not group:
                print(f"  {prefix:25s} : 0")
                continue

            rng.shuffle(group)
            take = group[:n_per]
            for img, lbl in take:
                shutil.copy2(img, out_img / img.name)
                shutil.copy2(lbl, out_lbl / lbl.name)
            print(f"  {prefix:25s} : {len(take)}")
            used += len(take)

        # Nếu không match prefix nào, lấy ngẫu nhiên toàn bộ
        if used == 0 and pairs_all:
            rng.shuffle(pairs_all)
            take = pairs_all[: max(n_per * 2, 50)]
            for img, lbl in take:
                shutil.copy2(img, out_img / img.name)
                shutil.copy2(lbl, out_lbl / lbl.name)
            used = len(take)
            print(f"  (fallback random) : {used}")

        total[split] = used

    print(f"\nMini dataset: train={total['train']} | val={total['val']}")
    print(f"Thư mục: {MINI.resolve()}")
    return total


def make_yaml():
    YAML_PATH.parent.mkdir(parents=True, exist_ok=True)
    YAML_PATH.write_text(
        f"""# Mini set — train thử CPU
path: {MINI.resolve().as_posix()}
train: images/train
val: images/val
test: images/val

names:
  0: crack
""",
        encoding="utf-8",
    )
    print("yaml →", YAML_PATH.resolve())

    sample = next((MINI / "labels" / "train").glob("*.txt"), None)
    if sample:
        line = sample.read_text(encoding="utf-8").strip().splitlines()[0]
        n = len(line.split())
        print(f"Sample: {sample.name} | parts={n} (seg >= 7)")
        print(line[:100], "...")


def main():
    print("=" * 55)
    print("LOCAL MINI TRAIN (CPU) — mỗi bộ một ít, khớp img–label")
    print("=" * 55)

    assert (PRIMARY / "images" / "train").exists(), f"Thiếu {PRIMARY}/images/train"
    assert (PRIMARY / "labels" / "train").exists(), f"Thiếu {PRIMARY}/labels/train"

    total = build_mini()
    if total.get("train", 0) == 0:
        print("Không build được mini set. Dừng.")
        return

    make_yaml()

    model = YOLO(MODEL)
    model.train(
        data=str(YAML_PATH),
        epochs=EPOCHS,
        imgsz=IMGSZ,
        batch=BATCH,
        device=DEVICE,
        patience=5,
        save=True,
        project=str(PROJECT),
        name="exp",
        exist_ok=True,
        workers=0,      # Windows CPU ổn định hơn
        verbose=True,
    )

    best = PROJECT / "exp" / "weights" / "best.pt"
    print("\nbest.pt →", best.resolve())

    m = YOLO(str(best))
    metrics = m.val(data=str(YAML_PATH), split="val", device=DEVICE)

    print("\n=== BOX (mini) ===")
    print(f"P={metrics.box.mp:.4f}  R={metrics.box.mr:.4f}")
    print(f"mAP50={metrics.box.map50:.4f}  mAP50-95={metrics.box.map:.4f}")
    print("\n=== MASK (mini) ===")
    print(f"P={metrics.seg.mp:.4f}  R={metrics.seg.mr:.4f}")
    print(f"mAP50={metrics.seg.map50:.4f}  mAP50-95={metrics.seg.map:.4f}")
    print("=" * 55)
    print("Chỉ để kiểm tra pipeline. Số liệu thật → train full trên Kaggle.")


if __name__ == "__main__":
    main()