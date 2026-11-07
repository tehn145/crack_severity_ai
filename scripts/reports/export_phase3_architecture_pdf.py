"""
Script tạo file PDF thiết kế kiến trúc Phase 3 Structural Health Monitoring
Hỗ trợ Unicode tiếng Việt đầy đủ với font Arial của Windows
"""
import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Đăng ký font tiếng Việt chuẩn Arial
pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Italic', 'C:/Windows/Fonts/ariali.ttf'))

pdf_path = Path('d:/crack_severity_ai/outputs/reports/Kien_Truc_Phase_3_He_Thong_Giam_Dinh_Ket_Cau.pdf')
pdf_path.parent.mkdir(parents=True, exist_ok=True)

doc = SimpleDocTemplate(
    str(pdf_path),
    pagesize=A4,
    rightMargin=36,
    leftMargin=36,
    topMargin=36,
    bottomMargin=36
)

styles = getSampleStyleSheet()

# Custom styles tiếng Việt
title_style = ParagraphStyle(
    'DocTitle',
    fontName='Arial-Bold',
    fontSize=18,
    leading=22,
    textColor=colors.HexColor('#1E3A8A'),
    alignment=1, # Center
    spaceAfter=6
)

subtitle_style = ParagraphStyle(
    'DocSubtitle',
    fontName='Arial-Italic',
    fontSize=11,
    leading=14,
    textColor=colors.HexColor('#475569'),
    alignment=1,
    spaceAfter=15
)

h1_style = ParagraphStyle(
    'H1',
    fontName='Arial-Bold',
    fontSize=13,
    leading=17,
    textColor=colors.HexColor('#0F172A'),
    spaceBefore=12,
    spaceAfter=6
)

body_style = ParagraphStyle(
    'Body',
    fontName='Arial',
    fontSize=10,
    leading=14,
    textColor=colors.HexColor('#1E293B'),
    spaceAfter=6
)

bullet_style = ParagraphStyle(
    'Bullet',
    fontName='Arial',
    fontSize=9.5,
    leading=13.5,
    textColor=colors.HexColor('#334155'),
    leftIndent=15,
    spaceAfter=4
)

callout_style = ParagraphStyle(
    'Callout',
    fontName='Arial-Bold',
    fontSize=10,
    leading=14,
    textColor=colors.HexColor('#B45309')
)

story = []

# Header Banner
story.append(Paragraph("DỰ ÁN NGHIÊN CỨU & KHÓA LUẬN TỐT NGHIỆP: CRACK SEVERITY AI", subtitle_style))
story.append(Paragraph("KIẾN TRÚC CHI TIẾT PHASE 3:<br/>HỆ THỐNG GIÁM ĐỊNH MỨC ĐỘ NGUY HIỂM & NGUY CƠ SẬP ĐỔ KẾT CẤU TOÀN DIỆN", title_style))
story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=12))

# Giới thiệu
intro_text = (
    "<b>Tầm nhìn chiến lược:</b> Hệ thống không dừng lại ở việc khoanh vùng vết nứt trên từng bức ảnh đơn lẻ, "
    "mà phát triển thành một <b>Hệ thống Chuyên gia Giám định Sức khỏe Kết cấu Công trình (Structural Health Monitoring - SHM)</b>. "
    "Kỹ sư chỉ cần tải lên một thư mục chứa toàn bộ ảnh chụp hiện trường (ví dụ: toàn bộ tầng 1), "
    "hệ thống sẽ tự động tổng hợp không gian, hợp nhất đa tổn thương và đưa ra dự báo nguy cơ suy thoái kết cấu công trình."
)
story.append(Paragraph(intro_text, body_style))
story.append(Spacer(1, 8))

# Phần 1: Bốn Trụ Cột Đột Phá
story.append(Paragraph("1. BỐN TÍNH NĂNG ĐỘT PHÁ CỦA PHASE 3", h1_style))

p1 = (
    "<b>1.1. Xử lý Trừ hao Chồng lấn Không gian (Image Overlap Deduplication):</b><br/>"
    "• Khi chụp hiện trường, các ảnh chụp góc nghiêng hoặc lia máy sẽ có vùng giao thoa trùng lặp (Overlapping).<br/>"
    "• <i>Giải pháp:</i> Ứng dụng thuật toán so khớp đặc trưng hình học <b>ORB Feature Matching + Ma trận Homography</b> để nhận diện vùng chồng lấn giữa các bức ảnh liên kề.<br/>"
    "• Tự động trừ phần diện tích giao thoa (Intersection Area) để tính chính xác 100% tỷ lệ hư hại thực tế trên toàn bộ diện tích sàn/vách quét mà không bị phóng đại do chụp trùng lặp."
)
story.append(Paragraph(p1, bullet_style))

p2 = (
    "<b>1.2. Phân cấp Vị trí Cấu kiện Chịu Lực (Critical Structural Risk Multiplier):</b><br/>"
    "• Nứt 1mm ở tường ngăn trang trí chỉ gây mất thẩm mỹ, nhưng nứt 0.5mm ở chân cột chịu lực tầng 1 có thể làm sập cả tòa nhà.<br/>"
    "• <i>Trọng số nguy hiểm theo vị trí kết cấu:</i><br/>"
    "   - <b>Chân cột chịu lực / Trụ chính (Columns):</b> Hệ số nhân mức độ nguy hiểm = <b>3.0×</b><br/>"
    "   - <b>Nút khung giao Dầm - Cột (Beam-Column Joints):</b> Hệ số nhân mức độ nguy hiểm = <b>3.5×</b> (vùng chịu ứng suất cắt tối đa)<br/>"
    "   - <b>Bụng dầm chính / Kèo vượt nhịp (Girders):</b> Hệ số nhân mức độ nguy hiểm = <b>2.5×</b><br/>"
    "   - <b>Tường ngăn / Vách thứ cấp:</b> Hệ số chuẩn = <b>1.0×</b>."
)
story.append(Paragraph(p2, bullet_style))

