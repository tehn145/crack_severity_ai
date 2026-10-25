/* ============================================================
 * Crack Severity AI v3 — SPA
 * Views: Dashboard / Wizard kiểm tra / Hồ sơ / Phân tích / Thiết lập
 * Luồng: Draft → Submitted → Approved (phân vai demo: engineer/manager)
 * ============================================================ */
"use strict";

const $ = (id) => document.getElementById(id);
const SEV_COLOR = { L0: "#7f8c8d", L1: "#16a34a", L2: "#d97706", L3: "#dc2626" };
const SEV_FALLBACK = { color: "#b3bcc5" };

const state = {
  file: null, result: null, activeDet: -1,
  showMask: true, showBox: true, step: 1,
  meta: null, charts: {},
};

/* ================= ROUTER ================= */
function go(route) {
  location.hash = route;
}
function onRoute() {
  const name = (location.hash || "#/dashboard").replace("#/", "");
  const views = ["dashboard", "inspect", "inspections", "analytics", "settings"];
  const v = views.includes(name) ? name : "dashboard";
  views.forEach((x) => ($("view-" + x).hidden = x !== v));
  document.querySelectorAll(".sidebar nav a").forEach((a) =>
    a.classList.toggle("active", a.getAttribute("href") === "#/" + v));
  if (v === "dashboard") loadDashboard();
  if (v === "inspections") loadInspections();
  if (v === "analytics") loadAnalytics();
  if (v === "settings") loadSettings();
}
window.addEventListener("hashchange", onRoute);

/* ================= INIT ================= */
async function init() {
  try {
    const meta = await (await fetch("/api/meta")).json();
    state.meta = meta;
    $("component").innerHTML = meta.components
      .map((c) => `<option>${c[0].toUpperCase() + c.slice(1)}</option>`).join("");
    $("f-component").innerHTML =
      `<option value="">— Tất cả cấu kiện —</option>` +
      meta.components.map((c) => `<option>${c[0].toUpperCase() + c.slice(1)}</option>`).join("");
    $("app-version").textContent = "Phiên bản " + meta.version;
    renderLegend(meta.severity_scale);
  } catch { /* giữ default */ }
  health(); setInterval(health, 30000);
  $("conf").addEventListener("input", (e) => ($("confVal").textContent = e.target.value));
  setupDropzone(); setupPaste();
  $("file").addEventListener("change", (e) => setFile(e.target.files[0]));
  $("btn-demo").addEventListener("click", useDemoImage);
  $("btn-run").addEventListener("click", runPredict);
  $("btn-save").addEventListener("click", saveInspection);
  $("btn-refresh").addEventListener("click", loadInspections);
  $("f-search").addEventListener("input", loadInspections);
  $("f-status").addEventListener("change", loadInspections);
  $("f-component").addEventListener("change", loadInspections);
  setupWizard(); setupToggles(); setupProjectPicker();
  onRoute();
}

async function health() {
  try {
    const h = await (await fetch("/api/health")).json();
    $("health-dot").className = "dot " + (h.model_loaded ? "ok" : "bad");
    $("health-status").textContent = h.model_loaded ? "Sẵn sàng · " + h.version : "Chưa load weight";
  } catch { $("health-status").textContent = "Mất kết nối API"; }
}

/* ================= DASHBOARD ================= */
async function loadDashboard() {
  let d;
  try { d = await (await fetch("/api/dashboard")).json(); }
  catch { return; }
  const k = d.kpi;
  const kpi = (label, val, cls = "") =>
    `<div class="kpi ${cls}"><div class="k-label">${label}</div><div class="k-value">${val}</div></div>`;
  $("kpi-row").innerHTML =
    kpi("Dự án / tòa nhà", k.projects) +
    kpi("Hồ sơ kiểm định", k.inspections) +
    kpi("Vết nứt ghi nhận", k.cracks, "k-red") +
    kpi("Chờ phê duyệt", k.pending, "k-amber") +
    kpi("Conf trung bình", k.avg_conf ?? "—", "k-green");
  $("recent-table").querySelector("tbody").innerHTML = d.recent
    .map((x) => `<tr>
      <td><b>CSA-${String(x.id).padStart(5, "0")}</b></td>
      <td>${x.created_at.replace("T", " ")}</td><td>${esc(x.building)}</td>
      <td>${esc(x.floor)}</td><td>${esc(x.component)}</td><td><b>${x.n_cracks}</b></td>
      <td>${statusBadge(x.status)}</td></tr>`).join("");
  drawCharts(d);
}

