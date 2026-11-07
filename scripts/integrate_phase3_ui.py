# Script tích hợp Phase 3 vào app/static/index.html và app/static/app.js
from pathlib import Path

# 1. Cập nhật index.html
index_path = Path("app/static/index.html")
index_text = index_path.read_text(encoding="utf-8")

# Thêm tab nav
nav_target = '<a href="#/inspect" data-view="inspect">Phiếu kiểm tra</a>'
nav_replacement = '''<a href="#/inspect" data-view="inspect">Phiếu kiểm tra</a>
      <a href="#/phase3" data-view="phase3">🤖 Giám định SHM (Phase 3)</a>'''

if 'data-view="phase3"' not in index_text:
    index_text = index_text.replace(nav_target, nav_replacement)

# Thêm badge AI component vào wpane-1
comp_target = '<label>Cấu kiện <select id="component"></select></label>'
comp_replacement = '''<label>Cấu kiện (AI tự động chọn khi có ảnh) <select id="component"></select></label>
            </div>
            <div id="ai-component-tag" style="grid-column:1/-1;font-size:12.5px;color:#1d4ed8;background:#eff6ff;padding:7px 12px;border-radius:6px;border:1px solid #bfdbfe;display:none;"></div>
            <div>'''
if 'id="ai-component-tag"' not in index_text:
    index_text = index_text.replace(comp_target, comp_replacement)

# Thêm view-phase3 vào main
phase3_section = '''
      <!-- PHASE 3 SHM CONSOLE EMBEDDED -->
      <section id="view-phase3" class="view" hidden>
        <div class="page-head">
          <div>
            <h1>Structural Health Monitoring (SHM) Console — Phase 3</h1>
            <p>Hệ thống giám định toàn diện: Dual Inference (Phase 1.2 + Phase 2) + Khử trùng lặp ORB + AI Phân loại cấu kiện + Chỉ số sụp đổ SCI</p>
          </div>
          <div class="head-actions">
            <a class="btn ghost" href="/phase3" target="_blank">Mở toàn màn hình ↗</a>
          </div>
        </div>

        <div style="background:#fff;border:1px solid #cbd5e1;border-radius:12px;overflow:hidden;box-shadow:0 4px 15px rgba(0,0,0,0.05);min-height:800px;">
          <iframe src="/phase3" style="width:100%;height:850px;border:none;" title="Phase 3 SHM Console"></iframe>
        </div>
      </section>
'''

if 'id="view-phase3"' not in index_text:
    # Chèn trước view-analytics
    analytics_target = '<!-- INFERENCE ENGINE -->'
    index_text = index_text.replace(analytics_target, phase3_section + '\n      ' + analytics_target)

index_path.write_text(index_text, encoding="utf-8")
print("index.html updated!")

# 2. Cập nhật app.js
appjs_path = Path("app/static/app.js")
appjs_text = appjs_path.read_text(encoding="utf-8")

# Thêm 'phase3' vào views router
views_target = 'const views = ["gateway", "dashboard", "inspect", "inspections", "severity", "analytics", "settings"];'
views_replacement = 'const views = ["gateway", "dashboard", "inspect", "phase3", "inspections", "severity", "analytics", "settings"];'
if '"phase3"' not in appjs_text:
    appjs_text = appjs_text.replace(views_target, views_replacement)

# Thêm gọi autoClassifyComponent vào setFile
setfile_target = '  $("preview").src = URL.createObjectURL(f);\n  $("preview").hidden = false;'
setfile_replacement = '''  $("preview").src = URL.createObjectURL(f);
  $("preview").hidden = false;
  autoClassifyComponent(f);'''

if 'autoClassifyComponent(f);' not in appjs_text:
    appjs_text = appjs_text.replace(setfile_target, setfile_replacement)

# Thêm hàm autoClassifyComponent
ai_func = '''
async function autoClassifyComponent(file) {
  try {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/phase3/classify-component", { method: "POST", body: fd });
    if (!res.ok) return;
    const data = await res.json();
    if (data.component_name) {
      const sel = $("component");
      if (sel) {
        for (let opt of sel.options) {
          const t = opt.text.toLowerCase();
          if (
            (data.component_type === "column" && t.includes("cột")) ||
            (data.component_type === "beam" && t.includes("dầm")) ||
            (data.component_type === "beam_column_joint" && t.includes("dầm")) ||
            (data.component_type === "wall" && t.includes("tường")) ||
            (data.component_type === "slab" && t.includes("sàn")) ||
            (data.component_type === "stair" && t.includes("thang"))
          ) {
            sel.value = opt.value;
            break;
          }
        }
      }
      const tag = document.getElementById("ai-component-tag");
      if (tag) {
        tag.style.display = "block";
        tag.innerHTML = `🤖 <b>AI Tự động nhận diện cấu kiện:</b> ${data.component_name} (${(data.confidence * 100).toFixed(0)}% tin cậy) · Hệ số rủi ro: <b>${data.risk_multiplier}x</b><br><small style="color:#475569">${data.evidence || ""}</small>`;
      }
      toast(`🤖 AI đã nhận diện: ${data.component_name} (${data.risk_multiplier}x)`);
    }
  } catch (err) {
    console.warn("AI classify failed", err);
  }
}
'''

if 'function autoClassifyComponent' not in appjs_text:
    appjs_text += '\n' + ai_func

appjs_path.write_text(appjs_text, encoding="utf-8")
print("app.js updated!")
