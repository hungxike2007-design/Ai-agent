import pyodbc
import os
import bcrypt
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# Chuỗi kết nối đến SQL Server — đọc từ biến môi trường
_DB_SERVER = os.getenv("DB_SERVER", "localhost")
_DB_NAME   = os.getenv("DB_NAME",   "QuanLyAIAgent")
_DB_TRUSTED = os.getenv("DB_TRUSTED_CONNECTION", "yes")
CONN_STR = (
    f"Driver={{SQL Server}};"
    f"Server={_DB_SERVER};"
    f"Database={_DB_NAME};"
    f"Trusted_Connection={_DB_TRUSTED};"
)

# --- CẤU HÌNH GEMINI TẬP TRUNG ---
# Đọc danh sách API Keys từ biến môi trường GEMINI_API_KEYS
# (các key phân cách nhau bằng dấu phẩy trong file .env)
_raw_keys = os.getenv("GEMINI_API_KEYS", "")
GEMINI_API_KEYS = [k.strip() for k in _raw_keys.split(",") if k.strip()]
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-flash-latest")

# Danh sách lỗi cho biết key cần được xoay vòng (hết quota, hết hạn, hoặc không hợp lệ)
_ROTATABLE_ERROR_KEYWORDS = [
    'quota', 'resource exhausted', '429',
    'rate limit', 'rateLimitExceeded', 'too many requests',
    'expired', 'invalid', 'unauthenticated', '400'
]


class GeminiKeyRotator:
    """
    Quản lý danh sách Gemini API keys và tự động xoay vòng (round-robin)
    khi key hiện tại gặp lỗi quota / rate-limit.

    Cách dùng:
        rotator = GeminiKeyRotator()          # dùng singleton toàn cục
        response = rotator.generate(prompt)   # tự xoay key nếu cần
    """

    def __init__(self, keys: list = None, model_name: str = None):
        import google.generativeai as genai
        self._genai = genai
        
        db_keys = []
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ConfigValue FROM SystemConfigs WHERE ConfigKey = 'APIKeys'")
            row = cursor.fetchone()
            if row and row[0]:
                db_keys = [k.strip() for k in row[0].replace('\r', '').split('\n') if k.strip()]
            conn.close()
        except:
            pass

        self._keys = [k for k in (keys or db_keys or GEMINI_API_KEYS) if k and 'REPLACE_WITH' not in k]
        if not self._keys:
            raise ValueError(
                "Chưa cấu hình Gemini API Key! "
                "Hãy thêm ít nhất 1 key hợp lệ vào Cấu hình AI hoặc trong database.py"
            )
        self._model_name = model_name or GEMINI_MODEL_NAME
        self._index = 0          # index key đang dùng
        self._model = None
        self._apply_current_key()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _apply_current_key(self):
        """Cấu hình genai với key tại vị trí _index hiện tại."""
        key = self._keys[self._index]
        self._genai.configure(api_key=key)
        self._model = self._genai.GenerativeModel(self._model_name)
        print(f"[KeyRotator] Đang dùng Key #{self._index + 1} "
              f"({'*' * 8}{key[-6:]})")

    def _rotate(self):
        """Chuyển sang key kế tiếp theo vòng tròn."""
        self._index = (self._index + 1) % len(self._keys)
        self._apply_current_key()

    @staticmethod
    def _is_rotatable_error(err: Exception) -> bool:
        err_str = str(err).lower()
        return any(kw in err_str for kw in _ROTATABLE_ERROR_KEYWORDS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_model(self):
        """Trả về GenerativeModel đang dùng."""
        return self._model

    def get_current_api_key(self):
        """Trả về API key hiện tại đang dùng (để cho LangChain sử dụng)."""
        return self._keys[self._index]

    def generate(self, prompt: str, generation_config=None, target_model=None):
        """
        Gọi model.generate_content(). Nếu gặp lỗi quota thì tự xoay sang key
        tiếp theo và thử lại (tối đa quay hết 1 vòng tất cả keys).
        Nếu target_model bị lỗi NOT_FOUND, tự động fallback về model mặc định.
        """
        start_index = self._index
        attempts = 0
        last_err = None

        while attempts < len(self._keys):
            try:
                model_to_use = self._model
                if target_model:
                    model_to_use = self._genai.GenerativeModel(target_model)
                
                if generation_config:
                    return model_to_use.generate_content(prompt, generation_config=generation_config)
                return model_to_use.generate_content(prompt)
            except Exception as e:
                err_str = str(e).lower()
                # Nếu model bị 404 NOT_FOUND → fallback về model mặc định
                if 'not_found' in err_str or '404' in err_str:
                    if target_model and target_model != self._model_name:
                        print(f"[KeyRotator] Model '{target_model}' không tồn tại → Fallback về '{self._model_name}'")
                        target_model = None  # Reset để dùng self._model (model mặc định)
                        continue
                
                if self._is_rotatable_error(e):
                    print(f"[KeyRotator] Key #{self._index + 1} gặp lỗi hoặc hết quota → thử key tiếp theo…")
                    last_err = e
                    self._rotate()
                    attempts += 1
                    # Nếu đã quay đủ 1 vòng về đúng điểm xuất phát, dừng
                    if self._index == start_index:
                        break
                else:
                    raise  # lỗi khác (invalid key, network, ...) → ném ra ngay

        raise Exception(
            f"Tất cả {len(self._keys)} API key đều gặp lỗi hoặc hết quota.\n"
            "Hãy kiểm tra lại danh sách key trong Cấu hình AI hoặc đợi quota reset.\n"
            f"Lỗi cuối cùng: {last_err}"
        )


# Singleton toàn cục — tất cả controller chỉ cần import biến này
_key_rotator: GeminiKeyRotator | None = None


def get_key_rotator() -> GeminiKeyRotator:
    """Trả về singleton GeminiKeyRotator (lazy-init)."""
    global _key_rotator
    if _key_rotator is None:
        _key_rotator = GeminiKeyRotator()
    return _key_rotator



def configure_ai():
    """Backward-compatible: trả về model hiện tại của rotator."""
    return get_key_rotator().get_model()

def get_connection():
    """Hàm tạo kết nối đến Database"""
    return pyodbc.connect(CONN_STR)

def init_db_schema():
    """Tự động kiểm tra và nâng cấp cấu trúc Database (Migrations)"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Kiểm tra và tạo bảng SystemConfigs nếu chưa có
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID('SystemConfigs') AND type in ('U'))
            BEGIN
                CREATE TABLE SystemConfigs (
                    ConfigKey NVARCHAR(100) PRIMARY KEY,
                    ConfigValue NVARCHAR(MAX) NULL
                );
            END
        """)
        conn.commit()
        
        # Seed các giá trị mặc định cho SystemConfigs nếu bảng trống
        cursor.execute("SELECT COUNT(*) FROM SystemConfigs")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO SystemConfigs (ConfigKey, ConfigValue) VALUES ('DefaultPrompt', '')")
            cursor.execute("INSERT INTO SystemConfigs (ConfigKey, ConfigValue) VALUES ('Temperature', '0.7')")
            cursor.execute("INSERT INTO SystemConfigs (ConfigKey, ConfigValue) VALUES ('MaxTokens', '8192')")
            cursor.execute("INSERT INTO SystemConfigs (ConfigKey, ConfigValue) VALUES ('APIKeys', '')")
            conn.commit()
            print("[DB SCHEMA] Đã tạo và seed dữ liệu mặc định cho bảng SystemConfigs.")

        # 2. Kiểm tra và thêm cột PlotlyJSON vào bảng Reports nếu chưa có
        cursor.execute("""
            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('Reports') AND name = 'PlotlyJSON'
            )
            BEGIN
                ALTER TABLE Reports ADD PlotlyJSON NVARCHAR(MAX)
            END
        """)
        conn.commit()

        # 3. Kiểm tra và thêm cột FileSize vào bảng ExcelFiles nếu chưa có
        cursor.execute("""
            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('ExcelFiles') AND name = 'FileSize'
            )
            BEGIN
                ALTER TABLE ExcelFiles ADD FileSize BIGINT DEFAULT 0
            END
        """)
        conn.commit()
        
        conn.close()
    except Exception as e:
        print(f"[DB SCHEMA] Lỗi cập nhật cấu trúc: {e}")

