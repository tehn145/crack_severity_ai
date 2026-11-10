# ==============================================================================
# PHASE 1.A: EASY CRACK SPECIALIST (YOLOv8m-seg @ 1024px)
# Target: Box mAP50 >= 93.5% (Vượt kỷ lục SOTA MDPI 2024 YOLOv8-CA: 92.4%)
# Bề mặt mục tiêu: Tường bê tông phẳng, mặt đường nhựa asphalt, bề mặt phẳng
# Chuẩn hóa tiền xử lý: Bilateral Filter + CLAHE + ~12% Negative Backgrounds
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

# Tìm file zip Phase 1.A trong input (hoặc nếu Kaggle đã giải nén sẵn)
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
    # Trường hợp dataset đã được giải nén sẵn bởi Kaggle Datasets
    candidates = list(INPUT_DIR.rglob("images/train"))
    if candidates:
        source_root = candidates[0].parent.parent
        print(f"📂 Tìm thấy thư mục dataset có sẵn: {source_root}")
        WORK_DIR = source_root
    else:
        raise FileNotFoundError("❌ Không tìm thấy dataset Phase 1.A! Vui lòng upload phase1_a_easy_surfaces.zip.")

# Kiểm tra số lượng ảnh
train_imgs = list((WORK_DIR / "images" / "train").glob("*.jpg")) + list((WORK_DIR / "images" / "train").glob("*.png"))
val_imgs = list((WORK_DIR / "images" / "val").glob("*.jpg")) + list((WORK_DIR / "images" / "val").glob("*.png"))
test_imgs = list((WORK_DIR / "images" / "test").glob("*.jpg")) + list((WORK_DIR / "images" / "test").glob("*.png"))

print(f"\n✅ DATASET PHASE 1.A SẴN SÀNG:")
print(f"   - Train images : {len(train_imgs):,}")
print(f"   - Val images   : {len(val_imgs):,}")
print(f"   - Test images  : {len(test_imgs):,}")
print(f"   - Total images : {len(train_imgs) + len(val_imgs) + len(test_imgs):,}")

# Tạo file data.yaml chuẩn
yaml_data = {
    "path": str(WORK_DIR),
    "train": "images/train",
    "val": "images/val",
    "test": "images/test",
    "nc": 1,
    "names": {0: "crack"}
}
yaml_path = Path("/kaggle/working/data_p1a.yaml")
with open(yaml_path, "w", encoding="utf-8") as f:
    yaml.dump(yaml_data, f, default_flow_style=False)
print(f"📄 File cấu hình đã sẵn sàng tại: {yaml_path}")

# ─────────────────────────────────────────────────────────────────────────────
# CELL 3 — HUẤN LUYỆN YOLOv8m-seg VỚI SIÊU THAM SỐ TỐI ƯU CHO SOTA
# ─────────────────────────────────────────────────────────────────────────────
from ultralytics import YOLO

# Khởi tạo từ pre-trained YOLOv8m-seg (Medium kiến trúc phân giải cao)
model = YOLO("yolov8m-seg.pt")

print("\n🚀 BẮT ĐẦU HUẤN LUYỆN PHASE 1.A — EASY CRACK SPECIALIST...")
results = model.train(
    data=str(yaml_path),
    epochs=80,
    imgsz=1024,                     # Độ phân giải 1024px để bắt trọn rãnh nứt vi mô
    batch=8,                        # Phù hợp GPU T4 16GB
    optimizer="AdamW",
    lr0=0.01,
    lrf=0.01,
    warmup_epochs=3.0,
    close_mosaic=10,
    # Tăng cường dữ liệu chuẩn kỹ thuật kết cấu
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
    name="phase1_a_easy_v5",
    exist_ok=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# CELL 4 — ĐÁNH GIÁ CHÍNH XÁC TRÊN TẬP TEST ĐỘC LẬP & SO SÁNH VỚI SOTA
# ─────────────────────────────────────────────────────────────────────────────
best_pt = Path("/kaggle/working/runs/phase1_a_easy_v5/weights/best.pt")
print(f"\n🔍 Nạp mô hình tốt nhất từ: {best_pt}")
eval_model = YOLO(str(best_pt))

# Đánh giá trên tập test (chưa từng thấy trong lúc train)
metrics = eval_model.val(data=str(yaml_path), split="test", imgsz=1024)

box_map50 = metrics.box.map50 * 100
mask_map50 = metrics.seg.map50 * 100
box_map50_95 = metrics.box.map * 100
mask_map50_95 = metrics.seg.map * 100

print("\n" + "=" * 65)
print("🏆 KẾT QUẢ ĐÁNH GIÁ PHASE 1.A — ĐỐI CHIẾU SOTA THẾ GIỚI")
print("=" * 65)
print(f"📊 Box mAP50        : {box_map50:.2f}%  (Mục tiêu SOTA: >= 93.5%)")
print(f"📊 Mask mAP50       : {mask_map50:.2f}%")
print(f"📊 Box mAP50-95     : {box_map50_95:.2f}%")
print(f"📊 Mask mAP50-95    : {mask_map50_95:.2f}%")
print("-" * 65)
print(f"📌 Kỷ lục Paper MDPI 2024 (YOLOv8-CA) : 92.40% mAP50")

if box_map50 >= 93.5:
    print(f"🎉 XÁC LẬP KỶ LỤC MỚI! Vượt SOTA thế giới +{box_map50 - 92.4:.2f}%! ĐÃ ĐẾN LÚC ĂN MỪNG! 🥳🚀")
elif box_map50 >= 92.4:
    print(f"✅ Vượt qua Paper MDPI 2024 (+{box_map50 - 92.4:.2f}%)!")
else:
    print(f"⚠️ Đạt {box_map50:.2f}% (Cần thêm epochs hoặc tinh chỉnh threshold).")
print("=" * 65)

# ─────────────────────────────────────────────────────────────────────────────
# CELL 5 — ĐÓNG GÓI KẾT QUẢ TẢI VỀ MÁY (BEST.PT, MATRIX, CHARTS)
# ─────────────────────────────────────────────────────────────────────────────
out_zip = Path("/kaggle/working/phase1_a_results.zip")
run_dir = Path("/kaggle/working/runs/phase1_a_easy_v5")

files_to_save = [
    run_dir / "weights/best.pt",
    run_dir / "weights/last.pt",
    run_dir / "results.csv",
    run_dir / "results.png",
    run_dir / "confusion_matrix.png",
    run_dir / "confusion_matrix_normalized.png",
    run_dir / "val_batch0_pred.jpg",
    run_dir / "val_batch1_pred.jpg",
]

with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in files_to_save:
        if f.exists():
            zf.write(f, arcname=f.name)
            print(f"  + Đã thêm {f.name} vào gói tải về.")

print(f"\n📦 Gói kết quả tải về: {out_zip} ({out_zip.stat().st_size / (1024*1024):.2f} MB)")
