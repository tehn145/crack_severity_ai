// Crack Severity AI — Bộ slide bảo vệ khóa luận (20 slides, 13.33x7.5)
// Palette: xám bê tông + cam an toàn | Font: Segoe UI | Motif: card bo góc + số lớn + vết nứt
const pptxgen = require("pptxgenjs");

const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.author = "Ngô Kim Thành - Trần Công Thành";
p.title = "Crack Severity AI - Bảo vệ khóa luận";

const W = 13.33, H = 7.5, M = 0.55;
const DARK = "1E2A32", INK = "1F2A33", MUTED = "6B7C87", PRIMARY = "46626E";
const PRIM_LT = "E7EEF1", SOFT = "F4F7F9", ACCENT = "E8590C", WHITE = "FFFFFF";
const OK = "2E7D32", WARN = "C77700", BAD = "C62828";
const F = "Segoe UI";
const IMG = "D:/crack_severity_ai/outputs/pptx";

const bu = () => ({ code: "25B8", indent: 12, color: ACCENT });
const shadow = () => ({ type: "outer", color: "1F2A33", blur: 7, offset: 2, angle: 60, opacity: 0.16 });

function crackMotif(s, y = 1.1, x0 = 0) {
  const seg = [[x0 + 0.2, y], [x0 + 2.2, y + 0.25], [x0 + 3.4, y - 0.15], [x0 + 5.0, y + 0.35],
               [x0 + 6.6, y + 0.05], [x0 + 8.2, y + 0.5], [x0 + 9.9, y + 0.2], [x0 + 11.6, y + 0.65], [x0 + 13.1, y + 0.4]];
  for (let i = 0; i < seg.length - 1; i++)
    s.addShape(p.shapes.LINE, { x: seg[i][0], y: seg[i][1], w: seg[i + 1][0] - seg[i][0], h: seg[i + 1][1] - seg[i][1], line: { color: ACCENT, width: 1.6 } });
}
function head(s, kicker, title) {
  s.addText(kicker.toUpperCase(), { x: M, y: 0.32, w: W - 2 * M, h: 0.32, fontSize: 12, fontFace: F, bold: true, color: ACCENT, charSpacing: 2, margin: 0 });
  s.addText(title, { x: M, y: 0.62, w: W - 2 * M, h: 0.75, fontSize: 30, fontFace: F, bold: true, color: INK, margin: 0 });
}
function card(s, x, y, w, h, fill = WHITE) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, rectRadius: 0.09, shadow: shadow(), line: { color: "E3E9ED", width: 0.75 } });
}
function stat(s, x, y, w, num, label, color = ACCENT) {
  s.addText(num, { x, y, w, h: 0.72, fontSize: 40, fontFace: F, bold: true, color, align: "center", margin: 0 });
  s.addText(label, { x, y: y + 0.72, w, h: 0.55, fontSize: 12.5, fontFace: F, color: MUTED, align: "center", margin: 0 });
}

/* ============ S1 — BÌA ============ */
let s = p.addSlide();
s.background = { color: DARK };
crackMotif(s, 1.0);
s.addText("BÁO CAO KHÓA LUẬN TỐT NGHIỆP", { x: M, y: 1.75, w: W - 2 * M, h: 0.4, fontSize: 15, fontFace: F, bold: true, color: "9FB3BE", charSpacing: 3, align: "center", margin: 0 });
s.addText([
  { text: "PHÁT HIỆN VÀ PHÂN LOẠI VẾT NỨT BỀ MẶT\n", options: { color: WHITE } },
  { text: "CÔNG TRÌNH XÂY DỰNG TỪ ẢNH 2D", options: { color: WHITE } },
], { x: 0.8, y: 2.25, w: W - 1.6, h: 1.5, fontSize: 34, fontFace: F, bold: true, align: "center", margin: 0 });
s.addText("Ứng dụng học sâu 2 giai đoạn: YOLOv8s-seg + quy tắc ACI 224R-01 / TCVN 9381:2012", { x: 1.5, y: 3.85, w: W - 3, h: 0.4, fontSize: 15, fontFace: F, italic: true, color: ACCENT, align: "center", margin: 0 });
s.addText("Crack Severity AI", { x: 1.5, y: 4.35, w: W - 3, h: 0.55, fontSize: 24, fontFace: F, bold: true, color: WHITE, align: "center", margin: 0 });
s.addText([
  { text: "GVHD:  TS. Phan Xuân Thiện", options: { breakLine: true } },
  { text: "Sinh viên:  Ngô Kim Thành — 23521447   ·   Trần Công Thành — 23521463", options: {} },
], { x: 2.5, y: 5.45, w: W - 5, h: 0.95, fontSize: 14.5, fontFace: F, color: "C9D6DD", align: "center", paraSpaceAfter: 6, margin: 0 });
s.addText("TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN — ĐHQG TP.HCM   ·   2026", { x: 2.5, y: 6.75, w: W - 5, h: 0.35, fontSize: 11.5, fontFace: F, color: "7E93A0", align: "center", margin: 0 });

