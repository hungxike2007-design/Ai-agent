import pandas as pd
import os

def convert_excel_to_csv_chunked(xlsx_path, csv_path, chunk_size=50000):
    """
    Đọc file Excel theo từng chunk và ghi ra CSV để tránh tràn RAM.
    """
    if os.path.exists(csv_path):
        os.remove(csv_path)
        
    try:
        # Sử dụng engine openpyxl để hỗ trợ đọc chunksize tốt nhất cho xlsx
        chunks = pd.read_excel(xlsx_path, chunksize=chunk_size, engine='openpyxl')
        first_chunk = True
        
        for chunk in chunks:
            # Ghi ra CSV (chỉ ghi header ở chunk đầu tiên)
            chunk.to_csv(csv_path, mode='a', index=False, header=first_chunk)
            first_chunk = False
            
        return True
    except Exception as e:
        print(f"Lỗi khi convert chunked: {e}")
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
