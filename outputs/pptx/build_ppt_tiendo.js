// BÁO CÁO TIẾN ĐỘ KLNC — Crack Severity AI (focus: thí nghiệm chính xác + so sánh SOTA)
// 19 slides · 13.33x7.5 · palette bê tông + cam · Segoe UI
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.author = "Ngô Kim Thành - Trần Công Thành";
p.title = "Crack Severity AI - Báo cáo tiến độ";

const W = 13.33, H = 7.5, M = 0.55;
const DARK = "1E2A32", INK = "1F2A33", MUTED = "6B7C87", PRIMARY = "46626E";
const PRIM_LT = "E7EEF1", SOFT = "F4F7F9", ACCENT = "E8590C", WHITE = "FFFFFF";
const OK = "2E7D32", WARN = "C77700", BAD = "C62828";
const F = "Segoe UI";
const bu = () => ({ code: "25B8", indent: 12, color: ACCENT });
const shadow = () => ({ type: "outer", color: "1F2A33", blur: 7, offset: 2, angle: 60, opacity: 0.16 });

function crackMotif(s, y = 1.0) {
  const seg = [[0.2, y], [2.2, y + 0.25], [3.4, y - 0.15], [5.0, y + 0.35], [6.6, y + 0.05],
               [8.2, y + 0.5], [9.9, y + 0.2], [11.6, y + 0.65], [13.1, y + 0.4]];
  for (let i = 0; i < seg.length - 1; i++)
    s.addShape(p.shapes.LINE, { x: seg[i][0], y: seg[i][1], w: seg[i + 1][0] - seg[i][0], h: seg[i + 1][1] - seg[i][1], line: { color: ACCENT, width: 1.6 } });
}
function head(s, kicker, title) {
  s.addText(kicker.toUpperCase(), { x: M, y: 0.3, w: W - 2 * M, h: 0.32, fontSize: 12, fontFace: F, bold: true, color: ACCENT, charSpacing: 2, margin: 0 });
  s.addText(title, { x: M, y: 0.6, w: W - 2 * M, h: 0.75, fontSize: 28, fontFace: F, bold: true, color: INK, margin: 0 });
}
function card(s, x, y, w, h, fill = WHITE) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, rectRadius: 0.09, shadow: shadow(), line: { color: "E3E9ED", width: 0.75 } });
}
function stat(s, x, y, w, num, label, color = ACCENT) {
  s.addText(num, { x, y, w, h: 0.72, fontSize: 38, fontFace: F, bold: true, color, align: "center", margin: 0 });
  s.addText(label, { x, y: y + 0.72, w, h: 0.55, fontSize: 12, fontFace: F, color: MUTED, align: "center", margin: 0 });
}
const th = (t) => ({ text: t, options: { bold: true, color: WHITE, fill: { color: PRIMARY } } });

/* S1 — BÌA */
let s = p.addSlide(); s.background = { color: DARK };
crackMotif(s, 1.0);
s.addText("BÁO CÁO TIẾN ĐỘ KHÓA LUẬN TỐT NGHIỆP", { x: M, y: 1.8, w: W - 2 * M, h: 0.4, fontSize: 15, fontFace: F, bold: true, color: "9FB3BE", charSpacing: 3, align: "center", margin: 0 });
s.addText([
  { text: "PHÁT HIỆN VÀ PHÂN LOẠI VẾT NỨT BỀ MẶT\n", options: { color: WHITE } },
  { text: "CÔNG TRÌNH XÂY DỰNG TỪ ẢNH 2D", options: { color: WHITE } },
], { x: 0.8, y: 2.3, w: W - 1.6, h: 1.5, fontSize: 33, fontFace: F, bold: true, align: "center", margin: 0 });
s.addText("Tiến độ kỹ thuật: thí nghiệm đối chứng · so sánh SOTA · kiểm chứng đo lường ±1px", { x: 1.2, y: 3.9, w: W - 2.4, h: 0.4, fontSize: 15, fontFace: F, italic: true, color: ACCENT, align: "center", margin: 0 });
s.addText("Crack Severity AI", { x: 1.5, y: 4.4, w: W - 3, h: 0.55, fontSize: 23, fontFace: F, bold: true, color: WHITE, align: "center", margin: 0 });
s.addText([
  { text: "GVHD:  TS. Phan Xuân Thiện", options: { breakLine: true } },
  { text: "Sinh viên:  Ngô Kim Thành — 23521447   ·   Trần Công Thành — 23521463", options: {} },
], { x: 2.5, y: 5.5, w: W - 5, h: 0.95, fontSize: 14.5, fontFace: F, color: "C9D6DD", align: "center", paraSpaceAfter: 6, margin: 0 });
s.addText("TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN — ĐHQG TP.HCM   ·   27/10/2026", { x: 2.5, y: 6.75, w: W - 5, h: 0.35, fontSize: 11.5, fontFace: F, color: "7E93A0", align: "center", margin: 0 });

