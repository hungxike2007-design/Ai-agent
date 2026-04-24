import pyodbc

# Chuỗi kết nối đến SQL Server của Hùng
CONN_STR = r"Driver={SQL Server};Server=TOM\SQLEXPRESS;Database=QuanLyAIAgent;Trusted_Connection=yes;"

# --- CẤU HÌNH GEMINI TẬP TRUNG ---
# Bạn chỉ cần thay đổi Key ở đây, tất cả các file khác sẽ tự cập nhật theo
GEMINI_API_KEY = "AIzaSyBluRZiICeQSpaWc3xcZ_1SYeEifIqU1kg"
GEMINI_MODEL_NAME = "gemini-flash-latest" 

def configure_ai():
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(GEMINI_MODEL_NAME)

def get_connection():
    """Hàm tạo kết nối đến Database"""
    return pyodbc.connect(CONN_STR)

# --- PHẦN 1: QUẢN LÝ NGƯỜI DÙNG (USERS) ---

def register_user(username, password, fullname, email, avatar=None):
    """Hàm lưu người dùng mới (Hỗ trợ cả avatar từ Google)"""
    conn = get_connection()
    cursor = conn.cursor()
    # Cập nhật query để hỗ trợ cột Avatar nếu Hùng đã thêm vào bảng
    query = """
        INSERT INTO Users (Username, Password, FullName, Email, Role, Avatar) 
        VALUES (?, ?, ?, ?, ?, ?)
    """
    try:
        cursor.execute(query, (username, password, fullname, email, 'User', avatar))
        conn.commit()
    except Exception as e:
        print(f"Lỗi register_user: {e}")
    finally:
        conn.close()

def check_login(email, password):
    """Hàm kiểm tra đăng nhập truyền thống"""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT UserID, Username, FullName, Role FROM Users WHERE Email = ? AND Password = ?"
    cursor.execute(query, (email, password))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    # Hùng liệt kê rõ tên cột theo thứ tự bạn muốn lấy
    # 0: UserID, 1: Username, 2: Email, 3: FullName
    query = "SELECT UserID, Username, Email, FullName FROM Users WHERE Email = ?"
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    conn.close()
    return user

# --- PHẦN 2: KẾT NỐI TÀI KHOẢN GOOGLE ---

def get_user_by_google_id(google_id):
    """Lấy thông tin User thông qua liên kết GoogleID"""
    conn = get_connection()
    cursor = conn.cursor()
    # Join bảng Users và GoogleAccounts để lấy đầy đủ data
    query = """
        SELECT u.UserID, u.Username, u.FullName, u.Email, u.Role, g.AvatarURL
        FROM Users u
        JOIN GoogleAccounts g ON u.UserID = g.UserID
        WHERE g.GoogleID = ?
    """
    cursor.execute(query, (google_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_password(email, new_password):
    conn = get_connection()
    cursor = conn.cursor()
    query = "UPDATE Users SET Password = ? WHERE Email = ?"
    cursor.execute(query, (new_password, email))
    conn.commit()
    conn.close()

def link_google_account(google_id, user_id, email, avatar_url):
    """Tạo liên kết giữa UserID hiện tại và tài khoản Google"""
    conn = get_connection()
    cursor = conn.cursor()
    query = "INSERT INTO GoogleAccounts (GoogleID, UserID, Email, AvatarURL) VALUES (?, ?, ?, ?)"
    try:
        cursor.execute(query, (google_id, user_id, email, avatar_url))
        conn.commit()
    except Exception as e:
        print(f"Lỗi link_google_account: {e}")
    finally:
        conn.close()

# --- PHẦN 3: QUẢN LÝ BÁO CÁO AI (REPORTS) ---

def save_report(user_id, title, query_text, ai_response, tokens=0):
    """Lưu lịch sử báo cáo mà AI đã sinh ra"""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO Reports (UserID, Title, QueryText, AiResponse, TokenUsed)
        VALUES (?, ?, ?, ?, ?)
    """
    try:
        cursor.execute(query, (user_id, title, query_text, ai_response, tokens))
        conn.commit()
    except Exception as e:
        print(f"Lỗi save_report: {e}")
    finally:
        conn.close()

def get_user_reports(user_id):
    """Lấy danh sách các báo cáo cũ của người dùng"""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM Reports WHERE UserID = ? ORDER BY CreatedAt DESC"
    cursor.execute(query, (user_id,))
    reports = cursor.fetchall()
    conn.close()
    return reports

# --- PHẦN 4: CẤU HÌNH HỆ THỐNG ---

def get_all_system_configs():
    """Lấy toàn bộ cấu hình hệ thống từ DB"""
    configs = {
        "DefaultPrompt": "",
        "Temperature": 0.7,
        "MaxTokens": 2048
    }
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ConfigKey, ConfigValue FROM SystemConfigs")
        rows = cursor.fetchall()
        for row in rows:
            key = row[0]
            val = row[1]
            if key == 'Temperature':
                configs[key] = float(val) if val else 0.7
            elif key == 'MaxTokens':
                configs[key] = int(val) if val else 2048
            else:
                configs[key] = val
        conn.close()
    except Exception as e:
        print(f"Lỗi lấy cấu hình hệ thống: {e}")
    return configs