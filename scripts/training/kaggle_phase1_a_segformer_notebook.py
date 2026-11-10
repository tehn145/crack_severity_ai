# ==============================================================================
# KAGGLE NOTEBOOK HOÀN CHỈNH — CHẠY TỪ ĐẦU ĐẾN CUỐI (TỰ ĐỘNG 100%)
# Mô hình: NVIDIA SegFormer-B3 (Vision Transformer Semantic Segmentation)
# Tập dữ liệu: Phase 1.A Easy Crack Specialist (19,133 ảnh sạch)
# Tính năng: 
#   - Tự động nạp vào SSD siêu tốc có thanh tiến độ tqdm
#   - Chống tràn bộ nhớ OOM (Gradient Checkpointing + Batch 4 + Accumulation 2)
#   - Tăng tốc phần cứng GPU Tensor Cores (AMP FP16)
#   - Thanh tiến độ tqdm thời gian thực cho TẤT CẢ các bước
# ==============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# Ô 1: CÀI ĐẶT THƯ VIỆN & CẤU HÌNH BỘ NHỚ CHỐNG PHÂN MẢNH
# ─────────────────────────────────────────────────────────────────────────────
!pip install -q transformers evaluate albumentations datasets accelerate torchmetrics

import os, sys, shutil, json, time, gc
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import SegformerForSemanticSegmentation
from tqdm.auto import tqdm

# Dọn sạch VRAM
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()

print("=" * 60)
print(f"PyTorch version : {torch.__version__}")
print(f"CUDA available  : {torch.cuda.is_available()}")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
print(f"Thiết bị đang dùng: {device} ({gpu_name})")
print("=" * 60)

# ─────────────────────────────────────────────────────────────────────────────
# Ô 2: CHUYỂN DỮ LIỆU SANG SSD CỤC BỘ (CÓ THANH ĐO TIẾN ĐỘ THỜI GIAN THỰC)
# ─────────────────────────────────────────────────────────────────────────────
dest_dir = Path("/kaggle/working/data")
dest_dir.mkdir(parents=True, exist_ok=True)

# Tự động tìm nguồn dataset trong /kaggle/input
input_root = None
for root, dirs, files in os.walk("/kaggle/input"):
    if "images" in dirs and "masks" in dirs:
        input_root = Path(root)
        break
if not input_root:
    for root, dirs, files in os.walk("/kaggle/input"):
        if "images" in dirs:
            input_root = Path(root)
            break

print(f"📂 Đã tìm thấy dataset tại: {input_root}")

# Kiểm tra nếu chưa copy thì mới copy
train_check = dest_dir / "images" / "train"
if not train_check.exists() or len(list(train_check.glob("*.jpg"))) == 0:
    all_files = []
    for root, dirs, files in os.walk(input_root):
        for f in files:
            all_files.append(Path(root) / f)

    print(f"📦 Đang chuyển {len(all_files):,} files sang ổ SSD NVMe...")

    def copy_file(src):
        rel = src.relative_to(input_root)
        tgt = dest_dir / rel
        tgt.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, tgt)

    with ThreadPoolExecutor(max_workers=16) as executor:
        list(tqdm(
            executor.map(copy_file, all_files),
            total=len(all_files),
            desc="⚡ Nạp dữ liệu vào SSD",
            unit="file"
        ))
else:
    print("⚡ Dữ liệu đã có sẵn trên SSD cục bộ, bỏ qua bước copy!")

train_imgs = list((dest_dir / "images" / "train").glob("*.jpg"))
val_imgs = list((dest_dir / "images" / "val").glob("*.jpg"))
test_imgs = list((dest_dir / "images" / "test").glob("*.jpg"))

print(f"\n✅ DỮ LIỆU SẴN SÀNG TRÊN SSD CỤC BỘ:")
print(f"   • Train images : {len(train_imgs):,} ảnh")
print(f"   • Val images   : {len(val_imgs):,} ảnh")
print(f"   • Test images  : {len(test_imgs):,} ảnh")
print(f"   • Tổng cộng    : {len(train_imgs) + len(val_imgs) + len(test_imgs):,} ảnh")