/* S2 — AGENDA */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Nội dung", "Đi theo chuỗi thí nghiệm — mỗi số liệu đều tái lập được");
const ag = [
  ["01", "Tiến độ tổng thể & pipeline dữ liệu (con số exact của từng bước)"],
  ["02", "Thí nghiệm 1 — Baseline v1 + chẩn đoán theo từng nguồn dữ liệu"],
  ["03", "Thí nghiệm 2 — Đối chứng A/B (640 vs 1280px) + phân tích thất bại v2"],
  ["04", "Thí nghiệm 3 — So sánh SOTA trên 2 benchmark quốc tế (DeepCrack, 3DCrack)"],
  ["05", "Thí nghiệm 4 — Negative mining & hard-case vân đá (đo FP chính xác)"],
  ["06", "Thí nghiệm 5 — Kiểm chứng đo lường Phase 2 ±1px + case dài-mảnh"],
];
ag.forEach((it, i) => {
  const y = 1.65 + i * 0.92;
  s.addText(it[0], { x: M, y, w: 1.0, h: 0.8, fontSize: 30, fontFace: F, bold: true, color: i % 2 ? PRIMARY : ACCENT, margin: 0 });
  s.addText(it[1], { x: M + 1.15, y: y + 0.1, w: W - 2 * M - 1.3, h: 0.6, fontSize: 16.5, fontFace: F, color: INK, valign: "middle", margin: 0 });
  if (i < 5) s.addShape(p.shapes.LINE, { x: M + 1.15, y: y + 0.82, w: W - 2 * M - 1.3, h: 0, line: { color: "E3E9ED", width: 0.75 } });
});

/* S3 — TIẾN ĐỘ TỔNG THỂ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Tiến độ", "5/5 mốc kỹ thuật của giai đoạn hiện tại đã hoàn thành");
const ms = [
  ["Dữ liệu chuẩn hóa", "20.956 file quét · 15.947 ảnh chuẩn · 100% khớp nhãn", "XONG", OK],
  ["Baseline v1 @640", "F1 0.655 · P 0.823 · mức ảnh 99.9%", "XONG", OK],
  ["Đối chứng v2 @1280", "F1 0.514 — đánh giá & loại có căn cứ", "XONG", OK],
  ["So sánh SOTA", "DeepCrack 98.3% ResUNet · 3DCrack −11%", "XONG", OK],
  ["Hard-case vân đá", "303 ảnh · FP đo theo 4 ngưỡng conf", "XONG", OK],
  ["v3 — hard-negative", "Gộp vân đá train lại 960px", "ĐANG LÀM", WARN],
  ["Lớp B đúng nghĩa", "Segmentation mặt phẳng cấu kiện", "KẾ HOẠCH", MUTED],
];
ms.forEach((m, i) => {
  const y = 1.62 + i * 0.76;
  card(s, M, y, W - 2 * M, 0.64, i === 5 ? "FFF6EF" : WHITE);
  s.addText(m[0], { x: M + 0.25, y: y + 0.05, w: 3.2, h: 0.52, fontSize: 13.5, fontFace: F, bold: true, color: INK, valign: "middle", margin: 0 });
  s.addText(m[1], { x: M + 3.6, y: y + 0.05, w: 6.6, h: 0.52, fontSize: 12, fontFace: F, color: MUTED, valign: "middle", margin: 0 });
  s.addText(m[2], { x: M + 10.35, y: y + 0.05, w: 1.85, h: 0.52, fontSize: 11.5, fontFace: F, bold: true, color: m[3], valign: "middle", align: "right", margin: 0 });
});

/* S4 — PIPELINE DỮ LIỆU (con số exact) */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Kỹ thuật dữ liệu", "Pipeline 5 bước — mọi con số đều kiểm chứng bằng script");
const s4 = [
  ["20.956", "file quét khớp tên 1:1", "(5 nguồn mask + txt)"],
  ["4.196", "ảnh mặt đường đã loại", "(CFD·CRACK500·CrackTree·GAPS384)"],
  ["118", "nhãn thiếu đã bổ sung", "(pseudo-GT conf ≥ 0.6)"],
  ["3.000", "ảnh nền thêm vào train", "(METU·SDNET — tổng nền 4.048)"],
  ["7 + 14", "ảnh trùng MD5 + đụng tên đã xử lý", "(bug Windows FS đã sửa)"],
];
s4.forEach((it, i) => {
  const y = 1.62 + i * 1.02;
  s.addText(it[0], { x: M, y, w: 2.1, h: 0.9, fontSize: 30, fontFace: F, bold: true, color: i % 2 ? PRIMARY : ACCENT, margin: 0 });
  s.addText(it[1], { x: M + 2.3, y: y + 0.08, w: 4.6, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: INK, margin: 0 });
  s.addText(it[2], { x: M + 2.3, y: y + 0.5, w: 4.6, h: 0.4, fontSize: 11.5, fontFace: F, color: MUTED, margin: 0 });
  if (i < 4) s.addShape(p.shapes.LINE, { x: M, y: y + 0.94, w: 6.9, h: 0, line: { color: "E3E9ED", width: 0.75 } });
});
card(s, 7.75, 1.62, 5.03, 5.0, SOFT);
s.addText("Kiểm chứng tự động sau build", { x: 8.0, y: 1.85, w: 4.5, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: INK, margin: 0 });
const c4 = [
  "Image–label khớp 100%: 0 thiếu / 0 thừa / 0 rỗng sai chỗ (train-val-test)",
  "Nhãn polygon thuần — đã xử lý lỗi “labels mix segment and detection rows” của Ultralytics",
  "Báo cáo Excel 20.956 dòng kèm kết luận từng file (lấy primary / ảnh âm / loại)",
  "Split 80/10/10 bằng hash deterministic — val/test BẤT BIẾN giữa mọi phiên bản (so sánh công bằng)",
];
s.addText(c4.map((t, i) => ({ text: t, options: { bullet: bu(), breakLine: i < 3 } })), { x: 8.0, y: 2.32, w: 4.55, h: 4.1, fontSize: 12, fontFace: F, color: MUTED, paraSpaceAfter: 10, margin: 0 });

