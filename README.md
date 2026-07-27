# 🏗️ Concrete Crack Detection using YOLOv7

This project applies **YOLOv7** deep learning models to detect cracks in concrete structures. It is designed for training on **Google Colab** (due to GPU requirements) and inference using Python scripts. The goal is to provide an automated, efficient, and accurate method for structural damage detection.

---

## 📂 Project Structure

```text
concrete-crack-thesis/
│
├── README.md                # Project overview, setup instructions, usage
├── requirements.txt         # Python dependencies
├── .gitignore               # Ignore datasets, large weights, logs
│
├── notebooks/               # Jupyter/Colab notebooks
│   ├── train_yolov7.ipynb   # Training notebook
│   └── inference_demo.ipynb # Demo notebook for crack detection
│
├── src/                     # Source code
│   ├── data_loader.py       # Custom dataset loader
│   ├── train.py             # Training script
│   ├── inference.py         # Inference script
│   └── utils.py             # Helper functions
│
├── configs/                 # Config files
│   └── yolov7_config.yaml   # Model/training configuration
│
├── datasets/                # Dataset folder (sample images only)
│   ├── images/              # Example images
│   └── labels/              # YOLO-format labels
│
├── outputs/                 # Model outputs
│   ├── weights/             # Trained model weights (.pt files)
│   ├── logs/                # Training logs
│   └── results/             # Detection results
│
└── docs/                    # Documentation
    └── project_report.md    # Notes, methodology, references
```

---

## ⚙️ Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tehn145/crack-detection-thesis.git
   cd concrete-crack-detection
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Set up Google Colab:**
   * Upload the repository to your Google Drive.
   * Open `notebooks/train_yolov7.ipynb` in Google Colab.
   * Connect to a GPU runtime (`Runtime > Change runtime type > GPU`).

---

## 📊 Dataset

* The dataset used is **StructGuard** (or your custom dataset).
* Due to file size limits, only sample images are included in the `datasets/` directory.
* The full dataset can be downloaded from the original source repository.

---

## 🚀 Training

To start training using Google Colab or your local machine, run:

```bash
python src/train.py --config configs/yolov7_config.yaml --data datasets/
```

---

## 🔍 Inference

Run inference on test images:

```bash
python src/inference.py --weights outputs/weights/best.pt --source datasets/images/sample.jpg
```

> **Note:** Detection results will be automatically saved in the `outputs/results/` directory.

---

## 📈 Results

* **Detection Accuracy:** *(To be updated after experiments)*
* Example output visualizations are stored in `outputs/results/`.

---

## 📚 References

* [YOLOv7 Official Repository](https://github.com/WongKinYiu/yolov7)
* [StructGuard Dataset](https://github.com/)
* Awesome Crack Detection Papers