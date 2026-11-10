"""Demo so sánh và trực quan hóa mô hình Phase 1.A Easy Crack Specialist.

So sánh trực tiếp:
1. YOLOv11m-seg @ 800px (CNN Instance Segmentation)
2. NVIDIA SegFormer-B3 (Vision Transformer Semantic Segmentation)
3. Dual Ensemble (Hợp thể cộng hưởng 2 mô hình)
"""

import sys
import os
import cv2
import numpy as np
import torch
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(r"D:\crack_severity_ai")
YOLO_WEIGHTS = ROOT_DIR / "weights" / "phase1" / "results phase 1a yolo11 8nov2026" / "best.pt"
SEG_WEIGHTS = ROOT_DIR / "weights" / "phase1" / "results phase 1a seg 8nov2026" / "segformer_crack_best.pt"
TEST_IMG_DIR = ROOT_DIR / "data" / "processed" / "phase1" / "v5_phase1_a_easy" / "images" / "test"
OUT_DEMO_DIR = ROOT_DIR / "outputs" / "demo"

OUT_DEMO_DIR.mkdir(parents=True, exist_ok=True)


def load_models():
    print(f"📦 Đang nạp mô hình YOLOv11m-seg từ: {YOLO_WEIGHTS.name} ...", flush=True)
    from ultralytics import YOLO
    yolo_model = YOLO(str(YOLO_WEIGHTS))

    seg_model = None
    try:
        from transformers import SegformerForSemanticSegmentation
        print(f"📦 Đang nạp mô hình SegFormer-B3 từ: {SEG_WEIGHTS.name} ...", flush=True)
        seg_model = SegformerForSemanticSegmentation.from_pretrained(
            "nvidia/mit-b3",
            num_labels=2,
            id2label={0: "background", 1: "crack"},
            label2id={"background": 0, "crack": 1}
        )
        state_dict = torch.load(str(SEG_WEIGHTS), map_location="cpu")
        seg_model.load_state_dict(state_dict)
        seg_model.eval()
        print("✅ Đã nạp thành công cả 2 mô hình!", flush=True)
    except Exception as e:
        print(f"⚠️ Chưa thể nạp SegFormer ({e}), demo sẽ tập trung vào YOLOv11m-seg.", flush=True)

    return yolo_model, seg_model


