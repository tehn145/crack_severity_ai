/* ============================================================
 * Crack Severity AI v4 — SPA (light modern theme)
 * Views: Dashboard / Wizard / Hồ sơ / Phase 2 / Model / Thiết lập
 * Luồng: Draft → Submitted → Approved (vai demo: engineer/manager)
 * Phase 2 tự động: phát hiện nứt → chip mức độ ngay (GSD mặc định 0.2,
 * hiệu chuẩn bằng 📏 Đo GSD hoặc nhập tay → tự tính lại).
 * ============================================================ */
"use strict";

const $ = (id) => document.getElementById(id);
const SEV_COLOR = { L0: "#64748b", L1: "#059669", L2: "#d97706", L3: "#dc2626" };
const SEV_FALLBACK = { color: "#A8ADB1" };
const DEFAULT_GSD = 0.2; // mm/px — ảnh chụp gần; gắn nhãn "giả định" tới khi hiệu chuẩn

const state = {
  file: null, result: null, activeDet: -1,
  showMask: true, showBox: true, step: 1,
  meta: null, charts: {},
  calibrating: false, calPoints: [], throughFlags: [],
  gsdCalibrated: false,
};

/* ================= ROUTER ================= */
function go(route) { location.hash = route; }
function onRoute() {
  const name = (location.hash || "#/dashboard").replace("#/", "");
  const views = ["gateway", "dashboard", "inspect", "inspections", "severity", "analytics", "settings"];
  const v = views.includes(name) ? name : "gateway";
  views.forEach((x) => ($("view-" + x).hidden = x !== v));
  document.querySelectorAll(".sidebar nav a").forEach((a) =>
    a.classList.toggle("active", a.dataset.view === v));
  if (v === "gateway") return;
  if (v === "dashboard") loadDashboard();
  if (v === "inspections") loadInspections();
  if (v === "analytics") loadAnalytics();
  if (v === "severity") loadSeverityView();
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
    renderLegend(meta.severity_scale);
  } catch { /* giữ mặc định */ }
  health(); setInterval(health, 30000);
  $("conf").addEventListener("input", (e) => ($("confVal").textContent = e.target.value));
  $("gsd").addEventListener("input", () => {
    state.gsdCalibrated = Math.abs(parseFloat($("gsd").value) - DEFAULT_GSD) > 1e-9;
  });
  setupDropzone(); setupPaste(); setupCalibration();
  $("file").addEventListener("change", (e) => setFile(e.target.files[0]));
  $("btn-demo").addEventListener("click", useDemoImage);
  $("btn-run").addEventListener("click", runPredict);
  $("btn-save").addEventListener("click", saveInspection);
  $("btn-refresh").addEventListener("click", loadInspections);
  $("f-search").addEventListener("input", loadInspections);
  $("f-status").addEventListener("change", loadInspections);
  $("f-component").addEventListener("change", loadInspections);
  setupWizard(); setupToggles(); setupProjectPicker(); setupSeverityCalc();
  onRoute();
}

async function health() {
  try {
    const h = await (await fetch("/api/health")).json();
    $("health-dot").className = "dot " + (h.model_loaded ? "ok" : "bad");
    $("health-status").textContent = h.model_loaded ? "Model sẵn sàng" : "Chưa load weight";
  } catch { $("health-status").textContent = "Mất kết nối API"; }
}