function drawCharts(d) {
  const opts = { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom", labels: { boxWidth: 11, font: { size: 10.5 } } } } };
  if (window.__noCharts || typeof Chart === "undefined") {
    document.querySelectorAll(".chart-box").forEach((b) =>
      (b.innerHTML = '<div class="no-charts">Biểu đồ cần kết nối CDN (Chart.js).<br>Số liệu: ' +
        JSON.stringify(d.by_severity) + "</div>"));
    return;
  }
  const sev = d.by_severity || {};
  mkChart("ch-sev", "doughnut", {
    labels: Object.keys(sev).map((s) => s + " — " + ({ L0: "Hairline", L1: "Minor", L2: "Moderate", L3: "Severe" }[s] || "")),
    datasets: [{ data: Object.values(sev), backgroundColor: Object.keys(sev).map((s) => SEV_COLOR[s] || "#999") }],
  }, { ...opts, cutout: "58%" });
  const comp = d.by_component || {};
  mkChart("ch-comp", "bar", {
    labels: Object.keys(comp), datasets: [{ data: Object.values(comp), backgroundColor: "#2e86c1", borderRadius: 6 }],
  }, { ...opts, plugins: { legend: { display: false } } });
  mkChart("ch-trend", "line", {
    labels: d.trend.labels, datasets: [{ data: d.trend.values, borderColor: "#14508c", backgroundColor: "rgba(46,134,193,.15)", fill: true, tension: .35, pointRadius: 3 }],
  }, { ...opts, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } });
}
function mkChart(id, type, data, opts) {
  if (state.charts[id]) state.charts[id].destroy();
  const el = $(id); if (!el) return;
  state.charts[id] = new Chart(el, { type, data, options: opts });
}

/* ================= WIZARD ================= */
function setupWizard() {
  $("w1-next").addEventListener("click", () => gotoStep(2));
  $("w2-next").addEventListener("click", () => gotoStep(3));
  $("w3-next").addEventListener("click", () => { renderReview(); gotoStep(4); });
  document.querySelectorAll("[data-goto]").forEach((b) =>
    b.addEventListener("click", () => gotoStep(+b.dataset.goto)));
}
function gotoStep(n) {
  state.step = n;
  for (let i = 1; i <= 4; i++) {
    $("wpane-" + i).hidden = i !== n;
    const el = document.querySelector(`.wstep[data-step="${i}"]`);
    el.classList.toggle("active", i === n);
    el.classList.toggle("done", i < n);
    if (i < n) el.querySelector(".wnum").textContent = "✓";
    else el.querySelector(".wnum").textContent = i;
  }
  if (n === 3 && state.file && !state.result) runPredict();
}

async function setupProjectPicker() {
  await reloadProjects();
  $("btn-new-project").addEventListener("click", async () => {
    const name = prompt("Tên dự án / tòa nhà mới:");
    if (!name?.trim()) return;
    const address = prompt("Địa chỉ (tuỳ chọn):") || "";
    try {
      const body = new FormData();
      body.append("name", name.trim()); body.append("address", address);
      const r = await fetch("/api/projects", { method: "POST", body });
      if (!r.ok) throw new Error((await r.json()).detail);
      toast(`Đã tạo dự án "${name.trim()}"`, "ok");
      await reloadProjects(name.trim());
    } catch (e) { toast("Lỗi tạo dự án: " + e.message, "err"); }
  });
}
async function reloadProjects(selectName) {
  try {
    const list = await (await fetch("/api/projects")).json();
    $("project").innerHTML = list
      .map((p) => `<option value="${p.id}">${esc(p.name)}${p.address ? " — " + esc(p.address) : ""}</option>`)
      .join("");
    if (selectName) {
      const opt = [...$("project").options].find((o) => o.text.includes(selectName));
      if (opt) $("project").value = opt.value;
    }
  } catch { /* bỏ qua */ }
}

