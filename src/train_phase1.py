"""
Train Phase 1 - Detection (Crack / No-Crack)
"""

import argparse
from pathlib import Path
from models.phase1_detector import Phase1Detector

def main():
    parser = argparse.ArgumentParser(description="Train Phase 1 Detector")
    parser.add_argument("--data", type=str, default="data/processed/phase1/data.yaml",
                        help="Path to data.yaml")
    parser.add_argument("--model-size", type=str, default="n", choices=["n", "s", "m", "l", "x"])
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=224)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--project", type=str, default="runs/phase1")
    parser.add_argument("--name", type=str, default="train")
    args = parser.parse_args()

    # Kiểm tra data.yaml
    if not Path(args.data).exists():
        raise FileNotFoundError(f"Không tìm thấy {args.data}. Hãy chạy prepare_data trước.")

    print("=" * 60)
    print("PHASE 1 TRAINING - Crack / No-Crack Detection")
    print("=" * 60)

    detector = Phase1Detector(model_size=args.model_size)
    
    results = detector.train(
        data_yaml=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name=args.name
    )

    # Sau khi train xong, best.pt nằm ở:
    # runs/phase1/train/weights/best.pt
    print("\n[✓] Training finished!")
    print(f"Best model saved at: {args.project}/{args.name}/weights/best.pt")
    print("Hãy copy file best.pt vào thư mục weights/phase1/best.pt")

if __name__ == "__main__":
    main()