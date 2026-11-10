# ==============================================================================
# PHASE 1.A — TOURNAMENT MODEL 1: YOLOv11m-seg @ 1024px (Ultralytics SOTA 2024)
# Target: Box mAP50 >= 93.5% - 94.5% (Vượt kỷ lục MDPI 2024 YOLOv8-CA: 92.4%)
# Bề mặt mục tiêu: Tường phẳng, bê tông phẳng, mặt đường nhựa asphalt (SẠCH 100%)
# ==============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# CELL 1 — CÀI ĐẶT MÔI TRƯỜNG & KIỂM TRA GPU
# ─────────────────────────────────────────────────────────────────────────────
# !pip install -q ultralytics

import os, sys, shutil, zipfile, yaml
from pathlib import Path
import torch

print("=" * 60)
print(f"PyTorch version : {torch.__version__}")
print(f"CUDA available  : {torch.cuda.is_available()}")
print(f"GPU count       : {torch.cuda.device_count()}")
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
print("=" * 60)

# ─────────────────────────────────────────────────────────────────────────────
# CELL 2 — GIẢI NÉN DATASET PHASE 1.A & THIẾT LẬP DATA.YAML
# ─────────────────────────────────────────────────────────────────────────────
INPUT_DIR = Path("/kaggle/input")
WORK_DIR = Path("/kaggle/working/dataset_p1a")

if WORK_DIR.exists():
    shutil.rmtree(WORK_DIR)
WORK_DIR.mkdir(parents=True, exist_ok=True)

# Tìm file zip Phase 1.A trong input
zip_files = list(INPUT_DIR.rglob("*.zip"))
p1a_zip = None
for z in zip_files:
    if "phase1_a" in z.name.lower() or "easy" in z.name.lower():
        p1a_zip = z
        break

if p1a_zip:
    print(f"📦 Đang giải nén {p1a_zip.name} vào {WORK_DIR}...")
    with zipfile.ZipFile(p1a_zip, "r") as zf:
        zf.extractall(WORK_DIR)
else:
    candidates = list(INPUT_DIR.rglob("images/train"))
    if candidates:
        WORK_DIR = candidates[0].parent.parent
        print(f"📂 Tìm thấy thư mục dataset có sẵn: {WORK_DIR}")
    else:
        raise FileNotFoundError("❌ Không tìm thấy dataset Phase 1.A! Vui lòng upload phase1_a_easy_surfaces.zip.")

train_imgs = list((WORK_DIR / "images" / "train").glob("*.jpg"))
val_imgs = list((WORK_DIR / "images" / "val").glob("*.jpg"))
test_imgs = list((WORK_DIR / "images" / "test").glob("*.jpg"))

print(f"\n✅ DATASET PHASE 1.A SẠCH SẴN SÀNG:")
print(f"   - Train images : {len(train_imgs):,}")
print(f"   - Val images   : {len(val_imgs):,}")
print(f"   - Test images  : {len(test_imgs):,}")
print(f"   - Total images : {len(train_imgs) + len(val_imgs) + len(test_imgs):,}")

yaml_path = Path("/kaggle/working/data_p1a.yaml")
yaml_data = {
    "path": str(WORK_DIR),
    "train": "images/train",
    "val": "images/val",
    "test": "images/test",
    "nc": 1,
    "names": {0: "crack"}
}
with open(yaml_path, "w", encoding="utf-8") as f:
    yaml.dump(yaml_data, f, default_flow_style=False)

# ─────────────────────────────────────────────────────────────────────────────
# CELL 3 — HUẤN LUYỆN YOLOv11m-seg (SIÊU THAM SỐ TỐI ƯU CẠNH NỨT)
# ─────────────────────────────────────────────────────────────────────────────
from ultralytics import YOLO

# Nạp model thế hệ mới nhất YOLO11m-seg
model = YOLO("yolo11m-seg.pt")

print("\n🚀 BẮT ĐẦU HUẤN LUYỆN YOLOv11m-seg TRÊN TẬP SẠCH PHASE 1.A...")
results = model.train(
    data=str(yaml_path),
    epochs=80,
    imgsz=1024,                     # Độ phân giải cao bắt rãnh nứt vi mô
    batch=8,
    optimizer="AdamW",
    lr0=0.01,
    lrf=0.01,
    warmup_epochs=3.0,
    close_mosaic=10,
    mosaic=1.0,
    copy_paste=0.4,
    degrees=10.0,
    fliplr=0.5,
    flipud=0.5,
    hsv_h=0.015,
    hsv_s=0.6,
    hsv_v=0.4,
    device="0,1" if torch.cuda.device_count() > 1 else 0,
    workers=2,
    save=True,
    save_period=10,
    project="/kaggle/working/runs",
    name="phase1_a_yolo11m_seg",
    exist_ok=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# CELL 4 — ĐÁNH GIÁ TRÊN TẬP TEST & ĐỐI CHIẾU SOTA
# ─────────────────────────────────────────────────────────────────────────────
best_pt = Path("/kaggle/working/runs/phase1_a_yolo11m_seg/weights/best.pt")
eval_model = YOLO(str(best_pt))
metrics = eval_model.val(data=str(yaml_path), split="test", imgsz=1024)

box_map50 = metrics.box.map50 * 100
mask_map50 = metrics.seg.map50 * 100

print("\n" + "=" * 65)
print("🏆 KẾT QUẢ ĐÁNH GIÁ YOLOv11m-seg — ĐỐI CHIẾU SOTA THẾ GIỚI")
print("=" * 65)
print(f"📊 Box mAP50  : {box_map50:.2f}%  (Kỷ lục MDPI 2024: 92.40% | Mục tiêu: >= 93.5%)")
print(f"📊 Mask mAP50 : {mask_map50:.2f}%")
print("=" * 65)

# ─────────────────────────────────────────────────────────────────────────────
# CELL 5 — ĐÓNG GÓI KẾT QUẢ TẢI VỀ MÁY
# ─────────────────────────────────────────────────────────────────────────────
out_zip = Path("/kaggle/working/phase1_a_yolo11_results.zip")
run_dir = Path("/kaggle/working/runs/phase1_a_yolo11m_seg")

with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in [run_dir / "weights/best.pt", run_dir / "results.csv", run_dir / "confusion_matrix.png"]:
        if f.exists():
            zf.write(f, arcname=f.name)
print(f"\n📦 Gói kết quả đã sẵn sàng tải về: {out_zip}")