/* ================= ẢNH ĐẦU VÀO ================= */
function setFile(f) {
  if (!f || !f.type.startsWith("image/")) return toast("Tệp không phải ảnh", "err");
  state.file = f;
  $("preview").src = URL.createObjectURL(f);
  $("preview").hidden = false;
  $("status").textContent = "";
}
function setupDropzone() {
  const dz = $("dropzone");
  ["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("drag"); }));
  ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("drag"); }));
  dz.addEventListener("drop", (e) => setFile(e.dataTransfer.files[0]));
}
function setupPaste() {
  document.addEventListener("paste", (e) => {
    const item = [...(e.clipboardData?.items || [])].find((i) => i.type.startsWith("image/"));
    if (item) {
      const f = item.getAsFile();
      setFile(new File([f], "clipboard.png", { type: f.type }));
      toast("Đã dán ảnh từ clipboard ✨");
    }
  });
}
async function useDemoImage() {
  try {
    const r = await fetch("/api/demo-image");
    if (!r.ok) throw new Error();
    setFile(new File([await r.blob()], "mau.jpg", { type: "image/jpeg" }));
    toast("Đã nạp ảnh mẫu từ tập test");
  } catch { toast("Không lấy được ảnh mẫu", "err"); }
}

/* ================= PREDICT ================= */
async function runPredict() {
  if (!state.file) return toast("Chưa có ảnh", "err");
  const st = $("status");
  st.className = "status";
  $("btn-run").disabled = true;
  $("btn-run").textContent = "⏳ Đang phân tích...";
  try {
    const fd = new FormData();
    fd.append("file", state.file);
    fd.append("conf", $("conf").value);
    fd.append("imgsz", $("imgsz").value);
    fd.append("gsd_mm_per_px", $("gsd").value || "0");
    const r = await fetch("/api/predict", { method: "POST", body: fd });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
    state.result = await r.json();
    state.activeDet = -1;
    renderResult(state.result);
    st.textContent = `Hoàn tất trong ${state.result.elapsed_ms} ms.`;
    st.className = "status ok";
    $("w3-next").disabled = false;
  } catch (e) {
    st.textContent = "Lỗi: " + e.message;
    st.className = "status err";
    toast("Phân tích thất bại: " + e.message, "err");
  } finally {
    $("btn-run").disabled = false;
    $("btn-run").textContent = "🔍 Chạy phân tích";
  }
}

function renderResult(res) {
  $("result-empty").hidden = true;
  $("result").hidden = false;
  const n = res.n_cracks, sev = res.severity_summary || {}, gsd = res.gsd_mm_per_px;
  let chips = `<span class="chip ${n === 0 ? "green" : "red"}">${n} vết nứt</span>
    <span class="chip">Ảnh ${res.image_wh[0]}×${res.image_wh[1]}</span>
    <span class="chip">${res.elapsed_ms} ms</span>`;
  if (gsd) {
    chips += `<span class="chip">GSD ${gsd} mm/px</span>`;
    for (const [lv, cnt] of Object.entries(sev)) chips += `<span class="chip amber">L${lv.slice(1)}: ${cnt}</span>`;
  } else if (n) chips += `<span class="chip">chưa định lượng (thiếu GSD)</span>`;
  $("summary").innerHTML = chips;

  $("annotated").onload = () => drawOverlay();
  $("annotated").src = "data:image/jpeg;base64," + res.annotated_jpg_b64;

  $("det-table").querySelector("tbody").innerHTML = res.detections
    .map((d, i) => {
      const s = d.severity;
      const sevHtml = s
        ? `<span class="sev" style="background:${s.color}">L${s.level} ${s.name} · ${s.width_mm}mm</span>`
        : `<span class="sev none">chưa định lượng</span>`;
      return `<tr data-i="${i}"><td><b>${i + 1}</b></td><td class="mono">${d.conf.toFixed(2)}</td>
        <td class="mono">${d.length_px ?? "-"}</td><td class="mono">${d.width_mean_px ?? "-"}</td>
        <td class="mono">${d.width_px ?? "-"}</td><td class="mono">${d.area_px ?? "-"}</td>
        <td class="mono">${d.angle_deg ?? "-"}</td><td>${sevHtml}</td></tr>`;
    }).join("");
  $("det-table").querySelectorAll("tr[data-i]").forEach((tr) =>
    tr.addEventListener("click", () => selectDet(+tr.dataset.i)));
}

