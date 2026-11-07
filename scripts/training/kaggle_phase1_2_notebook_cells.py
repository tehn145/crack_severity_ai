# ==============================================================================
# PHASE 1.2: MULTI-SURFACE ULTIMATE CRACK SEGMENTATION (YOLOv8s-seg)
# Bê tông | Mặt đường nhựa | Trụ cầu | Gạch men & Gốm sứ | Di tích gạch cổ | Tường gạch xây
# ==============================================================================

# ------------------------------------------------------------------------------
# CELL 1: GIẢI NÉN DATASET PHASE 1.2 & THIẾT LẬP CẤU HÌNH DATA.YAML
# ------------------------------------------------------------------------------
import os, zipfile, shutil
from pathlib import Path

# Tìm file zip Phase 1.2 dataset trong input
input_dir = Path("/kaggle/input")
zip_candidates = list(input_dir.rglob("*.zip"))
print(f"Tìm thấy các file zip trong input: {[z.name for z in zip_candidates]}")

work_dataset = Path("/kaggle/working/dataset")
if work_dataset.exists():
    shutil.rmtree(work_dataset)
work_dataset.mkdir(parents=True, exist_ok=True)

p1_2_zip = None
for z in zip_candidates:
    if "phase1_2" in z.name.lower() or "multisurface" in z.name.lower():
        p1_2_zip = z
        break

if p1_2_zip is None and zip_candidates:
    p1_2_zip = zip_candidates[0]

print(f"-> Đang giải nén: {p1_2_zip} vào {work_dataset}...")
with zipfile.ZipFile(p1_2_zip, 'r') as zip_ref:
    zip_ref.extractall(work_dataset)

train_imgs = list((work_dataset / "images/train").glob("*.jpg"))
val_imgs = list((work_dataset / "images/val").glob("*.jpg"))
print(f"✅ Giải nén hoàn tất! Train: {len(train_imgs):,} ảnh | Val: {len(val_imgs):,} ảnh")

# Cấu hình data.yaml
data_yaml_content = f"""path: {work_dataset.as_posix()}
train: images/train
val: images/val
test: images/test

nc: 1
names:
  0: crack
"""
yaml_file = work_dataset / "data.yaml"
yaml_file.write_text(data_yaml_content, encoding="utf-8")
print(f"✅ Đã tạo data.yaml chuẩn tại: {yaml_file}")


# ------------------------------------------------------------------------------
# CELL 2: NẠP TRỌNG SỐ BEST.PT (PHA 1.1) VÀ TIẾP TỤC TRAIN PHA 1.2
# ------------------------------------------------------------------------------
from ultralytics import YOLO
import torch

# Tìm checkpoint best.pt từ Pha 1.1
ckpt_candidates = list(input_dir.rglob("best.pt"))
print(f"Tìm thấy checkpoints trong input: {[str(c) for c in ckpt_candidates]}")

if ckpt_candidates:
    weights_path = str(ckpt_candidates[0])
else:
    # Nếu còn trong cùng session Kaggle cũ
    weights_path = "/kaggle/working/runs/yolov8s_seg_v3_core/weights/best.pt"

print(f"-> Khởi động từ trọng số Pha 1.1: {weights_path}")
model = YOLO(weights_path)

# Huấn luyện tiếp Pha 1.2 (Fine-tune trên tập Đa Bề Mặt Toàn Diện)
results = model.train(
    data=str(yaml_file),
    epochs=60,         # 60 epochs là hoàn hảo vì mô hình đã có sẵn nền tảng vững chắc từ Pha 1.1
    imgsz=800,
    batch=8,
    device='0,1' if torch.cuda.device_count() > 1 else 0,
    workers=2,
    lr0=0.001,         # Learning rate 0.001 (thấp hơn 0.01 ban đầu) giúp cập nhật mượt mà
    lrf=0.01,
    patience=15,
    save=True,
    save_period=10,
    amp=True,
    project="/kaggle/working/runs",
    name="yolov8s_seg_phase1_2_ultimate",
    exist_ok=True
)