# ─────────────────────────────────────────────────────────────────────────────
# Ô 3: DATASET LOADER & KHỞI TẠO KIẾN TRÚC NVIDIA SEGFORMER-B3
# ─────────────────────────────────────────────────────────────────────────────
class FastCrackDataset(Dataset):
    def __init__(self, root_dir: Path, split: str = "train"):
        self.img_dir = root_dir / "images" / split
        self.msk_dir = root_dir / "masks" / split
        self.images = sorted(list(self.img_dir.glob("*.jpg")))

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_p = self.images[idx]
        msk_p = self.msk_dir / f"{img_p.stem}.png"

        img = cv2.imread(str(img_p))
        if img is None:
            img = np.zeros((512, 512, 3), dtype=np.uint8)
        else:
            img = cv2.resize(img, (512, 512), interpolation=cv2.INTER_LINEAR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).transpose(2, 0, 1) / 255.0

        if msk_p.exists():
            msk = cv2.imread(str(msk_p), cv2.IMREAD_GRAYSCALE)
            if msk is None:
                msk = np.zeros((512, 512), dtype=np.int64)
            else:
                msk = cv2.resize(msk, (512, 512), interpolation=cv2.INTER_NEAREST)
                msk = (msk > 127).astype(np.int64)
        else:
            msk = np.zeros((512, 512), dtype=np.int64)

        return {
            "pixel_values": torch.tensor(img, dtype=torch.float32),
            "labels": torch.tensor(msk, dtype=torch.long)
        }

train_ds = FastCrackDataset(dest_dir, "train")
val_ds = FastCrackDataset(dest_dir, "val")
test_ds = FastCrackDataset(dest_dir, "test")

# Batch_size=4 an toàn tuyệt đối cho VRAM (chỉ tốn ~4GB)
train_loader = DataLoader(train_ds, batch_size=4, shuffle=True, num_workers=4, pin_memory=True)
val_loader = DataLoader(val_ds, batch_size=4, shuffle=False, num_workers=2, pin_memory=True)
test_loader = DataLoader(test_ds, batch_size=4, shuffle=False, num_workers=2, pin_memory=True)

# Khởi tạo mô hình SegFormer-B3
id2label = {0: "background", 1: "crack"}
label2id = {"background": 0, "crack": 1}

model = SegformerForSemanticSegmentation.from_pretrained(
    "nvidia/mit-b3",
    num_labels=2,
    id2label=id2label,
    label2id=label2id
)

# Kích hoạt Gradient Checkpointing tiết kiệm 60% VRAM
model.gradient_checkpointing_enable()
model.to(device)

print(f"🚀 Nạp thành công kiến trúc NVIDIA SegFormer-B3 trên {device} (Đã bật Gradient Checkpointing)!")

# ─────────────────────────────────────────────────────────────────────────────
# Ô 4: HUẤN LUYỆN TURBO GPU (15 EPOCHS — CÓ THANH TIẾN ĐỘ THỜI GIAN THỰC)
# ─────────────────────────────────────────────────────────────────────────────
optimizer = torch.optim.AdamW(model.parameters(), lr=6e-5, weight_decay=1e-2)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=15)
scaler = torch.amp.GradScaler("cuda")

accumulation_steps = 2  # Tích lũy 2 bước -> Tương đương batch_size=8 hoàn hảo
best_val_loss = float("inf")
save_path = Path("/kaggle/working/segformer_crack_best.pt")

print("\n🚀 BẮT ĐẦU HUẤN LUYỆN TURBO SEGFORMER-B3 (15 EPOCHS)...")

