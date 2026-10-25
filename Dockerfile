# Crack Severity AI — Phase 1 serving (FastAPI + Ultralytics, CPU)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MODEL_PATH=/srv/weights/best.pt

# HF Spaces chạy container với UID 1000 — tạo user đúng chuẩn
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

WORKDIR /srv

# Torch CPU trước (nhẹ hơn bản CUDA rất nhiều)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY app/requirements-app.txt app/requirements-app.txt
RUN pip install --no-cache-dir -r app/requirements-app.txt

COPY app/ app/

# Weight KHÔNG nạp vào image:
#  - local : mount qua volume  ./weights:/srv/weights   (docker-compose)
#  - deploy: app tự tải runtime qua env MODEL_REPO (Hugging Face Hub)
RUN mkdir -p /srv/weights /srv/app/data && chown -R appuser:appuser /srv
USER appuser

EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
