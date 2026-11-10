import sys
import os
import random
import cv2
import numpy as np
import torch
import shutil
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(r"D:\crack_severity_ai")
YOLO_WEIGHTS = ROOT_DIR / "weights" / "phase1" / "results phase 1a yolo11 8nov2026" / "best.pt"
SEG_WEIGHTS = ROOT_DIR / "weights" / "phase1" / "results phase 1a seg 8nov2026" / "segformer_crack_best.pt"
TEST_IMG_DIR = ROOT_DIR / "data" / "processed" / "phase1" / "v5_phase1_a_easy" / "images" / "test"
OUT_DEMO_DIR = ROOT_DIR / "outputs" / "demo" / "random_tests"
ARTIFACT_DIR = Path(r"C:\Users\ngoki\.gemini\antigravity\brain\774e93cd-4171-4601-9e48-40b3c2b50a36")

OUT_DEMO_DIR.mkdir(parents=True, exist_ok=True)


def load_models():
    from ultralytics import YOLO
    from transformers import SegformerForSemanticSegmentation

    print("📦 Đang nạp YOLOv11m-seg...", flush=True)
    yolo_model = YOLO(str(YOLO_WEIGHTS))

    print("📦 Đang nạp SegFormer-B3...", flush=True)
    seg_model = SegformerForSemanticSegmentation.from_pretrained(
        "nvidia/mit-b3",
        num_labels=2,
        id2label={0: "background", 1: "crack"},
        label2id={"background": 0, "crack": 1}
    )
    seg_model.load_state_dict(torch.load(str(SEG_WEIGHTS), map_location="cpu"))
    seg_model.eval()

    return yolo_model, seg_model