/* S5 — THÍ NGHIỆM 1: BASELINE */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Thí nghiệm 1 — Baseline", "v1: YOLOv8s-seg @640px · Kaggle T4 · sweep ngưỡng conf");
s.addChart(p.charts.BAR, [
  { name: "v1 @conf 0.25", labels: ["Precision", "Recall", "F1", "mAP50"], values: [0.797, 0.555, 0.655, 0.599] },
], {
  x: M, y: 1.7, w: 6.7, h: 4.5, barDir: "col",
  chartColors: ["46626E"], showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK,
  dataLabelFontSize: 12, dataLabelFormatCode: "0.000",
  catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, valAxisMaxVal: 1, valAxisMinVal: 0,
  valGridLine: { color: "EDF1F4", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false,
  chartArea: { fill: { color: "FFFFFF" } },
});
card(s, 7.55, 1.7, 5.23, 2.15, "EAF6EE");
s.addText([
  { text: "Đạt / vượt mục tiêu", options: { bold: true, color: OK, breakLine: true } },
  { text: "Độ chính xác mức ảnh 99.9% (kỳ vọng 95%)", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "FP trên 400 ảnh nền: chỉ 9 ảnh (2.2%)", options: { bullet: bu(), color: MUTED } },
], { x: 7.85, y: 1.92, w: 4.7, h: 1.8, fontSize: 12.5, fontFace: F, paraSpaceAfter: 8, margin: 0 });
card(s, 7.55, 4.05, 5.23, 2.15, "FDF1E8");
s.addText([
  { text: "Điểm yếu đã định lượng", options: { bold: true, color: WARN, breakLine: true } },
  { text: "75.5% vết bỏ sót là vết nhỏ (cạnh < 32px)", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "FP chiếm 20%: vết mảnh duplicated / lệch IoU", options: { bullet: bu(), color: MUTED } },
], { x: 7.85, y: 4.27, w: 4.7, h: 1.8, fontSize: 12.5, fontFace: F, paraSpaceAfter: 8, margin: 0 });
s.addText("Điều kiện: 1.491 ảnh test · 3.531 vết GT · IoU ≥ 0.5 · Nguồn: scripts/evaluate_phase1.py", { x: M, y: 6.45, w: 9, h: 0.35, fontSize: 11, fontFace: F, color: MUTED, margin: 0 });

/* S6 — CHẨN ĐOÁN THEO NGUỒN */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Thí nghiệm 1 — phân tách", "F1 theo từng nguồn: chỉ ra chính xác mô hình yếu ở đâu");
s.addChart(p.charts.BAR, [{
  name: "F1", labels: ["Rissbilder", "Volker", "crack_seg/DC", "3DCrack", "DeepCrack", "Ultralytics", "Roads&Bridges"],
  values: [0.544, 0.499, 0.610, 0.649, 0.764, 0.811, 0.841],
}], {
  x: M, y: 1.7, w: 7.5, h: 4.6, barDir: "bar",
  chartColors: ["E8590C", "E8590C", "46626E", "46626E", "46626E", "46626E", "46626E"],
  varyColors: true, showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK, dataLabelFontSize: 11,
  catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, valAxisMaxVal: 1, valAxisMinVal: 0,
  valGridLine: { color: "EDF1F4", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false,
  chartArea: { fill: { color: "FFFFFF" } }, catAxisLabelFontSize: 11, dataLabelFormatCode: "0.00",
});
card(s, 8.4, 1.7, 4.38, 4.6, SOFT);
s.addText("Vì sao Volker/Rissbilder yếu?", { x: 8.68, y: 1.95, w: 3.9, h: 0.4, fontSize: 13.5, fontFace: F, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "Giả thuyết 1 — nhãn thiếu?", options: { bold: true, color: INK, breakLine: true } },
  { text: "Audit 3.810 ảnh train: chỉ 118/5.700+ vết thiếu (0.9%) → LOẠI giả thuyết", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Kết luận: do vết mảnh dày đặc (Rissbilder TB 4,1 vết/ảnh) + imgsz 640", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Hành động: tăng độ phân giải (đối chứng ở thí nghiệm 2)", options: { bullet: bu(), color: ACCENT } },
], { x: 8.68, y: 2.4, w: 3.9, h: 3.7, fontSize: 12, fontFace: F, paraSpaceAfter: 9, margin: 0 });
s.addText("Phương pháp: matching tham lam theo conf giảm dần, IoU ≥ 0.5 — cùng bộ test bất biến", { x: M, y: 6.5, w: 9, h: 0.35, fontSize: 11, fontFace: F, color: MUTED, margin: 0 });

/* S7 — THÍ NGHIỆM 2: A/B SWEEP */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Thí nghiệm 2 — đối chứng A/B", "Sweep ngưỡng conf toàn dải: 640px thắng trên MỌI ngưỡng");
const t7 = [
  [th("conf ≥"), th("A: P"), th("A: R"), th("A: F1"), th("B: P"), th("B: R"), th("B: F1")],
  ["0.25", "0.797", "0.555", { text: "0.655", options: { bold: true, color: OK } }, "0.516", "0.511", "0.513"],
  ["0.35", "—", "—", "—", "0.554", "0.478", "0.514"],
  ["0.45", "—", "—", "—", "0.608", "0.445", "0.514"],
  ["0.55", "—", "—", "—", "0.683", "0.378", "0.487"],
  ["0.65", "—", "—", "—", "0.744", "0.244", "0.368"],
];
s.addTable(t7, { x: M, y: 1.72, w: 7.3, colW: [1.0, 1.05, 1.05, 1.05, 1.05, 1.05, 1.05], fontSize: 12, fontFace: F, color: INK, border: { pt: 0.75, color: "E3E9ED" }, rowH: 0.46, valign: "middle", align: "center", margin: 0.03 });
card(s, 8.15, 1.72, 4.63, 2.5, SOFT);
s.addText("Kết luận đối chứng", { x: 8.45, y: 1.94, w: 4, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "Giữ A (640px) — F1 0.655 > 0.514 tốt nhất của B", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "B chỉ thắng FP ảnh nền: 1.5% so với 2.2%", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Nguyên nhân: box mảnh @1280 cực nhạy với IoU 0.5", options: { bullet: bu(), color: MUTED } },
], { x: 8.45, y: 2.38, w: 4.05, h: 1.7, fontSize: 12, fontFace: F, paraSpaceAfter: 8, margin: 0 });
card(s, 8.15, 4.4, 4.63, 1.95, "FDECEC");
s.addText([
  { text: "Bài học quy trình (đã ghi experiment_log)", options: { bold: true, color: BAD, breakLine: true } },
  { text: "Checkpoint B trỏ “v2epoch74/last.pt” — bản last của lượt resume, không phải best thật", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "v3: train tiếp từ weight A @960px + tải đúng best.pt", options: { bullet: bu(), color: MUTED } },
], { x: 8.45, y: 4.6, w: 4.05, h: 1.6, fontSize: 11.5, fontFace: F, paraSpaceAfter: 7, margin: 0 });
s.addText("Sweep post-hoc chính xác: greedy theo conf giảm dần — không cần chạy lại model mỗi ngưỡng", { x: M, y: 6.55, w: 9, h: 0.35, fontSize: 11, fontFace: F, color: MUTED, margin: 0 });

/* S8 — THÍ NGHIỆM 3: SOTA 1 */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Thí nghiệm 3 — so sánh SOTA", "Benchmark quốc tế: DeepCrack — đạt 98.3% mức ResUNet");
s.addChart(p.charts.BAR, [
  { name: "Nhóm (YOLOv8s-seg)", labels: ["DeepCrack", "3DCrack"], values: [0.819, 0.708] },
  { name: "ResUNet (bài báo)", labels: ["DeepCrack", "3DCrack"], values: [0.833, 0.795] },
], {
  x: M, y: 1.75, w: 7.3, h: 4.4, barDir: "col", barGapWidthPct: 60,
  chartColors: ["E8590C", "46626E"], showValue: true, dataLabelPosition: "outEnd",
  dataLabelColor: INK, dataLabelFontSize: 11.5, dataLabelFormatCode: "0.000",
  catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, valAxisMaxVal: 1, valAxisMinVal: 0,
  valGridLine: { color: "EDF1F4", size: 0.5 }, catGridLine: { style: "none" },
  showLegend: true, legendPos: "b", legendColor: MUTED, legendFontSize: 11,
  chartArea: { fill: { color: "FFFFFF" } }, catAxisLabelFontSize: 12,
});
card(s, 8.25, 1.75, 4.53, 4.4, SOFT);
s.addText("Vì sao so sánh được?", { x: 8.55, y: 1.98, w: 4, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: INK, margin: 0 });
const c8 = [
  "Bài so sánh: arXiv:2508.10256 (Georgia Tech, 2025) — review + benchmark hệ thống nhất hiện nay",
  "Nhóm tự cài đặt ĐÚNG bộ metric của bài: IoU / Precision / Recall / Dice mức pixel",
  "Cùng 2 bộ dữ liệu: DeepCrack, 3DCrack (ảnh 512×624 — nhóm đang dùng)",
  "3DCrack và Khanh11k trong bài chính là 3DCrack_v1 + crack_segmentation_dataset của nhóm",
];
s.addText(c8.map((t, i) => ({ text: t, options: { bullet: bu(), breakLine: i < 3 } })), { x: 8.55, y: 2.42, w: 4.0, h: 3.6, fontSize: 11.5, fontFace: F, color: MUTED, paraSpaceAfter: 9, margin: 0 });
s.addText("Lưu ý trung thực: split của nhóm khác bài (hash 80/10/10 đa nguồn) — số tham chiếu tương đối, cùng loại metric.", { x: M, y: 6.45, w: W - 2 * M, h: 0.4, fontSize: 11, fontFace: F, color: MUTED, margin: 0 });

/* S9 — THÍ NGHIỆM 3: SOTA 2 (bảng phương pháp) */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Thí nghiệm 3 — vị trí giữa các phương pháp", "Cùng bài benchmark: các hướng đang mạnh nhất thế giới");
const t9 = [
  [th("Phương pháp"), th("Hướng tiếp cận"), th("DeepCrack Dice"), th("3DCrack Dice"), th("Ghi chú")],
  [{ text: "ResUNet", options: {} }, "CNN segmentation thuần", { text: "0.833", options: {} }, { text: "0.795", options: {} }, "Baseline chính của bài báo"],
  [{ text: "CrackSAM", options: {} }, "SAM + LoRA fine-tune", { text: "> 0.833*", options: {} }, { text: "> 0.795*", options: {} }, "Thắng đều mọi cài đặt (bài báo)"],
  [{ text: "UniMatch v2", options: {} }, "Semi-supervised + DINOv2", { text: "> 0.833*", options: {} }, { text: "> 0.795*", options: {} }, "Mạnh khi thiếu nhãn"],
  [{ text: "NHÓM", options: { bold: true, color: ACCENT } }, { text: "YOLOv8s-seg 1-stage + rules", options: { bold: true } }, { text: "0.819", options: { bold: true, color: ACCENT } }, { text: "0.708", options: { bold: true, color: ACCENT } }, { text: "98.3% / 89.2% ResUNet", options: { bold: true } }],
];
s.addTable(t9, { x: M, y: 1.75, w: W - 2 * M, colW: [2.2, 3.3, 2.2, 2.2, 2.31], fontSize: 12.5, fontFace: F, color: INK, border: { pt: 0.75, color: "E3E9ED" }, rowH: 0.52, valign: "middle", margin: 0.06 });
card(s, M, 4.75, 6.1, 1.9, SOFT);
s.addText("Phân tích khoảng cách", { x: M + 0.3, y: 4.95, w: 5, h: 0.4, fontSize: 13.5, fontFace: F, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "DeepCrack −1.4%: gần san lấp — dù nhóm train đa nguồn + không tối ưu riêng bộ này", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "3DCrack −11%: mask head YOLO decode 1/4 độ phân giải → mất vết 1–2px", options: { bullet: bu(), color: MUTED } },
], { x: M + 0.3, y: 5.38, w: 5.55, h: 1.2, fontSize: 11.5, fontFace: F, paraSpaceAfter: 7, margin: 0 });
card(s, 7.0, 4.75, 5.78, 1.9, "FFF6EF");
s.addText("Đánh đổi có chủ đích", { x: 7.3, y: 4.95, w: 5, h: 0.4, fontSize: 13.5, fontFace: F, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "Nhóm chọn 1-stage (detection) vì cần cascade sang Phase 2 đo đặc trưng", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "CrackSAM/UniMatch là segmentation thuần — không cho box/instance cho quy trình kiểm định", options: { bullet: bu(), color: MUTED } },
], { x: 7.3, y: 5.38, w: 5.2, h: 1.2, fontSize: 11.5, fontFace: F, paraSpaceAfter: 7, margin: 0 });
s.addText("* Bài báo mô tả CrackSAM / UniMatch v2 “cao hơn ResUNet mọi cài đặt” nhưng bảng số chưa công bố trong text — nhóm ghi mức tối thiểu tương ứng.", { x: M, y: 6.85, w: W - 2 * M, h: 0.4, fontSize: 10.5, fontFace: F, italic: true, color: MUTED, margin: 0 });

