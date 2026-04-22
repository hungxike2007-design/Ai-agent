from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
import pyodbc

admin_bp = Blueprint('admin', __name__)

def get_db_connection():
    conn_str = 'DRIVER={SQL Server};SERVER=LAPTOP-355TS2QT\HUY_DEV;DATABASE=QuanLyAIAgent;Trusted_Connection=yes;'
    return pyodbc.connect(conn_str)

@admin_bp.route('/dashboard') 
def dashboard():
    if session.get('role') != 'Admin':
        flash("Quyền truy cập bị từ chối!", "danger")
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Danh sách người dùng
    cursor.execute("SELECT UserID, Username, FullName, Email, Role FROM Users")
    users = cursor.fetchall()

    # 2. Danh sách file
    cursor.execute("""
        SELECT f.FileID, f.FileName, u.FullName, f.UploadDate 
        FROM ExcelFiles f JOIN Users u ON f.UserID = u.UserID
    """)
    files = cursor.fetchall()

    # 3. Danh sách phiên chat
    cursor.execute("""
        SELECT s.SessionID, s.SessionTitle, u.FullName, f.FileName, s.StartTime
        FROM ChatSessions s
        JOIN Users u ON s.UserID = u.UserID
        LEFT JOIN ExcelFiles f ON s.FileID = f.FileID
        ORDER BY s.StartTime DESC
    """)
    sessions = cursor.fetchall()

    # 4. Thống kê
    cursor.execute("SELECT SUM(TokensUsed) FROM TokenLogs")
    total_tokens = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM ChatSessions")
    total_requests = cursor.fetchone()[0] or 0

    conn.close()
    return render_template('admin_dashboard.html', 
                            users=users, files=files, sessions=sessions,
                            total_tokens=total_tokens, total_requests=total_requests,
                            total_users=len(users))

# --- CHỨC NĂNG MỚI: CẬP NHẬT QUYỀN USER ---
@admin_bp.route('/update_role', methods=['POST'])
def update_role():
    if session.get('role') != 'Admin':
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        data = request.json
        user_id = int(data.get('user_id'))
        new_role = data.get('new_role')

        if not user_id or not new_role or new_role not in ['Admin', 'User']:
            return jsonify({"status": "error", "message": "Dữ liệu không hợp lệ"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        # Chú ý: Cột là [Role], bảng là [Users]
        cursor.execute("UPDATE Users SET Role = ? WHERE UserID = ?", (new_role, user_id))
        conn.commit()
        conn.close()

        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Lỗi update_role: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
# --- CHỨC NĂNG MỚI: CẤU HÌNH PROMPT HỆ THỐNG ---
@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('role') != 'Admin': return redirect(url_for('auth.index'))
    
    from database import get_all_system_configs
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_prompt = request.form.get('system_prompt', '')
        temperature = request.form.get('temperature', '0.7')
        max_tokens = request.form.get('max_tokens', '2048')
        
        cursor.execute("UPDATE SystemConfigs SET ConfigValue = ? WHERE ConfigKey = 'DefaultPrompt'", (new_prompt,))
        cursor.execute("UPDATE SystemConfigs SET ConfigValue = ? WHERE ConfigKey = 'Temperature'", (temperature,))
        cursor.execute("UPDATE SystemConfigs SET ConfigValue = ? WHERE ConfigKey = 'MaxTokens'", (max_tokens,))
        conn.commit()
        flash("Cập nhật cấu hình thành công!", "success")

    conn.close()
    configs = get_all_system_configs()
    return render_template('admin_settings.html', configs=configs)

# --- CHỨC NĂNG XÓA (Đã có ON DELETE CASCADE nên code rất ngắn gọn) ---
@admin_bp.route('/delete_session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    if session.get('role') != 'Admin': return jsonify({"error": "Forbidden"}), 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Vì có ON DELETE CASCADE, chỉ cần xóa SessionID là ChatMessages tự mất
        cursor.execute("DELETE FROM ChatSessions WHERE SessionID = ?", (session_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Xóa thành công!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- CHỨC NĂNG XEM CHI TIẾT PHIÊN CHAT ---
@admin_bp.route('/get_session_chat/<int:session_id>')
def get_session_chat(session_id):
    if session.get('role') != 'Admin': return jsonify({"error": "Forbidden"}), 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Role, [Content], CreatedAt FROM ChatMessages WHERE SessionID = ? ORDER BY CreatedAt ASC", (session_id,))
        messages = cursor.fetchall()
        conn.close()
        return jsonify([{"role": row[0], "content": row[1], "time": str(row[2])} for row in messages])
    except Exception as e:
        return jsonify({"error": str(e)}), 500