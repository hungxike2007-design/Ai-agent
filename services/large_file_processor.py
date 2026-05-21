import pandas as pd
import os

def convert_excel_to_csv_chunked(xlsx_path, csv_path, chunk_size=50000):
    """
    Đọc file Excel và ghi ra CSV.
    """
    if os.path.exists(csv_path):
        os.remove(csv_path)
        
    try:
        # Pandas không hỗ trợ chunksize cho read_excel, tạm thời đọc toàn bộ
        df = pd.read_excel(xlsx_path)
        df.to_csv(csv_path, index=False)
        return True
    except Exception as e:
        print(f"Lỗi khi convert: {e}")
        return False

def read_sample_from_csv(csv_path, n_rows=50):
    """
    Đọc một sample từ file CSV mà không load toàn bộ.
    """
    try:
        df_sample = pd.read_csv(csv_path, nrows=n_rows)
        return df_sample
    except Exception as e:
        print(f"Lỗi khi đọc sample từ CSV: {e}")
        return pd.DataFrame()

def load_dataframe_from_file(file_path, **kwargs):
    """
    Đọc DataFrame từ file (Excel hoặc CSV) dựa vào extension.
    """
    if file_path.lower().endswith('.csv'):
        return pd.read_csv(file_path, **kwargs)
    else:
        return pd.read_excel(file_path, **kwargs)
