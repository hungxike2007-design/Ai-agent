def get_report_prompt(data_summary, style_preference):
    # Định nghĩa văn phong dựa trên đối tượng đọc báo cáo 
    styles = {
        "Giám đốc": "NGẮN GỌN, SÚC TÍCH. Tập trung vào doanh thu, dự báo và lời khuyên chiến lược.",
        "Kỹ thuật": "CHI TIẾT, ĐẦY ĐỦ. Trình bày thông số thống kê (Mean, Median), lỗi dữ liệu và bảng biểu."
    }
    
    selected_instruction = styles.get(style_preference, "Phổ thông")
    
    prompt = f"""
    Bạn là AI Agent phân tích dữ liệu chuyên nghiệp.
    Dữ liệu: {data_summary}
    Đối tượng đọc báo cáo: {style_preference}.
    Yêu cầu văn phong: {selected_instruction}
    
    Nhiệm vụ: Viết nội dung nhận xét, đánh giá và dự báo dựa trên dữ liệu.
    """
    return prompt