/* ================= OVERLAY ================= */
function drawOverlay() {
  const img = $("annotated"), c = $("overlay");
  if (!img.naturalWidth) return;
  c.width = img.naturalWidth; c.height = img.naturalHeight;
  const ctx = c.getContext("2d");
  ctx.clearRect(0, 0, c.width, c.height);
  (state.result?.detections || []).forEach((d, i) => {
    const color = d.severity?.color || SEV_FALLBACK.color;
    const act = i === state.activeDet;
    const [x1, y1, x2, y2] = d.bbox;
    if (state.showMask && d.mask_points) {
      ctx.beginPath();
      d.mask_points.forEach(([px, py], j) => (j ? ctx.lineTo(px, py) : ctx.moveTo(px, py)));
      ctx.closePath();
      ctx.fillStyle = hexA(color, act ? 0.55 : 0.28);
      ctx.fill();
      ctx.strokeStyle = hexA(color, 0.95);
      ctx.lineWidth = act ? 5 : 2.5;
      ctx.stroke();
    }
    if (state.showBox) {
      ctx.strokeStyle = hexA(color, act ? 1 : 0.75);
      ctx.lineWidth = act ? 5 : 2;
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
      const label = `#${i + 1} ${d.conf.toFixed(2)}`;
      ctx.font = "bold 26px Inter, Arial";
      const tw = ctx.measureText(label).width;
      ctx.fillStyle = hexA(color, 0.92);
      ctx.fillRect(x1, Math.max(0, y1 - 34), tw + 16, 32);
      ctx.fillStyle = "#fff";
      ctx.fillText(label, x1 + 8, Math.max(24, y1 - 10));
    }
  });
}
function hexA(hex, a) {
  const v = hex.replace("#", "");
  return `rgba(${parseInt(v.slice(0, 2), 16)},${parseInt(v.slice(2, 4), 16)},${parseInt(v.slice(4, 6), 16)},${a})`;
}
function selectDet(i) {
  state.activeDet = state.activeDet === i ? -1 : i;
  drawOverlay();
  document.querySelectorAll("#det-table tr[data-i]").forEach((tr) =>
    tr.classList.toggle("active", +tr.dataset.i === state.activeDet));
}
function setupToggles() {
  $("tg-mask").addEventListener("click", (e) => {
    state.showMask = !state.showMask;
    e.target.textContent = "Mask: " + (state.showMask ? "BẬT" : "TẮT");
    e.target.classList.toggle("off", !state.showMask); drawOverlay();
  });
  $("tg-box").addEventListener("click", (e) => {
    state.showBox = !state.showBox;
    e.target.textContent = "Khung: " + (state.showBox ? "BẬT" : "TẮT");
    e.target.classList.toggle("off", !state.showBox); drawOverlay();
  });
  $("btn-dl").addEventListener("click", () => {
    const c = $("overlay");
    const out = document.createElement("canvas");
    out.width = c.width; out.height = c.height;
    const ctx = out.getContext("2d");
    ctx.drawImage($("annotated"), 0, 0, out.width, out.height);
    ctx.drawImage(c, 0, 0);
    out.toBlob((b) => download(b, "crack_ai_ket_qua.png"), "image/png");
  });
}
function download(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = name; a.click();
}

