def get_report_prompt(data_summary, style_preference):
<<<<<<< Updated upstream
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
=======
    # Thiết lập tham số cho Al để định hướng phân tích chuẩn xác hơn [cite: 9]
    styles = {
        "Giám đốc": "Ngắn gọn, tập trung vào số liệu tổng quát và dự báo doanh thu.", # 
        "Kỹ thuật": "Chi tiết, trình bày đầy đủ bảng biểu và thông số kỹ thuật (Mean, Median)." # 
    }
    
    selected_style = styles.get(style_preference, "Phổ thông")
    
    # Prompt yêu cầu AI viết nội dung nhận xét và đánh giá 
    prompt = f"""
    Dữ liệu: {data_summary}
    Đối tượng: {style_preference}. Phong cách: {selected_style}
    Nhiệm vụ: Phân tích xu hướng và sinh báo cáo tự động.
>>>>>>> Stashed changes
    """
    return prompt