import traceback
from services.large_file_processor import convert_excel_to_csv_chunked
import pandas as pd

try:
    df = pd.DataFrame({'A': range(100), 'B': range(100)})
    df.to_excel('test_small.xlsx', index=False)
    
    print("Testing convert_excel_to_csv_chunked...")
    convert_excel_to_csv_chunked('test_small.xlsx', 'test_small.csv', chunk_size=10)
    print("Done testing.")
except Exception as e:
    traceback.print_exc()
