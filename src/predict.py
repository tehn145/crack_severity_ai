"""
Inference script - hỗ trợ Phase 1 (và sẽ mở rộng Phase 2 sau)
"""

import argparse
from pathlib import Path
from models.phase1_detector import Phase1Detector

def main():
    parser = argparse.ArgumentParser(description="Predict with Phase 1")
    parser.add_argument("--weights", type=str, required=True,
                        help="Path to best.pt of Phase 1")
    parser.add_argument("--source", type=str, required=True,
                        help="Image, folder, or video")
    parser.add_argument("--conf", type=float, default=0.5)
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--project", type=str, default="outputs/predictions")
    parser.add_argument("--name", type=str, default="phase1")
    args = parser.parse_args()

    if not Path(args.weights).exists():
        raise FileNotFoundError(f"Không tìm thấy weights: {args.weights}")

    print(f"[Phase1] Loading model from: {args.weights}")
    detector = Phase1Detector(model_path=args.weights)

    results = detector.predict(
        source=args.source,
        conf=args.conf,
        save=args.save,
        project=args.project,
        name=args.name
    )

    print(f"[✓] Prediction done. Results saved in {args.project}/{args.name}")

if __name__ == "__main__":
    main()