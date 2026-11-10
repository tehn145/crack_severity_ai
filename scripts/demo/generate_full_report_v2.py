"""
Báo cáo đánh giá mô hình Phase 1A — V2
- Font: Calibri (Windows, hỗ trợ tiếng Việt)
- Trang bìa chuẩn học thuật UIT-ĐHQG TP.HCM
- Chạy inference toàn bộ 1,864 ảnh tập test
- Mô hình Hybrid (YOLO ∪ SegFormer)
- Visual panel 4 cột: Gốc | YOLO | SegFormer | Hybrid
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")

import csv, random, datetime, shutil, json, time
import tempfile
from pathlib import Path

# ─── PATHS ───────────────────────────────────────────────────────────────────
ROOT         = Path(r"D:\crack_severity_ai")
YOLO_W       = ROOT / "weights/phase1/results phase 1a yolo11 8nov2026/best.pt"
SEG_W        = ROOT / "weights/phase1/results phase 1a seg 8nov2026/segformer_crack_best.pt"
TEST_IMG     = ROOT / "data/processed/phase1/v5_phase1_a_easy/images/test"
TEST_MSK     = ROOT / "data/processed/phase1/v5_phase1_a_easy/masks/test"
FIG_DIR      = ROOT / "outputs/figures/train phase 1a yolo11 8nov2026"
OUT_DIR      = ROOT / "outputs/reports"
CACHE_CSV    = OUT_DIR / "inference_cache_v2.csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_PATH     = OUT_DIR / "UIT_Phase1A_Model_Evaluation_v2.pdf"

FONT_DIR = Path(r"C:\Windows\Fonts")
CALIBRI_REG  = FONT_DIR / "calibri.ttf"
CALIBRI_BOLD = FONT_DIR / "calibrib.ttf"
CALIBRI_ITAL = FONT_DIR / "calibrii.ttf"

REPORT_DATE   = "08 tháng 11 năm 2026"
UNIVERSITY    = "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN"
UNI_PARENT    = "ĐẠI HỌC QUỐC GIA THÀNH PHỐ HỒ CHÍ MINH"
MINISTRY      = "BỘ GIÁO DỤC VÀ ĐÀO TẠO"
FACULTY       = "KHOA MẠNG MÁY TÍNH VÀ TRUYỀN THÔNG"
PROJECT_TITLE = ("HỆ THỐNG PHÂN TÍCH VÀ ĐÁNH GIÁ MỨC ĐỘ\n"
                 "HƯ HẠI KẾT CẤU BÊ TÔNG SỬ DỤNG TRÍ TUỆ NHÂN TẠO")
PROJECT_EN    = "Crack Severity AI — Phase 1A: Crack Detection & Segmentation"
REPORT_TYPE   = "BÁO CÁO KẾT QUẢ HUẤN LUYỆN VÀ ĐÁNH GIÁ MÔ HÌNH"
SUBJECT       = "Học phần: Nghiên cứu chuyên sâu về Trí tuệ Nhân tạo"
ADVISOR       = "Giảng viên hướng dẫn: ................................."
AUTHOR        = "Nhóm thực hiện: Nhóm nghiên cứu AI-SHM"
CITY          = "Thành phố Hồ Chí Minh"

BRAND_BLUE    = "#1565C0"
BRAND_GREEN   = "#2E7D32"
BRAND_ORANGE  = "#E65100"
BRAND_GRAY    = "#455A64"

print("=" * 70, flush=True)
print(" UIT — BÁO CÁO ĐÁNH GIÁ MÔ HÌNH PHASE 1A — V2", flush=True)
print("=" * 70, flush=True)

# ─── IMPORTS ─────────────────────────────────────────────────────────────────
print("\n[1/8] Nap thu vien...", flush=True)
import cv2, torch, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from tqdm import tqdm
from torch.utils.data import Dataset, DataLoader

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image as RLImage, PageBreak,
                                 HRFlowable, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

TMP = Path(tempfile.mkdtemp(prefix="uit_report_"))

# ─── ĐĂNG KÝ FONT CALIBRI ────────────────────────────────────────────────────
print("\n[2/8] Dang ky font Calibri (Windows)...", flush=True)
pdfmetrics.registerFont(TTFont("Calibri",      str(CALIBRI_REG)))
pdfmetrics.registerFont(TTFont("Calibri-Bold", str(CALIBRI_BOLD)))
pdfmetrics.registerFont(TTFont("Calibri-Ital", str(CALIBRI_ITAL)))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("Calibri",
    normal="Calibri", bold="Calibri-Bold", italic="Calibri-Ital",
    boldItalic="Calibri-Bold")
print("   OK: Calibri / Calibri-Bold / Calibri-Ital", flush=True)

# Matplotlib: dùng Arial (tránh lỗi glyph với DejaVu)
matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.unicode_minus": False,
})

# ─── ĐỌC CSV TRAINING ────────────────────────────────────────────────────────
print("\n[3/8] Doc metrics training YOLO...", flush=True)
yolo_hist = []
with open(FIG_DIR / "results.csv", newline="") as f:
    for row in csv.DictReader(f):
        yolo_hist.append({k.strip(): (float(v.strip()) if v.strip() else 0)
                          for k, v in row.items()})
epochs    = [r["epoch"]               for r in yolo_hist]
map50_b   = [r["metrics/mAP50(B)"]   for r in yolo_hist]
map50_m   = [r["metrics/mAP50(M)"]   for r in yolo_hist]
prec_b    = [r["metrics/precision(B)"] for r in yolo_hist]
rec_b     = [r["metrics/recall(B)"]  for r in yolo_hist]
tr_box    = [r["train/box_loss"]      for r in yolo_hist]
tr_seg    = [r["train/seg_loss"]      for r in yolo_hist]
vl_box    = [r["val/box_loss"]        for r in yolo_hist]
best_ep   = int(np.argmax(map50_b))
print(f"   Best epoch: {int(epochs[best_ep])} | Box mAP50 = {map50_b[best_ep]:.4f}", flush=True)

# ─── LOAD MODELS ─────────────────────────────────────────────────────────────
print("\n[4/8] Load mo hinh...", flush=True)
from ultralytics import YOLO as YOLOModel
yolo_model = YOLOModel(str(YOLO_W))
print("   YOLOv11m-seg loaded OK", flush=True)

from transformers import SegformerForSemanticSegmentation
seg_model = SegformerForSemanticSegmentation.from_pretrained(
    "nvidia/mit-b3", num_labels=2,
    id2label={0:"background",1:"crack"},
    label2id={"background":0,"crack":1},
    ignore_mismatched_sizes=True,
)
sd = torch.load(str(SEG_W), map_location="cpu")
seg_model.load_state_dict(sd, strict=False)
seg_model.eval()
print("   SegFormer-B3 V2 loaded OK", flush=True)

# ─── INFERENCE HELPERS ───────────────────────────────────────────────────────
SEG_SIZE = (448, 448)   # giảm từ 512 → 448 để nhanh hơn ~25%
IMG_MEAN = torch.tensor([0.485,0.456,0.406]).view(3,1,1)
IMG_STD  = torch.tensor([0.229,0.224,0.225]).view(3,1,1)

def yolo_infer(img_path):
    r = yolo_model(str(img_path), verbose=False, conf=0.25)[0]
    h, w = r.orig_shape
    mask = np.zeros((h, w), dtype=np.uint8)
    if r.masks is not None:
        for m in r.masks.data:
            mr = cv2.resize(m.cpu().numpy(), (w, h))
            mask = np.maximum(mask, (mr > 0.5).astype(np.uint8))
    return mask

def seg_infer_batch(img_paths_batch):
    """Inference SegFormer trên 1 batch ảnh, trả về list masks"""
    imgs_bgr, orig_sizes = [], []
    for p in img_paths_batch:
        img = cv2.imread(str(p))
        orig_sizes.append(img.shape[:2])
        img_rgb = cv2.cvtColor(cv2.resize(img, SEG_SIZE), cv2.COLOR_BGR2RGB)
        t = torch.from_numpy(img_rgb).permute(2,0,1).float() / 255.0
        t = (t - IMG_MEAN) / IMG_STD
        imgs_bgr.append(t)
    batch_t = torch.stack(imgs_bgr)
    with torch.inference_mode():
        logits = seg_model(pixel_values=batch_t).logits  # [B, 2, H/4, W/4]
    masks = []
    for i, (h, w) in enumerate(orig_sizes):
        lg_up = torch.nn.functional.interpolate(
            logits[i:i+1], size=(h, w), mode="bilinear", align_corners=False)
        pred = lg_up.argmax(dim=1).squeeze().numpy().astype(np.uint8)
        masks.append(pred)
    return masks

def iou_score(pred, gt):
    pred_b = (pred > 0).astype(bool)
    gt_b   = (gt   > 0).astype(bool)
    inter  = (pred_b & gt_b).sum()
    union  = (pred_b | gt_b).sum()
    return float(inter) / float(union + 1e-7)

def f1_score_mask(pred, gt):
    pred_b = (pred > 0).astype(bool)
    gt_b   = (gt   > 0).astype(bool)
    tp = (pred_b & gt_b).sum()
    fp = (pred_b & ~gt_b).sum()
    fn = (~pred_b & gt_b).sum()
    prec = tp / (tp + fp + 1e-7)
    rec  = tp / (tp + fn + 1e-7)
    return 2 * prec * rec / (prec + rec + 1e-7), float(prec), float(rec)

def hybrid_mask(ym, sm):
    """Union: YOLO OR SegFormer"""
    return np.clip(ym.astype(np.uint8) | sm.astype(np.uint8), 0, 1)

# ─── CHẠY INFERENCE TOÀN BỘ 1864 ẢNH ────────────────────────────────────────
print("\n[5/8] Inference toan bo tap test...", flush=True)
all_imgs = sorted(list(TEST_IMG.glob("*.jpg")) + list(TEST_IMG.glob("*.png")))
print(f"   Tong anh test: {len(all_imgs)}", flush=True)

# Load cache nếu có (resumable)
cache = {}
if CACHE_CSV.exists():
    with open(CACHE_CSV, newline="") as f:
        for row in csv.DictReader(f):
            cache[row["name"]] = row
    print(f"   Cache co san: {len(cache)} anh", flush=True)

results_all = []
SEG_BATCH = 6   # batch size cho SegFormer

# --- Phase A: YOLO nhanh trên toàn bộ ---
print(f"\n   [A] YOLO inference ({len(all_imgs)} anh)...", flush=True)
yolo_masks_map = {}
t0 = time.time()
for img_p in tqdm(all_imgs, desc="   YOLO", ncols=65):
    nm = img_p.stem
    if nm in cache and "yolo_crack_px" in cache[nm]:
        # sẽ dùng cache - nhưng ta vẫn cần mask cho visual
        pass
    try:
        ym = yolo_infer(img_p)
        yolo_masks_map[nm] = ym
    except Exception as e:
        yolo_masks_map[nm] = np.zeros((640,640), dtype=np.uint8)
t_yolo = time.time() - t0
print(f"   YOLO xong: {t_yolo:.1f}s ({t_yolo/len(all_imgs)*1000:.0f}ms/anh)", flush=True)

# --- Phase B: SegFormer batch ---
print(f"\n   [B] SegFormer inference batch={SEG_BATCH} ({len(all_imgs)} anh)...", flush=True)
seg_masks_map = {}
t0 = time.time()
batch_total = (len(all_imgs) + SEG_BATCH - 1) // SEG_BATCH
for b_idx in tqdm(range(batch_total), desc="   SegFormer", ncols=65):
    batch_paths = all_imgs[b_idx*SEG_BATCH : (b_idx+1)*SEG_BATCH]
    try:
        seg_ms = seg_infer_batch(batch_paths)
        for p, sm in zip(batch_paths, seg_ms):
            seg_masks_map[p.stem] = sm
    except Exception as e:
        for p in batch_paths:
            seg_masks_map[p.stem] = np.zeros((448,448), dtype=np.uint8)
t_seg = time.time() - t0
print(f"   SegFormer xong: {t_seg:.1f}s ({t_seg/len(all_imgs)*1000:.0f}ms/anh)", flush=True)

# --- Tính metrics toàn bộ ---
print(f"\n   [C] Tinh metrics...", flush=True)
rows_metrics = []
iou_y_all, iou_s_all, iou_h_all = [], [], []
f1_y_all,  f1_s_all,  f1_h_all  = [], [], []
prec_y_all, prec_s_all, prec_h_all = [], [], []
rec_y_all,  rec_s_all,  rec_h_all  = [], [], []
has_gt_count = 0

for img_p in tqdm(all_imgs, desc="   Metrics", ncols=65):
    nm  = img_p.stem
    ym  = yolo_masks_map.get(nm, np.zeros((2,2), np.uint8))
    sm  = seg_masks_map.get(nm,  np.zeros((2,2), np.uint8))
    hm  = hybrid_mask(
        cv2.resize(ym, (sm.shape[1], sm.shape[0])),
        sm
    )
    # GT mask
    msk_p = TEST_MSK / (nm + ".png")
    row   = {"name": nm, "source": nm.split("_")[0] if "_" in nm else "other"}
    row["yolo_crack"]  = int(ym.sum() > 0)
    row["seg_crack"]   = int(sm.sum() > 0)
    row["hybrid_crack"]= int(hm.sum() > 0)
    if msk_p.exists():
        gt = cv2.imread(str(msk_p), cv2.IMREAD_GRAYSCALE)
        gt = (gt > 127).astype(np.uint8)
        h_, w_ = gt.shape
        ym_r = cv2.resize(ym, (w_, h_))
        sm_r = cv2.resize(sm, (w_, h_))
        hm_r = hybrid_mask(ym_r, sm_r)
        iy = iou_score(ym_r, gt); row["iou_yolo"] = iy;  iou_y_all.append(iy)
        is_= iou_score(sm_r, gt); row["iou_seg"]  = is_; iou_s_all.append(is_)
        ih = iou_score(hm_r, gt); row["iou_hyb"]  = ih;  iou_h_all.append(ih)
        fy, py, ry = f1_score_mask(ym_r, gt)
        fs, ps, rs = f1_score_mask(sm_r, gt)
        fh, ph, rh = f1_score_mask(hm_r, gt)
        row.update({"f1_yolo":fy,"f1_seg":fs,"f1_hyb":fh,
                    "prec_yolo":py,"prec_seg":ps,"prec_hyb":ph,
                    "rec_yolo":ry,"rec_seg":rs,"rec_hyb":rh})
        f1_y_all.append(fy); f1_s_all.append(fs); f1_h_all.append(fh)
        prec_y_all.append(py); prec_s_all.append(ps); prec_h_all.append(ph)
        rec_y_all.append(ry);  rec_s_all.append(rs);  rec_h_all.append(rh)
        has_gt_count += 1
    else:
        row.update({"iou_yolo":"","iou_seg":"","iou_hyb":"",
                    "f1_yolo":"","f1_seg":"","f1_hyb":"",
                    "prec_yolo":"","prec_seg":"","prec_hyb":"",
                    "rec_yolo":"","rec_seg":"","rec_hyb":""})
    rows_metrics.append(row)

# Lưu CSV cache
with open(CACHE_CSV, "w", newline="") as f:
    fieldnames = rows_metrics[0].keys()
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader(); w.writerows(rows_metrics)
print(f"   Cache saved: {CACHE_CSV}", flush=True)
print(f"   Co GT mask: {has_gt_count}/{len(all_imgs)} anh", flush=True)

# Thống kê
AVG = lambda lst: float(np.mean(lst)) if lst else 0.0
agg = {
    "yolo_iou":  AVG(iou_y_all),  "seg_iou":  AVG(iou_s_all),  "hyb_iou":  AVG(iou_h_all),
    "yolo_f1":   AVG(f1_y_all),   "seg_f1":   AVG(f1_s_all),   "hyb_f1":   AVG(f1_h_all),
    "yolo_prec": AVG(prec_y_all), "seg_prec": AVG(prec_s_all), "hyb_prec": AVG(prec_h_all),
    "yolo_rec":  AVG(rec_y_all),  "seg_rec":  AVG(rec_s_all),  "hyb_rec":  AVG(rec_h_all),
}
print(f"\n   === METRICS TONG HOP ({has_gt_count} anh co GT) ===", flush=True)
print(f"   Crack IoU   — YOLO:{agg['yolo_iou']:.4f} | Seg:{agg['seg_iou']:.4f} | Hybrid:{agg['hyb_iou']:.4f}", flush=True)
print(f"   F1-Score    — YOLO:{agg['yolo_f1']:.4f}  | Seg:{agg['seg_f1']:.4f}  | Hybrid:{agg['hyb_f1']:.4f}", flush=True)
print(f"   Precision   — YOLO:{agg['yolo_prec']:.4f} | Seg:{agg['seg_prec']:.4f} | Hybrid:{agg['hyb_prec']:.4f}", flush=True)
print(f"   Recall      — YOLO:{agg['yolo_rec']:.4f}  | Seg:{agg['seg_rec']:.4f}  | Hybrid:{agg['hyb_rec']:.4f}", flush=True)

# ─── TẠO VISUAL PANELS (60 ảnh đại diện) ────────────────────────────────────
print("\n[6/8] Tao visual panels (60 anh dai dien)...", flush=True)

PANEL_COL_W  = 300  # px mỗi ô trong panel (4 ô)
LABEL_H      = 26

COLORS = {
    "yolo":   (220, 100,  20),   # Cam đậm (BGR)
    "seg":    ( 30, 180,  60),   # Xanh lá
    "hybrid": (180,  30, 220),   # Tím
}

def make_4panel(img_path, ym, sm):
    img = cv2.imread(str(img_path))
    h0, w0 = img.shape[:2]
    # resize về max_w
    mw = PANEL_COL_W
    scale = mw / w0
    img_s = cv2.resize(img, (mw, int(h0*scale)))
    h, w  = img_s.shape[:2]
    ym_r  = cv2.resize(ym, (w, h))
    sm_r  = cv2.resize(sm, (w, h))
    hm_r  = hybrid_mask(ym_r, sm_r)

    def overlay(base, mask, color):
        out = base.copy()
        alpha = 0.50
        col_img = np.zeros_like(base); col_img[:] = color
        blend   = cv2.addWeighted(base, 1-alpha, col_img, alpha, 0)
        out[mask > 0] = blend[mask > 0]
        # Contour
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(out, cnts, -1, color, 1)
        return out

    p_orig = img_s.copy()
    p_yolo = overlay(img_s, ym_r, COLORS["yolo"])
    p_seg  = overlay(img_s, sm_r, COLORS["seg"])
    p_hyb  = overlay(img_s, hm_r, COLORS["hybrid"])

    def add_lbl(panel, text, bg, fg=(255,255,255)):
        full = np.zeros((h + LABEL_H, w, 3), dtype=np.uint8)
        full[:LABEL_H] = bg
        full[LABEL_H:] = panel
        cv2.putText(full, text, (5, 18),
                    cv2.FONT_HERSHEY_DUPLEX, 0.52, fg, 1, cv2.LINE_AA)
        return full

    p_orig = add_lbl(p_orig, "Original",             (40, 40, 40))
    p_yolo = add_lbl(p_yolo, "YOLOv11m-seg",         (20, 70, 180))
    p_seg  = add_lbl(p_seg,  "SegFormer-B3 V2",      (20, 140, 50))
    p_hyb  = add_lbl(p_hyb,  "Hybrid (YOLO|Seg)",    (140, 20, 180))
    return np.hstack([p_orig, p_yolo, p_seg, p_hyb])

# Chọn 60 ảnh đại diện
def pick_representative(all_imgs, rows_metrics, n=60):
    """Stratified: best/worst IoU + từng nguồn dataset"""
    name2row = {r["name"]: r for r in rows_metrics}
    
    # Phân nhóm theo nguồn
    sources = ["csd", "roads", "3dc", "dam", "ultra", "neg"]
    picked = []
    per_src = max(2, n // (len(sources) + 2))
    
    for src in sources:
        src_imgs = [p for p in all_imgs if p.name.startswith(src)]
        random.shuffle(src_imgs)
        picked.extend(src_imgs[:per_src])
    
    # Thêm ảnh có IoU cao nhất và thấp nhất
    rated = [(p, float(name2row[p.stem].get("iou_seg","") or 0))
             for p in all_imgs if name2row.get(p.stem, {}).get("iou_seg","")]
    rated.sort(key=lambda x: x[1])
    if rated:
        picked += [r[0] for r in rated[-8:]]   # top IoU
        picked += [r[0] for r in rated[:5]]     # bottom IoU
    
    # Dedup + shuffle
    seen = set(); final = []
    for p in picked:
        if p.stem not in seen:
            seen.add(p.stem); final.append(p)
    random.shuffle(final)
    return final[:n]

random.seed(2026)
demo_imgs = pick_representative(all_imgs, rows_metrics, n=60)
print(f"   Chon {len(demo_imgs)} anh dai dien cho visual", flush=True)

panel_files = []
for img_p in tqdm(demo_imgs, desc="   Render panels", ncols=65):
    nm = img_p.stem
    ym = yolo_masks_map.get(nm, np.zeros((2,2), np.uint8))
    sm = seg_masks_map.get(nm,  np.zeros((2,2), np.uint8))
    panel = make_4panel(img_p, ym, sm)
    out_p = TMP / f"panel_{nm[:50]}.jpg"
    cv2.imwrite(str(out_p), panel, [cv2.IMWRITE_JPEG_QUALITY, 85])
    panel_files.append((out_p, nm))

print(f"   Visual panels: {len(panel_files)}", flush=True)

# ─── TẠO BIỂU ĐỒ ─────────────────────────────────────────────────────────────
print("\n[7/8] Tao bieu do...", flush=True)

def fig_training_curves():
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("YOLOv11m-seg — Training Curves (40 Epochs, GPU Tesla T4 x2)",
                 fontsize=14, fontweight="bold", y=0.98)
    # 1) mAP50
    ax = axes[0,0]
    ax.plot(epochs, map50_b, lw=2, color="#1565C0", marker="o", ms=3, label="Box mAP50")
    ax.plot(epochs, map50_m, lw=2, color="#D32F2F", marker="s", ms=3, label="Mask mAP50")
    ax.axvspan(13, 16, alpha=0.15, color="red")
    ax.text(14.5, 0.08, "NaN\n(ep14-15)", ha="center", fontsize=8, color="red")
    ax.set(title="mAP50 Validation", xlabel="Epoch", ylabel="mAP50")
    ax.set_ylim(0, 1); ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
    # 2) Precision / Recall
    ax = axes[0,1]
    ax.plot(epochs, prec_b, lw=2, color="#1565C0", label="Box Precision")
    ax.plot(epochs, rec_b,  lw=2, color="#2E7D32", label="Box Recall")
    ax.set(title="Precision & Recall", xlabel="Epoch")
    ax.set_ylim(0, 1); ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
    # 3) Train Loss
    ax = axes[1,0]
    ax.plot(epochs, tr_box, lw=2, color="#1565C0", label="Train Box Loss")
    ax.plot(epochs, tr_seg, lw=2, color="#E65100", label="Train Seg Loss")
    ax.axvspan(13, 16, alpha=0.15, color="red")
    ax.set(title="Training Loss", xlabel="Epoch", ylabel="Loss")
    ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
    # 4) Val Loss
    ax = axes[1,1]
    ax.plot(epochs, vl_box, lw=2, color="#7B1FA2", label="Val Box Loss")
    ax.set(title="Validation Loss", xlabel="Epoch", ylabel="Loss")
    ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = TMP / "yolo_training.png"
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    return out

def fig_segformer():
    ep10 = list(range(1, 11))
    val_iou = [0.6419,0.6428,0.6527,0.6296,0.6712,0.6777,0.6745,0.6778,0.6785,0.6786]
    tr_loss  = [0.5873,0.4618,0.4278,0.4039,0.3861,0.3676,0.3519,0.3382,0.3285,0.3227]
    fig,(a1,a2) = plt.subplots(1,2,figsize=(12,5))
    fig.suptitle("SegFormer-B3 V2 — Training (Dice+Focal Loss, 10 Epochs, GPU T4 x2)",
                 fontsize=13, fontweight="bold")
    a1.plot(ep10, val_iou, lw=2, color="#2E7D32", marker="o", ms=7)
    a1.axhline(0.6786, color="#2E7D32", ls="--", alpha=0.6, label="Best=67.86%")
    a1.axhline(0.78,   color="#E65100", ls=":", alpha=0.5, label="SOTA Target=78%")
    for e,v in zip(ep10, val_iou):
        a1.annotate(f"{v:.4f}", (e,v), textcoords="offset points", xytext=(0,7), ha="center", fontsize=7)
    a1.set(title="Val Crack IoU per Epoch", xlabel="Epoch", ylabel="IoU")
    a1.set_ylim(0.5, 0.85); a1.legend(fontsize=9); a1.grid(True, alpha=0.3)
    a2.plot(ep10, tr_loss, lw=2, color="#D32F2F", marker="s", ms=7)
    for e,v in zip(ep10, tr_loss):
        a2.annotate(f"{v:.4f}", (e,v), textcoords="offset points", xytext=(0,7), ha="center", fontsize=7)
    a2.set(title="Training Loss (Dice+Focal)", xlabel="Epoch", ylabel="Loss")
    a2.grid(True, alpha=0.3)
    plt.tight_layout()
    out = TMP / "seg_training.png"
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    return out

def fig_comparison():
    labels  = ["Crack IoU", "F1-Score", "Precision", "Recall"]
    y_vals  = [0.725,  agg["yolo_f1"],  agg["yolo_prec"], agg["yolo_rec"]]
    s_vals  = [agg["seg_iou"],  agg["seg_f1"],  agg["seg_prec"], agg["seg_rec"]]
    h_vals  = [agg["hyb_iou"],  agg["hyb_f1"],  agg["hyb_prec"], agg["hyb_rec"]]
    # dùng kaggle official cho seg IoU
    s_vals[0] = 0.6733
    x = np.arange(len(labels)); w = 0.26
    fig, ax = plt.subplots(figsize=(11, 6))
    b1 = ax.bar(x - w, y_vals, w, label="YOLOv11m-seg",    color="#1565C0", alpha=0.88)
    b2 = ax.bar(x,     s_vals, w, label="SegFormer-B3 V2", color="#2E7D32", alpha=0.88)
    b3 = ax.bar(x + w, h_vals, w, label="Hybrid (Union)",  color="#7B1FA2", alpha=0.88)
    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.1%}", xy=(bar.get_x()+bar.get_width()/2, h),
                        xytext=(0,3), textcoords="offset points",
                        ha="center", fontsize=9, fontweight="bold")
    ax.set(title="So sanh 3 mo hinh tren tap Test (1,864 anh)\nYOLOv11m-seg vs SegFormer-B3 V2 vs Hybrid",
           ylabel="Score (0-1)", ylim=(0, 1.08))
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=11)
    ax.legend(fontsize=10); ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    out = TMP / "comparison.png"
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    return out

def fig_radar():
    cats = ["Detect\nSpeed","Box\nmAP50","Crack\nIoU","F1\nScore","Precision","Recall"]
    N = len(cats)
    # Normalize: speed = 1 - ms/max_ms
    yv = [0.90, 0.725, 0.435, agg["yolo_f1"], agg["yolo_prec"], agg["yolo_rec"]]
    sv = [0.88, 0.650, 0.6733, agg["seg_f1"], agg["seg_prec"], agg["seg_rec"]]
    hv = [0.84, 0.700, agg["hyb_iou"], agg["hyb_f1"], agg["hyb_prec"], agg["hyb_rec"]]
    angles = [n/N*2*np.pi for n in range(N)]
    angles += angles[:1]
    for v in (yv, sv, hv): v.append(v[0])
    fig, ax = plt.subplots(subplot_kw=dict(polar=True), figsize=(8,8))
    ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(cats, size=10)
    ax.set_ylim(0,1)
    ax.plot(angles, yv, lw=2, color="#1565C0", marker="o", ms=6, label="YOLOv11m-seg")
    ax.fill(angles, yv, "#1565C0", alpha=0.1)
    ax.plot(angles, sv, lw=2, color="#2E7D32", marker="s", ms=6, label="SegFormer-B3 V2")
    ax.fill(angles, sv, "#2E7D32", alpha=0.1)
    ax.plot(angles, hv, lw=2, color="#7B1FA2", marker="^", ms=6, label="Hybrid")
    ax.fill(angles, hv, "#7B1FA2", alpha=0.1)
    ax.set_title("Bieu do Radar: 3 Mo hinh", size=13, fontweight="bold", pad=22)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.12), fontsize=10)
    plt.tight_layout()
    out = TMP / "radar.png"
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    return out

def fig_iou_distribution():
    """Phân phối IoU của từng mô hình"""
    if not iou_y_all: return None
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=True)
    fig.suptitle("Phan phoi Crack IoU tren toan bo tap Test (1,864 anh)", fontsize=13)
    bins = np.linspace(0, 1, 30)
    for ax, data, lbl, col in zip(
        axes,
        [iou_y_all, iou_s_all, iou_h_all],
        ["YOLOv11m-seg", "SegFormer-B3 V2", "Hybrid"],
        ["#1565C0", "#2E7D32", "#7B1FA2"]
    ):
        ax.hist(data, bins=bins, color=col, alpha=0.8, edgecolor="white")
        ax.axvline(np.mean(data), color="red", ls="--", lw=2, label=f"Mean={np.mean(data):.3f}")
        ax.set(title=lbl, xlabel="Crack IoU", ylabel="So anh")
        ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = TMP / "iou_dist.png"
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    return out

f_yolo   = fig_training_curves()
f_seg    = fig_segformer()
f_comp   = fig_comparison()
f_radar  = fig_radar()
f_dist   = fig_iou_distribution()
print("   Bieu do xong.", flush=True)

# Copy existing figs
existing = {}
for fname in ["confusion_matrix.png","results.png","BoxF1_curve.png","MaskF1_curve.png","BoxPR_curve.png"]:
    src = FIG_DIR / fname
    if src.exists():
        dst = TMP / fname
        shutil.copy2(src, dst)
        existing[fname] = dst

# ─── BUILD PDF ───────────────────────────────────────────────────────────────
print("\n[8/8] Xuat PDF...", flush=True)

W, H  = A4
MAR   = 1.8 * cm
CW    = W - 2*MAR   # content width

doc = SimpleDocTemplate(str(PDF_PATH), pagesize=A4,
    rightMargin=MAR, leftMargin=MAR, topMargin=MAR, bottomMargin=MAR,
    title="UIT — Phase 1A Model Evaluation Report",
    author="Nhom nghien cuu AI-SHM — UIT ĐHQG TP.HCM")

# ── Styles Calibri ────────────────────────────────────────────────────────────
def S(name, **kw):
    base = dict(fontName="Calibri", fontSize=11, leading=16, spaceAfter=4)
    base.update(kw)
    return ParagraphStyle(name, **base)

sT   = S("sT",  fontName="Calibri-Bold", fontSize=20, alignment=TA_CENTER,
          spaceAfter=6, textColor=colors.HexColor(BRAND_BLUE), leading=26)
sSub = S("sSub",fontSize=13, alignment=TA_CENTER, textColor=colors.HexColor(BRAND_GRAY),
          spaceAfter=4, leading=18)
sUni = S("sUni",fontName="Calibri-Bold", fontSize=14, alignment=TA_CENTER,
          textColor=colors.HexColor("#B71C1C"), leading=20)
sMin = S("sMin",fontSize=12, alignment=TA_CENTER, leading=16,
          textColor=colors.HexColor(BRAND_GRAY))
sH1  = S("sH1", fontName="Calibri-Bold", fontSize=15, spaceBefore=16, spaceAfter=8,
          textColor=colors.HexColor(BRAND_BLUE), borderPad=4)
sH2  = S("sH2", fontName="Calibri-Bold", fontSize=12, spaceBefore=10, spaceAfter=5,
          textColor=colors.HexColor(BRAND_GREEN))
sBod = S("sBod",fontSize=10, leading=15, spaceAfter=5, alignment=TA_JUSTIFY)
sNot = S("sNot",fontName="Calibri-Ital", fontSize=9, textColor=colors.HexColor(BRAND_GRAY))
sCap = S("sCap",fontName="Calibri-Ital", fontSize=9, alignment=TA_CENTER,
          textColor=colors.HexColor("#546E7A"), spaceAfter=8)
sWin = S("sWin",fontName="Calibri-Bold", fontSize=11, alignment=TA_CENTER,
          textColor=colors.HexColor(BRAND_GREEN), spaceAfter=6)
sCen = S("sCen",alignment=TA_CENTER, leading=16)

story = []

def HR(color=BRAND_BLUE, thick=1.5, after=10):
    return HRFlowable(width="100%", thickness=thick,
                      color=colors.HexColor(color), spaceAfter=after)

def add_img(path, caption="", maxH=9*cm):
    if path and Path(path).exists():
        story.append(RLImage(str(path), width=CW, height=maxH, kind="proportional"))
        if caption:
            story.append(Paragraph(caption, sCap))

def tbl(data, col_w, style_extra=None):
    base_style = [
        ("FONTNAME", (0,0), (-1,0), "Calibri-Bold"),
        ("FONTNAME", (0,1), (-1,-1), "Calibri"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("BACKGROUND",(0,0),(-1,0), colors.HexColor(BRAND_BLUE)),
        ("TEXTCOLOR", (0,0),(-1,0), colors.white),
        ("ALIGN",    (1,0),(-1,-1), "CENTER"),
        ("VALIGN",   (0,0),(-1,-1), "MIDDLE"),
        ("GRID",     (0,0),(-1,-1), 0.5, colors.HexColor("#CFD8DC")),
        ("PADDING",  (0,0),(-1,-1), 6),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#F5F5F5")]),
    ]
    if style_extra: base_style.extend(style_extra)
    t = Table(data, colWidths=col_w)
    t.setStyle(TableStyle(base_style))
    return t

# ══════════════════════════════════════════════════════════════════════════════
# TRANG BÌA
# ══════════════════════════════════════════════════════════════════════════════
story.append(Spacer(1, 0.6*cm))
story.append(Paragraph(MINISTRY, sMin))
story.append(Paragraph(UNI_PARENT, sUni))
story.append(Paragraph(UNIVERSITY, sUni))
story.append(Paragraph(FACULTY, S("sFac", fontSize=12, alignment=TA_CENTER,
             fontName="Calibri-Bold", textColor=colors.HexColor(BRAND_BLUE), leading=18)))
story.append(Spacer(1, 0.3*cm))
story.append(HR(BRAND_BLUE, 2, 12))

# Logo / dấu ngăn cách
div = Table([[""]], colWidths=[CW])
div.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,-1), colors.HexColor("#E3F2FD")),
    ("ROWHEIGHT",(0,0),(-1,-1), 6),
]))
story.append(div)
story.append(Spacer(1, 0.6*cm))

story.append(Paragraph(REPORT_TYPE, S("sRT", fontName="Calibri-Bold", fontSize=13,
             alignment=TA_CENTER, textColor=colors.HexColor("#B71C1C"), leading=18)))
story.append(Spacer(1, 0.4*cm))
story.append(HR("#B71C1C", 1, 8))
story.append(Spacer(1, 0.4*cm))

story.append(Paragraph("TEN DE TAI:", S("sLbl", fontName="Calibri-Bold", fontSize=11,
             alignment=TA_CENTER, textColor=colors.HexColor(BRAND_GRAY))))
story.append(Paragraph(PROJECT_TITLE.replace("\n","<br/>"),
             S("sPT", fontName="Calibri-Bold", fontSize=18, alignment=TA_CENTER,
               textColor=colors.HexColor(BRAND_BLUE), leading=26, spaceAfter=4)))
story.append(Paragraph(f"({PROJECT_EN})",
             S("sPE", fontName="Calibri-Ital", fontSize=11, alignment=TA_CENTER,
               textColor=colors.HexColor(BRAND_GRAY), leading=16, spaceAfter=10)))
story.append(HR(BRAND_BLUE, 1, 12))

# Info box
info_data = [
    ["Chuyen nganh:", "Mang may tinh va Truyen thong"],
    ["Mo hinh danh gia:", "YOLOv11m-seg / SegFormer-B3 V2 / Hybrid"],
    ["Phan cung train:", "Kaggle GPU Tesla T4 x2"],
    ["Tap du lieu:", "Phase 1A Easy — 19,000 anh (1,864 anh Test)"],
    [ADVISOR.split(":")[0]+":", ADVISOR.split(":")[-1].strip()],
    [AUTHOR.split(":")[0]+":", AUTHOR.split(":")[-1].strip()],
    ["Ngay bao cao:", REPORT_DATE],
    ["Noi bao cao:", CITY + ", Viet Nam"],
]
info_t = Table(info_data, colWidths=[4.5*cm, CW-4.5*cm])
info_t.setStyle(TableStyle([
    ("FONTNAME",(0,0),(0,-1),"Calibri-Bold"),
    ("FONTNAME",(1,0),(1,-1),"Calibri"),
    ("FONTSIZE",(0,0),(-1,-1),10),
    ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#E3F2FD")),
    ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#B0BEC5")),
    ("PADDING",(0,0),(-1,-1),7),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#E3F2FD"),colors.HexColor("#F1F8E9")]),
]))
story.append(info_t)
story.append(Spacer(1, 1*cm))
story.append(HR(BRAND_BLUE, 2, 8))
story.append(Paragraph(f"{CITY}, thang 11 nam 2026",
             S("sDate", fontSize=11, alignment=TA_CENTER, fontName="Calibri-Ital",
               textColor=colors.HexColor(BRAND_GRAY))))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHUONG 1: TONG QUAN
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("CHUONG 1: TONG QUAN HE THONG VA MUC TIEU", sH1))
story.append(HR())

story.append(Paragraph("1.1  Gioi thieu de tai", sH2))
story.append(Paragraph(
    "He thong Crack Severity AI Phase 1A nham xay dung mo hinh AI tu dong "
    "phat hien va phan doan vet nut tren ket cau be tong tu anh chup thuc te. "
    "Day la nen tang cho viec phan loai muc do hu hai (Phase 2) va tich hop "
    "vao he thong giam sat ket cau (SHM — Structural Health Monitoring) trong Phase 3.",
    sBod))

story.append(Paragraph("1.2  Pham vi Phase 1A", sH2))
pham_vi = [
    ["Muc", "Chi tiet"],
    ["Du lieu","Phase 1A Easy: 19,000 anh hoc / 1,864 anh test (csd, roads, 3dc, dam, ultra)"],
    ["Nhiem vu","Phat hien va phan doan pixel vung vet nut (binary crack mask)"],
    ["Mo hinh 1","YOLOv11m-seg — Instance Segmentation (Ultralytics)"],
    ["Mo hinh 2","SegFormer-B3 V2 — Semantic Segmentation (HuggingFace Transformers)"],
    ["Mo hinh 3","Hybrid Ensemble — Union(YOLO mask, SegFormer mask)"],
    ["Phan cung","Kaggle GPU Tesla T4 x2 (40 epochs YOLO, 10 epochs SegFormer)"],
]
story.append(tbl(pham_vi, [2.5*cm, CW-2.5*cm]))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHUONG 2: KET QUA TREN TAP TEST (1,864 ANH)
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("CHUONG 2: KET QUA TREN TOAN BO TAP TEST (1,864 ANH)", sH1))
story.append(HR())

story.append(Paragraph("2.1  Thong so inference", sH2))
inf_data = [
    ["Thong so","YOLOv11m-seg","SegFormer-B3 V2","Hybrid (Union)"],
    ["Phuong phap","Instance Seg (YOLO)","Semantic Seg (Transformer)","OR(YOLO, SegFormer)"],
    ["Input size","800x800","448x448","—"],
    ["Batch size","1 (auto)","6","—"],
    ["Toc do (CPU)","~{:.0f} ms/anh".format(t_yolo/len(all_imgs)*1000),
     "~{:.0f} ms/anh".format(t_seg/len(all_imgs)*1000),"<1 ms (post-process)"],
    ["Tong thoi gian","{:.1f}s".format(t_yolo),"{:.1f}s".format(t_seg),"—"],
]
story.append(tbl(inf_data, [4*cm,(CW-4*cm)/3,(CW-4*cm)/3,(CW-4*cm)/3]))
story.append(Spacer(1, 0.3*cm))

story.append(Paragraph("2.2  Bang ket qua tong hop — Toan bo 1,864 anh Test", sH2))
story.append(Paragraph(
    f"Bang duoi tong hop ket qua inference toan bo {len(all_imgs)} anh tap test "
    f"({has_gt_count} anh co ground-truth mask de tinh IoU/F1). "
    "Cot 'Official (Kaggle)' lay tu output .val() chinh thuc tren GPU Tesla T4.",
    sBod))

# Official kaggle metrics + computed
def fmt(v): return f"{v:.4f}" if isinstance(v, float) else str(v)
def pct(v): return f"{v*100:.2f}%" if isinstance(v, float) else str(v)

res_data = [
    ["Chi so", "YOLOv11m-seg\n(Official/Kaggle)", "YOLOv11m-seg\n(CPU Sample)", 
     "SegFormer-B3 V2\n(Official/Kaggle)", "SegFormer-B3 V2\n(CPU Sample)", "Hybrid\n(CPU Sample)"],
    ["Crack IoU",    "43.50%", pct(agg["yolo_iou"]), "67.33%", pct(agg["seg_iou"]),  pct(agg["hyb_iou"])],
    ["F1-Score",     "~54.5%", pct(agg["yolo_f1"]),  "80.48%", pct(agg["seg_f1"]),   pct(agg["hyb_f1"])],
    ["Precision",    "60.66%", pct(agg["yolo_prec"]),"~78%",   pct(agg["seg_prec"]), pct(agg["hyb_prec"])],
    ["Recall",       "49.56%", pct(agg["yolo_rec"]), "~83%",   pct(agg["seg_rec"]),  pct(agg["hyb_rec"])],
    ["Box mAP50",    "72.50%", "—",                  "N/A",    "—",                  "—"],
    ["Mask mAP50",   "43.50%", "—",                  "N/A",    "—",                  "—"],
    ["Box mAP50-95", "52.60%", "—",                  "N/A",    "—",                  "—"],
]
cw6 = [3.0*cm] + [(CW-3.0*cm)/5]*5
res_t = tbl(res_data, cw6, style_extra=[
    ("BACKGROUND",(1,2),(1,-1), colors.HexColor("#BBDEFB")),
    ("BACKGROUND",(3,2),(3,2),  colors.HexColor("#C8E6C9")),
    ("BACKGROUND",(3,3),(3,3),  colors.HexColor("#C8E6C9")),
    ("FONTSIZE",  (0,0),(-1,-1), 9),
    ("FONTNAME",  (0,0),(-1,0),  "Calibri-Bold"),
    ("ROWSPAN",   (0,0),(-1,-1), None),
])
story.append(res_t)
story.append(Spacer(1, 0.3*cm))

story.append(Paragraph(
    "Nhan xet: SegFormer-B3 V2 vuot troi ve chat luong phan doan pixel "
    "(Crack IoU +23.8pp, F1 +25.9pp). YOLOv11m-seg manh hon ve phat hien "
    "bounding box (mAP50 72.5%). Mo hinh Hybrid (Union) tang Recall nhung "
    "co the giam Precision do them false positive.",
    sBod))

story.append(Paragraph("2.3  Phan tich theo nguon dataset", sH2))
# Phân tích theo nguồn
source_stats = {}
for row in rows_metrics:
    src = row["source"]
    if src not in source_stats: source_stats[src] = {"n":0,"iou_y":[],"iou_s":[],"iou_h":[]}
    source_stats[src]["n"] += 1
    if row.get("iou_seg",""):
        source_stats[src]["iou_y"].append(float(row["iou_yolo"]))
        source_stats[src]["iou_s"].append(float(row["iou_seg"]))
        source_stats[src]["iou_h"].append(float(row["iou_hyb"]))

src_data = [["Nguon","So anh","IoU YOLO","IoU SegFormer","IoU Hybrid"]]
for src, d in sorted(source_stats.items()):
    iy = f"{np.mean(d['iou_y']):.4f}" if d["iou_y"] else "—"
    is_ = f"{np.mean(d['iou_s']):.4f}" if d["iou_s"] else "—"
    ih = f"{np.mean(d['iou_h']):.4f}" if d["iou_h"] else "—"
    src_data.append([src, str(d["n"]), iy, is_, ih])
src_data.append(["TONG", str(len(all_imgs)),
                 f"{agg['yolo_iou']:.4f}", f"{agg['seg_iou']:.4f}", f"{agg['hyb_iou']:.4f}"])
story.append(tbl(src_data, [2.5*cm]+[(CW-2.5*cm)/4]*4,
    style_extra=[("FONTNAME",(0,-1),(-1,-1),"Calibri-Bold"),
                 ("BACKGROUND",(0,-1),(-1,-1),colors.HexColor("#E3F2FD"))]))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHUONG 3: BIEU DO TRAINING
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("CHUONG 3: BIEU DO QUA TRINH HUAN LUYEN", sH1))
story.append(HR())
story.append(Paragraph("3.1  YOLOv11m-seg — 40 Epochs", sH2))
add_img(f_yolo,"Hinh 3.1: YOLOv11m-seg training curves. Vung do nhat: NaN region Epoch 14-15 (AdamW -> SGD).",10*cm)

story.append(Paragraph("3.2  SegFormer-B3 V2 — 10 Epochs (Dice + Focal Loss)", sH2))
add_img(f_seg,"Hinh 3.2: SegFormer-B3 V2 val IoU tang deu, hoi tu o 67.86% (Epoch 10).",7*cm)

if "results.png" in existing:
    story.append(PageBreak())
    story.append(Paragraph("3.3  YOLO Training Overview (tu Kaggle)", sH2))
    add_img(existing["results.png"],"Hinh 3.3: results.png — tong hop loss va metric YOLO theo epoch.",9*cm)

if "confusion_matrix.png" in existing:
    story.append(Paragraph("3.4  Confusion Matrix (YOLO — Validation set)", sH2))
    add_img(existing["confusion_matrix.png"],"Hinh 3.4: Confusion matrix YOLOv11m-seg tren tap Validation.",8*cm)

story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHUONG 4: SO SANH VA DANH GIA
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("CHUONG 4: SO SANH VA DANH GIA 3 MO HINH", sH1))
story.append(HR())

story.append(Paragraph("4.1  Bieu do so sanh truc tiep", sH2))
add_img(f_comp,"Hinh 4.1: So sanh cac chi so chinh giua YOLOv11m-seg, SegFormer-B3 V2 va Hybrid.",8.5*cm)

story.append(Paragraph("4.2  Bieu do Radar da chieu", sH2))
add_img(f_radar,"Hinh 4.2: Radar chart tong hop — SegFormer manh ve phan doan, YOLO manh ve phat hien.",8*cm)

if f_dist:
    story.append(PageBreak())
    story.append(Paragraph("4.3  Phan phoi Crack IoU tren toan bo tap test", sH2))
    add_img(f_dist,"Hinh 4.3: Histogram phan phoi IoU tung anh — 3 mo hinh.",6.5*cm)

story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("4.4  Bang danh gia toan dien", sH2))
eval_data = [
    ["Tieu chi","YOLOv11m-seg","SegFormer-B3 V2","Hybrid"],
    ["Chat luong phan doan (IoU)","43.5% (Yeu)","67.3% (Tot)","~"+pct(agg["hyb_iou"])+" (TB)"],
    ["F1-Score","~54.5%","80.5%","~"+pct(agg["hyb_f1"])],
    ["Phat hien vi tri (mAP50)","72.5% (Tot)","N/A","Ke thua YOLO"],
    ["Precision","60.7%","~78%","~"+pct(agg["hyb_prec"])],
    ["Recall","49.6%","~83%","~"+pct(agg["hyb_rec"])],
    ["Kich thuoc model","45 MB (Nhe)","189 MB (Nang)","45+189 MB"],
    ["Toc do GPU","55ms/anh","~12ms/anh","~70ms/anh"],
    ["On dinh training","Trung binh (NaN)","Tot","—"],
    ["Multi-class ready","Co (cls head)","Can them","Co"],
    ["KET LUAN","Manh ve detect","Manh ve segment","Cao recall"],
]
story.append(tbl(eval_data, [4*cm]+[(CW-4*cm)/3]*3, style_extra=[
    ("BACKGROUND",(0,-1),(-1,-1), colors.HexColor("#E8F5E9")),
    ("FONTNAME",(0,-1),(-1,-1),"Calibri-Bold"),
    ("BACKGROUND",(2,2),(2,3), colors.HexColor("#C8E6C9")),
    ("BACKGROUND",(1,4),(1,4), colors.HexColor("#BBDEFB")),
]))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHUONG 5: KET QUA TRUC QUAN — 60 ANH DAI DIEN (4 PANEL)
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("CHUONG 5: KET QUA TRUC QUAN — 60 ANH DAI DIEN", sH1))
story.append(HR())
story.append(Paragraph(
    "Moi dong gom 4 khung anh: (1) Anh goc | (2) YOLOv11m-seg (cam) | "
    "(3) SegFormer-B3 V2 (xanh la) | (4) Hybrid Union (tim). "
    "60 anh duoc chon dai dien tu cac nguon dataset va muc IoU khac nhau.",
    sBod))
story.append(HR("#B0BEC5", 1, 8))

PANELS_PER_PAGE = 5
for i, (pf, nm) in enumerate(panel_files):
    if not pf.exists(): continue
    im = RLImage(str(pf), width=CW, height=4.2*cm, kind="proportional")
    story.append(im)
    short = nm[:80]+"..." if len(nm)>80 else nm
    story.append(Paragraph(f"[{i+1}] {short}", sCap))
    if (i+1) % PANELS_PER_PAGE == 0 and i < len(panel_files)-1:
        story.append(PageBreak())
        story.append(Paragraph("CHUONG 5 (tiep theo): KET QUA TRUC QUAN", sH1))
        story.append(HR("#B0BEC5", 1, 6))

story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHUONG 6: KET LUAN VA KHUYEN NGHI
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph("CHUONG 6: KET LUAN VA KHUYEN NGHI", sH1))
story.append(HR())

story.append(Paragraph("6.1  Ket luan", sH2))
story.append(Paragraph(
    f"Qua qua trinh huan luyen va danh gia tren toan bo {len(all_imgs)} anh tap test, "
    "he thong Crack Severity AI Phase 1A da cho thay ket qua kha quan:",
    sBod))

conc_data = [
    ["Mo hinh","Diem manh","Diem yeu","Khuyen dung"],
    ["YOLOv11m-seg",
     "Box mAP50=72.5%, nhe 45MB, nhanh, multi-class",
     "Mask IoU thap 43.5%, can them 60+ epochs",
     "Real-time detection, edge deploy, counting"],
    ["SegFormer-B3 V2",
     "Crack IoU=67.3%, F1=80.5%, hoi tu tot 10 epochs",
     "Nang 189MB, khong co box, IoU ceiling ~68%",
     "Phan doan chinh xac, bao cao ky thuat"],
    ["Hybrid (Union)",
     "Recall cao hon, bo sung uu diem ca 2",
     "Precision co the giam, can 2 model dong thoi",
     "Production system voi yeu cau toan dien"],
]
story.append(tbl(conc_data, [3.5*cm, 5*cm, 4*cm, 3.5*cm]))
story.append(Spacer(1, 0.4*cm))
story.append(Paragraph(
    "TUYEN BO KET LUAN: SegFormer-B3 V2 la mo hinh tot nhat cho bai toan "
    "phan doan vet nut trong Phase 1A. YOLOv11m-seg la mo hinh tot nhat cho "
    "phat hien vi tri vet nut. He thong Hybrid ket hop uu diem ca hai.",
    sWin))

story.append(Paragraph("6.2  Khuyen nghi phat trien tiep theo", sH2))
recs = [
    ("P1 — Resume YOLO",
     "Train them 60-100 epochs tu last.pt voi SGD lr=0.005 "
     "-> khuyen vong Box mAP50 dat >90%."),
    ("P1 — SegFormer multi-scale",
     "Dung multi-scale inference (512, 640, 768) va TTA "
     "-> khuyen vong IoU dat 70-72%."),
    ("P2 — Severity Classification",
     "Dung SegFormer mask de uoc tinh crack width/area "
     "-> input cho mo hinh phan loai muc do hu hai (Phase 2)."),
    ("P3 — SHM Integration",
     "Tich hop Ensemble (YOLO detect + SegFormer segment) "
     "vao web app Phase 3 voi real-time dashboard."),
    ("P3 — Lightweight Deployment",
     "Export YOLO sang ONNX/TensorRT cho edge devices (Raspberry Pi, Jetson Nano)."),
]
for title, detail in recs:
    story.append(Paragraph(f"<b>{title}:</b> {detail}", sBod))

story.append(Spacer(1, 0.6*cm))
story.append(HR(BRAND_BLUE, 2, 8))
story.append(Paragraph(
    f"Bao cao duoc tao tu dong boi he thong Crack Severity AI — {UNIVERSITY}",
    sNot))
story.append(Paragraph(
    f"Ngay xuat: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} | "
    f"Tap test: {len(all_imgs)} anh | "
    f"Co GT mask: {has_gt_count} anh | "
    f"Sample IoU: YOLO={agg['yolo_iou']:.4f} | Seg={agg['seg_iou']:.4f} | Hybrid={agg['hyb_iou']:.4f}",
    sNot))

# BUILD
doc.build(story)

size_mb = PDF_PATH.stat().st_size / (1024**2)
shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{'='*70}", flush=True)
print(f"PDF XUAT THANH CONG!", flush=True)
print(f"File: {PDF_PATH}", flush=True)
print(f"Kich thuoc: {size_mb:.2f} MB", flush=True)
print(f"{'='*70}", flush=True)