/* ================= DASHBOARD ================= */
async function loadDashboard() {
  const h = new Date().getHours();
  $("greet").textContent =
    h < 11 ? "Tổng quan buổi sáng" : h < 14 ? "Tổng quan buổi trưa" : h < 18 ? "Tổng quan buổi chiều" : "Tổng quan buổi tối";

  let d;
  try { d = await (await fetch("/api/dashboard")).json(); } catch { return; }
  const k = d.kpi;

  const latest = d.recent?.[0];
  if (latest) {
    $("hero-img").src = `/api/inspections/${latest.id}/image_annotated`;
    $("hero-tag").textContent =
      `CSA-${String(latest.id).padStart(5, "0")}, ${latest.created_at.replace("T", " ")}, ${latest.n_cracks} vết nứt`;
  } else {
    $("hero-tag").textContent = "CHƯA CÓ HỒ SƠ — ẢNH MẪU TỪ TẬP TEST";
  }

  const metric = (label, num, sub, stripe) =>
    `<div class="metric stripe-${stripe}"><div class="m-label">${label}</div><div class="m-value">${num}</div><div class="m-sub">${sub}</div></div>`;
  $("kpi-row").innerHTML =
    metric("PROJECTS", k.projects, "dự án / tòa nhà", "info") +
    metric("INSPECTIONS", k.inspections, "hồ sơ kiểm định", "info") +
    metric("CRACKS", k.cracks, "vết nứt ghi nhận", "crit") +
    metric("PENDING", k.pending, "chờ phê duyệt", "warn") +
    metric("AVG CONF", k.avg_conf ?? "—", "độ tin cậy trung bình", "ok");

  $("recent-table").querySelector("tbody").innerHTML = d.recent.length
    ? d.recent.map((x) => `<tr>
        <td><b class="mono">CSA-${String(x.id).padStart(5, "0")}</b></td>
        <td><img class="thumb" src="/api/inspections/${x.id}/image_annotated" onerror="this.style.visibility='hidden'"></td>
        <td class="mono">${x.created_at.replace("T", " ")}</td><td>${esc(x.building)}</td>
        <td>${esc(x.floor)}</td><td>${esc(x.component)}</td><td class="mono">${x.n_cracks}</td>
        <td>${statusBadge(x.status)}</td></tr>`).join("")
    : `<tr><td colspan="8" class="empty-state">Chưa có hồ sơ — lập phiếu kiểm tra đầu tiên.</td></tr>`;
  drawCharts(d);
}

function drawCharts(d) {
  const base = { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 10.5 }, usePointStyle: true } } } };
  if (window.__noCharts || typeof Chart === "undefined") {
    document.querySelectorAll(".chart-box").forEach((b) =>
      (b.innerHTML = `<div class="no-charts">Biểu đồ cần CDN Chart.js (lần đầu chạy online).<br>Số liệu: ${esc(JSON.stringify(d.by_severity))}</div>`));
    return;
  }
  const sev = d.by_severity || {};
  mkChart("ch-sev", "doughnut", {
    labels: Object.keys(sev).map((s) => `${s} — ${({ L0: "Hairline", L1: "Minor", L2: "Moderate", L3: "Severe" })[s] || ""}`),
    datasets: [{ data: Object.values(sev), backgroundColor: Object.keys(sev).map((s) => SEV_COLOR[s] || "#94a3b8"), borderWidth: 2, borderColor: "#fff" }],
  }, { ...base, cutout: "60%" });
  const comp = d.by_component || {};
  mkChart("ch-comp", "bar", {
    labels: Object.keys(comp), datasets: [{ data: Object.values(comp), backgroundColor: "#2563eb", borderRadius: 7, maxBarThickness: 42 }],
  }, { ...base, plugins: { legend: { display: false } } });
  mkChart("ch-trend", "line", {
    labels: d.trend.labels,
    datasets: [{ data: d.trend.values, borderColor: "#2563eb", backgroundColor: "rgba(37,99,235,.12)", fill: true, tension: .38, pointRadius: 3, pointBackgroundColor: "#fff", pointBorderColor: "#2563eb" }],
  }, { ...base, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } });
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
    el.querySelector(".wnum").textContent = i < n ? "✓" : i;
  }
  if (n === 3 && state.file && !state.result) runPredict();
  window.scrollTo({ top: 0, behavior: "smooth" });
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

