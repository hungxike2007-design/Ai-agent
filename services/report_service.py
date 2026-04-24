# ── CÁC STYLE GỌN (mỗi style < 80 token) ────────────────────────────────────
_STYLES = {
    "Kỹ thuật":  "Phân tích thống kê: tổng quan (dòng/cột/null), bảng Mean/Median/Std/Min/Max cho cột số, xu hướng, outlier, kết luận và khuyến nghị.",
    "Quản lý":   "Executive Summary ngắn gọn: 3 điểm nổi bật, kết quả chính (bullet), rủi ro, khuyến nghị hành động.",
    "Học thuật": "Báo cáo nghiên cứu: Giới thiệu → Phương pháp → Kết quả (bảng N/Mean±SD/Min-Max) → Bàn luận → Kết luận.",
    "Kinh doanh":"Phân tích KPI: bảng KPI (chỉ số/giá trị/đánh giá 🟢🟡🔴), hiệu suất top/bottom, rủi ro, cơ hội tăng trưởng, action items.",
    "Phổ thông": "Ngôn ngữ dễ hiểu: tóm tắt 1 câu, 3-5 con số đáng chú ý, giải thích ý nghĩa, gợi ý thực tế.",
}

# ── QUY TẮC CHUNG (chỉ cần 1 lần, ngắn gọn) ─────────────────────────────────
_RULES = "Bắt đầu ngay nội dung. Dùng Markdown (##, **, |bảng|, -). Chỉ dùng số liệu có thật. Không viết lời mở đầu/kết thúa thừa."


def get_report_prompt(data_summary: str, style_preference: str) -> str:
    """Tạo prompt tối ưu token cho AI phân tích báo cáo."""
    instruction = _STYLES.get(style_preference, _STYLES["Phổ thông"])
    return (
        f"AI phân tích dữ liệu. {_RULES}\n\n"
        f"Style: {style_preference} — {instruction}\n\n"
        f"Dữ liệu:\n{data_summary}"
    )


def get_available_styles():
    """Trả về danh sách các phong cách báo cáo có sẵn."""
    return list(_STYLES.keys())