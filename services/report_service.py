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

# ── QUY TẮC CHUNG (chỉ cần 1 lần, ngắn gọn) ─────────────────────────────────
_RULES = "Bắt đầu ngay nội dung. Dùng Markdown (##, **, |bảng|, -). Chỉ dùng số liệu có thật. Không viết lời mở đầu/kết thúc thừa."


def get_report_prompt(data_summary: str, style_preference: str) -> str:
    """Tạo prompt tối ưu token cho AI phân tích báo cáo."""
    instruction = _STYLES.get(style_preference, _STYLES["Phổ thông"])
    return (
        f"Bạn là một chuyên gia phân tích dữ liệu chuyên nghiệp. {_RULES}\n\n"
        f"Phong cách báo cáo: {style_preference} — {instruction}\n\n"
        f"Dữ liệu cần phân tích:\n{data_summary}"
    )


def get_available_styles():
    """Trả về danh sách các phong cách báo cáo có sẵn."""
    return list(_STYLES.keys())