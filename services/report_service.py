def get_report_prompt(data_summary, style_preference):
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
    """
    return prompt