/* S10 — THÍ NGHIỆM 4: NEGATIVE MINING */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Thí nghiệm 4a — negative mining", "Ảnh nền giảm báo giả: đo trên 400 ảnh mẫu cố định seed=42");
s.addChart(p.charts.BAR, [
  { name: "Không có negative (v0)", labels: ["FP ảnh nền"], values: [4.5] },
  { name: "1.048 noncrack (v1)", labels: ["FP ảnh nền"], values: [2.2] },
  { name: "+3.000 METU/SDNET (v2)", labels: ["FP ảnh nền"], values: [1.5] },
], {
  x: M, y: 1.8, w: 6.9, h: 4.3, barDir: "col", barGapWidthPct: 50,
  chartColors: ["94A3B8", "46626E", "E8590C"], varyColors: true,
  showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK, dataLabelFontSize: 13,
  dataLabelFormatCode: "0.0\"%\"",
  catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, valAxisMaxVal: 5, valAxisMinVal: 0,
  valGridLine: { color: "EDF1F4", size: 0.5 }, catGridLine: { style: "none" },
  showLegend: false, chartArea: { fill: { color: "FFFFFF" } }, catAxisLabelFontSize: 11,
});
card(s, 7.75, 1.8, 5.03, 4.3, SOFT);
s.addText("Cách tiến hành chính xác", { x: 8.05, y: 2.02, w: 4.5, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: INK, margin: 0 });
const c10 = [
  "Chọn 400/1.353 ảnh âm bằng random seed=42 — cùng bộ ảnh cho mọi lần đo, so sánh công bằng",
  "Conf của các lần báo nhầm: trung bình 0.45, max 0.79 — nâng ngưỡng còn giảm nữa",
  "Ảnh nền gồm: vân gạch trang trí (noncrack), bê tông lành (METU Neg), tường/sàn cầu lành (SDNET UD/UW)",
  "Kết luận: negative mining giảm FP ×3 (4.5% → 1.5%) — giữ nguyên trong v3",
];
s.addText(c10.map((t, i) => ({ text: t, options: { bullet: bu(), breakLine: i < 3 } })), { x: 8.05, y: 2.48, w: 4.5, h: 3.5, fontSize: 11.5, fontFace: F, color: MUTED, paraSpaceAfter: 9, margin: 0 });

