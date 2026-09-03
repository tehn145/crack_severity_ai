"""
Phase 1 Detector - Binary classification: Crack / No-Crack
Sử dụng YOLOv11 Classification hoặc Detection tùy chọn.
"""

from ultralytics import YOLO
from pathlib import Path
import torch

class Phase1Detector:
    def __init__(self, model_path: str = None, model_size: str = "n"):
        """
        Args:
            model_path: đường dẫn tới file .pt đã train (best.pt). 
                        Nếu None thì load pretrained YOLOv11.
            model_size: 'n', 's', 'm', 'l', 'x'
        """
        if model_path and Path(model_path).exists():
            self.model = YOLO(model_path)
            print(f"[Phase1] Loaded trained model from: {model_path}")
        else:
            # Dùng classification model cho binary (nhanh & đủ tốt)
            self.model = YOLO(f"yolo11{model_size}-cls.pt")
            print(f"[Phase1] Loaded pretrained yolo11{model_size}-cls.pt")

    def train(self, data_yaml: str, epochs: int = 50, imgsz: int = 224, 
              batch: int = 32, project: str = "runs/phase1", name: str = "train"):
        """Train Phase 1"""
        results = self.model.train(
            data=data_yaml,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            project=project,
            name=name,
            exist_ok=True,
            pretrained=True,
            optimizer="AdamW",
            lr0=0.001,
            patience=15,
            save=True,
            plots=True
        )
        return results

    def predict(self, source, conf: float = 0.5, save: bool = False, **kwargs):
        """Dự đoán có nứt hay không"""
        results = self.model.predict(
            source=source,
            conf=conf,
            save=save,
            **kwargs
        )
        return results

    def val(self, data_yaml: str = None):
        """Đánh giá trên tập validation"""
        return self.model.val(data=data_yaml)