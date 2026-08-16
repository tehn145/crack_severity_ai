# Crack Severity AI

**Hệ thống AI multi-task dựa trên YOLOv11 phát hiện, đo bề rộng và phân loại mức độ nghiêm trọng vết nứt bề mặt công trình xây dựng**

> End-to-end multi-task deep learning system for crack detection, marker-free width measurement, and severity classification according to ACI & TCVN standards.

---

## 1. Giới thiệu đề tài

Đề tài tập trung vào việc xây dựng hệ thống trí tuệ nhân tạo giám sát (supervised) kết hợp Computer Vision để:

- Phát hiện vết nứt trên bề mặt bê tông / kết cấu công trình
- Đo bề rộng vết nứt (mm) **không cần marker vật lý**
- Phân loại mức độ nghiêm trọng theo tiêu chuẩn **ACI 224R** và **TCVN**

Hệ thống hướng tới ứng dụng thực tế trong công tác kiểm định và bảo trì công trình tại Việt Nam.

### Điểm mới của đề tài

- Sử dụng **YOLOv11** (công nghệ mới nhất hiện nay)
- Multi-task learning: Detection + Segmentation + Width Regression + Severity Classification
- Đo bề rộng **marker-free** (không cần thước hoặc laser)
- Dataset hybrid: tổng hợp public dataset + dữ liệu tự thu thập từ công trình thực tế Việt Nam
- Phân loại severity theo dual-standard (quốc tế + Việt Nam)

---

## 2. Cấu trúc dự án

```text
crack_severity_ai/
├── data/
│   ├── raw/
│   │   ├── public/                 # Dataset công khai
│   │   └── self_collected/         # Ảnh tự thu thập
│   ├── processed/
│   │   ├── images/
│   │   ├── masks/
│   │   └── labels/
│   ├── splits/
│   └── data.yaml
├── configs/
│   ├── yolo11_seg.yaml
│   ├── multitask_yolo11.yaml
│   └── hyp.yaml
├── src/
│   ├── models/
│   │   ├── multitask_yolo11.py
│   │   └── heads.py
│   ├── utils/
│   │   ├── width_measurement.py
│   │   ├── scale_estimation.py
│   │   ├── metrics.py
│   │   └── visualization.py
│   ├── data/
│   │   ├── dataset.py
│   │   ├── transforms.py
│   │   └── prepare_data.py
│   ├── train.py
│   ├── val.py
│   └── predict.py
├── notebooks/
│   ├── 01_prepare_dataset.ipynb
│   ├── 02_train_yolo11_seg.ipynb
│   └── 03_multitask_and_eval.ipynb
├── runs/                           # Kết quả training (Ultralytics tự tạo)
├── weights/                        # Model đã train
├── scripts/
│   ├── download_public_datasets.ps1
│   └── annotate_helper.py
├── outputs/
│   ├── checkpoints/
│   ├── logs/
│   ├── predictions/
│   └── figures/
├── requirements.txt
└── README.md

3. Công nghệ sử dụng

Model chính: YOLOv11-seg (Ultralytics)
Framework: PyTorch + Ultralytics
Ngôn ngữ: Python 3.10+
Môi trường hỗ trợ: Kaggle, VS Code, Google Colab, Local GPU
Thư viện chính:
ultralytics
opencv-python
numpy
pandas
scikit-learn
matplotlib
torch
torchvision



4. Cài đặt môi trường
Bash# Di chuyển vào thư mục dự án
cd crack_severity_ai

# Tạo môi trường ảo (khuyến nghị)
python -m venv venv

# Kích hoạt môi trường ảo
# Windows:
.\venv\Scripts\activate
# Linux / Mac:
source venv/bin/activate

# Cài đặt các thư viện
pip install -r requirements.txt

5. Dataset
5.1. Nguồn dữ liệu

Public datasets: METU Concrete Crack, SDNET2018, Crack500, CFD, DeepCrack, Concrete Crack Segmentation...
Self-collected: Ảnh chụp thực tế từ các công trình xây dựng tại Việt Nam (có đo tay ground-truth bề rộng vết nứt)

5.2. Cấu trúc dữ liệu sau khi xử lý

images/: Ảnh đầu vào
labels/: Annotation định dạng YOLO (bounding box + segmentation)
metadata.csv: Chứa các thông tin image_id, width_mm, severity_class, scale_factor...

5.3. Định nghĩa mức độ nghiêm trọng (Severity)



































ClassMức độBề rộng tham khảo (mm)Ý nghĩa0No Crack0Không có vết nứt1Minor< 0.3Vết nứt sợi tóc (hairline)2Moderate0.3 – 1.0Cần theo dõi3Severe> 1.0Cần can thiệp / sửa chữa

6. Training
6.1. Train baseline YOLOv11 Segmentation
Bashyolo segment train data=data/data.yaml model=yolo11s-seg.pt epochs=100 imgsz=640 batch=16 name=yolo11_seg_baseline
6.2. Train Multi-task (Detection + Segmentation + Width + Severity)
Bashpython src/train.py --config configs/multitask_yolo11.yaml

7. Inference (Dự đoán)
Bashpython src/predict.py --weights weights/best.pt --source path/to/image_or_folder --save
Kết quả đầu ra:

Bounding box + Instance mask
Bề rộng vết nứt (mm)
Mức độ nghiêm trọng + độ tin cậy
Ảnh trực quan hóa kết quả


8. Các chỉ số đánh giá

Detection: mAP@0.5, mAP@0.5:0.95
Segmentation: mIoU, Dice Coefficient
Width measurement: MAE (mm), Relative Error (%)
Severity classification: Accuracy, Precision, Recall, F1-score, Confusion Matrix


9. Lộ trình phát triển

 Xây dựng cấu trúc dự án
 Tổng hợp và chuẩn hóa dataset public
 Thu thập & gán nhãn dữ liệu thực tế (có đo width)
 Train baseline YOLOv11-seg
 Xây dựng module đo width + scale estimation (marker-free)
 Xây dựng và train multi-task model
 Đánh giá toàn diện trên dữ liệu thực địa
 Viết báo cáo khóa luận và hướng tới paper


10. Thành viên thực hiện

Sinh viên thực hiện: Ngô Kim Thành - 23524117; Trần Công Thành - 23521463.
Giảng viên hướng dẫn: TS. Phan Xuân Thiện
Trường / Khoa: Khoa Mạng máy tính và truyền thông, Trường Đại học Công nghệ Thông tin, ĐHQG-HCM


11. Tài liệu tham khảo chính

Ultralytics YOLOv11 Official Documentation
Các nghiên cứu về crack detection, quantification và severity classification (2024–2026)
ACI 224R-01 – Control of Cracking in Concrete Structures
Các tiêu chuẩn TCVN liên quan đến giới hạn bề rộng vết nứt bê tông