def run_yolo_inference(yolo_model, img_bgr, conf=0.25):
    h, w = img_bgr.shape[:2]
    results = yolo_model.predict(img_bgr, imgsz=800, conf=conf, verbose=False)[0]

    yolo_vis = img_bgr.copy()
    yolo_mask = np.zeros((h, w), dtype=np.uint8)

    boxes = []
    confs = []

    if results.masks is not None:
        for seg, box in zip(results.masks.xy, results.boxes):
            b_conf = float(box.conf.item())
            confs.append(b_conf)
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            boxes.append(xyxy)

            poly = np.array(seg, dtype=np.int32)
            cv2.fillPoly(yolo_mask, [poly], 255)
            # Vẽ đường viền cyan
            cv2.polylines(yolo_vis, [poly], isClosed=True, color=(255, 255, 0), thickness=2)
            # Vẽ box
            cv2.rectangle(yolo_vis, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (0, 200, 255), 2)
            label_text = f"crack {b_conf:.2f}"
            cv2.putText(yolo_vis, label_text, (xyxy[0], max(xyxy[1] - 6, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

    # Phủ overlay màu Cyan bán trong suốt
    overlay = yolo_vis.copy()
    overlay[yolo_mask > 0] = (255, 200, 0)
    cv2.addWeighted(overlay, 0.45, yolo_vis, 0.55, 0, yolo_vis)

    return yolo_vis, yolo_mask, confs


def run_segformer_inference(seg_model, img_bgr, thresh=0.35):
    if seg_model is None:
        return img_bgr.copy(), np.zeros(img_bgr.shape[:2], dtype=np.uint8)

    h, w = img_bgr.shape[:2]
    # Resize về 512x512
    resized = cv2.resize(img_bgr, (512, 512), interpolation=cv2.INTER_LINEAR)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).transpose(2, 0, 1) / 255.0
    tensor = torch.tensor(rgb, dtype=torch.float32).unsqueeze(0)

    with torch.no_grad():
        outputs = seg_model(pixel_values=tensor)
        logits = torch.nn.functional.interpolate(outputs.logits, size=(h, w), mode="bilinear", align_corners=False)
        probs = torch.nn.functional.softmax(logits, dim=1)[0, 1, :, :].cpu().numpy()

    seg_mask = (probs > thresh).astype(np.uint8) * 255
    seg_vis = img_bgr.copy()

    # Overlay màu tím/hồng (Magenta)
    overlay = seg_vis.copy()
    overlay[seg_mask > 0] = (255, 0, 255)
    cv2.addWeighted(overlay, 0.5, seg_vis, 0.5, 0, seg_vis)
    contours, _ = cv2.findContours(seg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(seg_vis, contours, -1, (255, 50, 200), 2)

    return seg_vis, seg_mask


def run_ensemble(img_bgr, yolo_mask, seg_mask):
    ens_vis = img_bgr.copy()
    h, w = img_bgr.shape[:2]

    both = (yolo_mask > 0) & (seg_mask > 0)
    yolo_only = (yolo_mask > 0) & (seg_mask == 0)
    seg_only = (seg_mask > 0) & (yolo_mask == 0)

    overlay = ens_vis.copy()
    # Xanh lá: Cả 2 mô hình cùng đồng thuận (High Confidence)
    overlay[both] = (0, 255, 0)
    # Cyan: Chỉ YOLO thấy
    overlay[yolo_only] = (255, 200, 0)
    # Magenta: Chỉ SegFormer thấy
    overlay[seg_only] = (255, 0, 255)

    cv2.addWeighted(overlay, 0.55, ens_vis, 0.45, 0, ens_vis)

    # Chú thích
    cv2.putText(ens_vis, "XANH LA: Dong thuan (YOLO+Seg)", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(ens_vis, "CYAN: YOLO | MAGENTA: SegFormer", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

    return ens_vis


def create_panel(orig, yolo_v, seg_v, ens_v, filename):
    # Chuẩn hóa về cùng chiều cao 480px
    target_h = 480
    panels = []
    titles = ["1. ANH GOC", "2. YOLOV11m-seg", "3. SEGFORMER-B3", "4. ENSEMBLE HOP THE"]
    
    for img, title in zip([orig, yolo_v, seg_v, ens_v], titles):
        h, w = img.shape[:2]
        new_w = int(w * (target_h / h))
        res = cv2.resize(img, (new_w, target_h))
        # Ghi tiêu đề panel
        cv2.rectangle(res, (0, 0), (new_w, 35), (20, 20, 20), -1)
        cv2.putText(res, title, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        panels.append(res)

    combined = np.hstack(panels)
    out_p = OUT_DEMO_DIR / f"demo_comparison_{filename}.jpg"
    cv2.imwrite(str(out_p), combined)
    print(f"✅ Đã tạo ảnh Demo so sánh tại: {out_p}", flush=True)
    return out_p


def main():
    yolo_model, seg_model = load_models()

    # Chọn 4 mẫu đại diện từ Test set
    test_files = sorted(list(TEST_IMG_DIR.glob("*.jpg")))
    if not test_files:
        print("❌ Không tìm thấy ảnh test trong thư mục.")
        return

    # Lấy 1 ảnh csd, 1 ảnh roads, 1 ảnh 3dc
    samples = []
    for prefix in ["csd_", "roads_", "3dc_", "dam_"]:
        match = [f for f in test_files if f.name.startswith(prefix)]
        if match:
            samples.append(match[len(match) // 2])  # lấy mẫu giữa

    if not samples:
        samples = test_files[:4]

    print(f"\n🚀 Đang chạy Demo suy luận trên {len(samples)} ảnh mẫu Test Set...", flush=True)

    summary_results = []
    for i, img_path in enumerate(samples):
        print(f"\n--- [Ảnh {i+1}/{len(samples)}]: {img_path.name} ---", flush=True)
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            continue

        yolo_vis, yolo_mask, confs = run_yolo_inference(yolo_model, img_bgr)
        seg_vis, seg_mask = run_segformer_inference(seg_model, img_bgr)
        ens_vis = run_ensemble(img_bgr, yolo_mask, seg_mask)

        out_img = create_panel(img_bgr, yolo_vis, seg_vis, ens_vis, img_path.stem)

        # Tính toán diện tích vết nứt
        yolo_area = np.sum(yolo_mask > 0)
        seg_area = np.sum(seg_mask > 0)
        both_area = np.sum((yolo_mask > 0) & (seg_mask > 0))
        total_pixels = img_bgr.shape[0] * img_bgr.shape[1]

        summary_results.append({
            "image": img_path.name,
            "yolo_detections": len(confs),
            "max_conf": max(confs) if confs else 0.0,
            "yolo_area_pct": (yolo_area / total_pixels) * 100,
            "seg_area_pct": (seg_area / total_pixels) * 100,
            "agreement_pct": (both_area / (max(yolo_area, seg_area) + 1e-6)) * 100,
            "demo_path": str(out_img)
        })

    print("\n" + "=" * 70, flush=True)
    print("📊 BẢNG TỔNG HỢP KẾT QUẢ SUY LUẬN THỰC CHIẾN DEMO:", flush=True)
    for res in summary_results:
        print(f"  • {res['image']}:")
        print(f"      YOLOv11: {res['yolo_detections']} vết nứt (Conf cao nhất: {res['max_conf']:.2f}, Diện tích: {res['yolo_area_pct']:.2f}%)")
        print(f"      SegFormer: Diện tích nứt {res['seg_area_pct']:.2f}%")
        print(f"      Độ đồng thuận 2 mô hình (Agreement): {res['agreement_pct']:.1f}%")
    print("=" * 70, flush=True)


if __name__ == "__main__":
    main()