p3 = (
    "<b>1.3. Mô hình Tích hợp Đa Hư hỏng Liên hoàn (Hybrid Defect Interaction):</b><br/>"
    "• Kết hợp song song kết quả từ <b>Phase 1.2 (Chuyên gia Nứt)</b> và <b>Phase 2 (Chuyên gia Bong tróc & Lộ cốt thép)</b>.<br/>"
    "• Trong cơ học kết cấu, khi vết nứt xuất hiện đồng thời cùng mảng bong tróc và lộ cốt thép bị gỉ, kết cấu bê tông đã mất hoàn toàn khả năng chịu lực dính bám.<br/>"
    "• Hệ thống thiết lập ma trận tương tác: Vùng không gian xuất hiện cả <b>Crack + Spalling + Exposed Rebar</b> sẽ tự động kích hoạt mức cảnh báo phá hủy kết cấu giòn khẩn cấp (Compound Failure)."
)
story.append(Paragraph(p3, bullet_style))

p4 = (
    "<b>1.4. Bộ Chỉ Số Định Lượng Dự Báo Sụp Đổ Toàn Bộ Công Trình:</b><br/>"
    "• <b>Damage-to-Area Ratio (DAR):</b> Tỷ lệ phần trăm diện tích hư hỏng trên toàn bộ không gian quét.<br/>"
    "• <b>Structural Collapse Index (SCI):</b> Chỉ số rủi ro sập đổ công trình (tính từ 0% đến 100%) kết hợp giữa diện tích nứt, độ mở rộng nứt (W mm), vùng lộ cốt thép và vị trí chịu lực chính."
)
story.append(Paragraph(p4, bullet_style))
story.append(Spacer(1, 8))

# Bảng phân cấp
story.append(Paragraph("2. BẢNG PHÂN CẤP NGUY CƠ SẬP ĐỔ & HÀNH ĐỘNG KHUYẾN NGHỊ", h1_style))

table_data = [
    ["Cấp độ Rủi ro", "Chỉ số SCI", "Hiện trạng Kết cấu Nhận diện", "Khuyến nghị Kỹ thuật / Hành động"],
    ["Cấp 1: AN TOÀN", "< 15%", "Nứt vi mô bề mặt co ngót, không lộ thép", "Theo dõi định kỳ 6 tháng, sơn phủ chống thấm"],
    ["Cấp 2: CẢNH BÁO", "15% - 35%", "Nứt dầm/sàn trung bình (0.2-0.5mm), bong tróc nhỏ", "Trám keo Epoxy chống ẩm xâm thực cốt thép"],
    ["Cấp 3: NGUY HIỂM", "35% - 60%", "Nứt kết cấu (>0.5mm) tại dầm/cột, lộ cốt thép gỉ", "Chống cọc phụ trợ, dán sợi Carbon (CFRP) gia cố dầm/cột"],
    ["Cấp 4: KHẨN CẤP", ">= 60%", "Vỡ nát chân cột chính, đứt gãy liên kết dầm-cột", "SƠ TÁN KHẨN CẤP! Nguy cơ sập đổ cục bộ tầng 1"]
]

col_widths = [85, 65, 180, 190]
t = Table(table_data, colWidths=col_widths)
t.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
    ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8.5),
    ('ALIGN', (0, 0), (1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#ECFDF5')), # Xanh lá
    ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#FEFCE8')), # Vàng
    ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#FFF7ED')), # Cam
    ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#FEF2F2')), # Đỏ
    ('TEXTCOLOR', (0, 4), (0, 4), colors.HexColor('#DC2626')),
    ('FONTNAME', (0, 4), (0, 4), 'Arial-Bold'),
]))
story.append(t)
story.append(Spacer(1, 12))

# Phần 3: Lộ trình và Giá trị
story.append(Paragraph("3. GIÁ TRỊ CẠNH TRANH CHO BUỔI BẢO VỆ KHÓA LUẬN", h1_style))
diff_text = (
    "<b>Tại sao đề tài này sẽ đạt điểm tuyệt đối?</b><br/>"
    "• <b>Vượt xa các bài toán đồ án thông thường:</b> Các nhóm khác chỉ dừng ở mức nhận diện có/không trên từng ảnh mạng internet. Đề tài của bạn giải quyết trọn vẹn quy trình kiểm định ngoài đời thực: <b>Quét thư mục toàn bộ tầng nhà ➔ Trừ hao không gian chồng lấn ➔ Nhận diện vị trí cấu kiện chịu lực chính ➔ Đánh giá rủi ro sập đổ theo tiêu chuẩn xây dựng</b>.<br/>"
    "• <b>Sản phẩm hoàn chỉnh:</b> Gồm 2 Model AI chuyên biệt (P1.2 nứt đa bề mặt + P2 bong tróc cốt thép) được tích hợp trong một Web App Demo trực quan, hỗ trợ xuất báo cáo PDF giám định cho chủ đầu tư."
)
story.append(Paragraph(diff_text, body_style))

# Xây dựng file PDF
doc.build(story)
print(f"Đã tạo file PDF thành công tại: {pdf_path}")