for epoch in range(1, 16):
    model.train()
    total_loss = 0
    optimizer.zero_grad()
    
    pbar = tqdm(train_loader, desc=f"Epoch [{epoch:02d}/15] Train", leave=False)

    for step, batch in enumerate(pbar):
        pixel_values = batch["pixel_values"].to(device, non_blocking=True)
        labels = batch["labels"].to(device, non_blocking=True)

        with torch.amp.autocast("cuda"):
            outputs = model(pixel_values=pixel_values, labels=labels)
            loss = outputs.loss / accumulation_steps

        scaler.scale(loss).backward()

        if (step + 1) % accumulation_steps == 0 or (step + 1) == len(train_loader):
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()

        total_loss += (loss.item() * accumulation_steps)
        current_avg = total_loss / (step + 1)
        pbar.set_postfix({"loss": f"{current_avg:.4f}", "lr": f"{scheduler.get_last_lr()[0]:.2e}"})

    scheduler.step()
    avg_loss = total_loss / len(train_loader)

    # Đánh giá Validation
    model.eval()
    val_loss = 0
    val_pbar = tqdm(val_loader, desc=f"Epoch [{epoch:02d}/15] Val", leave=False)
    with torch.no_grad():
        for batch in val_pbar:
            p_val = batch["pixel_values"].to(device, non_blocking=True)
            l_val = batch["labels"].to(device, non_blocking=True)
            with torch.amp.autocast("cuda"):
                out = model(pixel_values=p_val, labels=l_val)
            val_loss += out.loss.item()
            val_pbar.set_postfix({"val_loss": f"{val_loss / (len(val_pbar) or 1):.4f}"})

    avg_val = val_loss / len(val_loader)
    print(f"✅ Epoch [{epoch:02d}/15] -> Train Loss: {avg_loss:.4f} | Val Loss: {avg_val:.4f}")

    if avg_val < best_val_loss:
        best_val_loss = avg_val
        torch.save(model.state_dict(), save_path)
        print(f"   ⭐ Đã lưu Checkpoint tốt nhất tại: {save_path} (Val Loss: {avg_val:.4f})")

print(f"\n🎉 Huấn luyện SegFormer-B3 hoàn tất! File đã lưu tại: {save_path}")

# ─────────────────────────────────────────────────────────────────────────────
# Ô 5: ĐÁNH GIÁ SOTA TRÊN TẬP TEST & ĐÓNG GÓI TẢI VỀ MÁY
# ─────────────────────────────────────────────────────────────────────────────
print("\n📊 Đang đánh giá chất lượng mô hình trên tập TEST độc lập...")
model.load_state_dict(torch.load(save_path))
model.eval()

intersection_total = 0
union_total = 0
tp_total = 0
fp_total = 0
fn_total = 0

with torch.no_grad():
    for batch in tqdm(test_loader, desc="Đang đánh giá Test set"):
        p_test = batch["pixel_values"].to(device)
        l_test = batch["labels"].to(device)

        with torch.amp.autocast("cuda"):
            outputs = model(pixel_values=p_test)
            logits = outputs.logits
            upsampled_logits = nn.functional.interpolate(
                logits, size=(512, 512), mode="bilinear", align_corners=False
            )
            preds = torch.argmax(upsampled_logits, dim=1)

        preds_crack = (preds == 1)
        labels_crack = (l_test == 1)

        intersection = (preds_crack & labels_crack).sum().item()
        union = (preds_crack | labels_crack).sum().item()
        tp = intersection
        fp = (preds_crack & (~labels_crack)).sum().item()
        fn = ((~preds_crack) & labels_crack).sum().item()

        intersection_total += intersection
        union_total += union
        tp_total += tp
        fp_total += fp
        fn_total += fn

iou_crack = (intersection_total / union_total) * 100 if union_total > 0 else 0
f1_crack = (2 * tp_total / (2 * tp_total + fp_total + fn_total)) * 100 if (2 * tp_total + fp_total + fn_total) > 0 else 0

print("\n" + "=" * 65)
print("🏆 KẾT QUẢ ĐÁNH GIÁ SEGFORMER-B3 TRÊN TẬP TEST ĐỘC LẬP")
print("=" * 65)
print(f"📊 Crack IoU     : {iou_crack:.2f}%  (Mục tiêu SOTA: >= 80% - 85%)")
print(f"📊 Crack F1-Score: {f1_crack:.2f}%  (Mục tiêu: >= 92% - 95%)")
print("=" * 65)

# Đóng gói file zip tải về
import zipfile
out_zip = Path("/kaggle/working/segformer_b3_crack_results.zip")
with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(save_path, arcname="segformer_crack_best.pt")
print(f"\n📦 File kết quả đã sẵn sàng tải về: {out_zip} ({out_zip.stat().st_size / (1024*1024):.2f} MB)")