/* S11 — THÍ NGHIỆM 4B: HARD CASE VÂN ĐÁ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Thí nghiệm 4b — hard-case vân đá", "303 ảnh out-of-domain (0 ảnh trong train) · đo FP theo 4 ngưỡng");
const t11 = [
  [th("conf ≥"), th("FP vết (A)"), th("FP ảnh (A)"), th("FP vết (B)"), th("FP ảnh (B)")],
  ["0.25", "107", "30.7%", "350", "72.3%"],
  ["0.35", "89", "27.4%", "235", "57.1%"],
  ["0.45", { text: "74", options: { bold: true, color: OK } }, { text: "24.1%", options: { bold: true, color: OK } }, "128", "36.3%"],
  ["0.55", "65", "21.5%", { text: "53", options: { bold: true, color: OK } }, { text: "17.2%", options: { bold: true, color: OK } }],
];
s.addTable(t11, { x: M, y: 1.75, w: 7.2, colW: [1.2, 1.5, 1.5, 1.5, 1.5], fontSize: 12.5, fontFace: F, color: INK, border: { pt: 0.75, color: "E3E9ED" }, rowH: 0.5, valign: "middle", align: "center", margin: 0.04 });
s.addText("A = v1 @640 (đang dùng) · B = v2 @1280 · FP ảnh = % ảnh vân đá bị báo nhầm ≥ 1 vết", { x: M, y: 4.45, w: 7.2, h: 0.4, fontSize: 11, fontFace: F, color: MUTED, margin: 0 });
card(s, 8.05, 1.75, 4.73, 4.55, SOFT);
s.addText("Khả năng học tổng quát", { x: 8.35, y: 1.98, w: 4, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: INK, margin: 0 });
const c11 = [
  "Vết nứt ĐÁ thật (có GT): A vẫn bắt 39.5% recall, precision 73.1% — mô hình hiểu khái niệm nứt, không thuộc lòng bê tông",
  "Sylvie: F1 0.677 (khá) · forest: F1 0.357, pixel Dice 0.19 — vân đá dày đặc là khó nhất",
  "Kết luận: vẫn nhầm (dự kiến) — v3 gộp một phần vân đá làm hard-negative nhãn rỗng, mục tiêu FP ảnh < 10%",
];
s.addText(c11.map((t, i) => ({ text: t, options: { bullet: bu(), breakLine: i < 2 } })), { x: 8.35, y: 2.44, w: 4.15, h: 3.7, fontSize: 11.5, fontFace: F, color: MUTED, paraSpaceAfter: 10, margin: 0 });
card(s, M, 5.0, 7.2, 1.3, "FDF1E8");
s.addText([
  { text: "Số liệu chi tiết từng ảnh: ", options: { bold: true, color: INK } },
  { text: "outputs/reports/hard_cases_v1_640_*.md + per_image.csv — 303 dòng, mỗi ảnh một dòng (gt/pred/tp/fp/fn).", options: { color: MUTED } },
], { x: M + 0.25, y: 5.2, w: 6.7, h: 0.9, fontSize: 11.5, fontFace: F, margin: 0 });

/* S12 — THÍ NGHIỆM 5: KIỂM CHỨNG ĐO LƯỜNG */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Thí nghiệm 5a — kiểm chứng đo lường", "Phase 2 đo đúng chưa? Mask chuẩn kích thước đã biết");
const t12 = [
  [th("Đại lượng"), th("GT"), th("Hệ thống đo"), th("Lệch"), th("Ngưỡng nghiệm thu")],
  ["Bề rộng lớn nhất", "1–20 px", "DT chính xác + hiệu chỉnh ½ px", { text: "≤ 1.0 px", options: { bold: true, color: OK } }, "≤ 1 px (lượng tử hóa)"],
  ["Chiều dài", "50–400 px", "minAreaRect", { text: "0.0 px", options: { bold: true, color: OK } }, "≤ 2 px"],
  ["Góc trục chính", "0–90°", "Moments (không dùng minAreaRect)", { text: "0.0°", options: { bold: true, color: OK } }, "≤ 1°"],
  ["Rẽ nhánh", "vết chữ Y / thẳng", "Skeleton Zhang–Suen", { text: "đúng cả 2", options: { bold: true, color: OK } }, "phát hiện Y, không báo nhầm"],
];
s.addTable(t12, { x: M, y: 1.75, w: W - 2 * M, colW: [2.5, 1.7, 3.5, 1.6, 2.93], fontSize: 12.5, fontFace: F, color: INK, border: { pt: 0.75, color: "E3E9ED" }, rowH: 0.56, valign: "middle", margin: 0.06 });
card(s, M, 4.85, 6.1, 1.85, "EAF6EE");
s.addText([
  { text: "2 lỗi đã bắt được nhờ kiểm chứng", options: { bold: true, color: OK, breakLine: true } },
  { text: "Góc: minAreaRect cho thanh ngang = 90° → chuyển sang moments", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Bề rộng: DT đo center-to-center (+1px lẻ, +2px chẵn) → hiệu chỉnh 2×(d−0.5)", options: { bullet: bu(), color: MUTED } },
], { x: M + 0.3, y: 5.05, w: 5.55, h: 1.5, fontSize: 11.5, fontFace: F, paraSpaceAfter: 7, margin: 0 });
card(s, 7.0, 4.85, 5.78, 1.85, SOFT);
s.addText([
  { text: "Ý nghĩa với hội đồng", options: { bold: true, color: INK, breakLine: true } },
  { text: "Trước khi nói “app đo được bề rộng vết nứt”, nhóm chứng minh đo ĐÚNG trong giới hạn ±1px — bằng phương pháp mask tổng hợp GT đã biết.", options: { color: MUTED } },
], { x: 7.3, y: 5.05, w: 5.2, h: 1.5, fontSize: 11.5, fontFace: F, paraSpaceAfter: 7, margin: 0 });
s.addText("Nguồn: scripts/validate_measurements.py → outputs/reports/validate_measurements_*.md", { x: M, y: 6.85, w: 9, h: 0.35, fontSize: 11, fontFace: F, color: MUTED, margin: 0 });

/* S13 — THÍ NGHIỆM 5B: CASE DÀI-MẢNH */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Thí nghiệm 5b — phân loại đa yếu tố", "Case thực tế: vết DÀI nhưng MẢNH — bề rộng đơn thuần sai");
const t13 = [
  [th("Cấu hình vết"), th("Neo ACI (width)"), th("Yếu tố cộng"), th("Kết quả")],
  [{ text: "Mảnh 0.15mm · ngắn 15mm · nhạt", options: {} }, "L1 Minor", "—", { text: "L1 Minor", options: { color: OK, bold: true } }],
  [{ text: "Mảnh 0.15mm · DÀI 750mm · nhạt", options: {} }, "L1 Minor", "+1 (dài ≥ 300mm)", { text: "L2 Moderate", options: { color: WARN, bold: true } }],
  [{ text: "Mảnh 0.15mm · DÀI 750mm · ĐẬM 50%", options: {} }, "L1 Minor", "+1 dài · +1 đậm (≥30%)", { text: "L3 Severe", options: { color: BAD, bold: true } }],
  [{ text: "Bất kỳ · xuyên cấu kiện", options: {} }, "—", "cưỡng chế", { text: "L3 Severe", options: { color: BAD, bold: true } }],
];
s.addTable(t13, { x: M, y: 1.75, w: W - 2 * M, colW: [4.3, 2.4, 2.9, 3.23], fontSize: 12.5, fontFace: F, color: INK, border: { pt: 0.75, color: "E3E9ED" }, rowH: 0.56, valign: "middle", margin: 0.06 });
card(s, M, 4.9, 6.1, 1.8, SOFT);
s.addText("Độ đậm đo như thế nào?", { x: M + 0.3, y: 5.1, w: 5, h: 0.4, fontSize: 13.5, fontFace: F, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "contrast = (sáng nền − sáng vết) / sáng nền", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Nền = vòng đệm 9px quanh vết (bối cảnh cục bộ)", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Vết sâu hiện tối hơn nền → proxy độ sâu; hairline cạn thường mờ", options: { bullet: bu(), color: MUTED } },
], { x: M + 0.3, y: 5.52, w: 5.55, h: 1.1, fontSize: 11.5, fontFace: F, paraSpaceAfter: 6, margin: 0 });
card(s, 7.0, 4.9, 5.78, 1.8, "FFF6EF");
s.addText([
  { text: "Mọi kết quả đều có unit test", options: { bold: true, color: INK, breakLine: true } },
  { text: "Case dài-mảnh ở trên là test tự động trong pytest (28/28 pass) — không phải demo chọn lọc.", options: { color: MUTED } },
], { x: 7.3, y: 5.1, w: 5.2, h: 1.4, fontSize: 11.5, fontFace: F, paraSpaceAfter: 7, margin: 0 });

