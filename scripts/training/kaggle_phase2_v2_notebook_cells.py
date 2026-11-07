# ==============================================================================
# PHASE 2: MULTI-DEFECT CONCRETE DAMAGE SEGMENTATION (ĐỘC LẬP / STANDALONE)
# Dataset: /kaggle/input/datasets/tcongthanh/phase2-multidefect  (pre-extracted)
# 4 Classes: crack | spalling | exposed_rebar | corrosion
# Model: YOLOv8s-seg.pt (standalone, không phụ thuộc Phase 1)
# ==============================================================================


# ─────────────────────────────────────────────────────────────────────────────
# CELL 1 — CÀI ĐẶT & KIỂM TRA MÔI TRƯỜNG
# ─────────────────────────────────────────────────────────────────────────────
!pip install -q ultralytics

import os, yaml
from pathlib import Path
import torch

print(f"PyTorch version : {torch.__version__}")
print(f"CUDA available  : {torch.cuda.is_available()}")
print(f"GPU count       : {torch.cuda.device_count()}")
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")

# ─────────────────────────────────────────────────────────────────────────────
# CELL 2 — KIỂM TRA CẤU TRÚC DATASET & TẠO DATA.YAML
# ─────────────────────────────────────────────────────────────────────────────
# Dataset đã được Kaggle tự extract từ ZIP khi upload
DATASET_ROOT = Path("/kaggle/input/datasets/tcongthanh/phase2-multidefect")

# Liệt kê cấu trúc thực tế để xác nhận
print("=" * 60)
print(f"📁 Cấu trúc dataset tại: {DATASET_ROOT}")
print("=" * 60)
for item in sorted(DATASET_ROOT.rglob("*"))[:40]:
    rel = item.relative_to(DATASET_ROOT)
    depth = len(rel.parts)
    print("  " * (depth - 1) + ("📁 " if item.is_dir() else "📄 ") + item.name)

# ─── Tìm thư mục images/train và images/val ───────────────────────────────
# Thử nhiều cấu trúc có thể xảy ra:
possible_roots = [
    DATASET_ROOT,
    DATASET_ROOT / "phase2-multidefect",
    DATASET_ROOT / "dataset",
]

data_root = None
for candidate in possible_roots:
    if (candidate / "images" / "train").exists():
        data_root = candidate
        break

if data_root is None:
    # Tìm sâu hơn
    found = list(DATASET_ROOT.rglob("images/train"))
    if found:
        data_root = found[0].parent.parent
        print(f"⚠️ Tìm thấy images/train tại: {data_root}")
    else:
        raise FileNotFoundError("❌ Không tìm thấy thư mục images/train! Kiểm tra lại cấu trúc ZIP.")

train_imgs = list((data_root / "images/train").rglob("*.jpg")) + \
             list((data_root / "images/train").rglob("*.png"))
val_imgs   = list((data_root / "images/val").rglob("*.jpg")) + \
             list((data_root / "images/val").rglob("*.png"))
test_imgs  = list((data_root / "images/test").rglob("*.jpg")) + \
             list((data_root / "images/test").rglob("*.png")) if (data_root / "images/test").exists() else []

print(f"\n✅ Dataset root   : {data_root}")
print(f"   Train images  : {len(train_imgs):,}")
print(f"   Val images    : {len(val_imgs):,}")
print(f"   Test images   : {len(test_imgs):,}")
print(f"   Total         : {len(train_imgs) + len(val_imgs) + len(test_imgs):,}")

# ─── Kiểm tra file data.yaml gốc (nếu có) ────────────────────────────────
existing_yaml = data_root / "data.yaml"
if existing_yaml.exists():
    print(f"\n📄 Tìm thấy data.yaml gốc:")
    print(existing_yaml.read_text(encoding="utf-8"))

# ─── Tạo data.yaml chuẩn cho training ────────────────────────────────────
DATA_YAML_PATH = Path("/kaggle/working/data_phase2.yaml")

data_yaml_content = {
    "path": str(data_root),
    "train": "images/train",
    "val":   "images/val",
    "test":  "images/test" if (data_root / "images/test").exists() else "images/val",
    "nc": 4,
    "names": {
        0: "crack",
        1: "spalling",
        2: "exposed_rebar",
        3: "corrosion"
    }
}

with open(DATA_YAML_PATH, "w", encoding="utf-8") as f:
    yaml.dump(data_yaml_content, f, default_flow_style=False, allow_unicode=True)

print(f"\n✅ data.yaml đã tạo tại: {DATA_YAML_PATH}")
print(DATA_YAML_PATH.read_text(encoding="utf-8"))


