import pandas as pd

def get_cleaning_suggestions(df):
<<<<<<< Updated upstream
    suggestions = []
    
    # Kiểm tra ô trống (Null) - [cite: 6]
=======
    # Logic: Al tự động phát hiện lỗi dữ liệu (ô trống, sai định dạng) 
    suggestions = []
    
    # Kiểm tra ô trống (Null) [cite: 7, 157]
>>>>>>> Stashed changes
    null_data = df.isnull().sum()
    for col, count in null_data.items():
        if count > 0:
            suggestions.append({
                "column": col,
<<<<<<< Updated upstream
                "issue": f"Có {count} ô trống",
                "action": "Điền giá trị trung bình hoặc xóa dòng"
            })
            
    # Kiểm tra dữ liệu rác (Ví dụ: giá trị âm ở cột số lượng) - 
=======
                "issue": f"Có {count} dòng bị trống",
                "action": "Điền giá trị trung bình hoặc Xóa dòng"
            })
            
    # Kiểm tra dữ liệu rác (Ví dụ: cột 'Số lượng' có giá trị âm) 
>>>>>>> Stashed changes
    for col in df.select_dtypes(include=['number']).columns:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            suggestions.append({
                "column": col,
<<<<<<< Updated upstream
                "issue": f"Có {neg_count} giá trị âm",
                "action": "Xóa dòng rác hoặc lấy giá trị tuyệt đối"
=======
                "issue": f"Phát hiện {neg_count} giá trị âm không hợp lệ",
                "action": "Xóa dòng rác"
>>>>>>> Stashed changes
            })
    return suggestions