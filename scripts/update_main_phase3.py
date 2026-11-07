# Script cập nhật app/main.py
from pathlib import Path

p = Path("app/main.py")
content = p.read_text(encoding="utf-8")

if "from .phase3_endpoints import router as phase3_router" not in content:
    content = content.replace(
        "from .model_service import DEFAULT_IMGSZ, detect, get_model\n",
        "from .model_service import DEFAULT_IMGSZ, detect, get_model\nfrom .phase3_endpoints import router as phase3_router\n",
    )

if "app.include_router(phase3_router)" not in content:
    content = content.replace(
        'app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")\n',
        'app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")\napp.include_router(phase3_router)\n',
    )

content = content.replace('APP_VERSION = "3.1.0-phase1+2"', 'APP_VERSION = "3.2.0-phase3-shm"')

p.write_text(content, encoding="utf-8")
print("app/main.py updated!")