/* ================= STEP 4: REVIEW + SAVE ================= */
function renderReview() {
  const r = state.result;
  if (!r) return;
  const nSev = {};
  r.detections.forEach((d) => { if (d.severity) nSev[`L${d.severity.level}`] = (nSev[`L${d.severity.level}`] || 0) + 1; });
  $("review-box").innerHTML = `
    <div class="table-wrap"><table>
      <tr><td style="width:170px"><b>Dự án / tòa nhà</b></td><td>${$("project").selectedOptions[0]?.text || "—"}</td></tr>
      <tr><td><b>Tầng / cấu kiện</b></td><td>${esc($("floor").value) || "—"} · ${$("component").value}</td></tr>
      <tr><td><b>Người kiểm tra</b></td><td>${esc($("engineer").value) || "—"}</td></tr>
      <tr><td><b>Ảnh</b></td><td>${esc(state.file?.name || "")} (${Math.round((state.file?.size || 0) / 1024)} KB)</td></tr>
      <tr><td><b>Kết quả AI</b></td><td><b>${r.n_cracks}</b> vết nứt · ${r.elapsed_ms} ms · conf ${$("conf").value} · imgsz ${$("imgsz").value}</td></tr>
      <tr><td><b>Mức độ (đề xuất)</b></td><td>${Object.entries(nSev).map(([k, v]) => `<span class="sev" style="background:${SEV_COLOR[k]}">${k}: ${v}</span>`).join(" ") || (r.n_cracks ? "chưa định lượng" : "—")}</td></tr>
      <tr><td><b>GSD</b></td><td>${r.gsd_mm_per_px ? r.gsd_mm_per_px + " mm/px" : "chưa có"}</td></tr>
    </table></div>`;
}
async function saveInspection() {
  if (!state.file || !state.result) return;
  try {
    const fd = new FormData();
    fd.append("file", state.file);
    fd.append("annotated_jpg_b64", state.result.annotated_jpg_b64);
    fd.append("detections_json", JSON.stringify(state.result.detections.map(({ mask_points, ...rest }) => rest)));
    fd.append("building", $("project").selectedOptions[0]?.text.split(" — ")[0] || "");
    fd.append("floor", $("floor").value);
    fd.append("component", $("component").value);
    fd.append("note", $("note").value);
    fd.append("gsd_mm_per_px", $("gsd").value || "0");
    fd.append("project_id", $("project").value || "0");
    fd.append("engineer", $("engineer").value);
    fd.append("status", $("save-status").value);
    const r = await fetch("/api/inspections", { method: "POST", body: fd });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const out = await r.json();
    toast(`Hồ sơ CSA-${String(out.id).padStart(5, "0")} đã lưu (${out.n_cracks} vết) 🎉`, "ok");
    state.result = null; state.file = null;
    $("preview").hidden = true; $("result").hidden = true; $("result-empty").hidden = false;
    gotoStep(1);
    go("#/inspections");
  } catch (e) { toast("Lỗi lưu hồ sơ: " + e.message, "err"); }
}

/* ================= HỒ SƠ ================= */
async function loadInspections() {
  try {
    const list = await (await fetch("/api/inspections?limit=200")).json();
    $("nav-count").textContent = list.length; $("nav-count").hidden = false;
    const q = $("f-search").value.toLowerCase();
    const fSt = $("f-status").value, fComp = $("f-component").value;
    const rows = list.filter((x) =>
      (!fSt || x.status === fSt) &&
      (!fComp || (x.component || "").toLowerCase() === fComp.toLowerCase()) &&
      (!q || `${x.id} ${x.building} ${x.floor} ${x.engineer}`.toLowerCase().includes(q)));
    $("ins-empty").hidden = rows.length > 0;
    $("ins-table").querySelector("tbody").innerHTML = rows
      .map((x) => `<tr>
        <td><b>CSA-${String(x.id).padStart(5, "0")}</b></td>
        <td><img class="thumb" src="/api/inspections/${x.id}/image_annotated" onerror="this.style.visibility='hidden'"></td>
        <td>${x.created_at.replace("T", " ")}</td><td>${esc(x.building)}</td><td>${esc(x.floor)}</td>
        <td>${esc(x.component)}</td><td>${esc(x.engineer) || "—"}</td><td><b>${x.n_cracks}</b></td>
        <td>${statusBadge(x.status)}</td>
        <td style="white-space:nowrap">
          <button class="btn tiny" onclick="openDetail(${x.id})">Chi tiết</button>
          <a class="btn tiny" href="/api/inspections/${x.id}/report.html" target="_blank">🖨️ Báo cáo</a>
          ${x.status === "submitted" && $("role").value === "manager"
            ? `<button class="btn tiny primary" onclick="approve(${x.id})">✓ Duyệt</button>` : ""}
        </td></tr>`).join("");
  } catch { /* bỏ qua */ }
}