/* ============ S2 — NỘI DUNG ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Nội dung", "Trình bày theo luồng nghiêm cứu");
const agenda = [
  ["01", "Đặt vấn đề, mục tiêu và kiến trúc 2 giai đoạn"],
  ["02", "Dữ liệu: thu thập, lọc domain, chuẩn hóa và kiểm soát chất lượng"],
  ["03", "Phase 1 — Huấn luyện, chẩn đoán, so sánh SOTA, hard-case vân đá"],
  ["04", "Phase 2 — Thang ACI/TCVN, đo lường kiểm chứng, phân loại đa yếu tố"],
  ["05", "Hệ thống kiểm định tích hợp + DevOps + kiểm thử tự động"],
  ["06", "Kết luận, hạn chế và hướng phát triển"],
];
agenda.forEach((it, i) => {
  const y = 1.62 + i * 0.92;
  s.addText(it[0], { x: M, y, w: 1.0, h: 0.8, fontSize: 30, fontFace: F, bold: true, color: i % 2 ? PRIMARY : ACCENT, margin: 0 });
  s.addText(it[1], { x: M + 1.15, y: y + 0.1, w: W - 2 * M - 1.3, h: 0.6, fontSize: 17, fontFace: F, color: INK, valign: "middle", margin: 0 });
  if (i < 5) s.addShape(p.shapes.LINE, { x: M + 1.15, y: y + 0.82, w: W - 2 * M - 1.3, h: 0, line: { color: "E3E9ED", width: 0.75 } });
});

/* ============ S3 — ĐẶT VẤN ĐỀ ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Đặt vấn đề", "Kiểm định vết nứt thủ công: chậm, chủ quan, thiếu chuẩn hóa");
const pains = [
  ["Chậm và tốn nhân lực", "Kỹ sư phải kiểm tra thủ công từng cấu kiện, ảnh chụp về xử lý hàng giờ."],
  ["Đánh giá chủ quan", "Mức độ nghiêm trọng phụ thuộc kinh nghiệm; thiếu chuẩn hóa theo tiêu chuẩn."],
  ["Bỏ sót vết mảnh", "Vết nứt siêu mảnh (1–3px) dễ bị bỏ qua — chính là tín hiệu tiến triển sớm."],
];
pains.forEach((it, i) => {
  const y = 1.72 + i * 1.5;
  card(s, M, y, 6.6, 1.3, SOFT);
  s.addText(it[0], { x: M + 0.3, y: y + 0.14, w: 6, h: 0.4, fontSize: 15.5, fontFace: F, bold: true, color: INK, margin: 0 });
  s.addText(it[1], { x: M + 0.3, y: y + 0.56, w: 6, h: 0.62, fontSize: 12.5, fontFace: F, color: MUTED, margin: 0 });
});
s.addImage({ path: `${IMG}/img_goc.jpg`, x: 7.6, y: 1.72, w: 5.2, h: 3.67, rounding: false, sizing: { type: "cover", w: 5.2, h: 3.67 } });
s.addText("Ảnh kiểm định thực tế — vết nứt bề mặt bê tông (bộ DeepCrack)", { x: 7.6, y: 5.5, w: 5.2, h: 0.35, fontSize: 11, fontFace: F, color: MUTED, margin: 0 });
s.addText([
  { text: "Mục tiêu: ", options: { bold: true, color: ACCENT } },
  { text: "hệ thống học sâu 2 giai đoạn — phát hiện vết nứt tự động và phân loại mức độ theo tiêu chuẩn ACI 224R-01 / TCVN 9381:2012, giải thích được với hội đồng.", options: { color: INK } },
], { x: M, y: 6.45, w: W - 2 * M, h: 0.7, fontSize: 14.5, fontFace: F, margin: 0 });

/* ============ S4 — KIẾN TRÚC ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Kiến trúc", "Cascade 2 giai đoạn trên ảnh 2D");
const arch = [
  ["Ảnh 2D hiện trường", SOFT, INK, "Điện thoại / UAV\ncột · tường · dầm · sàn"],
  ["PHASE 1 — Phát hiện", PRIM_LT, INK, "YOLOv8s-seg\nmask + box vết nứt"],
  ["PHASE 2 — Mức độ", PRIM_LT, INK, "Lớp A (morphology)\n+ Lớp B (ngữ cảnh)"],
  ["L0 – L3severity", PRIM_LT, INK, "ACI 224R-01\nTCVN 9381:2012"],
  ["Hồ sơ & báo cáo", SOFT, INK, "Lưu hồ sơ\nBáo cáo PDF"],
];
arch.forEach((a, i) => {
  const x = M + i * 2.52, w = 2.28, y = 2.3, h = 1.9;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: a[1] }, rectRadius: 0.08, shadow: shadow(), line: { color: "E3E9ED", width: 0.75 } });
  s.addText(a[0], { x: x + 0.12, y: y + 0.18, w: w - 0.24, h: 0.6, fontSize: 13.5, fontFace: F, bold: true, color: INK, align: "center", margin: 0 });
  s.addText(a[3], { x: x + 0.12, y: y + 0.85, w: w - 0.24, h: 0.9, fontSize: 11.5, fontFace: F, color: MUTED, align: "center", margin: 0 });
  if (i < 4) s.addText("→", { x: x + w - 0.04, y: y + 0.68, w: 0.36, h: 0.5, fontSize: 22, fontFace: F, bold: true, color: ACCENT, align: "center", margin: 0 });
});
s.addText([
  { text: "Nguyên tắc thiết kế:  ", options: { bold: true, color: INK } },
  { text: "Phase 1 trả mask giúp Phase 2 đo đặc trưng hình học; Phase 2 là quy tắc minh bạch (rule-based) bám tiêu chuẩn — không hộp đen.", options: { color: MUTED } },
], { x: M, y: 4.75, w: W - 2 * M, h: 0.6, fontSize: 13.5, fontFace: F, margin: 0 });
card(s, M, 5.55, W - 2 * M, 1.35, SOFT);
s.addText([
  { text: "Phạm vi:  ", options: { bold: true, color: INK } },
  { text: "ảnh 2D, bề mặt bê tông/tường/kết cấu nhà–cầu. Không dùng ảnh 3D, ảnh nhiệt, cảm biến chuyên dụng. Đối tượng thí điểm: công trình nhà cao tầng.", options: { color: MUTED } },
], { x: M + 0.3, y: 5.85, w: W - 2 * M - 0.6, h: 0.8, fontSize: 13, fontFace: F, margin: 0 });

/* ============ S5 — DỮ LIỆU ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Dữ liệu", "Thu thập, lọc domain và phân vai");
stat(s, 0.7, 1.55, 2.7, "15.947", "ảnh train+val+test chuẩn hóa");
stat(s, 3.6, 1.55, 2.7, "4.048", "ảnh nền (negative) chống báo giả");
stat(s, 6.5, 1.55, 2.7, "303", "ảnh hard-case vân đá (riêng)");
stat(s, 9.4, 1.55, 2.7, "66.000+", "ảnh thô khảo sát ban đầu", PRIMARY);
const tbl = [
  [{ text: "Bộ dữ liệu", options: { bold: true, color: WHITE, fill: { color: PRIMARY } } },
   { text: "Vai trò", options: { bold: true, color: WHITE, fill: { color: PRIMARY } } },
   { text: "Ghi chú", options: { bold: true, color: WHITE, fill: { color: PRIMARY } } }],
  ["DeepCrack · Ultralytics CrackSeg · 3DCrack_v1", "Train chính", "Bê tông / tường"],
  ["Rissbilder · Volker · Eugen (crack_seg)", "Train chính", "Vết mảnh dày — khó nhất"],
  ["Roads_and_Bridges", "Train chính", "Cầu / kết cấu ngoài"],
  ["METU Neg · SDNET UD/UW · noncrack", "Negative (nhãn rỗng)", "Chống báo giả"],
  ["CFD · CRACK500 · CrackTree · GAPS384", "LOẠI", "Mặt đường — ngoài phạm vi"],
  ["forest · Sylvie (vân đá)", "Hard-case test", "Đo FP, không train"],
];
s.addTable(tbl, { x: M, y: 3.15, w: W - 2 * M, colW: [5.4, 2.9, 3.93], fontSize: 12, fontFace: F, color: INK, border: { pt: 0.75, color: "E3E9ED" }, rowH: 0.42, valign: "middle", margin: 0.06 });
s.addText("Quyết định then chốt: loại bỏ toàn bộ bộ mặt đường để tập trung domain công trình building — giải quyết bài toán đa domain của baseline.", { x: M, y: 6.55, w: W - 2 * M, h: 0.55, fontSize: 12.5, fontFace: F, italic: true, color: MUTED, margin: 0 });

/* ============ S6 — CHUẨN HÓA ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Chất lượng dữ liệu", "Pipeline chuẩn hóa 5 bước — kết quả kiểm chứng 100%");
const steps6 = [
  ["1", "Quét khớp 1:1", "20.956 file: ảnh ↔ mask/txt khớp tên chính xác"],
  ["2", "Chuẩn hóa nhãn", "Mọi nguồn về YOLO polygon thuần, class 0 = crack"],
  ["3", "Khử trùng", "MD5 bỏ ảnh trùng; sửa 14 đụng tên (Windows FS)"],
  ["4", "Audit nhãn", "118 pseudo-GT conf≥0.6 bổ sung cho Rissbilder/Volker"],
  ["5", "Chia split", "80/10/10 hash deterministic — val/test bất biến"],
];
steps6.forEach((it, i) => {
  const x = M + i * 2.52, w = 2.3;
  s.addShape(p.shapes.OVAL, { x: x + w / 2 - 0.35, y: 1.75, w: 0.7, h: 0.7, fill: { color: i === 1 || i === 3 ? ACCENT : PRIMARY } });
  s.addText(it[0], { x: x + w / 2 - 0.35, y: 1.75, w: 0.7, h: 0.7, fontSize: 22, fontFace: F, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0 });
  s.addText(it[1], { x, y: 2.6, w, h: 0.4, fontSize: 13.5, fontFace: F, bold: true, color: INK, align: "center", margin: 0 });
  s.addText(it[2], { x: x + 0.05, y: 3.0, w: w - 0.1, h: 1.0, fontSize: 11, fontFace: F, color: MUTED, align: "center", margin: 0 });
});
card(s, M, 4.35, W - 2 * M, 2.2, SOFT);
s.addText("Kiểm chứng tự động sau mỗi lần build", { x: M + 0.35, y: 4.55, w: 8, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: INK, margin: 0 });
const checks6 = [
  "Image–label khớp 100% (0 thiếu / 0 thừa) ở cả train, val, test",
  "Polygon thuần — xử lý triệt để lỗi “labels mix segment and detection rows”",
  "Toàn bộ nhãn tiếng Việt + báo cáo Excel xuất kèm từng file (20.956 dòng)",
];
s.addText(checks6.map((t, i) => ({ text: t, options: { bullet: bu(), breakLine: i < 2 } })), { x: M + 0.4, y: 5.0, w: W - 2 * M - 0.8, h: 1.4, fontSize: 12.5, fontFace: F, color: MUTED, paraSpaceAfter: 7, margin: 0 });

/* ============ S7 — PHASE 1 KẾT QUẢ ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Phase 1 — kết quả", "Mô hình v1: YOLOv8s-seg · Kaggle T4 · 100 epochs");
const m7 = [["0.823", "Precision", OK], ["0.565", "Recall", WARN], ["0.599", "mAP50", PRIMARY], ["0.999", "Độ chính xác mức ảnh", OK], ["0.655", "F1 instance", PRIMARY]];
m7.forEach((m, i) => {
  const x = M + i * 2.5, w = 2.3;
  card(s, x, 1.6, w, 1.5, i === 3 ? "EAF6EE" : WHITE);
  s.addText(m[0], { x, y: 1.75, w, h: 0.65, fontSize: 30, fontFace: F, bold: true, color: m[2], align: "center", margin: 0 });
  s.addText(m[1], { x, y: 2.42, w, h: 0.5, fontSize: 11.5, fontFace: F, color: MUTED, align: "center", margin: 0 });
});
s.addImage({ path: `${IMG}/img_dudoan.jpg`, x: M, y: 3.45, w: 4.6, h: 3.25, sizing: { type: "cover", w: 4.6, h: 3.25 } });
s.addText("Kết quả suy luận thực tế — mask màu + confidence", { x: M, y: 6.75, w: 4.6, h: 0.35, fontSize: 11, fontFace: F, color: MUTED, margin: 0 });
s.addText([
  { text: "Điểm nhấn", options: { bold: true, color: INK, breakLine: true } },
  { text: "Precision 82.3% — ít báo nhầm trên công trình thật", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Độ chính xác mức ảnh 99.9% — vượt kỳ vọng 95%", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Tốc độ 5.9ms/ảnh trên T4 — đủ chạy thời gian thực", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Điểm cần cải thiện", options: { bold: true, color: INK, breakLine: true } },
  { text: "Recall 56.5% — bỏ sót vết mảnh; 75.5% vết bỏ sót có cạnh < 32px", options: { bullet: bu(), color: MUTED } },
], { x: 5.6, y: 3.55, w: 7.2, h: 3.2, fontSize: 13.5, fontFace: F, paraSpaceAfter: 8, margin: 0 });

/* ============ S8 — CHẨN ĐOÁN THEO NGUỒN ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Phase 1 — chẩn đoán", "Hiệu năng theo từng nguồn dữ liệu (F1, IoU ≥ 0.5)");
s.addChart(p.charts.BAR, [{
  name: "F1", labels: ["Roads&Bridges", "DeepCrack", "3DCrack", "Ultralytics", "crack_seg/DC", "Rissbilder", "Volker"],
  values: [0.841, 0.764, 0.649, 0.811, 0.610, 0.544, 0.499],
}], {
  x: M, y: 1.7, w: 7.6, h: 4.6, barDir: "bar",
  chartColors: ["46626E", "46626E", "46626E", "46626E", "46626E", "E8590C", "E8590C"],
  varyColors: true, showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK, dataLabelFontSize: 11,
  catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, valAxisMaxVal: 1, valAxisMinVal: 0,
  valGridLine: { color: "EDF1F4", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false,
  chartArea: { fill: { color: "FFFFFF" } }, catAxisLabelFontSize: 11, dataLabelFormatCode: "0.00",
});
card(s, 8.5, 1.7, 4.28, 4.6, SOFT);
s.addText("Phát hiện then chốt", { x: 8.8, y: 1.95, w: 3.7, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "Mạnh: Ultralytics (0.81), Roads & Bridges (0.84)", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Yếu: Volker (0.50), Rissbilder (0.54) — vết mảnh dày đặc", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Audit nhãn xác nhận KHÔNG phải do thiếu nhãn — chỉ 118/5.7k vết", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Kết luận: tăng độ phân giải + tiền xử lý là hướng đúng", options: { bullet: bu(), color: INK } },
], { x: 8.8, y: 2.4, w: 3.75, h: 3.7, fontSize: 12.5, fontFace: F, paraSpaceAfter: 9, margin: 0 });
s.addText("Nguồn: scripts/evaluate_phase1.py — 1.491 ảnh test, 3.531 vết GT", { x: M, y: 6.5, w: 8, h: 0.35, fontSize: 11, fontFace: F, color: MUTED, margin: 0 });

/* ============ S9 — SOTA ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Định vị quốc tế", "So sánh với bài tổng quan SOTA (arXiv:2508.10256, Georgia Tech 2025)");
s.addChart(p.charts.BAR, [
  { name: "Mô hình của nhóm", labels: ["DeepCrack", "3DCrack"], values: [0.819, 0.708] },
  { name: "ResUNet (bài báo, 100% data)", labels: ["DeepCrack", "3DCrack"], values: [0.833, 0.795] },
], {
  x: M, y: 1.75, w: 7.4, h: 4.4, barDir: "col", barGapWidthPct: 60,
  chartColors: ["E8590C", "46626E"], showValue: true, dataLabelPosition: "outEnd",
  dataLabelColor: INK, dataLabelFontSize: 11.5, dataLabelFormatCode: "0.000",
  catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, valAxisMaxVal: 1, valAxisMinVal: 0,
  valGridLine: { color: "EDF1F4", size: 0.5 }, catGridLine: { style: "none" },
  showLegend: true, legendPos: "b", legendColor: MUTED, legendFontSize: 11,
  chartArea: { fill: { color: "FFFFFF" } }, catAxisLabelFontSize: 12,
});
card(s, 8.35, 1.75, 4.43, 4.4, SOFT);
s.addText("Đọc kết quả", { x: 8.65, y: 2.0, w: 3.8, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "DeepCrack: đạt 98.3% mức ResUNet — ngang tầm baseline quốc tế dù train đa nguồn", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "3DCrack: −11% — vết mảnh 1–2px, mask head của YOLO decode ở 1/4 độ phân giải", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Metric pixel-level IoU/P/R/Dice cài đặt đúng chuẩn bài báo", options: { bullet: bu(), color: MUTED } },
], { x: 8.65, y: 2.45, w: 3.85, h: 3.5, fontSize: 12.5, fontFace: F, paraSpaceAfter: 9, margin: 0 });
s.addText("Lưu ý: chia tập khác bài báo (hash 80/10/10 đa nguồn) — số mang tính tham chiếu tương đối, cùng loại metric.", { x: M, y: 6.45, w: W - 2 * M, h: 0.4, fontSize: 11, fontFace: F, color: MUTED, margin: 0 });

/* ============ S10 — A/B + HARD CASE ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Thực nghiệm đối chứng", "Cấu hình A (640px) vs B (1280px) + hard-case vân đá");
const t10 = [
  [{ text: "Chỉ số", options: { bold: true, color: WHITE, fill: { color: PRIMARY } } },
   { text: "A — 640px", options: { bold: true, color: WHITE, fill: { color: PRIMARY } } },
   { text: "B — 1280px", options: { bold: true, color: WHITE, fill: { color: PRIMARY } } }],
  ["F1 instance (best conf)", { text: "0.655", options: { bold: true, color: OK } }, "0.514"],
  ["Precision @conf 0.45", { text: "0.731", options: { bold: true, color: OK } }, "0.608"],
  ["FP trên ảnh nền", "2.2%", { text: "1.5%", options: { bold: true, color: OK } }],
  ["FP ảnh vân đá @0.45", { text: "24.1%", options: { bold: true, color: OK } }, "36.3%"],
];
s.addTable(t10, { x: M, y: 1.7, w: 7.3, colW: [3.1, 2.1, 2.1], fontSize: 12.5, fontFace: F, color: INK, border: { pt: 0.75, color: "E3E9ED" }, rowH: 0.5, valign: "middle", margin: 0.06 });
card(s, 8.15, 1.7, 4.63, 3.0, SOFT);
s.addText("Quyết định", { x: 8.45, y: 1.92, w: 4, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "Giữ cấu hình A làm model chính — F1 cao hơn trên toàn dải ngưỡng", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Checkpoint B là bản last của lượt resume — bài học quy trình tải best.pt", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "B ưu thế FP nền (1.5%) — dữ liệu negative phát huy đúng vai trò", options: { bullet: bu(), color: MUTED } },
], { x: 8.45, y: 2.35, w: 4.05, h: 2.2, fontSize: 12, fontFace: F, paraSpaceAfter: 8, margin: 0 });
card(s, M, 5.0, W - 2 * M, 1.85, "FDF1E8");
s.addText([
  { text: "Hard-case vân đá (303 ảnh, 509 vết — không có trong train):  ", options: { bold: true, color: INK } },
  { text: "model A @conf 0.45 → precision 73.1% trên vết đá, recall 39.5% (vật liệu lạ); 24.1% ảnh bị báo nhầm ≥1 vết — giảm còn 21.5% ở conf 0.55. Khuyến nghị: gộp một phần vân đá làm hard-negative trong v3.", options: { color: "5A4632" } },
], { x: M + 0.3, y: 5.25, w: W - 2 * M - 0.6, h: 1.4, fontSize: 13, fontFace: F, margin: 0 });

/* ============ S11 — THANG 4 MỨC ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Phase 2 — thang mức độ", "4 mức bám ACI 224R-01 và TCVN 9381:2012");
const lv = [
  ["L0", "Hairline", "< 0.1 mm", "Vô hại — do co ngót", "Theo dõi, ghi nhận", "94A3B8"],
  ["L1", "Minor", "0.1 – 0.3 mm", "Ảnh hưởng thẩm mỹ nhẹ", "Theo dõi định kỳ", "16A34A"],
  ["L2", "Moderate", "0.3 – 1.0 mm", "Vượt ngưỡng phơi nhiễm", "Đánh giá, lên kế hoạch xử lý", "D97706"],
  ["L3", "Severe", "≥ 1.0 mm", "Nguy cơ kết cấu / thấm", "Kiểm tra kết cấu ngay", "DC2626"],
];
lv.forEach((l, i) => {
  const x = M + i * 3.12, w = 2.88, y = 1.75, h = 3.1;
  card(s, x, y, w, h, WHITE);
  s.addShape(p.shapes.OVAL, { x: x + 0.22, y: y + 0.2, w: 0.62, h: 0.62, fill: { color: l[5] } });
  s.addText(l[0], { x: x + 0.22, y: y + 0.2, w: 0.62, h: 0.62, fontSize: 17, fontFace: F, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0 });
  s.addText(l[1], { x: x + 0.98, y: y + 0.22, w: w - 1.1, h: 0.35, fontSize: 15.5, fontFace: F, bold: true, color: INK, margin: 0 });
  s.addText(l[2], { x: x + 0.98, y: y + 0.58, w: w - 1.1, h: 0.32, fontSize: 12.5, fontFace: F, bold: true, color: l[5], margin: 0 });
  s.addText(l[3], { x: x + 0.22, y: y + 1.15, w: w - 0.44, h: 0.75, fontSize: 12, fontFace: F, color: MUTED, margin: 0 });
  s.addShape(p.shapes.LINE, { x: x + 0.22, y: y + 2.0, w: w - 0.44, h: 0, line: { color: "E3E9ED", width: 0.75 } });
  s.addText([{ text: "Hành động: ", options: { bold: true, color: INK } }, { text: l[4], options: { color: MUTED } }],
    { x: x + 0.22, y: y + 2.1, w: w - 0.44, h: 0.9, fontSize: 11.5, fontFace: F, margin: 0 });
});
s.addText([
  { text: "Quy đổi mm:  ", options: { bold: true, color: INK } },
  { text: "bề rộng lớn nhất (px) × GSD (mm/pixel) — GSD hiệu chuẩn ngay trên ảnh bằng công cụ đo 2 điểm vào vật chuẩn (thước, gạch, cửa).", options: { color: MUTED } },
], { x: M, y: 5.15, w: W - 2 * M, h: 0.6, fontSize: 13.5, fontFace: F, margin: 0 });
card(s, M, 5.9, W - 2 * M, 1.0, SOFT);
s.addText([
  { text: "Đo lường đã kiểm chứng:  ", options: { bold: true, color: OK } },
  { text: "bề rộng lệch ≤ 1px · chiều dài 0px · góc 0° · branching đúng — đạt giới hạn lượng tử hóa pixel (mask chuẩn hóa kích thước đã biết).", options: { color: MUTED } },
], { x: M + 0.3, y: 6.12, w: W - 2 * M - 0.6, h: 0.6, fontSize: 13, fontFace: F, margin: 0 });

/* ============ S12 — ĐA YẾU TỐ ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Phase 2 — phân loại đa yếu tố", "Bề rộng một mình KHÔNG đủ — vết dài mảnh, vết đậm cạn phải phân biệt được");
const f12 = [
  ["Neo chuẩn ACI", "Bề rộng MAX × GSD tra thang L0–L3", PRIMARY],
  ["+1  Chiều dài ≥ 300 mm", "Hư hỏng lan rộng — vết dài nguy cơ tiến triển", ACCENT],
  ["+1  Độ đậm ≥ 30%", "Tối hơn nền cục bộ — proxy cho độ sâu vết", ACCENT],
  ["+1  Lớp B: nhánh / đa mặt phẳng", "Mạng lưới nứt, giao cắt cấu kiện", ACCENT],
  ["L3 tuyệt đối  Xuyên cấu kiện", "Kỹ sư đánh dấu trực tiếp trên hồ sơ", BAD],
];
f12.forEach((f, i) => {
  const y = 1.68 + i * 0.78;
  card(s, M, y, 7.3, 0.66, i === 0 ? PRIM_LT : WHITE);
  s.addText(f[0], { x: M + 0.28, y: y + 0.08, w: 3.4, h: 0.5, fontSize: 13.5, fontFace: F, bold: true, color: f[2], valign: "middle", margin: 0 });
  s.addText(f[1], { x: M + 3.8, y: y + 0.08, w: 3.35, h: 0.5, fontSize: 11.5, fontFace: F, color: MUTED, valign: "middle", margin: 0 });
});
card(s, 8.2, 1.68, 4.58, 4.6, "FDF1E8");
s.addText("Case kiểm chứng", { x: 8.5, y: 1.9, w: 4, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "Vết DÀI NHƯNG MẢNH", options: { bold: true, color: INK, breakLine: true } },
  { text: "Bề rộng 0.15 mm → neo ACI = L1 Minor", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Chiều dài 750 mm ≥ 300 → +1", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "Độ đậm 50% ≥ 30% → +1 (nghi sâu)", options: { bullet: bu(), breakLine: true, color: MUTED } },
  { text: "= L3 Severe", options: { bold: true, color: BAD, breakLine: true } },
  { text: "Cùng vết đó nếu NHẠT (contrast 10%) chỉ lên L2 — hệ thống phân biệt được đậm/nhạt theo đúng yêu cầu kiểm định.", options: { color: MUTED } },
], { x: 8.5, y: 2.35, w: 4.0, h: 3.7, fontSize: 12.5, fontFace: F, paraSpaceAfter: 8, margin: 0 });
s.addText("Mỗi yếu tố +1, tối đa +2, chặn L3 · lý do hiển thị trên từng chip mức độ trong app · ngưỡng 300mm/30% hiệu chuẩn tiếp trên ảnh thực.", { x: M, y: 6.55, w: W - 2 * M, h: 0.55, fontSize: 12, fontFace: F, color: MUTED, margin: 0 });

/* ============ S13 — HỆ THỐNG ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Hệ thống kiểm định", "Ứng dụng web hoàn chỉnh 6 phân hệ — quy trình công ty");
const sys = [
  ["📊", "Dashboard", "KPI, biểu đồ xu hướng, hồ sơ gần đây"],
  ["📋", "Phiếu kiểm tra", "Wizard 4 bước · chụp/tải ảnh · AI tự phân tích"],
  ["🗂️", "Hồ sơ kiểm định", "Lọc, tìm kiếm, thumbnail, xuất CSV"],
  ["📈", "Phase 2 · Mức độ", "Thang ACI/TCVN + máy tính phân loại trực tiếp"],
  ["🧪", "Model", "Benchmark test + so SOTA minh bạch"],
  ["⚙️", "Thiết lập", "Thang, tham số, vai trò kỹ sư/quản lý"],
];
sys.forEach((it, i) => {
  const x = M + (i % 3) * 4.15, y = 1.72 + Math.floor(i / 3) * 1.85, w = 3.9, h = 1.62;
  card(s, x, y, w, h, WHITE);
  s.addText(it[0], { x: x + 0.25, y: y + 0.18, w: 0.6, h: 0.6, fontSize: 24, margin: 0 });
  s.addText(it[1], { x: x + 0.95, y: y + 0.2, w: w - 1.1, h: 0.4, fontSize: 14.5, fontFace: F, bold: true, color: INK, margin: 0 });
  s.addText(it[2], { x: x + 0.95, y: y + 0.62, w: w - 1.15, h: 0.85, fontSize: 11.5, fontFace: F, color: MUTED, margin: 0 });
});
card(s, M, 5.7, W - 2 * M, 1.2, SOFT);
s.addText([
  { text: "Công nghệ:  ", options: { bold: true, color: INK } },
  { text: "FastAPI · Ultralytics YOLOv8s-seg · SQLite · Vanilla JS · Docker · GitHub Actions CI/CD (deploy Hugging Face Spaces) · 28 unit test + 7 bước E2E tự động.", options: { color: MUTED } },
], { x: M + 0.3, y: 5.95, w: W - 2 * M - 0.6, h: 0.75, fontSize: 13, fontFace: F, margin: 0 });

/* ============ S14 — LUỒNG HỒ SƠ ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Hệ thống kiểm định", "Luồng hồ sơ chuẩn quy trình kiểm định công ty");
const flow = [
  ["1", "Kỹ sư tạo phiếu", "Chọn dự án/tầng/\ncấu kiện · chụp ảnh"],
  ["2", "AI phân tích", "Phát hiện mask\n+ đo đặc trưng px"],
  ["3", "Phase 2 tự động", "Chip L0–L3\n+ tick xuyên cấu kiện"],
  ["4", "Nộp hồ sơ", "Trạng thái\nCHỜ DUYỆT"],
  ["5", "Quản lý duyệt", "DUYỆT → khóa hồ sơ\nghi người + thời điểm"],
  ["6", "Báo cáo PDF", "Letterhead + chữ ký kép\nin/xuất lưu hành"],
];
flow.forEach((f, i) => {
  const x = M + i * 2.12, w = 1.95, y = 1.9;
  card(s, x, y, w, 1.95, i === 4 ? PRIM_LT : WHITE);
  s.addShape(p.shapes.OVAL, { x: x + 0.14, y: y + 0.14, w: 0.44, h: 0.44, fill: { color: ACCENT } });
  s.addText(f[0], { x: x + 0.14, y: y + 0.14, w: 0.44, h: 0.44, fontSize: 15, fontFace: F, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0 });
  s.addText(f[1], { x: x + 0.14, y: y + 0.66, w: w - 0.28, h: 0.4, fontSize: 12.5, fontFace: F, bold: true, color: INK, margin: 0 });
  s.addText(f[2], { x: x + 0.14, y: y + 1.06, w: w - 0.28, h: 0.8, fontSize: 10.5, fontFace: F, color: MUTED, margin: 0 });
  if (i < 5) s.addText("→", { x: x + w + 0.0, y: y + 0.72, w: 0.22, h: 0.4, fontSize: 16, fontFace: F, bold: true, color: ACCENT, align: "center", margin: 0 });
});
card(s, M, 4.35, W - 2 * M, 2.35, SOFT);
s.addText("Tính năng nổi bật trong luồng", { x: M + 0.3, y: 4.55, w: 8, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: INK, margin: 0 });
const f14 = [
  "Overlay tương tác: bấm từng vết nứt ↔ tô sáng trên ảnh; bật/tắt mask & khung; tải PNG kết quả",
  "Hiệu chuẩn GSD trực quan: bấm 2 điểm vào vật chuẩn → mọi vết tự phân loại lại tức thì",
  "Báo cáo kiểm định PDF: letterhead, mã CSA-xxxxx, mức độ từng vết, 2 ô chữ ký (kỹ sư / quản lý)",
  "Xuất CSV toàn bộ hồ sơ phục vụ thống kê và lưu trữ lâu dài",
];
s.addText(f14.map((t, i) => ({ text: t, options: { bullet: bu(), breakLine: i < 3 } })), { x: M + 0.35, y: 5.0, w: W - 2 * M - 0.7, h: 1.6, fontSize: 12.5, fontFace: F, color: MUTED, paraSpaceAfter: 7, margin: 0 });

/* ============ S15 — DEVOPS ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "DevOps & chất lượng", "Quy trình công ty: tự động hóa từ commit đến deploy");
const dv = [
  ["GitHub Actions CI", "Mỗi push: ruff lint → pytest → import check; fail = chặn deploy"],
  ["CD → HF Spaces", "CI pass trên main → tự build Docker image và deploy công khai"],
  ["Docker hoá", "1 lệnh docker compose up: API + model + DB + giao diện"],
  ["Kiểm thử", "28 unit test (đặc trưng, severity, API) + E2E 7 bước thực tế"],
];
dv.forEach((it, i) => {
  const x = M + (i % 2) * 6.2, y = 1.72 + Math.floor(i / 2) * 1.45, w = 5.95, h = 1.25;
  card(s, x, y, w, h, WHITE);
  s.addText(it[0], { x: x + 0.28, y: y + 0.14, w: w - 0.56, h: 0.38, fontSize: 14.5, fontFace: F, bold: true, color: INK, margin: 0 });
  s.addText(it[1], { x: x + 0.28, y: y + 0.55, w: w - 0.56, h: 0.6, fontSize: 12, fontFace: F, color: MUTED, margin: 0 });
});
card(s, M, 4.85, W - 2 * M, 2.0, SOFT);
s.addText("Kiểm chứng end-to-end (mỗi lần thay đổi)", { x: M + 0.3, y: 5.05, w: 9, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: INK, margin: 0 });
const e15 = [
  "predict (mask + severity theo GSD)  →  lưu hồ sơ SQLite  →  phê duyệt vai quản lý",
  "tái phân loại hồ sơ đã lưu từ px (không cần model)  →  báo cáo in PDF  →  dashboard cập nhật",
];
s.addText(e15.map((t, i) => ({ text: t, options: { bullet: bu(), breakLine: i < 1 } })), { x: M + 0.35, y: 5.5, w: W - 2 * M - 0.7, h: 1.1, fontSize: 12.5, fontFace: F, color: MUTED, paraSpaceAfter: 8, margin: 0 });

/* ============ S16 — KẾT QUẢ TỔNG HỢP ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Kết quả tổng hợp", "Những con số định nghĩa dự án");
const k16 = [
  ["99.9%", "độ chính xác mức ảnh\n(kỳ vọng 95%)", OK],
  ["0.819", "Dice DeepCrack —\nngang baseline SOTA", ACCENT],
  ["±1px", "sai số đo bề rộng vết\n(đã kiểm chứng)", OK],
  ["0.513", "F1 trên vân đá\n(out-of-domain)", PRIMARY],
  ["1.5–2.2%", "FP trên ảnh nền", PRIMARY],
  ["28+7", "unit test + E2E pass", OK],
];
k16.forEach((k, i) => {
  const x = M + (i % 3) * 4.15, y = 1.75 + Math.floor(i / 3) * 2.1, w = 3.9, h = 1.85;
  card(s, x, y, w, h, WHITE);
  s.addText(k[0], { x, y: y + 0.15, w, h: 0.8, fontSize: 40, fontFace: F, bold: true, color: k[2], align: "center", margin: 0 });
  s.addText(k[1], { x: x + 0.2, y: y + 1.05, w: w - 0.4, h: 0.7, fontSize: 12, fontFace: F, color: MUTED, align: "center", margin: 0 });
});
s.addText("Tất cả số liệu tái lập được từ script trong repo (evaluate_phase1, compare_with_sota, validate_measurements, eval_hard_cases).", { x: M, y: 6.35, w: W - 2 * M, h: 0.5, fontSize: 12, fontFace: F, italic: true, color: MUTED, margin: 0 });

/* ============ S17 — HẠN CHẾ ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Thẳng thắn", "Hạn chế và bài học rút ra");
const lim = [
  ["Recall vết siêu mảnh", "75.5% vết bỏ sót có cạnh < 32px — giới hạn của imgsz 640 và mask head 1/4 độ phân giải."],
  ["v2 @1280 chưa đạt", "Checkpoint resume (epoch ~74) cho F1 0.514 < 0.655 — bài học quy trình tải đúng best.pt."],
  ["Vân đá chưa gộp train", "24.1% ảnh vân đá vẫn bị báo nhầm — cần hard-negative trong v3."],
  ["Độ đậm phụ thuộc ánh sáng", "Contrast cần chụp ánh sáng đều; ngưỡng 300mm/30% cần hiệu chuẩn trên ảnh thực."],
];
lim.forEach((it, i) => {
  const y = 1.7 + i * 1.28;
  card(s, M, y, W - 2 * M, 1.1, i % 2 ? WHITE : SOFT);
  s.addText(it[0], { x: M + 0.3, y: y + 0.12, w: 3.6, h: 0.85, fontSize: 14, fontFace: F, bold: true, color: INK, valign: "middle", margin: 0 });
  s.addText(it[1], { x: M + 4.1, y: y + 0.12, w: W - 2 * M - 4.4, h: 0.85, fontSize: 12.5, fontFace: F, color: MUTED, valign: "middle", margin: 0 });
});

/* ============ S18 — HƯỚNG PHÁT TRIỂN ============ */
s = p.addSlide(); s.background = { color: WHITE };
head(s, "Hướng phát triển", "Lộ trình cụ thể cho giai đoạn tiếp theo");
const rd = [
  ["v3 — Huấn luyện", "Gộp hard-negative vân đá + train 960px từ weight v1 + tải đúng best.pt; mục tiêu FP vân đá < 10%"],
  ["Phase 2 nâng cao", "Lớp B đúng nghĩa: segmentation mặt phẳng cấu kiện; học thống kê khi có dữ liệu mm thực đo"],
  ["Mở rộng dữ liệu", "Pseudo-label kho class-only 45k+ ảnh (METU/SDNET Positive) khi v3 đạt chuẩn"],
  ["Triển khai thực tế", "Đồng bộ UAV/chụp định kỳ; theo dõi tiến triển vết nứt giữa các lần kiểm tra"],
];
rd.forEach((it, i) => {
  const y = 1.72 + i * 1.28;
  s.addText(`0${i + 1}`, { x: M, y, w: 0.95, h: 1.05, fontSize: 34, fontFace: F, bold: true, color: i % 2 ? PRIMARY : ACCENT, margin: 0 });
  s.addText(it[0], { x: M + 1.1, y: y + 0.05, w: 3.6, h: 1.0, fontSize: 15, fontFace: F, bold: true, color: INK, margin: 0 });
  s.addText(it[1], { x: M + 4.85, y: y + 0.05, w: W - 2 * M - 4.95, h: 1.0, fontSize: 12.5, fontFace: F, color: MUTED, margin: 0 });
  if (i < 3) s.addShape(p.shapes.LINE, { x: M + 1.1, y: y + 1.08, w: W - 2 * M - 1.15, h: 0, line: { color: "E3E9ED", width: 0.75 } });
});