/* S14 — BUGS & SỬA (kỹ thuật chính xác) */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Kỷ luật kỹ thuật", "4 lỗi thật đã phát hiện bằng thí nghiệm — và đã sửa");
const bugs = [
  ["Đụng tên file khi build (Windows FS)", "Log ghi 18.790 ảnh nhưng đĩa 18.776", "Thêm hậu tố _2/_3 khi trùng tên → 14 ảnh được giữ lại"],
  ["Nhãn trộn box + polygon", "Ultralytics từ chối train task=segment", "Ép box → polygon 4 điểm tại nguồn; loại lỗi triệt để"],
  ["Eval chỉ chạy 1 ảnh (indent)", "Báo cáo sweep cho TP=2 — vô lý", "Thêm cảnh báo tự động khi xử lý < 99% số ảnh"],
  ["Góc minAreaRect lệch chuẩn", "Thanh ngang đo ra 90°", "Chuyển sang moments — kiểm chứng 0° lệch"],
];
bugs.forEach((b, i) => {
  const y = 1.68 + i * 1.32;
  card(s, M, y, W - 2 * M, 1.14, i % 2 ? WHITE : SOFT);
  s.addText(b[0], { x: M + 0.28, y: y + 0.1, w: 4.2, h: 0.95, fontSize: 13, fontFace: F, bold: true, color: INK, valign: "middle", margin: 0 });
  s.addText(b[1], { x: M + 4.7, y: y + 0.1, w: 3.6, h: 0.95, fontSize: 11.5, fontFace: F, color: BAD, valign: "middle", margin: 0 });
  s.addText(b[2], { x: M + 8.5, y: y + 0.1, w: 4.0, h: 0.95, fontSize: 11.5, fontFace: F, color: OK, valign: "middle", margin: 0 });
});

