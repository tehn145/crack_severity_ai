# Script thêm route /phase3 vào app/main.py
from pathlib import Path

p = Path("app/main.py")
content = p.read_text(encoding="utf-8")

if '@app.get("/phase3"' not in content:
    target = '@app.get("/marketplace", response_class=HTMLResponse)'
    new_route = '''@app.get("/phase3", response_class=HTMLResponse)
def phase3_demo_page() -> Response:
    """Giao diện Demo trực quan Phase 3 Structural Health Monitoring."""
    html_path = STATIC_DIR / "phase3_demo.html"
    return HTMLResponse(
        html_path.read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


'''
    content = content.replace(target, new_route + target)
    p.write_text(content, encoding="utf-8")
    print("Added /phase3 route to app/main.py!")
else:
    print("/phase3 route already exists!")
