# ==============================================================================
# PHASE 2: MULTI-DEFECT CONCRETE DAMAGE SEGMENTATION (ĐỘC LẬP / STANDALONE)
# Vết nứt (Crack) | Bong tróc (Spalling) | Lộ cốt thép (Exposed Rebar) | Gỉ sét (Corrosion)
# ==============================================================================

# ------------------------------------------------------------------------------
# CELL 1: GIẢI NÉN DATASET & THIẾT LẬP CẤU HÌNH DATA.YAML
# ------------------------------------------------------------------------------
import os, zipfile, shutil
from pathlib import Path

# Tìm file zip Phase 2 dataset được add vào input
input_dir = Path("/kaggle/input")
zip_candidates = list(input_dir.rglob("*.zip"))
print(f"Tìm thấy các file zip trong input: {[z.name for z in zip_candidates]}")

work_dataset = Path("/kaggle/working/dataset")
if work_dataset.exists():
    shutil.rmtree(work_dataset)
work_dataset.mkdir(parents=True, exist_ok=True)

# Tìm đúng file zip Phase 2
p2_zip = None
for z in zip_candidates:
    if "phase2" in z.name.lower() or "multidefect" in z.name.lower():
        p2_zip = z
        break

if p2_zip is None and zip_candidates:
    p2_zip = zip_candidates[0]

print(f"-> Đang giải nén: {p2_zip} vào {work_dataset}...")
with zipfile.ZipFile(p2_zip, 'r') as zip_ref:
    zip_ref.extractall(work_dataset)

train_imgs = list((work_dataset / "images/train").glob("*.jpg"))
val_imgs = list((work_dataset / "images/val").glob("*.jpg"))
print(f"✅ Giải nén hoàn tất! Train: {len(train_imgs):,} ảnh | Val: {len(val_imgs):,} ảnh")

# Tạo data.yaml với đường dẫn tuyệt đối cho Kaggle
data_yaml_content = f"""path: {work_dataset.as_posix()}
train: images/train
val: images/val
test: images/test

nc: 4
names:
  0: crack          # Vết nứt bê tông
  1: spalling       # Bong tróc bề mặt bê tông
  2: exposed_rebar  # Lộ cốt thép chịu lực
  3: corrosion      # Gỉ sét / Ăn mòn cốt thép
"""
yaml_file = work_dataset / "data.yaml"
yaml_file.write_text(data_yaml_content, encoding="utf-8")
print(f"✅ Đã tạo data.yaml chuẩn tại: {yaml_file}")


# ------------------------------------------------------------------------------
# CELL 2: HUẤN LUYỆN ĐỘC LẬP TỪ PRETRAINED WEIGHTS GỐC (YOLOv8s-seg.pt)
# ------------------------------------------------------------------------------
from ultralytics import YOLO
import torch

# Huấn luyện mô hình chuyên biệt độc lập từ pretrained chuẩn
print("-> Khởi tạo mô hình độc lập từ yolov8s-seg.pt...")
model = YOLO("yolov8s-seg.pt")

# Bắt đầu huấn luyện độc lập 100 epochs
results = model.train(
    data=str(yaml_file),
    epochs=100,        # 100 epochs đảm bảo hội tụ tối đa cho 4 lớp hư hại
    imgsz=800,
    batch=8,
    device='0,1' if torch.cuda.device_count() > 1 else 0,
    workers=2,
    lr0=0.01,          # Learning rate chuẩn của Ultralytics
    lrf=0.01,
    patience=20,
    save=True,
    save_period=10,
    amp=True,
    project="/kaggle/working/runs",
    name="yolov8s_seg_phase2_defect_standalone",
    exist_ok=True
)