/* S15 — HỆ THỐNG (ngắn gọn) */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Tích hợp", "Toàn bộ thí nghiệm chạy trong một hệ thống thật (không phải notebook rời)");
stat(s, 0.8, 1.7, 2.7, "6", "phân hệ ứng dụng web");
stat(s, 3.7, 1.7, 2.7, "28+7", "unit test + E2E pass");
stat(s, 6.6, 1.7, 2.7, "160ms", "suy luận/ảnh (CPU)");
stat(s, 9.5, 1.7, 2.7, "2", "CI/CD: lint+test → deploy", PRIMARY);
const c15 = [
  "Mỗi thí nghiệm trong deck đều có script chạy lại được trong repo (evaluate / compare_with_sota / eval_hard_cases / validate_measurements)",
  "Ứng dụng: Phiếu kiểm tra 4 bước → AI phát hiện + đo + phân loại L0–L3 tự động → hồ sơ chờ duyệt → quản lý duyệt → báo cáo PDF chữ ký kép",
  "Hiệu chuẩn GSD ngay trên ảnh (bấm 2 điểm vào thước) — tái phân loại tức thì, không chạy lại model",
  "DevOps: Docker + GitHub Actions; weight tải runtime từ Hugging Face, không commit git",
];
s.addText(c15.map((t, i) => ({ text: t, options: { bullet: bu(), breakLine: i < 3 } })), { x: M, y: 3.4, w: W - 2 * M, h: 3.3, fontSize: 13, fontFace: F, color: MUTED, paraSpaceAfter: 12, margin: 0 });

