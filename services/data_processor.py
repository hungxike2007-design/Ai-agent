import pandas as pd

def get_cleaning_suggestions(df):
    # Logic: Al tự động phát hiện lỗi dữ liệu (ô trống, sai định dạng) 
    suggestions = []
    
    # Kiểm tra ô trống (Null) [cite: 7, 157]
    null_data = df.isnull().sum()
    for col, count in null_data.items():
        if count > 0:
            suggestions.append({
                "column": col,
                "issue": f"Có {count} dòng bị trống",
                "action": "Điền giá trị trung bình hoặc Xóa dòng"
            })
            
    # Kiểm tra dữ liệu rác (Ví dụ: cột 'Số lượng' có giá trị âm) 
    for col in df.select_dtypes(include=['number']).columns:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            suggestions.append({
                "column": col,
                "issue": f"Phát hiện {neg_count} giá trị âm không hợp lệ",
                "action": "Xóa dòng rác"
            })
    return suggestions