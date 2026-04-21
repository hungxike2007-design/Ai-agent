from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
import pyodbc

admin_bp = Blueprint('admin', __name__)

def get_db_connection():
    # Hùng dùng chuỗi kết nối của máy Hùng nhé
    conn_str = 'DRIVER={SQL Server};SERVER=LAPTOP-FOEQL0GL;DATABASE=QuanLyAIAgent;Trusted_Connection=yes;'
    return pyodbc.connect(conn_str)

@admin_bp.route('/dashboard') 
def dashboard():
    if session.get('role') != 'Admin':
        flash("Quyền truy cập bị từ chối!", "danger")
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Quản lý người dùng: Lấy danh sách user
    cursor.execute("SELECT UserID, Username, FullName, Email, Role FROM Users")
    users = cursor.fetchall()

    # 2. Quản lý dữ liệu: Lấy danh sách file đã upload
    cursor.execute("""
        SELECT f.FileID, f.FileName, u.FullName, f.UploadDate 
        FROM ExcelFiles f JOIN Users u ON f.UserID = u.UserID
    """)
    files = cursor.fetchall()

    # 3. Quản lý phiên: Lấy danh sách lịch sử phân tích
    cursor.execute("""
        SELECT s.SessionID, s.SessionTitle, u.FullName, f.FileName, s.StartTime
        FROM ChatSessions s
        JOIN Users u ON s.UserID = u.UserID
        LEFT JOIN ExcelFiles f ON s.FileID = f.FileID
        ORDER BY s.StartTime DESC
    """)
    sessions = cursor.fetchall()

    # 4. Quản lý tài nguyên: Thống kê Token (Giữ nguyên để theo dõi chi phí)
    cursor.execute("SELECT SUM(TokensUsed) FROM TokenLogs")
    total_tokens = cursor.fetchone()[0] or 0

    # 5. CẬP NHẬT: Đếm số yêu cầu dựa trên số lượng Phiên phân tích (ChatSessions)
    # Điều này giúp con số trên Stats Card khớp với số dòng trong bảng Lịch sử
    cursor.execute("SELECT COUNT(*) FROM ChatSessions")
    total_requests = cursor.fetchone()[0] or 0

    conn.close()
    return render_template('admin_dashboard.html', 
                            users=users, 
                            files=files, 
                            sessions=sessions,
                            total_tokens=total_tokens,
                            total_requests=total_requests,
                            total_users=len(users))

# API MỚI: Lấy chi tiết đoạn chat để hiển thị trên Modal
@admin_bp.route('/get_session_chat/<int:session_id>')
def get_session_chat(session_id):
    if session.get('role') != 'Admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Truy vấn lấy nội dung tin nhắn dựa trên SessionID từ bảng ChatMessages
    cursor.execute("""
        SELECT Role, [Content], CreatedAt 
        FROM ChatMessages 
        WHERE SessionID = ? 
        ORDER BY CreatedAt ASC
    """, (session_id,))
    
    messages = []
    for row in cursor.fetchall():
        messages.append({
            "role": row[0],
            "content": row[1],
            "time": row[2].strftime('%H:%M:%S') if row[2] else "" # Định dạng giờ để hiển thị
        })
    conn.close()
    return jsonify(messages)

@admin_bp.route('/delete_session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Bước 1: Lấy FileID liên quan đến phiên này trước khi xóa phiên
        cursor.execute("SELECT FileID FROM ChatSessions WHERE SessionID = ?", (session_id,))
        row = cursor.fetchone()
        file_id = row[0] if row else None

        # Bước 2: Xóa tin nhắn (ChatMessages)
        cursor.execute("DELETE FROM ChatMessages WHERE SessionID = ?", (session_id,))
        
        # Bước 3: Xóa phiên chat (ChatSessions)
        cursor.execute("DELETE FROM ChatSessions WHERE SessionID = ?", (session_id,))

        if file_id:
            # Bước 4: Xóa các báo cáo (Reports) liên quan đến file này
            cursor.execute("DELETE FROM Reports WHERE FileID = ?", (file_id,))
            
            # Bước 5: Xóa thông tin file trong DB (ExcelFiles)
            # Lưu ý: Bạn nên lấy FilePath để xóa file vật lý trên ổ cứng nếu cần
            cursor.execute("DELETE FROM ExcelFiles WHERE FileID = ?", (file_id,))

        conn.commit()
        return jsonify({"status": "success", "message": "Đã xóa sạch phiên, báo cáo và file liên quan"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()