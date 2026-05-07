# ── CÁC STYLE GỌN (Phát triển theo hướng phổ thông cho mọi lĩnh vực) ────────────────
_STYLES = {
    "Kỹ thuật":  "Phân tích thống kê toàn diện: bao gồm cấu trúc dữ liệu, các chỉ số đo lường trung tâm (Mean, Median), độ phân tán (Std, Range), phát hiện outlier và các khuyến nghị kỹ thuật.",
    "Quản lý":   "Tóm tắt điều hành (Executive Summary): Tập trung vào các kết quả then chốt, những điểm nổi bật quan trọng nhất, rủi ro tiềm ẩn và các đề xuất hành động ngắn gọn.",
    "Học thuật": "Báo cáo nghiên cứu chuyên sâu: Cấu trúc theo định dạng hàn lâm gồm Giới thiệu, Phương pháp luận, Phân tích dữ liệu chi tiết, Thảo luận kết quả và Kết luận khoa học.",
    "Kinh doanh":"Phân tích Hiệu suất & Chỉ số (KPI): Tập trung vào việc đánh giá các mục tiêu, so sánh hiệu suất giữa các nhóm, xác định cơ hội tăng trưởng và tối ưu hóa quy trình.",
    "Phổ thông": "Ngôn ngữ đại chúng: Sử dụng cách diễn đạt đơn giản, tránh thuật ngữ chuyên môn, tập trung vào việc giải thích ý nghĩa của các con số một cách dễ hiểu nhất.",
    "Xu hướng":  "Phân tích Xu hướng & Biến động: Tập trung vào sự thay đổi của dữ liệu theo thời gian hoặc theo nhóm, xác định các quy luật lặp lại và dự báo khả năng trong tương lai.",
    "So sánh":   "Phân tích So sánh & Đối chiếu: Thực hiện việc so sánh đa chiều giữa các danh mục, xác định sự khác biệt đáng kể và tìm ra các điểm tương quan quan trọng.",
    "Giải pháp": "Phân tích Giải pháp & Đề xuất: Tập trung vào việc tìm ra nguyên nhân gốc rễ của các vấn đề trong dữ liệu và đưa ra các giải pháp thực tế, có tính ứng dụng cao.",
}

# ── QUY TẮC ĐỊNH DẠNG (áp dụng skill Report Generation + Technical Writing) ──────
_FORMAT_RULES = """[QUY TẮC ĐỊNH DẠNG BẮT BUỘC]
1. Bắt đầu ngay nội dung phân tích, KHÔNG viết lời chào hay mở đầu thừa.
2. Dùng Markdown chuẩn:
   - ## cho tiêu đề mục chính
   - **bold** cho số liệu quan trọng (chỉ dùng ở ngoài bảng)
   - Bảng Markdown |Cột 1|Cột 2|. LƯU Ý: KHÔNG sử dụng dấu ** bên trong các ô của bảng.
   - Danh sách - cho các điểm phân tích
3. Mỗi mục phải có SỐ LIỆU CỤ THỂ từ dữ liệu (không nói chung chung).
4. Kết thúc bằng mục "## Khuyến nghị" với các đề xuất hành động cụ thể.
5. PHẢI xuất ít nhất 1 bảng Markdown tóm tắt chỉ số chính."""

# ── CẤU TRÚC BÁO CÁO THEO TỪNG STYLE ────────────────────────────────────────────
_STRUCTURE = {
    "Kỹ thuật": "## Tổng quan dữ liệu\n## Thống kê mô tả\n## Phân tích phân phối\n## Phát hiện bất thường\n## Khuyến nghị",
    "Quản lý": "## Tóm tắt điều hành\n## Các chỉ số then chốt\n## Rủi ro & Cảnh báo\n## Đề xuất hành động",
    "Học thuật": "## Giới thiệu\n## Phương pháp phân tích\n## Kết quả chi tiết\n## Thảo luận\n## Kết luận",
    "Kinh doanh": "## Tổng quan hiệu suất\n## Bảng KPI chính\n## Phân tích theo nhóm\n## Cơ hội & Rủi ro\n## Khuyến nghị",
    "Phổ thông": "## Dữ liệu nói gì?\n## Những điểm nổi bật\n## Điều cần lưu ý\n## Gợi ý tiếp theo",
    "Xu hướng": "## Tổng quan xu hướng\n## Phân tích biến động\n## Quy luật lặp lại\n## Dự báo\n## Khuyến nghị",
    "So sánh": "## Tổng quan so sánh\n## Bảng đối chiếu\n## Điểm khác biệt nổi bật\n## Tương quan\n## Khuyến nghị",
    "Giải pháp": "## Phát hiện vấn đề\n## Phân tích nguyên nhân\n## Bảng đánh giá mức độ\n## Giải pháp đề xuất\n## Kế hoạch hành động",
}


def get_report_prompt(data_summary: str, style_preference: str) -> str:
    """
    Tạo prompt tối ưu cho AI phân tích báo cáo.
    Áp dụng skills: Report Generation, Technical Writing, Data Analysis.
    - Chỉ dẫn cấu trúc rõ ràng → AI trả đúng format
    - Yêu cầu bảng Markdown → Báo cáo chuyên nghiệp
    - Quy tắc ngắn gọn → Tiết kiệm token prompt
    """
    instruction = _STYLES.get(style_preference, _STYLES["Phổ thông"])
    structure = _STRUCTURE.get(style_preference, _STRUCTURE["Phổ thông"])

    return (
        f"Bạn là chuyên gia phân tích dữ liệu. Viết báo cáo bằng tiếng Việt.\n\n"
        f"{_FORMAT_RULES}\n\n"
        f"Phong cách: {style_preference} — {instruction}\n\n"
        f"Cấu trúc báo cáo PHẢI theo:\n{structure}\n\n"
        f"Dữ liệu cần phân tích:\n{data_summary}"
    )


def get_available_styles():
    """Trả về danh sách các phong cách báo cáo có sẵn."""
    return list(_STYLES.keys())