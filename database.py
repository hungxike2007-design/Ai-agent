import pyodbc

# Chuỗi kết nối đến SQL Server của Hùng
CONN_STR = r"Driver={SQL Server};Server=LAPTOP-FOEQL0GL;Database=QuanLyAIAgent;Trusted_Connection=yes;"

# --- CẤU HÌNH GEMINI TẬP TRUNG ---
# Thêm tất cả API Keys vào danh sách bên dưới.
# Hệ thống sẽ tự động xoay vòng sang key tiếp theo khi key hiện tại hết quota.
GEMINI_API_KEYS = [
    "",  # Key 1
    "",  # Key 2
    "",  # Key 3
]
GEMINI_MODEL_NAME = "gemini-flash-latest"  # quota miễn phí cao hơn gemini-2.0-flash

# Danh sách lỗi cho biết key đã hết hạn mức hoặc bị giới hạn tốc độ
_QUOTA_ERROR_KEYWORDS = [
    'quota', 'resource exhausted', '429',
    'rate limit', 'rateLimitExceeded', 'too many requests',
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
        self._keys = [k for k in (keys or GEMINI_API_KEYS) if k and 'REPLACE_WITH' not in k]
        if not self._keys:
            raise ValueError(
                "Chưa cấu hình Gemini API Key! "
                "Hãy thêm ít nhất 1 key hợp lệ vào danh sách GEMINI_API_KEYS trong database.py"
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
    def _is_quota_error(err: Exception) -> bool:
        err_str = str(err).lower()
        return any(kw in err_str for kw in _QUOTA_ERROR_KEYWORDS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_model(self):
        """Trả về GenerativeModel đang dùng."""
        return self._model

    def generate(self, prompt: str, generation_config=None):
        """
        Gọi model.generate_content(). Nếu gặp lỗi quota thì tự xoay sang key
        tiếp theo và thử lại (tối đa quay hết 1 vòng tất cả keys).
        """
        start_index = self._index
        attempts = 0
        last_err = None

        while attempts < len(self._keys):
            try:
                if generation_config:
                    return self._model.generate_content(prompt, generation_config=generation_config)
                return self._model.generate_content(prompt)
            except Exception as e:
                if self._is_quota_error(e):
                    print(f"[KeyRotator] Key #{self._index + 1} hết quota → thử key tiếp theo…")
                    last_err = e
                    self._rotate()
                    attempts += 1
                    # Nếu đã quay đủ 1 vòng về đúng điểm xuất phát, dừng
                    if self._index == start_index:
                        break
                else:
                    raise  # lỗi khác (invalid key, network, ...) → ném ra ngay

        raise Exception(
            f"Tất cả {len(self._keys)} API key đều đã hết quota.\n"
            "Hãy thêm key mới hoặc đợi đến 07:00 sáng hôm sau để quota reset.\n"
            f"Lỗi gốc: {last_err}"
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
        return True
    except Exception as e:
        print(f"Lỗi save_feedback: {e}")
        return False
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