/* S16 — TUẦN TỚI */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Tuần tới", "Kế hoạch gắn trực tiếp với kết quả đã đo");
const nx = [
  ["v3 — hard-negative", "Gộp ~150 ảnh vân đá (nhãn rỗng) vào train · fine-tune từ weight A @960px · tải đúng best.pt", "Mục tiêu: FP ảnh vân đá 24.1% → <10%, F1 test ≥ 0.70"],
  ["Nghiệm thu thang Phase 2", "Chụp ảnh thực có thước tham chiếu · hiệu chuẩn ngưỡng 300mm / 30% trên dữ liệu thật", "Chuyển “đề xuất” → chính thức"],
  ["Lớp B đúng nghĩa", "Segmentation mặt phẳng cấu kiện thay heuristic skeleton", "Tín hiệu multi_plane có căn cứ hình học"],
];
nx.forEach((it, i) => {
  const y = 1.7 + i * 1.7;
  s.addText(`0${i + 1}`, { x: M, y, w: 1.0, h: 1.45, fontSize: 36, fontFace: F, bold: true, color: i % 2 ? PRIMARY : ACCENT, margin: 0 });
  s.addText(it[0], { x: M + 1.15, y: y + 0.05, w: 3.4, h: 1.35, fontSize: 15, fontFace: F, bold: true, color: INK, valign: "top", margin: 0 });
  s.addText(it[1], { x: M + 4.7, y: y + 0.05, w: 5.0, h: 1.35, fontSize: 12, fontFace: F, color: MUTED, margin: 0 });
  s.addText(it[2], { x: M + 9.85, y: y + 0.05, w: 2.9, h: 1.35, fontSize: 11.5, fontFace: F, bold: true, color: ACCENT, margin: 0 });
  if (i < 2) s.addShape(p.shapes.LINE, { x: M + 1.15, y: y + 1.5, w: W - 2 * M - 1.15, h: 0, line: { color: "E3E9ED", width: 0.75 } });
});

/* S17 — KẾT LUẬN */
s = p.addSlide(); s.background = { color: DARK };
crackMotif(s, 0.9);
s.addText("KẾT LUẬN TIẾN ĐỘ", { x: M, y: 1.7, w: W - 2 * M, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: "9FB3BE", charSpacing: 3, margin: 0 });
const cl = [
  ["Đo được thì mới nói được", "Mọi kết luận đều đi kèm điều kiện đo: tập nào, ngưỡng nào, IoU bao nhiêu — tái lập bằng script công khai"],
  ["So được với thế giới", "DeepCrack đạt 98.3% baseline ResUNet của bài SOTA 2025 bằng đúng bộ metric của bài — 3DCrack còn −11% đã định lượng nguyên nhân"],
  ["Thất bại cũng là kết quả", "Đối chứng 1280px loại có căn cứ + 4 lỗi hệ thống phát hiện và sửa — đó là tiến độ kỹ thuật thật"],
];
cl.forEach((c, i) => {
  const y = 2.3 + i * 1.4;
  s.addText(`0${i + 1}`, { x: M, y, w: 1.0, h: 1.15, fontSize: 40, fontFace: F, bold: true, color: ACCENT, margin: 0 });
  s.addText(c[0], { x: M + 1.2, y: y + 0.02, w: 4.3, h: 1.15, fontSize: 17, fontFace: F, bold: true, color: WHITE, margin: 0 });
  s.addText(c[1], { x: M + 5.6, y: y + 0.02, w: W - 2 * M - 5.7, h: 1.15, fontSize: 12.5, fontFace: F, color: "C9D6DD", margin: 0 });
  if (i < 2) s.addShape(p.shapes.LINE, { x: M, y: y + 1.22, w: W - 2 * M, h: 0, line: { color: "31424E", width: 0.75 } });
});

/* S18 — CẢM ƠN */
s = p.addSlide(); s.background = { color: DARK };
crackMotif(s, 1.2);
s.addText("TRÂN TRỌNG CẢM ƠN THẦY", { x: 0.8, y: 3.0, w: W - 1.6, h: 0.9, fontSize: 40, fontFace: F, bold: true, color: WHITE, align: "center", margin: 0 });
s.addText("Sẵn sàng trình bày chi tiết từng thí nghiệm — script & log đính kèm repo", { x: 1.5, y: 4.1, w: W - 3, h: 0.5, fontSize: 16, fontFace: F, color: ACCENT, align: "center", margin: 0 });
s.addText("Ngô Kim Thành — 23521447   ·   Trần Công Thành — 23521463   ·   GVHD: TS. Phan Xuân Thiện", { x: 1.5, y: 5.6, w: W - 3, h: 0.4, fontSize: 13, fontFace: F, color: "9FB3BE", align: "center", margin: 0 });

p.writeFile({ fileName: "D:/crack_severity_ai/outputs/pptx/CrackSeverity_AI_TienDo_KLNC.pptx" })
  .then(() => console.log("DONE"))
  .catch((e) => { console.error(e); process.exit(1); });
