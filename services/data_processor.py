import pandas as pd

def get_cleaning_suggestions(df):
    suggestions = []
    
    # Kiểm tra ô trống (Null) 
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

def generate_auto_chart(df, file_id):
    """
    Tự động phân tích và tạo một biểu đồ cơ bản dựa trên dữ liệu.
    Ưu tiên tạo Bar Chart cho các cột phân loại (Categorical).
    """
    import matplotlib
    matplotlib.use('Agg') # Không hiển thị UI
    import matplotlib.pyplot as plt
    import os

    chart_path = f"static/charts/chart_{file_id}.png"
    full_path = os.path.join(os.getcwd(), chart_path)
    
    # Xóa file cũ nếu có
    if os.path.exists(full_path):
        os.remove(full_path)

    # Tìm cột categorical (object/string) có số giá trị độc nhất <= 15
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    best_col = None
    for col in cat_cols:
        nunique = df[col].nunique()
        if 2 <= nunique <= 15:
            best_col = col
            break

    plt.figure(figsize=(8, 5))
    
    if best_col:
        # Nếu có cột categorical, đếm số lượng và vẽ Bar chart
        counts = df[best_col].value_counts()
        counts.plot(kind='bar', color='#10a37f', edgecolor='none')
        plt.title(f"Phân bố theo: {best_col}", fontsize=14, pad=15)
        plt.xlabel(best_col)
        plt.ylabel("Số lượng")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(full_path, transparent=True)
        plt.close()
        return "/" + chart_path
    
    # Nếu không có cột text phù hợp, thử tìm cột số
    num_cols = df.select_dtypes(include=['number']).columns
    if len(num_cols) > 0:
        first_num_col = num_cols[0]
        df[first_num_col].plot(kind='hist', bins=20, color='#10a37f', edgecolor='white')
        plt.title(f"Phân bố tần suất: {first_num_col}", fontsize=14, pad=15)
        plt.xlabel(first_num_col)
        plt.ylabel("Tần suất")
        plt.tight_layout()
        plt.savefig(full_path, transparent=True)
        plt.close()
        return "/" + chart_path

    # Nếu không vẽ được
    plt.close()
    return None