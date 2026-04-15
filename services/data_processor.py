import pandas as pd

def get_cleaning_suggestions(df):
    suggestions = []
    
    # Kiểm tra ô trống (Null) - [cite: 6]
    null_data = df.isnull().sum()
    for col, count in null_data.items():
        if count > 0:
            suggestions.append({
                "column": col,
                "issue": f"Có {count} ô trống",
                "action": "Điền giá trị trung bình hoặc xóa dòng"
            })
            
    # Kiểm tra dữ liệu rác (Ví dụ: giá trị âm ở cột số lượng) - 
    for col in df.select_dtypes(include=['number']).columns:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            suggestions.append({
                "column": col,
                "issue": f"Có {neg_count} giá trị âm",
                "action": "Xóa dòng rác hoặc lấy giá trị tuyệt đối"
            })
    return suggestions