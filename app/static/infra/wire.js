/* ============================================================
   INFRA-GUARD wire.js — Nối dữ liệu thật (API) vào template gốc
   KHÔNG sửa markup của template; chỉ bổ sung script này cuối trang.
   ============================================================ */
"use strict";

const IG = { inspections: [], dashboard: null };

document.addEventListener("DOMContentLoaded", () => {
  // Nút trên gateway → console
  document.querySelectorAll("button, a").forEach((el) => {
    const t = (el.textContent || "").toUpperCase();
    if (t.includes("INITIALIZE JURISDICTION ONBOARDING") || t.includes("AUTHENTICATE INSPECTION KEY") || t.includes("SIGN IN TO TERMINAL")) {
      el.addEventListener("click", (e) => { e.preventDefault(); sessionStorage.setItem("ig-entered", "1"); location.href = "/console"; });
    }
  });
  if (document.getElementById("inspection-workspace")) wireWorkspace();
});

function escA(s) {
  return String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

/* ================= WORKSPACE: quy trình phân tích (inject) ================= */
let wireLoaded = false;
function wireWorkspace() { /* được gọi khi workspace được inject */ }