# ─────────────────────────────────────────────────────────────────────────────
# CELL 3 — HUẤN LUYỆN PHASE 2 (STANDALONE, 100 EPOCHS)
# ─────────────────────────────────────────────────────────────────────────────
from ultralytics import YOLO

print("🚀 Khởi tạo model YOLOv8s-seg (standalone, pretrained COCO)...")
model = YOLO("yolov8s-seg.pt")  # Base weights từ COCO, KHÔNG dùng Phase 1

device = "0,1" if torch.cuda.device_count() > 1 else 0
print(f"📱 Device: {device} | GPUs: {torch.cuda.device_count()}")

RUN_NAME = "yolov8s_seg_phase2_multidefect"

results = model.train(
    data=str(DATA_YAML_PATH),
    task="segment",

    # ── Epochs & Learning Rate ───────────────────────────────────────────────
    epochs=100,          # Đủ cho 4 class hội tụ
    patience=25,         # Early stopping nếu không cải thiện 25 epoch liên tiếp

    # ── Image & Batch ────────────────────────────────────────────────────────
    imgsz=800,           # Nhất quán với Phase 1.2
    batch=8,             # Với dual T4: 8 ảnh/batch ổn định

    # ── Optimizer ────────────────────────────────────────────────────────────
    optimizer="auto",    # Ultralytics tự chọn SGD/Adam tối ưu
    lr0=0.01,            # Learning rate khởi đầu
    lrf=0.01,            # lr cuối = lr0 * lrf = 0.0001
    momentum=0.937,
    weight_decay=0.0005,

    # ── Augmentation ─────────────────────────────────────────────────────────
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,
    flipud=0.5,          # Flip dọc (ảnh công trình từ drone)
    fliplr=0.5,          # Flip ngang
    mosaic=1.0,          # Mosaic augmentation
    mixup=0.1,           # MixUp nhẹ
    copy_paste=0.3,      # Copy-paste mask: quan trọng cho class imbalanced!
    degrees=10,          # Xoay nhẹ
    perspective=0.0005,  # Perspective distortion thực tế
    erasing=0.3,         # Random erasing

    # ── Hardware ─────────────────────────────────────────────────────────────
    device=device,
    workers=2,
    amp=True,            # Mixed precision (nhanh hơn 20-30%)

    # ── Save & Log ───────────────────────────────────────────────────────────
    save=True,
    save_period=10,      # Lưu checkpoint mỗi 10 epoch
    project="/kaggle/working/runs",
    name=RUN_NAME,
    exist_ok=True,
    plots=True,          # Sinh confusion matrix, PR curve, ...
    val=True,
    verbose=True,
)

print("\n" + "=" * 60)
print("🎉 PHASE 2 TRAINING HOÀN TẤT!")
print("=" * 60)
weights_dir = Path(f"/kaggle/working/runs/{RUN_NAME}/weights")
for w in weights_dir.glob("*.pt"):
    size_mb = w.stat().st_size / 1024 / 1024
    print(f"  📦 {w.name}: {size_mb:.1f} MB")


# ─────────────────────────────────────────────────────────────────────────────
# CELL 4 — ĐÁNH GIÁ CUỐI CÙNG TRÊN best.pt
# ─────────────────────────────────────────────────────────────────────────────
from ultralytics import YOLO

best_pt = Path(f"/kaggle/working/runs/{RUN_NAME}/weights/best.pt")
print(f"🔍 Validating best.pt: {best_pt}")

best_model = YOLO(str(best_pt), task="segment")
val_results = best_model.val(
    data=str(DATA_YAML_PATH),
    imgsz=800,
    batch=8,
    device=0,
    split="val",
    save_json=True,
    plots=True,
    verbose=True,
)

print("\n" + "=" * 60)
print("📊 KẾT QUẢ NGHIỆM THU PHASE 2 (best.pt):")
print("=" * 60)
print(f"  Box  Precision : {val_results.box.mp:.4f}")
print(f"  Box  Recall    : {val_results.box.mr:.4f}")
print(f"  Box  mAP50     : {val_results.box.map50:.4f}")
print(f"  Box  mAP50-95  : {val_results.box.map:.4f}")
try:
    print(f"  Mask Precision : {val_results.seg.mp:.4f}")
    print(f"  Mask Recall    : {val_results.seg.mr:.4f}")
    print(f"  Mask mAP50     : {val_results.seg.map50:.4f}")
    print(f"  Mask mAP50-95  : {val_results.seg.map:.4f}")
except:
    pass

print(f"\n  Speed          : {val_results.speed}")
print(f"\n✅ Results saved to: /kaggle/working/runs/{RUN_NAME}/")
print("📥 Hãy download best.pt từ Output panel bên phải!")