/* ================= PREDICT (Phase 1 + Phase 2 tự động) ================= */
async function runPredict() {
  if (!state.file) return toast("Chưa có ảnh — hãy tải ảnh ở bước 2", "err");
  const st = $("status");
  st.className = "status";
  $("btn-run").disabled = true;
  $("btn-run").innerHTML = `<span class="spin"></span> Đang phân tích...`;
  try {
    const fd = new FormData();
    fd.append("file", state.file);
    fd.append("conf", $("conf").value);
    fd.append("imgsz", $("imgsz").value);
    // GSD mặc định 0.2 nếu chưa hiệu chuẩn → severity tính TỰ ĐỘNG ngay sau phân tích
    fd.append("gsd_mm_per_px", $("gsd").value || String(DEFAULT_GSD));
    const r = await fetch("/api/predict", { method: "POST", body: fd });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
    state.result = await r.json();
    state.activeDet = -1;
    state.throughFlags = new Array(state.result.n_cracks).fill(false);
    renderResult(state.result);
    const hr = $("hud-readout");
    if (hr) {
      hr.hidden = false;
      hr.innerHTML = `<b>${state.result.n_cracks}</b> CRACKS · CONF <b>${$("conf").value}</b> · IMGSZ <b>${$("imgsz").value}</b> · ${state.result.elapsed_ms} MS`;
    }
    st.textContent = `Hoàn tất trong ${state.result.elapsed_ms} ms — mức độ đã phân loại tự động.`;
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
  let chips = `
    <span class="chip ${n === 0 ? "green" : "red"}">${n} vết nứt</span>
    <span class="chip">Ảnh ${res.image_wh[0]}×${res.image_wh[1]}</span>
    <span class="chip">${res.elapsed_ms} ms</span>`;
  if (gsd) {
    chips += `<span class="chip ${state.gsdCalibrated ? "green" : "amber"}"
      title="${state.gsdCalibrated ? "GSD đã hiệu chuẩn" : "GSD mặc định — bấm Đo GSD để hiệu chuẩn"}">
      GSD ${gsd} mm/px${state.gsdCalibrated ? " (đã hiệu chuẩn)" : " (giả định — nên hiệu chuẩn)"}</span>`;
    for (const [lv, cnt] of Object.entries(sev)) chips += `<span class="chip amber">L${lv.slice(1)}: ${cnt}</span>`;
  } else if (n) chips += `<span class="chip">chưa định lượng (thiếu GSD)</span>`;
  $("summary").innerHTML = chips;

  $("annotated").onload = () => drawOverlay();
  $("annotated").src = "data:image/jpeg;base64," + res.annotated_jpg_b64;

  $("det-table").querySelector("tbody").innerHTML = res.detections
    .map((d, i) => {
      const s = d.severity;
      const sevHtml = s
        ? `<span class="sev${s.level === 3 ? " stamp" : ""}" style="${s.level === 3 ? `color:${s.color}` : `background:${s.color}`}" title="${esc((s.factors || []).join(", "))}">L${s.level} ${s.name} ${s.width_mm}mm</span>${s.factors?.length ? `<div class="hint" style="margin:2px 0 0">+ ${esc(s.factors.join(", "))}</div>` : ""}`
        : `<span class="sev none">chưa định lượng</span>`;
      return `<tr data-i="${i}"><td><b>${i + 1}</b></td><td class="mono">${d.conf.toFixed(2)}</td>
        <td class="mono">${d.length_px ?? "-"}</td>
        <td class="mono">${d.width_max_px ?? "-"}</td>
        <td class="mono">${d.contrast_ratio != null ? Math.round(d.contrast_ratio * 100) + "%" : "-"}</td>
        <td class="mono">${d.area_px ?? "-"}</td>
        <td class="mono">${d.angle_deg ?? "-"}</td>
        <td><input type="checkbox" class="thru-cb" data-i="${i}" title="Nứt xuyên cấu kiện → L3"
            ${state.throughFlags[i] ? "checked" : ""}></td>
        <td>${sevHtml}</td></tr>`;
    }).join("");
  $("det-table").querySelectorAll("tr[data-i]").forEach((tr) =>
    tr.addEventListener("click", (e) => {
      if (e.target.classList.contains("thru-cb")) return;
      selectDet(+tr.dataset.i);
    }));
  $("det-table").querySelectorAll(".thru-cb").forEach((cb) =>
    cb.addEventListener("change", () => {
      state.throughFlags[+cb.dataset.i] = cb.checked;
      if (parseFloat($("gsd").value) > 0) reclassify();
      else toast("Đã ghi nhận — nhập GSD để có mức độ");
    }));
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

/* ================= HIỆU CHUẨN GSD (đo thước trên ảnh) ================= */
function setupCalibration() {
  $("btn-cal").addEventListener("click", () => {
    state.calibrating = !state.calibrating;
    state.calPoints = [];
    $("btn-cal").textContent = state.calibrating ? "📏 Bấm 2 điểm..." : "📏 Đo GSD";
    $("btn-cal").classList.toggle("off", !state.calibrating);
    if (state.calibrating) toast("Bấm 2 điểm trên ảnh vào vật có chiều dài đã biết (thước, gạch, cửa...)");
    else drawOverlay();
  });
  $("overlay").addEventListener("click", (e) => {
    if (!state.calibrating) return;
    const c = $("overlay");
    const rect = c.getBoundingClientRect();
    const px = (e.clientX - rect.left) * (c.width / rect.width);
    const py = (e.clientY - rect.top) * (c.height / rect.height);
    state.calPoints.push([px, py]);
    if (state.calPoints.length < 2) {
      drawOverlay();
      const ctx = c.getContext("2d");
      ctx.fillStyle = "#facc15";
      ctx.beginPath(); ctx.arc(px, py, 7, 0, 7); ctx.fill();
      return;
    }
    const [[ax, ay], [bx, by]] = state.calPoints;
    const distPx = Math.hypot(bx - ax, by - ay);
    const mmStr = prompt(`Đo được ${distPx.toFixed(0)} px.\nNhập chiều dài THẬT của vật (mm):`, "300");
    state.calibrating = false; state.calPoints = [];
    $("btn-cal").textContent = "📏 Đo GSD";
    $("btn-cal").classList.remove("off");
    if (mmStr && parseFloat(mmStr) > 0 && distPx > 0) {
      const gsd = parseFloat(mmStr) / distPx;
      $("gsd").value = gsd.toFixed(4);
      state.gsdCalibrated = true;
      toast(`GSD = ${mmStr} mm ÷ ${distPx.toFixed(0)} px = ${gsd.toFixed(4)} mm/px ✅`, "ok");
      drawOverlay();
      const ctx = c.getContext("2d");
      ctx.strokeStyle = "#facc15"; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by); ctx.stroke();
      if (state.result) reclassify();
    } else drawOverlay();
  });
}

async function reclassify() {
  const gsd = parseFloat($("gsd").value);
  if (!state.result || !gsd || gsd <= 0) return;
  try {
    const fd = new FormData();
    fd.append("detections_json", JSON.stringify(state.result.detections));
    fd.append("gsd_mm_per_px", gsd);
    fd.append("through_flags", JSON.stringify(state.throughFlags));
    const r = await fetch("/api/severity", { method: "POST", body: fd });
    if (!r.ok) throw new Error((await r.json()).detail || "HTTP " + r.status);
    const out = await r.json();
    state.result.detections = out.detections;
    state.result.gsd_mm_per_px = out.gsd_mm_per_px;
    state.result.severity_summary = out.severity_summary;
    renderResult(state.result);
    toast("Đã phân loại lại theo GSD mới", "ok");
  } catch (e) { toast("Lỗi phân loại: " + e.message, "err"); }
}

/* ================= BƯỚC 4: REVIEW + SAVE ================= */
function renderReview() {
  const r = state.result;
  if (!r) return;
  const nSev = {};
  r.detections.forEach((d) => { if (d.severity) nSev[`L${d.severity.level}`] = (nSev[`L${d.severity.level}`] || 0) + 1; });
  $("review-box").innerHTML = `
    <div class="table-wrap"><table>
      <tr><td style="width:180px"><b>Dự án / tòa nhà</b></td><td>${$("project").selectedOptions[0]?.text || "—"}</td></tr>
      <tr><td><b>Tầng / cấu kiện</b></td><td>${esc($("floor").value) || "—"} · ${$("component").value}</td></tr>
      <tr><td><b>Người kiểm tra</b></td><td>${esc($("engineer").value) || "—"}</td></tr>
      <tr><td><b>Ảnh</b></td><td>${esc(state.file?.name || "")} (${Math.round((state.file?.size || 0) / 1024)} KB)</td></tr>
      <tr><td><b>Kết quả AI</b></td><td><b>${r.n_cracks}</b> vết nứt · ${r.elapsed_ms} ms · conf ${$("conf").value} · imgsz ${$("imgsz").value}</td></tr>
      <tr><td><b>Mức độ (đề xuất)</b></td><td>${Object.entries(nSev).map(([k, v]) => `<span class="sev" style="background:${SEV_COLOR[k]}">${k}: ${v}</span>`).join(" ") || (r.n_cracks ? "chưa định lượng" : "—")}</td></tr>
      <tr><td><b>GSD</b></td><td>${r.gsd_mm_per_px ? r.gsd_mm_per_px + " mm/px" + (state.gsdCalibrated ? "" : " <i>(giả định — nên hiệu chuẩn)</i>") : "chưa có"}</td></tr>
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
    fd.append("gsd_mm_per_px", $("gsd").value || String(DEFAULT_GSD));
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
    $("modal-title").innerHTML = `Hồ sơ CSA-${String(x.id).padStart(5, "0")} — ${statusBadge(x.status)}`;
    $("modal-body").innerHTML = `
      <img src="/api/inspections/${x.id}/image_annotated" style="width:100%;border-radius:12px" onerror="this.hidden=true">
      <table style="margin-top:12px">
        <tr><td style="width:160px;color:var(--muted)">Dự án/Tòa nhà</td><td>${esc(x.building)}</td></tr>
        <tr><td style="color:var(--muted)">Tầng / Cấu kiện</td><td>${esc(x.floor)} · ${esc(x.component)}</td></tr>
        <tr><td style="color:var(--muted)">Kỹ sư / Thời gian</td><td>${esc(x.engineer) || "—"} · ${x.created_at.replace("T", " ")}</td></tr>
        <tr><td style="color:var(--muted)">GSD</td><td>${x.gsd_mm_per_px ? x.gsd_mm_per_px + " mm/px" : "—"}</td></tr>
        <tr><td style="color:var(--muted)">Ghi chú</td><td>${esc(x.note)}</td></tr>
        ${x.approved_by ? `<tr><td style="color:var(--muted)">Phê duyệt</td><td><b>${esc(x.approved_by)}</b> · ${x.approved_at.replace("T", " ")}</td></tr>` : ""}
      </table>
      <div style="background:#f8fafc;border:1px solid var(--line);border-radius:12px;padding:13px 15px;margin-top:12px">
        <b style="font-size:12.5px">⚙️ Tính lại mức độ (Phase 2)</b>
        <div style="display:flex;gap:10px;align-items:center;margin-top:9px;flex-wrap:wrap">
          <input id="modal-gsd" type="number" step="0.001" min="0" placeholder="GSD mm/px"
            value="${x.gsd_mm_per_px || ""}" style="width:150px;margin:0">
          <button class="btn tiny primary" onclick="recalcSeverity(${x.id})">Tính lại từ px đã lưu</button>
          <span class="hint" style="margin:0">Áp thang ACI/TCVN lên đặc trưng px đã lưu — không cần chạy model.</span>
        </div>
      </div>
      <h3 style="font-size:13px;color:var(--ink);margin:14px 0 8px">Vết nứt (${x.n_cracks})</h3>
      <div class="table-wrap"><table>
        <thead><tr><th>#</th><th>Conf</th><th>Dài px</th><th>Rộng px</th><th>Mức độ</th></tr></thead>
        <tbody>${x.detections.map((d, i) => `<tr><td>${i + 1}</td><td class="mono">${d.conf?.toFixed(2)}</td>
          <td class="mono">${d.length_px ?? "—"}</td><td class="mono">${d.width_px ?? "—"}</td>
          <td>${d.severity ? `<span class="sev" style="background:${SEV_COLOR["L" + d.severity[1]] || "#94a3b8"}">${d.severity}</span>` : "—"}</td></tr>`).join("")}</tbody>
      </table></div>
      ${x.status === "submitted" && $("role").value === "manager"
        ? `<button class="btn primary big" style="margin-top:14px" onclick="approve(${x.id})">✓ Phê duyệt hồ sơ</button>` : ""}`;
    $("modal").hidden = false;
  } catch (e) { toast("Lỗi tải chi tiết: " + e.message, "err"); }
}

async function recalcSeverity(id) {
  const gsd = parseFloat($("modal-gsd").value);
  if (!gsd || gsd <= 0) return toast("Nhập GSD > 0", "err");
  try {
    const fd = new FormData();
    fd.append("gsd_mm_per_px", gsd);
    fd.append("through_flags", "[]");
    await (await fetch(`/api/inspections/${id}/severity`, { method: "POST", body: fd })).json();
    toast(`Hồ sơ CSA-${String(id).padStart(5, "0")} đã cập nhật mức độ theo GSD ${gsd} ✅`, "ok");
    openDetail(id);
  } catch (e) { toast("Lỗi tính lại: " + e.message, "err"); }
}

async function approve(id) {
  const by = prompt("Quản lý phê duyệt — họ tên:") || ($("role").value === "manager" ? "Quản lý" : "");
  if (!by) return;
  try {
    const b = new FormData();
    b.append("status", "approved"); b.append("by", by);
    await (await fetch(`/api/inspections/${id}/status`, { method: "POST", body: b })).json();
    $("modal").hidden = true;
    toast(`Hồ sơ CSA-${String(id).padStart(5, "0")} ĐÃ DUYỆT ✅`, "ok");
    loadInspections();
  } catch (e) { toast("Lỗi phê duyệt: " + e.message, "err"); }
}

/* ================= PHASE 2 VIEW ================= */
function loadSeverityView() {
  const scale = state.meta?.severity_scale;
  if (scale?.levels) {
    $("sev-scale").innerHTML = scale.levels
      .map((lv) => `<div class="sota-row">
        <span><span class="leg-swatch" style="background:${lv.color}"></span>
          <b>L${lv.level} ${lv.name}</b> — ${lv.vi}</span>
        <b>${lv.range}</b></div>`)
      .join("");
  }
  $("sev-validation").innerHTML = `
    <div class="sota-row"><span>Bề rộng lớn nhất (width_max)</span><b style="color:var(--ok)">lệch ≤ 1px ✅</b></div>
    <div class="sota-row"><span>Chiều dài</span><b style="color:var(--ok)">lệch 0px ✅</b></div>
    <div class="sota-row"><span>Góc trục chính</span><b style="color:var(--ok)">lệch 0° ✅</b></div>
    <div class="sota-row"><span>Rẽ nhánh (branching)</span><b style="color:var(--ok)">phát hiện đúng ✅</b></div>
    <p class="hint" style="margin-top:6px">Kiểm chứng trên mask chuẩn kích thước đã biết — giới hạn lượng tử hóa pixel ±1px.</p>`;
  if (!$("sc-run").dataset.bound) {
    $("sc-run").dataset.bound = "1";
    $("sc-run").addEventListener("click", runSeverityCalc);
  }
}

async function runSeverityCalc() {
  const gsd = parseFloat($("sc-gsd").value);
  const wmax = parseFloat($("sc-wmax").value);
  const wmean = parseFloat($("sc-wmean").value);
  const len = parseFloat($("sc-len").value);
  const contrast = (parseFloat($("sc-contrast").value) || 0) / 100;
  const through = $("sc-through").checked;
  const box = $("sc-result");
  if (!gsd || gsd <= 0 || isNaN(wmax)) {
    box.innerHTML = `<span class="status err">Nhập GSD và bề rộng hợp lệ.</span>`;
    return;
  }
  try {
    const fd = new FormData();
    fd.append("detections_json", JSON.stringify([{
      width_mean_px: wmean || wmax, width_max_px: wmax, length_px: len || null,
      branching: $("sc-branch").checked, multi_plane: $("sc-multi").checked,
      contrast_ratio: contrast,
    }]));
    fd.append("gsd_mm_per_px", gsd);
    fd.append("through_flags", JSON.stringify([through]));
    const r = await fetch("/api/severity", { method: "POST", body: fd });
    if (!r.ok) throw new Error((await r.json()).detail || "HTTP " + r.status);
    const out = await r.json();
    const s = out.detections[0].severity;
    box.innerHTML = `<div style="text-align:center;padding:8px 0">
      <span class="sev" style="background:${s.color};font-size:15px;padding:9px 22px">L${s.level} ${s.name}</span>
      <div style="margin-top:10px;font-size:13px">${s.vi}</div>
      <div class="hint" style="margin-top:6px">Rộng ${s.width_mm} mm (max) · dài ${s.length_mm ?? "?"} mm · đậm ${s.contrast != null ? Math.round(s.contrast * 100) + "%" : "?"}</div>
      ${s.factors?.length ? `<div class="hint" style="margin-top:4px;color:var(--warn)">⬆ ${esc(s.factors.join(" · "))}</div>` : `<div class="hint" style="margin-top:4px">Không có yếu tố tăng mức</div>`}
    </div>`;
  } catch (e) {
    box.innerHTML = `<span class="status err">Lỗi: ${esc(e.message)}</span>`;
  }
}

/* ================= MODEL / ANALYTICS ================= */
async function loadAnalytics() {
  let m;
  try { m = await (await fetch("/api/model-info")).json(); } catch { return; }
  const pair = (o) => `<div class="metric-pair">${Object.entries(o).map(([k, v]) =>
    `<div class="mp"><b>${typeof v === "number" ? v.toFixed(3) : v}</b><span>${k}</span></div>`).join("")}</div>`;
  const bar = (a, b) => {
    const pct = Math.min(100, Math.round((a / b) * 100));
    return `<div class="progress"><div style="width:${pct}%"></div></div>
      <span class="hint" style="margin:0 0 10px">Đạt ${pct}% so với baseline ResUNet của bài báo</span>`;
  };
  const cmp = m.model_compare || {};
  const cmpRow = (label, key, unit = "") => `<div class="sota-row"><span>${label}</span>
    <b>v1 ${cmp.v1_640[key]}${unit} / v2 ${cmp.v2_1280[key]}${unit}</b></div>`;
  $("analytics-body").innerHTML = `
    <div class="card"><h2>Benchmark tập test — <span class="sub">model active: ${m.active}</span></h2>
      <b style="font-size:12.5px">Box (bounding) — v1</b>${pair(m.test_metrics.box)}
      <b style="font-size:12.5px">Mask (segmentation) — v1</b>${pair(m.test_metrics.mask)}
      <div class="sota-row"><span>Độ chính xác mức ảnh (kỳ vọng 0.95)</span><b style="color:var(--ok)">${m.image_level_acc} ✅</b></div>
      <div class="sota-row"><span>FP trên ảnh âm (A so với B)</span><b>A 2.2% / B 1.5%</b></div>
    </div>
    <div class="card"><h2>So sánh v1 vs v2 <span class="sub">(instance IoU≥0.5 + pixel Dice)</span></h2>
      ${cmpRow("F1 instance", "inst_F1")}
      ${cmpRow("Precision", "inst_P")}
      ${cmpRow("Dice 3DCrack", "dice_3dcrack")}
      ${cmpRow("Dice DeepCrack", "dice_deepcrack")}
      ${cmpRow("FP ảnh âm", "neg_fp")}
      <div class="sota-row"><span>Kết luận</span>
        <b style="color:var(--ok);white-space:normal;text-align:right;max-width:55%">Giữ v1 — checkpoint v2 (epoch ~74) precision sụp ở IoU 0.5; v3 sẽ train lại đúng best.pt từ weight v1</b></div>
    </div>
    <div class="card"><h2>So sánh SOTA — ${m.sota_ref.paper}</h2>
      <div class="sota-row"><span><b>DeepCrack</b> — Dice hệ thống / ResUNet (bài báo)</span><b>${m.sota_ref.deepcrack.ours_dice} / ${m.sota_ref.deepcrack.resunet_dice}</b></div>
      ${bar(m.sota_ref.deepcrack.ours_dice, m.sota_ref.deepcrack.resunet_dice)}
      <div class="sota-row"><span><b>3DCrack</b> — Dice hệ thống / ResUNet (bài báo)</span><b>${m.sota_ref["3dcrack"].ours_dice} / ${m.sota_ref["3dcrack"].resunet_dice}</b></div>
      ${bar(m.sota_ref["3dcrack"].ours_dice, m.sota_ref["3dcrack"].resunet_dice)}
      <p class="hint" style="margin-top:8px">${m.sota_ref.note || ""}</p>
    </div>
    <div class="card"><h2>Phase 2 — Phân loại mức độ</h2>
      <div class="sota-row"><span>Kiểu</span><b style="white-space:normal;text-align:right;max-width:60%">${m.phase2.type}</b></div>
      <div class="sota-row"><span>Thang</span><b>${m.phase2.scale}</b></div>
      <div class="sota-row"><span>Đầu vào</span><b style="white-space:normal;text-align:right;max-width:55%">${m.phase2.inputs.join(" · ")}</b></div>
      <div class="sota-row"><span>Trạng thái</span><b style="color:var(--ok)">Tích hợp & hoạt động</b></div>
    </div>
    <div class="card"><h2>Cấu hình model & dữ liệu</h2>
      <div class="sota-row"><span>Model</span><b>${m.model}</b></div>
      <div class="sota-row"><span>v1</span><b style="white-space:normal;text-align:right;max-width:60%">${m.trained_v1}</b></div>
      <div class="sota-row"><span>v2</span><b style="white-space:normal;text-align:right;max-width:60%">${m.trained_v2}</b></div>
      <div class="sota-row"><span>Dữ liệu (train/val/test)</span><b>${m.data.train} / ${m.data.val} / ${m.data.test}</b></div>
      <div class="sota-row"><span>Ảnh âm train</span><b>${m.data.negatives_train}</b></div>
      <div class="sota-row"><span>Nguồn</span><b style="white-space:normal;text-align:right;max-width:55%">${m.data.sources.join(", ")}</b></div>
    </div>
    <div class="card"><h2>Lộ trình</h2>
      <div class="sota-row"><span>v1 — baseline imgsz 640</span><b style="color:var(--ok)">Hoàn thành · ACTIVE</b></div>
      <div class="sota-row"><span>v2 — imgsz 1280 (đã đánh giá, không tích hợp)</span><b style="color:var(--warn)">Tham chiếu</b></div>
      <div class="sota-row"><span>v3 — train lại imgsz 960 từ weight v1 + pseudo-label</span><b style="color:var(--muted)">Kế hoạch</b></div>
      <div class="sota-row"><span>Phase 2 — rule-based → học thống kê</span><b style="color:var(--ok)">Rule-based đang chạy</b></div>
    </div>`;
}

/* ================= SETTINGS ================= */
async function loadSettings() {
  try {
    const meta = await (await fetch("/api/meta")).json();
    $("scale-detail").innerHTML = (meta.severity_scale?.levels || [])
      .map((lv) => `<div class="sota-row">
        <span><span class="leg-swatch" style="background:${lv.color}"></span>
          <b>L${lv.level} ${lv.name}</b> — ${lv.vi}</span><b>${lv.range}</b></div>`).join("");
    $("settings-model").innerHTML = `
      <div class="sota-row"><span>Phiên bản hệ thống</span><b>${meta.version}</b></div>
      <div class="sota-row"><span>Ngưỡng conf mặc định</span><b>0.25</b></div>
      <div class="sota-row"><span>imgsz mặc định</span><b>640</b></div>
      <div class="sota-row"><span>GSD mặc định</span><b>0.2 mm/px (giả định)</b></div>
      <div class="sota-row"><span>Nguồn thang</span><b style="white-space:normal;text-align:right;max-width:55%">${meta.severity_scale?.reference || ""}</b></div>`;
    $("settings-about").innerHTML = `
      <div class="sota-row"><span>Stack</span><b style="white-space:normal;text-align:right;max-width:60%">FastAPI · Ultralytics YOLOv8s-seg · SQLite · Vanilla JS</b></div>
      <div class="sota-row"><span>Triển khai</span><b style="white-space:normal;text-align:right;max-width:60%">Docker · GitHub Actions CI/CD → Hugging Face Spaces</b></div>
      <div class="sota-row"><span>Kiểm thử</span><b>pytest 22 test · E2E 7 bước</b></div>
      <div class="sota-row"><span>Tài liệu</span><b style="white-space:normal;text-align:right;max-width:60%">docs/ (DEVOPS, standards/severity_definition, experiments/experiment_log, ARCHITECTURE)</b></div>`;
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