/* ============ S19 — KẾT LUẬN ============ */
s = p.addSlide(); s.background = { color: DARK };
crackMotif(s, 0.9);
s.addText("KẾT LUẬN", { x: M, y: 1.7, w: W - 2 * M, h: 0.4, fontSize: 14, fontFace: F, bold: true, color: "9FB3BE", charSpacing: 3, margin: 0 });
const con = [
  ["Phase 1 hoàn thiện", "Pipeline dữ liệu chuẩn hóa 100% · mô hình v1 ngang baseline SOTA trên DeepCrack · hệ thống đo lường đa nguồn"],
  ["Phase 2 end-to-end", "Thang ACI 224R-01/TCVN 9381:2012 · đo lường kiểm chứng ±1px · phân loại đa yếu tố giải thích được"],
  ["Sản phẩm thật", "Hệ thống kiểm định 6 phân hệ · luồng phê duyệt · báo cáo PDF · DevOps đầy đủ · 28+7 kiểm thử tự động"],
];
con.forEach((c, i) => {
  const y = 2.3 + i * 1.35;
  s.addText(`0${i + 1}`, { x: M, y, w: 1.0, h: 1.1, fontSize: 40, fontFace: F, bold: true, color: ACCENT, margin: 0 });
  s.addText(c[0], { x: M + 1.2, y: y + 0.02, w: 4.3, h: 1.1, fontSize: 17, fontFace: F, bold: true, color: WHITE, margin: 0 });
  s.addText(c[1], { x: M + 5.6, y: y + 0.02, w: W - 2 * M - 5.7, h: 1.1, fontSize: 12.5, fontFace: F, color: "C9D6DD", margin: 0 });
  if (i < 2) s.addShape(p.shapes.LINE, { x: M, y: y + 1.18, w: W - 2 * M, h: 0, line: { color: "31424E", width: 0.75 } });
});
s.addText("Mọi kết quả đều tái lập được bằng script công khai trong repo — nền tảng cho vòng v3 và nghiệm thu đề tài.", { x: M, y: 6.5, w: W - 2 * M, h: 0.5, fontSize: 13, fontFace: F, italic: true, color: "9FB3BE", margin: 0 });

/* ============ S20 — CẢM ƠN ============ */
s = p.addSlide(); s.background = { color: DARK };
crackMotif(s, 1.2);
s.addText("TRÂN TRỌNG CẢM ƠN HỘI ĐỒNG", { x: 0.8, y: 3.0, w: W - 1.6, h: 0.9, fontSize: 40, fontFace: F, bold: true, color: WHITE, align: "center", margin: 0 });
s.addText("Sẵn sàng trả lời câu hỏi — kèm demo trực tiếp hệ thống", { x: 1.5, y: 4.1, w: W - 3, h: 0.5, fontSize: 16, fontFace: F, color: ACCENT, align: "center", margin: 0 });
s.addText("Ngô Kim Thành — 23521447   ·   Trần Công Thành — 23521463   ·   GVHD: TS. Phan Xuân Thiện", { x: 1.5, y: 5.6, w: W - 3, h: 0.4, fontSize: 13, fontFace: F, color: "9FB3BE", align: "center", margin: 0 });

p.writeFile({ fileName: "D:/crack_severity_ai/outputs/pptx/CrackSeverity_AI_BaoVeKhoaLuan.pptx" })
  .then(() => console.log("PPTX done"))
  .catch((e) => { console.error(e); process.exit(1); });
