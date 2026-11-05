"""Kaggle GPU Training Script cho YOLOv8s-seg V3-Core Multi-Surface.

Cách sử dụng trên Kaggle (GPU T4 x2 hoặc P100):
1. Tạo Kaggle Notebook mới, bật Accelerator -> GPU T4 x2
2. Tải file `v3_core_multisurface.zip` lên phần Kaggle Datasets (hoặc upload trực tiếp vào Notebook).
3. Chạy script này để giải nén và huấn luyện tự động với cấu hình tối ưu.
"""

import os
import zipfile
from pathlib import Path

def setup_and_train():
    # 1. Đường dẫn dataset trên Kaggle
    dataset_zip = Path("/kaggle/input/v3-core-multisurface/v3_core_multisurface.zip")
    if not dataset_zip.exists():
        # Tìm trong các thư mục input
        found = list(Path("/kaggle/input").rglob("*.zip"))
        if found:
            dataset_zip = found[0]
            print(f"Tìm thấy file zip: {dataset_zip}")
        else:
            print("Vui lòng tải file v3_core_multisurface.zip vào Kaggle input!")
            return

    work_dir = Path("/kaggle/working/dataset")
    work_dir.mkdir(parents=True, exist_ok=True)
    
    print("Đang giải nén dataset...")
    with zipfile.ZipFile(dataset_zip, 'r') as zf:
        zf.extractall(work_dir)
    print("Giải nén hoàn tất!")

    # Cập nhật đường dẫn tuyệt đối vào data.yaml
    yaml_path = work_dir / "data.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("path: .", f"path: {work_dir.resolve().as_posix()}")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"File data.yaml đã sẵn sàng: {yaml_path}")

    # 2. Huấn luyện YOLOv8s-seg
    from ultralytics import YOLO

    print("Khởi tạo mô hình YOLOv8s-seg...")
    model = YOLO("yolov8s-seg.pt")

    print("Bắt đầu huấn luyện với cấu hình tối ưu cho vết nứt đa bề mặt...")
    results = model.train(
        data=str(yaml_path),
        epochs=150,
        imgsz=960,             # Độ phân giải cao phát hiện vết nứt li ti
        batch=16,              # Phù hợp GPU T4 16GB
        workers=4,
        device=0,              # GPU 0
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        patience=25,           # Early stopping nếu 25 epochs không cải thiện
        save=True,
        save_period=10,        # Lưu checkpoint mỗi 10 epochs
        project="/kaggle/working/runs",
        name="yolov8s_seg_v3_core",
        exist_ok=True,
        # Augmentations tối ưu cho vết nứt công trình
        degrees=15.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        flipud=0.5,
        mosaic=1.0,
        mixup=0.1
    )

    print("HUẤN LUYỆN HOÀN TẤT!")
    print(f"Best weights: /kaggle/working/runs/yolov8s_seg_v3_core/weights/best.pt")

if __name__ == "__main__":
    setup_and_train()