# --- PHẦN 1: QUẢN LÝ NGƯỜI DÙNG (USERS) ---

def _hash_password(plain_password: str) -> str:
    """Mã hóa mật khẩu bằng bcrypt (salt tự động)."""
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """So sánh mật khẩu người dùng nhập với mật khẩu đã mã hóa trong DB."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except (ValueError, TypeError):
        # Nếu hash không hợp lệ (ví dụ: password cũ lưu plain text) → so sánh trực tiếp
        return plain_password == hashed_password

def register_user(username, password, fullname, email, avatar=None):
    """Hàm lưu người dùng mới (Hỗ trợ cả avatar từ Google)"""
    conn = get_connection()
    cursor = conn.cursor()
    # Mã hóa mật khẩu trước khi lưu vào DB (trừ tài khoản Google dùng marker 'GOOGLE')
    stored_password = password if password == 'GOOGLE' else _hash_password(password)
    query = """
        INSERT INTO Users (Username, Password, FullName, Email, Role, Avatar) 
        VALUES (?, ?, ?, ?, ?, ?)
    """
    try:
        cursor.execute(query, (username, stored_password, fullname, email, 'User', avatar))
        conn.commit()
    except Exception as e:
        print(f"Lỗi register_user: {e}")
    finally:
        conn.close()

def check_login(email, password):
    """Hàm kiểm tra đăng nhập truyền thống (hỗ trợ cả bcrypt hash và plain text cũ)"""
    conn = get_connection()
    cursor = conn.cursor()
    # Lấy user theo email trước, rồi verify password bằng bcrypt
    query = "SELECT UserID, Username, FullName, Role, Password FROM Users WHERE Email = ?"
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    conn.close()
    if user and _verify_password(password, user[4]):
        # Trả về tuple KHÔNG chứa Password (giữ nguyên format cũ)
        return (user[0], user[1], user[2], user[3])
    return None

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
    """Cập nhật mật khẩu đã mã hóa bcrypt cho user"""
    conn = get_connection()
    cursor = conn.cursor()
    hashed = _hash_password(new_password)
    query = "UPDATE Users SET Password = ? WHERE Email = ?"
    cursor.execute(query, (hashed, email))
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
    # LƯU Ý: Bảng Reports hiện tại có cấu trúc khác (FileID thay vì UserID/Title)
    # Hàm này có vẻ là code cũ, tạm thời để lại nhưng tránh sử dụng nếu không khớp schema
    query = """
        INSERT INTO Reports (FileID, [Content], CreatedDate, Summary)
        VALUES (?, ?, GETDATE(), ?)
    """
    try:
        # Giả định query_text là file_id nếu gọi theo kiểu mới
        cursor.execute(query, (query_text, ai_response, title))
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
        "MaxTokens": 8192,
        "APIKeys": ""
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
                configs[key] = int(val) if val else 8192
            else:
                configs[key] = val
        conn.close()
    except Exception as e:
        print(f"Lỗi lấy cấu hình hệ thống: {e}")
    return configs

# --- PHẦN 5: QUẢN LÝ PHẢN HỒI (FEEDBACKS) ---

def save_feedback(user_id, rating, comment, category='Chung', session_id=None):
    """Lưu phản hồi / đánh giá từ người dùng"""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO Feedbacks (UserID, SessionID, Rating, Category, Comment, Status, CreatedAt, UpdatedAt)
        VALUES (?, ?, ?, ?, ?, N'Moi', GETDATE(), GETDATE())
    """
    try:
        cursor.execute(query, (user_id, session_id, rating, category, comment))
        conn.commit()
        return True, ""
    except Exception as e:
        print(f"Lỗi save_feedback: {e}")
        return False, str(e)
    finally:
        conn.close()