def run_yolo(yolo_model, img_bgr, conf=0.25):
    h, w = img_bgr.shape[:2]
    res = yolo_model.predict(img_bgr, imgsz=800, conf=conf, verbose=False)[0]

    yolo_vis = img_bgr.copy()
    yolo_mask = np.zeros((h, w), dtype=np.uint8)
    confs = []

    if res.masks is not None:
        for seg, box in zip(res.masks.xy, res.boxes):
            c = float(box.conf.item())
            confs.append(c)
            xyxy = box.xyxy[0].cpu().numpy().astype(int)

            poly = np.array(seg, dtype=np.int32)
            cv2.fillPoly(yolo_mask, [poly], 255)
            cv2.polylines(yolo_vis, [poly], True, (255, 255, 0), 2)
            cv2.rectangle(yolo_vis, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (0, 200, 255), 2)
            cv2.putText(yolo_vis, f"crack {c:.2f}", (xyxy[0], max(xyxy[1] - 5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

    overlay = yolo_vis.copy()
    overlay[yolo_mask > 0] = (255, 200, 0)
    cv2.addWeighted(overlay, 0.45, yolo_vis, 0.55, 0, yolo_vis)

    return yolo_vis, yolo_mask, confs


def run_seg(seg_model, img_bgr, thresh=0.35):
    h, w = img_bgr.shape[:2]
    resized = cv2.resize(img_bgr, (512, 512), interpolation=cv2.INTER_LINEAR)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).transpose(2, 0, 1) / 255.0
    tensor = torch.tensor(rgb, dtype=torch.float32).unsqueeze(0)

    with torch.no_grad():
        out = seg_model(pixel_values=tensor)
        logits = torch.nn.functional.interpolate(out.logits, size=(h, w), mode="bilinear", align_corners=False)
        probs = torch.nn.functional.softmax(logits, dim=1)[0, 1, :, :].cpu().numpy()

    seg_mask = (probs > thresh).astype(np.uint8) * 255
    seg_vis = img_bgr.copy()

    overlay = seg_vis.copy()
    overlay[seg_mask > 0] = (255, 0, 255)
    cv2.addWeighted(overlay, 0.5, seg_vis, 0.5, 0, seg_vis)
    contours, _ = cv2.findContours(seg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(seg_vis, contours, -1, (255, 50, 200), 2)

    return seg_vis, seg_mask


def run_ens(img_bgr, yolo_mask, seg_mask):
    ens_vis = img_bgr.copy()
    both = (yolo_mask > 0) & (seg_mask > 0)
    yolo_only = (yolo_mask > 0) & (seg_mask == 0)
    seg_only = (seg_mask > 0) & (yolo_mask == 0)

    overlay = ens_vis.copy()
    overlay[both] = (0, 255, 0)
    overlay[yolo_only] = (255, 200, 0)
    overlay[seg_only] = (255, 0, 255)

    cv2.addWeighted(overlay, 0.55, ens_vis, 0.45, 0, ens_vis)
    cv2.putText(ens_vis, "XANH LA: Dong thuan (YOLO+Seg)", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(ens_vis, "CYAN: YOLO | MAGENTA: SegFormer", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

    return ens_vis


def create_panel(orig, yolo_v, seg_v, ens_v, filename):
    target_h = 420
    panels = []
    titles = ["1. ANH GOC", "2. YOLOV11m-seg", "3. SEGFORMER-B3", "4. ENSEMBLE HOP THE"]

    for img, title in zip([orig, yolo_v, seg_v, ens_v], titles):
        h, w = img.shape[:2]
        new_w = int(w * (target_h / h))
        res = cv2.resize(img, (new_w, target_h))
        cv2.rectangle(res, (0, 0), (new_w, 32), (20, 20, 20), -1)
        cv2.putText(res, title, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        panels.append(res)

    combined = np.hstack(panels)
    out_p = OUT_DEMO_DIR / f"random_{filename}.jpg"
    cv2.imwrite(str(out_p), combined)

    # Copy sang artifact dir để hiển thị trên chat
    art_p = ARTIFACT_DIR / f"random_{filename}.jpg"
    shutil.copy2(out_p, art_p)

    return out_p, art_p


def main():
    yolo_model, seg_model = load_models()

    # Lấy toàn bộ ảnh trong test set (không lấy ảnh âm neg_ để test vết nứt thực sự)
    all_test = [f for f in TEST_IMG_DIR.glob("*.jpg") if not f.name.startswith("neg_")]
    print(f"📂 Tìm thấy {len(all_test):,} ảnh có nứt trong Test Set.", flush=True)

    # Chọn ngẫu nhiên 4 ảnh
    random.seed(42)  # có thể đổi hoặc bỏ seed
    random_samples = random.sample(all_test, 4)

    print("\n🎲 DANH SÁCH 4 ẢNH TEST ĐƯỢC CHỌN NGẪU NHIÊN:", flush=True)
    results = []

    for i, img_path in enumerate(random_samples):
        print(f"   [{i+1}/4] Đang phân tích: {img_path.name} ...", flush=True)
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            continue

        yolo_vis, yolo_mask, confs = run_yolo(yolo_model, img_bgr)
        seg_vis, seg_mask = run_seg(seg_model, img_bgr)
        ens_vis = run_ens(img_bgr, yolo_mask, seg_mask)

        out_p, art_p = create_panel(img_bgr, yolo_vis, seg_vis, ens_vis, f"sample_{i+1}")

        total_px = img_bgr.shape[0] * img_bgr.shape[1]
        yolo_area = np.sum(yolo_mask > 0)
        seg_area = np.sum(seg_mask > 0)
        both_area = np.sum((yolo_mask > 0) & (seg_mask > 0))

        agreement = (both_area / (max(yolo_area, seg_area) + 1e-6)) * 100

        results.append({
            "idx": i + 1,
            "filename": img_path.name,
            "yolo_count": len(confs),
            "max_conf": max(confs) if confs else 0.0,
            "yolo_area": (yolo_area / total_px) * 100,
            "seg_area": (seg_area / total_px) * 100,
            "agreement": agreement,
            "artifact_path": str(art_p.as_posix()),
            "out_path": str(out_p.as_posix())
        })

    print("\n" + "=" * 70, flush=True)
    print("📊 KẾT QUẢ PHÂN TÍCH 4 MẪU TEST RANDOM:")
    for r in results:
        print(f"  Mẫu {r['idx']} ({r['filename']}):")
        print(f"    - YOLOv11: {r['yolo_count']} vết nứt (Conf cao nhất: {r['max_conf']:.2f}, Diện tích: {r['yolo_area']:.2f}%)")
        print(f"    - SegFormer: Diện tích nứt {r['seg_area']:.2f}%")
        print(f"    - Độ đồng thuận (Ensemble Agreement): {r['agreement']:.1f}%")
    print("=" * 70, flush=True)


if __name__ == "__main__":
    main()
