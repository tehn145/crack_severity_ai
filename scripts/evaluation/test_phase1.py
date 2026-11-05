from ultralytics import YOLO
from pathlib import Path

# Load model
model = YOLO("weights/phase1/best.pt")

# Thử trên vài ảnh trong tập test
test_dir = Path("data/processed/phase1/images/test")
test_images = list(test_dir.glob("*.jpg"))[:5] + list(test_dir.glob("*.png"))[:5]

print(f"Đang chạy thử trên {len(test_images)} ảnh...")

results = model.predict(
    source=test_images,
    save=True,
    project="outputs/predictions",
    name="phase1_test",
    conf=0.25
)

print("Đã lưu kết quả tại: outputs/predictions/phase1_test")