async function openDetail(id) {
  try {
    const x = await (await fetch(`/api/inspections/${id}`)).json();
    $("modal-title").textContent = `Hồ sơ CSA-${String(x.id).padStart(5, "0")} — ${statusBadge(x.status)}`;
    $("modal-body").innerHTML = `
      <img src="/api/inspections/${x.id}/image_annotated" style="width:100%;border-radius:10px" onerror="this.hidden=true">
      <table style="margin-top:12px">
        <tr><td style="width:150px;color:var(--muted)">Dự án/Tòa nhà</td><td>${esc(x.building)}</td></tr>
        <tr><td style="color:var(--muted)">Tầng / Cấu kiện</td><td>${esc(x.floor)} · ${esc(x.component)}</td></tr>
        <tr><td style="color:var(--muted)">Kỹ sư / Thời gian</td><td>${esc(x.engineer) || "—"} · ${x.created_at.replace("T", " ")}</td></tr>
        <tr><td style="color:var(--muted)">GSD</td><td>${x.gsd_mm_per_px ? x.gsd_mm_per_px + " mm/px" : "—"}</td></tr>
        <tr><td style="color:var(--muted)">Ghi chú</td><td>${esc(x.note)}</td></tr>
        ${x.approved_by ? `<tr><td style="color:var(--muted)">Phê duyệt</td><td><b>${esc(x.approved_by)}</b> · ${x.approved_at.replace("T", " ")}</td></tr>` : ""}
      </table>
      <h3 style="font-size:13px;color:var(--brand-2)">Vết nứt (${x.n_cracks})</h3>
      <div class="table-wrap"><table>
        <thead><tr><th>#</th><th>Conf</th><th>Dài px</th><th>Rộng px</th><th>Mức độ</th></tr></thead>
        <tbody>${x.detections.map((d, i) => `<tr><td>${i + 1}</td><td class="mono">${d.conf?.toFixed(2)}</td>
          <td class="mono">${d.length_px ?? "—"}</td><td class="mono">${d.width_px ?? "—"}</td>
          <td>${d.severity ? `<span class="sev" style="background:${SEV_COLOR["L" + d.severity[1]] || "#999"}">${d.severity}</span>` : "—"}</td></tr>`).join("")}</tbody>
      </table></div>
      ${x.status === "submitted" && $("role").value === "manager"
        ? `<button class="btn primary big" style="margin-top:14px" onclick="approve(${x.id})">✓ Phê duyệt hồ sơ</button>` : ""}`;
    $("modal").hidden = false;
  } catch (e) { toast("Lỗi tải chi tiết: " + e.message, "err"); }
}

async function approve(id) {
  const by = prompt("Quản lý phê duyệt — họ tên:") || ($("role").value === "manager" ? "Quản lý" : "");
  if (!by) return;
  try {
    await (await fetch(`/api/inspections/${id}/status`, {
      method: "POST", body: (() => { const b = new FormData(); b.append("status", "approved"); b.append("by", by); return b; })(),
    })).json();
    $("modal").hidden = true;
    toast(`Hồ sơ CSA-${String(id).padStart(5, "0")} ĐÃ DUYỆT ✅`, "ok");
    loadInspections();
  } catch (e) { toast("Lỗi phê duyệt: " + e.message, "err"); }
}

