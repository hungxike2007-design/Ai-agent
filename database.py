import pyodbc

# Chuỗi kết nối đến SQL Server của Hùng
# Lưu ý: Dấu r trước ngoặc kép để tránh lỗi đường dẫn
CONN_STR = r"Driver={SQL Server};Server=LAPTOP-355TS2QT;Database=QuanLyAIAgent;Trusted_Connection=yes;"
def get_connection():
    """Hàm tạo kết nối đến Database"""
    return pyodbc.connect(CONN_STR)

def register_user(username, password, fullname, email):
    """Hàm lưu người dùng mới vào bảng Users"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Câu lệnh SQL INSERT khớp với các cột trong ảnh SSMS của bạn
    # UserID là khóa chính tự tăng nên không cần chèn vào đây
    query = """
        INSERT INTO Users (Username, Password, FullName, Email, Role) 
        VALUES (?, ?, ?, ?, ?)
    """
    
    # Mặc định khi đăng ký sẽ là quyền 'User'
    cursor.execute(query, (username, password, fullname, email, 'User'))
    
    conn.commit()
    conn.close()

def check_login(email, password):
    """Hàm kiểm tra đăng nhập"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tìm xem có ông nào trùng Email và Password không
    query = "SELECT FullName, Role FROM Users WHERE Email = ? AND Password = ?"
    cursor.execute(query, (email, password))
    
    user = cursor.fetchone() # Lấy ra 1 hàng kết quả đầu tiên
    conn.close()
    
    return user # Trả về thông tin user hoặc None nếu không tìm thấy