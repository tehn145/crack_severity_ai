# DEVOPS.md — Quy trình vận hành crack_severity_ai

Tài liệu này mô tả pipeline phát triển – kiểm thử – triển khai sản phẩm theo quy mô
"mini công ty", dùng cho chương bảo vệ khóa luận.

## 1. Kiến trúc serving

```
GitHub (main) ──push──► GitHub Actions
                          │
                          ├─ CI   : ruff lint → pytest → import check
                          │        (unit test đặc trưng Lớp A + smoke test API,
                          │         test cần GPU/weight tự skip trên CI)
                          │
                          └─ Deploy: upload app/ + Dockerfile lên HF Space
                                     (Docker SDK, port 7860, private)

HF Space (Docker) ──runtime──► tải best.pt từ HF Model Repo (MODEL_REPO)
                     │
                     ├─ FastAPI  /api/predict      (YOLOv8s-seg, CPU)
                     ├─ SQLite   hồ sơ kiểm định (inspections, detections)
                     └─ Static   giao diện kỹ sư kiểm định (HTML/JS)

Local dev  : uvicorn app.main:app --port 7860     (weight tại weights/phase1/)
Local docker: docker compose up                   (mount ./weights/phase1 → /srv/weights)
```

## 2. Thành phần

| Thành phần | File | Vai trò |
|---|---|---|
| API serving | `app/main.py` | FastAPI: predict, hồ sơ, báo cáo HTML/CSV |
| Model layer | `app/model_service.py` | Load YOLO 1 lần; đo đặc trưng Lớp A (slot Phase 2) |
| DB | `app/db.py` | SQLite: `inspections` + `detections` |
| UI | `app/static/` | Workflow kỹ sư kiểm định (thông tin → ảnh → kết quả → lưu → báo cáo) |
| Test | `tests/` | `test_features.py` (Lớp A), `test_api.py` (smoke, tự skip khi thiếu weight) |
| Container | `Dockerfile`, `docker-compose.yml` | Image CPU (torch CPU + headless opencv), volume weight + DB |
| CI | `.github/workflows/ci.yml` | lint + test mỗi push/PR |
| CD | `.github/workflows/deploy-hf.yml` | deploy sau CI pass trên main |

## 3. Biến môi trường

| Biến | Ý nghĩa | Mặc định |
|---|---|---|
| `MODEL_PATH` | Đường dẫn weight local | `weights/phase1/best.pt` |
| `MODEL_REPO` | HF Model Repo để tải weight runtime (deploy) | rỗng |
| `HF_TOKEN` | Token đọc Model Repo (deploy) | rỗng |
| `DEFAULT_CONF` / `DEFAULT_IMGSZ` | Tham số suy luận mặc định | 0.25 / 640 |

## 4. Runbook triển khai (làm 1 lần)

1. **Model Repo (Hugging Face)** — lưu weight:
   ```bash
   pip install -q huggingface_hub
   huggingface-cli login
   hf upload tehn145/crack-phase1 weights/phase1/best.pt best.pt
   ```
2. **Tạo Space** `tehn145/crack-severity-ai` (Docker SDK, Private) — deploy workflow tự tạo nếu chưa có.
3. **Secrets GitHub** (Settings → Secrets and variables → Actions):
   - `HF_TOKEN` = token có quyền write Spaces + read Models.
   - (tuỳ chọn) Variables `HF_SPACE_ID` = `<user>/<space>`.
4. Push lên `main` → CI chạy → auto deploy. Space bật env `MODEL_REPO=tehn145/crack-phase1`
   trong tab Settings của Space (một lần).

## 5. Vòng đời phát triển

```
feature-branch → PR → CI (lint+test) → merge main → Deploy HF
                                        ↘ nếu fail: chặn deploy
```

- Model mới: train trên Kaggle → tải best.pt → upload Model Repo → Space tự dùng ở lần
  khởi động kế tiếp (không cần deploy lại code).
- Code mới: push → CI → deploy tự động.
- Rollback: revert commit trên main → pipeline deploy lại bản trước.

## 6. Giám sát & sự cố

| Triệu chứng | Kiểm tra | Xử lý |
|---|---|---|
| Space 403/404 cho hội đồng | Space đang Private | mời reviewer qua "Invite" hoặc chuyển Public ngày bảo vệ |
| `/api/health` → `degraded` | log Space: thiếu weight | kiểm tra `MODEL_REPO`/`HF_TOKEN` trong Space settings |
| Phân tích chậm (>5s/ảnh) | Space CPU cơ bản | bình thường với 1280px; demo dùng 640 |
| Mất hồ sơ | volume `crack_data` bị xoá | DB chỉ là demo — export CSV định kỳ nếu cần giữ |

## 7. An toàn dữ liệu

- Ảnh hiện trường chỉ lưu trong volume của Space; không gửi dịch vụ ngoài nào khác.
- Space để **Private** trong lúc phát triển; ngày bảo vệ có thể chuyển Public hoặc dùng share-link.