/* ================= ANALYTICS ================= */
async function loadAnalytics() {
  let m;
  try { m = await (await fetch("/api/model-info")).json(); } catch { return; }
  const pair = (o) => `<div class="metric-pair">${Object.entries(o).map(([k, v]) =>
    `<div class="mp"><b>${typeof v === "number" ? v.toFixed(3) : v}</b><span>${k}</span></div>`).join("")}</div>`;
  const bar = (a, b) => {
    const pct = Math.min(100, Math.round((a / b) * 100));
    return `<div style="background:#e8eef5;border-radius:99px;height:9px;margin:5px 0 12px">
      <div style="width:${pct}%;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--brand-2),var(--accent))"></div>
      <span class="hint" style="margin:0">Đạt ${pct}% so với baseline ResUNet của bài báo</span></div>`;
  };
  $("analytics-body").innerHTML = `
    <div class="card"><h2>Benchmark tập test (v1 — imgsz 640)</h2>
      <b style="font-size:12.5px">Box (bounding)</b>${pair(m.test_metrics.box)}
      <b style="font-size:12.5px">Mask (segmentation)</b>${pair(m.test_metrics.mask)}
      <div class="sota-row"><span>Độ chính xác mức ảnh (kỳ vọng 0.95)</span><b>${m.image_level_acc} ✅</b></div>
      <div class="sota-row"><span>False positive trên ảnh âm</span><b>${(m.neg_fp_rate * 100).toFixed(1)}%</b></div>
    </div>
    <div class="card"><h2>So sánh SOTA — ${m.sota_ref.paper}</h2>
      <div class="sota-row"><span><b>DeepCrack</b> — Dice của hệ thống / ResUNet (bài báo)</span><b>${m.sota_ref.deepcrack.ours_dice} / ${m.sota_ref.deepcrack.resunet_dice}</b></div>
      ${bar(m.sota_ref.deepcrack.ours_dice, m.sota_ref.deepcrack.resunet_dice)}
      <div class="sota-row"><span><b>3DCrack</b> — Dice của hệ thống / ResUNet (bài báo)</span><b>${m.sota_ref["3dcrack"].ours_dice} / ${m.sota_ref["3dcrack"].resunet_dice}</b></div>
      ${bar(m.sota_ref["3dcrack"].ours_dice, m.sota_ref["3dcrack"].resunet_dice)}
      <p class="hint" style="margin-top:8px">v2 (imgsz 1280, dữ liệu cải thiện) đang huấn luyện — sẽ cập nhật tại đây.</p>
    </div>
    <div class="card"><h2>Cấu hình model & dữ liệu</h2>
      <div class="sota-row"><span>Model</span><b>${m.model}</b></div>
      <div class="sota-row"><span>Huấn luyện</span><b>${m.trained}</b></div>
      <div class="sota-row"><span>Dữ liệu (train/val/test)</span><b>${m.data.train} / ${m.data.val} / ${m.data.test}</b></div>
      <div class="sota-row"><span>Ảnh âm train (background)</span><b>${m.data.negatives_train}</b></div>
      <div class="sota-row"><span>Nguồn dữ liệu</span><b style="white-space:normal;text-align:right;max-width:60%">${m.data.sources.join(", ")}</b></div>
    </div>
    <div class="card"><h2>Lộ trình cải thiện</h2>
      <div class="sota-row"><span>v1 — baseline imgsz 640</span><b style="color:var(--ok)">Hoàn thành</b></div>
      <div class="sota-row"><span>v2 — imgsz 1280, T4x2, multi-scale, dữ liệu cải thiện (+3.000 ảnh âm, +118 pseudo-GT)</span><b style="color:var(--warn)">Đang train</b></div>
      <div class="sota-row"><span>v3 — pseudo-label mở rộng kho class-only (45k+ ảnh)</span><b style="color:var(--muted)">Kế hoạch</b></div>
      <div class="sota-row"><span>Phase 2 — severity rule-based (đã cắm demo) → học thống kê</span><b style="color:var(--muted)">Chờ chốt thang</b></div>
    </div>`;
}

/* ================= SETTINGS ================= */
async function loadSettings() {
  try {
    const meta = await (await fetch("/api/meta")).json();
    $("scale-detail").innerHTML = (meta.severity_scale?.levels || [])
      .map((lv) => `<div class="sota-row"><span><span class="leg-swatch" style="background:${lv.color}"></span>
        <b>L${lv.level} ${lv.name}</b> — ${lv.vi}</span><b>${lv.range}</b></div>`).join("");
    $("settings-model").innerHTML = `
      <div class="sota-row"><span>Phiên bản hệ thống</span><b>${meta.version}</b></div>
      <div class="sota-row"><span>Ngưỡng conf mặc định</span><b>0.25</b></div>
      <div class="sota-row"><span>imgsz mặc định</span><b>640</b></div>
      <div class="sota-row"><span>Nguồn thang</span><b style="white-space:normal;text-align:right;max-width:55%">${meta.severity_scale?.reference || ""}</b></div>`;
  } catch { /* bỏ qua */ }
}

/* ================= UTIL ================= */
function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}
function statusBadge(s) {
  const map = { draft: ["Bản nháp", "draft"], submitted: ["Chờ duyệt", "submitted"], approved: ["Đã duyệt", "approved"] };
  const [t, c] = map[s] || [s, "draft"];
  return `<span class="badge ${c}">${t}</span>`;
}
function renderLegend(scale) {
  if (!scale?.levels) return;
  $("severity-legend").hidden = false;
  $("legend-items").innerHTML = scale.levels
    .map((lv) => `<span class="leg-item"><span class="leg-swatch" style="background:${lv.color}"></span>L${lv.level} ${lv.name} (${lv.range})</span>`).join("");
}
function toast(msg, kind = "") {
  const t = document.createElement("div");
  t.className = "toast " + kind;
  t.textContent = msg;
  $("toasts").appendChild(t);
  setTimeout(() => { t.style.opacity = "0"; t.style.transition = "opacity .4s"; }, 3400);
  setTimeout(() => t.remove(), 3900);
}
$("role").addEventListener("change", loadInspections);

init();
