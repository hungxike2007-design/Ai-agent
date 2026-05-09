
import database
try:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Reports'")
    cols = [row[0] for row in cursor.fetchall()]
    print(f"Columns in Reports: {cols}")
    
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ExcelFiles'")
    cols = [row[0] for row in cursor.fetchall()]
    print(f"Columns in ExcelFiles: {cols}")
    
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ChatSessions'")
    cols = [row[0] for row in cursor.fetchall()]
    print(f"Columns in ChatSessions: {cols}")
    
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ChatMessages'")
    cols = [row[0] for row in cursor.fetchall()]
    print(f"Columns in ChatMessages: {cols}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
