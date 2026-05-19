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


# ── HỆ THỐNG TEMPLATE BÁO CÁO TỰ DO ──────────────────────────────────────────
_REPORT_TEMPLATES = {
    "full_analysis": {
        "name": "📊 Phân tích Toàn diện",
        "desc": "Báo cáo đầy đủ: thống kê, biểu đồ, nhận xét, khuyến nghị",
        "sections": ["overview", "statistics", "chart_insight", "detail", "recommendation"],
        "prompt_suffix": "Viết báo cáo TOÀN DIỆN gồm: Tổng quan, Thống kê chi tiết, Phân tích biểu đồ, Nhận xét chuyên sâu và Khuyến nghị hành động."
    },
    "executive": {
        "name": "📋 Tóm tắt Điều hành",
        "desc": "Ngắn gọn, tập trung KPI và đề xuất cho lãnh đạo",
        "sections": ["kpi", "highlights", "recommendation"],
        "prompt_suffix": "Viết TÓM TẮT ĐIỀU HÀNH ngắn gọn (tối đa 500 từ): Chỉ số then chốt (KPI), Điểm nổi bật quan trọng nhất, và 3-5 đề xuất hành động cụ thể."
    },
    "academic": {
        "name": "🎓 Nghiên cứu Học thuật",
        "desc": "Cấu trúc hàn lâm: Giới thiệu → Phương pháp → Kết quả → Kết luận",
        "sections": ["introduction", "methodology", "results", "discussion", "conclusion"],
        "prompt_suffix": "Viết BÁO CÁO HỌC THUẬT theo cấu trúc: I. Giới thiệu, II. Phương pháp phân tích, III. Kết quả chi tiết (với bảng số liệu), IV. Thảo luận, V. Kết luận."
    },
    "dashboard_kpi": {
        "name": "📈 Dashboard KPI",
        "desc": "Dạng bảng KPI nhanh, dễ scan, phù hợp trình chiếu",
        "sections": ["kpi_table", "trend", "alert"],
        "prompt_suffix": "Tạo BÁO CÁO DẠNG DASHBOARD: 1 bảng KPI chính (Markdown table), Phân tích xu hướng ngắn gọn, và Cảnh báo/Alert nếu có chỉ số bất thường. Ưu tiên dùng BẢNG và BULLET POINTS."
    },
    "quick_summary": {
        "name": "⚡ Tóm tắt Nhanh",
        "desc": "3-5 điểm chính, tiết kiệm token tối đa",
        "sections": ["summary"],
        "prompt_suffix": "Tóm tắt SIÊU NGẮN GỌN (tối đa 200 từ): Liệt kê 3-5 điểm quan trọng nhất từ dữ liệu dưới dạng bullet points."
    },
    "data_quality": {
        "name": "🔍 Đánh giá Chất lượng Dữ liệu",
        "desc": "Tập trung vào dữ liệu lỗi, thiếu sót, giá trị ngoại lai",
        "sections": ["missing_data", "outliers", "cleaning_recommendation"],
        "prompt_suffix": "Viết báo cáo ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU: Thống kê chi tiết các giá trị bị thiếu (missing values), phát hiện các giá trị ngoại lai (outliers), những bất thường trong dữ liệu và đưa ra đề xuất làm sạch dữ liệu cụ thể."
    },
    "comparative": {
        "name": "⚖️ Phân tích So sánh",
        "desc": "So sánh các nhóm, danh mục hoặc khoảng thời gian",
        "sections": ["comparison_table", "differences", "conclusion"],
        "prompt_suffix": "Viết báo cáo PHÂN TÍCH SO SÁNH: Nhóm dữ liệu theo các danh mục chính hoặc thời gian. Tạo bảng so sánh các chỉ số giữa các nhóm. Nhấn mạnh sự khác biệt lớn nhất và nguyên nhân tiềm ẩn."
    },
    "trend_forecast": {
        "name": "🔮 Phân tích Xu hướng & Dự báo",
        "desc": "Phân tích chuỗi thời gian và dự đoán tương lai",
        "sections": ["historical_trend", "seasonality", "forecast"],
        "prompt_suffix": "Viết báo cáo PHÂN TÍCH XU HƯỚNG: Xác định các mẫu (patterns) và xu hướng tăng/giảm qua thời gian. Tìm ra tính mùa vụ (nếu có) và đưa ra những dự báo hoặc giả định hợp lý cho tương lai dựa trên dữ liệu hiện tại."
    },
    "customer_insight": {
        "name": "👥 Thấu hiểu Hành vi (Insight)",
        "desc": "Phân tích đặc điểm, hành vi và phân khúc",
        "sections": ["demographics", "behavior", "segments", "action_plan"],
        "prompt_suffix": "Viết báo cáo THẤU HIỂU HÀNH VI: Phân tích sâu về đặc điểm của các đối tượng trong dữ liệu. Chia đối tượng thành các phân khúc (segments) khác nhau. Nêu bật hành vi đặc trưng của từng phân khúc và đề xuất chiến lược tương ứng."
    },
    "financial_audit": {
        "name": "💰 Kiểm toán & Hiệu quả Tài chính",
        "desc": "Tập trung vào doanh thu, chi phí, lợi nhuận, rủi ro",
        "sections": ["revenue_cost", "profit_margin", "financial_risk"],
        "prompt_suffix": "Viết báo cáo TÀI CHÍNH & KIỂM TOÁN: Tập trung tối đa vào các chỉ số liên quan đến dòng tiền (doanh thu, chi phí, lợi nhuận). Đánh giá tỷ suất lợi nhuận, phát hiện các rủi ro tài chính hoặc các khoản chi phí bất thường cần kiểm soát."
    }
}


def get_available_templates():
    """Trả về danh sách template cho UI."""
    return {k: {"name": v["name"], "desc": v["desc"]} for k, v in _REPORT_TEMPLATES.items()}


def get_template_report_prompt(data_summary: str, template_key: str, style_preference: str = "Phổ thông") -> str:
    """
    Tạo prompt báo cáo dựa trên template đã chọn.
    Kết hợp template structure + style preference + format rules.
    """
    template = _REPORT_TEMPLATES.get(template_key, _REPORT_TEMPLATES["full_analysis"])
    instruction = _STYLES.get(style_preference, _STYLES["Phổ thông"])

    return (
        f"Bạn là chuyên gia phân tích dữ liệu. Viết báo cáo bằng tiếng Việt.\n\n"
        f"{_FORMAT_RULES}\n\n"
        f"Phong cách: {style_preference} — {instruction}\n\n"
        f"YÊU CẦU TEMPLATE: {template['prompt_suffix']}\n\n"
        f"Dữ liệu cần phân tích:\n{data_summary}"
    )