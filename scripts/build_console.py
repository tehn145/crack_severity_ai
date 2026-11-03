#!/usr/bin/env python3
"""
build_console.py — Ghép 3 template Stitch thành 1 console đa-tab, 100% verbatim.

Cả 3 template có shell giống hệt (aside w-72 + header fixed + main pt-16).
Console = shell (lấy từ registry) + 3 tab-pane (main content verbatim của từng
template, kể toàn bộ hình minh họa Google-hosted) + toàn bộ modal/script của
từng template + bộ chuyển tab.

Xuất: app/static/infra/console.html (verbatim ghép, chỉ thêm script chuyển tab)
Chạy: python scripts/build_console.py
"""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path("docs/stitch_civilvision_deepscan_ai")
OUT = Path("app/static/infra/console.html")

TEMPLATES = [
    ("registry", "building_infrastructure_registry/code.html"),
    ("review", "structural_evaluation_pe_sign_off_review/code.html"),
    ("marketplace", "engineering_services_marketplace/code.html"),
]


def extract_body(html: str) -> str:
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    return m.group(1)


def extract_blocks(body: str) -> tuple[str, str, str, str]:
    """Trả về (aside, header, main_inner, rest) — verbatim."""
    # aside đầu tiên (fixed sidebar)
    a0 = body.index('<aside class="fixed left-0 top-0')
    a1 = body.index("</aside>", a0) + len("</aside>")
    aside = body[a0:a1]

    # header fixed
    h0 = body.index('<header class="fixed top-0 left-72')
    h1 = body.index("</header>", h0) + len("</header>")
    header = body[h0:h1]

    # main (một </main> duy nhất trong file)
    m0 = body.index('<main class="w-full pt-16')
    m1 = body.index("</main>", m0) + len("</main>")
    main_full = body[m0:m1]
    main_open = main_full[: main_full.index(">") + 1]
    main_inner = main_full[main_open.__len__(): -len("</main>")]

    # rest = body trừ aside/header/main (modal + script)
    rest = (body[:a0] + body[a1:h0] + body[h0 + len(header):m0] + body[m1:])
    # bỏ wrapper body-tag rỗng nếu có
    return aside, header, main_inner, rest


def main() -> None:
    parts = {}
    for tag, rel in TEMPLATES:
        html = (SRC / rel).read_text(encoding="utf-8", errors="ignore")
        aside, header, main_inner, rest = extract_blocks(extract_body(html))
        parts[tag] = {"aside": aside, "header": header, "main": main_inner, "rest": rest}
        print(f"[{tag}] main={len(main_inner)} rest={len(rest)}")

    registry_html = (SRC / TEMPLATES[0][1]).read_text(encoding="utf-8", errors="ignore")
    head = re.search(r"<head>.*?</head>", registry_html, re.S).group(0)

    # panic-check: trùng id giữa các main?
    ids_per = {}
    for tag in parts:
        ids_per[tag] = re.findall(r'id="([^"]+)"', parts[tag]["main"])
    dup = set(ids_per["registry"]) & set(ids_per["review"]) | \
        set(ids_per["registry"]) & set(ids_per["marketplace"]) | \
        set(ids_per["review"]) & set(ids_per["marketplace"])
    if dup:
        print("⚠️ ID trùng giữa các tab (cần scope):", sorted(dup))

    panes = "\n".join(
        f'<div class="tabpane" data-pane="{tag}" {"hidden" if i else ""}>{parts[tag]["main"]}</div>'
        for i, (tag, _) in enumerate(TEMPLATES)
    )
    rests = "\n".join(
        f'<div data-rest="{tag}" style="display:contents">{parts[tag]["rest"]}</div>'
        for tag, _ in TEMPLATES
    )

    switcher = r"""
<script>
  const styleEl = document.createElement("style");
  styleEl.textContent = `
    /* fix: overlay an (opacity-0 + pointer-events-none) van chan click qua con */
    #register-asset-modal.pointer-events-none *, #material-dna-drawer.pointer-events-none *,
    .pointer-events-none .pointer-events-auto { pointer-events: none !important; }
    aside nav a { transition: all .18s ease; transform-origin: left center; }
  `;
  document.head.appendChild(styleEl);
</script>

<script>
// ===== Tab switcher (ghep 3 module vao 1 console) =====
let igActiveLink = null;
const IG_PANES = ["registry", "review", "marketplace"];
const IG_TITLES = {
  registry: ["Building Registry", "Asset registry, crack progression va degradation velocity"],
  review: ["Structural Review - PE Sign-off", "Defect classification, telemetry breakdown va chu ky PE"],
  marketplace: ["Engineering Services Marketplace", "Mang luoi chuyen gia va dich vu kiem dinh"],
};
window.igSwitchTab = function (tag, linkEl) {
  if (!IG_PANES.includes(tag)) return false;
  IG_PANES.forEach((t) => {
    const pane = document.querySelector('[data-pane="' + t + '"]');
    if (pane) pane.hidden = t !== tag;
    const rest = document.querySelector('[data-rest="' + t + '"]');
    if (rest) rest.style.display = t === tag ? "" : "none";
  });
  const sideAside = document.querySelector("body > aside") || document.querySelector("aside");
  if (sideAside) {
    sideAside.querySelectorAll("nav a").forEach((a) => {
      const isActive = a === linkEl;
      const navEl = a.closest("nav");
      const on = ((navEl && navEl.dataset.activeClasses) || "").split(/\s+/).filter(Boolean);
      on.forEach((c) => a.classList.toggle(c, isActive));
      a.style.color = isActive ? "#ffffff" : "";
      a.style.transform = isActive ? "scale(1.06)" : "";
      a.style.background = isActive ? "var(--primary)" : "";
      a.querySelectorAll(".material-symbols-outlined").forEach((ic) => {
        ic.style.color = isActive ? "#93ccff" : "";
      });
    });
  }
  const crumb = document.getElementById("crumb");
  if (crumb && IG_TITLES[tag]) {
    crumb.innerHTML = IG_TITLES[tag][0] + "<small>" + IG_TITLES[tag][1] + "</small>";
  }
  return true;
};
document.querySelectorAll("body > aside nav a").forEach((a) => {
  const t = (a.textContent || "").toLowerCase();
  let tab = null;
  if (t.includes("building registry") || t.includes("field workspace")) tab = "registry";
  if (t.includes("structural review")) tab = "review";
  if (t.includes("engineering marketplace")) tab = "marketplace";
  if (tab) {
    a.dataset.tab = tab;
    a.addEventListener("click", (e) => { e.preventDefault(); igSwitchTab(tab, a); });
  }
});
</script>
"""

    console = (
        registry_html[: registry_html.index("<body")]
        + '<body class="bg-surface font-body-md text-on-surface antialiased">\n'
        + parts["registry"]["aside"] + "\n"
        + parts["registry"]["header"] + "\n"
        + '<main class="w-full pt-16 bg-surface min-h-screen">\n'
        + panes + "\n</main>\n"
        + rests + "\n"
        + switcher
        + '<script src="/static/infra/wire.js"></script>\n'
        + "</body></html>"
    )
    OUT.write_text(console, encoding="utf-8")
    print(f"Console: {OUT.resolve()} ({len(console)//1024} KB)")


if __name__ == "__main__":
    main()