def get_all_feedbacks(status_filter=None, limit=100):
    """Admin: Lấy danh sách tất cả phản hồi, có thể lọc theo trạng thái"""
    conn = get_connection()
    cursor = conn.cursor()
    if status_filter:
        query = """
            SELECT f.FeedbackID, u.FullName, u.Email, f.Rating, f.Category,
                   f.Comment, f.Status, f.AdminNote, f.CreatedAt, f.SessionID
            FROM Feedbacks f
            JOIN Users u ON f.UserID = u.UserID
            WHERE f.Status = ?
            ORDER BY f.CreatedAt DESC
        """
        cursor.execute(query, (status_filter,))
    else:
        query = """
            SELECT f.FeedbackID, u.FullName, u.Email, f.Rating, f.Category,
                   f.Comment, f.Status, f.AdminNote, f.CreatedAt, f.SessionID
            FROM Feedbacks f
            JOIN Users u ON f.UserID = u.UserID
            ORDER BY f.CreatedAt DESC
        """
        cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_feedback_status(feedback_id, status, admin_note=None):
    """Admin: Cập nhật trạng thái và ghi chú xử lý cho phản hồi"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Feedbacks
            SET Status = ?, AdminNote = ?, UpdatedAt = GETDATE()
            WHERE FeedbackID = ?
        """, (status, admin_note, feedback_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Lỗi update_feedback_status: {e}")
        return False
    finally:
        conn.close()

def get_feedback_stats():
    """Admin: Thống kê tổng quan phản hồi"""
    conn = get_connection()
    cursor = conn.cursor()
    stats = {"total": 0, "avg_rating": 0, "new_count": 0, "by_rating": {}, "by_category": {}}
    try:
        cursor.execute("SELECT COUNT(*), AVG(CAST(Rating AS FLOAT)), SUM(CASE WHEN Status = N'Moi' THEN 1 ELSE 0 END) FROM Feedbacks")
        row = cursor.fetchone()
        if row:
            stats["total"] = row[0] or 0
            stats["avg_rating"] = round(row[1] or 0, 1)
            stats["new_count"] = row[2] or 0
        cursor.execute("SELECT Rating, COUNT(*) FROM Feedbacks GROUP BY Rating ORDER BY Rating")
        for r in cursor.fetchall():
            stats["by_rating"][r[0]] = r[1]
        cursor.execute("SELECT Category, COUNT(*) FROM Feedbacks GROUP BY Category")
        for r in cursor.fetchall():
            stats["by_category"][r[0]] = r[1]
    except Exception as e:
        print(f"Lỗi get_feedback_stats: {e}")
    finally:
        conn.close()
    return stats

def delete_feedback(feedback_id):
    """Admin: Xóa một phản hồi"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Feedbacks WHERE FeedbackID = ?", (feedback_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Lỗi delete_feedback: {e}")
        return False
    finally:
        conn.close()