from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
import pyodbc
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def get_db_connection():
    conn_str = 'DRIVER={SQL Server};SERVER=TOM\SQLEXPRESS;DATABASE=QuanLyAIAgent;Trusted_Connection=yes;'
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
        import os
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Lấy thông tin file trước khi xóa session
        cursor.execute("""
            SELECT f.FilePath, f.FileID 
            FROM ChatSessions s
            LEFT JOIN ExcelFiles f ON s.FileID = f.FileID
            WHERE s.SessionID = ?
        """, (session_id,))
        info = cursor.fetchone()
        
        # 2. Xóa Session (ChatMessages sẽ tự xóa nhờ ON DELETE CASCADE)
        cursor.execute("DELETE FROM ChatSessions WHERE SessionID = ?", (session_id,))
        
        if info:
            file_path = info[0]
            file_id = info[1]
            
            if file_id:
                # 3. Xóa bản ghi trong Reports và ExcelFiles
                cursor.execute("DELETE FROM Reports WHERE FileID = ?", (file_id,))
                cursor.execute("DELETE FROM ExcelFiles WHERE FileID = ?", (file_id,))
                
                # 4. Xóa file vật lý trên server
                if file_path and os.path.exists(file_path):
                    try: os.remove(file_path)
                    except: pass
                
                # 5. Xóa biểu đồ
                chart_file = os.path.join(os.getcwd(), 'static', 'charts', f"chart_{file_id}.png")
                if os.path.exists(chart_file):
                    try: os.remove(chart_file)
                    except: pass

        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Đã xóa sạch phiên chat và các tệp liên quan!"})
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

# --- CHỨC NĂNG THỐNG KÊ (API) ---
@admin_bp.route('/stats_data')
def stats_data():
    if session.get('role') != 'Admin':
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Thống kê người dùng mới trong 7 ngày qua
        user_stats = []
        for i in range(6, -1, -1):
            date_obj = datetime.now() - timedelta(days=i)
            date_str = date_obj.strftime('%Y-%m-%d')
            try:
                # Group by date of CreatedAt (giả định có cột CreatedAt)
                cursor.execute("""
                    SELECT COUNT(*) FROM Users 
                    WHERE CAST(CreatedAt AS DATE) = ?
                """, (date_str,))
                count = cursor.fetchone()[0]
            except:
                count = 0
            user_stats.append({"date": date_obj.strftime('%d/%m'), "count": count})

        # 2. Thống kê trạng thái xử lý file Excel (Success vs Failed)
        cursor.execute("SELECT Status, COUNT(*) FROM ExcelFiles GROUP BY Status")
        file_rows = cursor.fetchall()
        file_stats = [{"status": str(row[0]), "count": row[1]} for row in file_rows]

        conn.close()
        return jsonify({
            "users": user_stats,
            "files": file_stats
        })
    except Exception as e:
        print(f"Lỗi stats_data: {e}")
        return jsonify({"error": str(e)}), 500

def _internal_delete_file(cursor, file_id):
    """Hàm nội bộ để xóa file và dữ liệu liên quan, dùng cho cả xóa đơn và xóa nhiều"""
    import os
    cursor.execute("SELECT FilePath FROM ExcelFiles WHERE FileID = ?", (file_id,))
    row = cursor.fetchone()
    if row:
        file_path = row[0]
        cursor.execute("DELETE FROM Reports WHERE FileID = ?", (file_id,))
        cursor.execute("DELETE FROM ChatSessions WHERE FileID = ?", (file_id,))
        cursor.execute("DELETE FROM ExcelFiles WHERE FileID = ?", (file_id,))
        if file_path and os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
        chart_file = os.path.join(os.getcwd(), 'static', 'charts', f"chart_{file_id}.png")
        if os.path.exists(chart_file):
            try: os.remove(chart_file)
            except: pass
        return True
    return False

# --- CHỨC NĂNG XÓA FILE HỆ THỐNG ---
@admin_bp.route('/delete_file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    if session.get('role') != 'Admin': return jsonify({"error": "Forbidden"}), 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if _internal_delete_file(cursor, file_id):
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "message": "Đã xóa file thành công!"})
        conn.close()
        return jsonify({"status": "error", "message": "Không tìm thấy file!"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- CHỨC NĂNG XÓA NHIỀU FILE ---
@admin_bp.route('/bulk_delete_files', methods=['POST'])
def bulk_delete_files():
    if session.get('role') != 'Admin': return jsonify({"error": "Forbidden"}), 403
    try:
        data = request.json
        file_ids = data.get('file_ids', [])
        if not file_ids:
            return jsonify({"status": "error", "message": "Không có file nào được chọn!"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        success_count = 0
        for fid in file_ids:
            if _internal_delete_file(cursor, int(fid)):
                success_count += 1
        
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Đã xóa thành công {success_count} tệp tin!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500