# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
import pyodbc
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def get_db_connection():
    conn_str = r'DRIVER={SQL Server};SERVER=LAPTOP-355TS2QT\HUY_DEV;DATABASE=QuanLyAIAgent;Trusted_Connection=yes;'
    return pyodbc.connect(conn_str)

@admin_bp.route('/dashboard') 
def dashboard():
    if session.get('role') != 'Admin':
        flash("Quyền truy cập bị từ chối!", "danger")
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Danh s\xc3\xa1ch ng\xc6\xb0\xe1\xbb\x9di d\xc3\xb9ng
    cursor.execute("SELECT UserID, Username, FullName, Email, Role FROM Users")
    users = cursor.fetchall()

    # 2. Danh sách xuất file
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

    # 4. Th\xe1\xbb\u2018ng k\xc3\xaa
    cursor.execute("SELECT SUM(TokensUsed) FROM TokenLogs")
    total_tokens = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM ChatSessions")
    total_requests = cursor.fetchone()[0] or 0

    conn.close()
    return render_template('admin_dashboard.html', 
                            users=users, files=files, sessions=sessions,
                            total_tokens=total_tokens, total_requests=total_requests,
                            total_users=len(users))

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
        cursor.execute("UPDATE Users SET Role = ? WHERE UserID = ?", (new_role, user_id))
        conn.commit()
        conn.close()

        return jsonify({"status": "success"})
    except Exception as e:
        print(f"L\xe1\xbb\u2014i update_role: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
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
        flash("Cập nhật thành công!", "success")

    conn.close()
    configs = get_all_system_configs()
    return render_template('admin_settings.html', configs=configs)

@admin_bp.route('/delete_session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    if session.get('role') != 'Admin': return jsonify({"error": "Forbidden"}), 403
    try:
        import os
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. L\xe1\xba\xa5y th\xc3\xb4ng tin file tr\xc6\xb0\xe1\xbb\u203ac khi x\xc3\xb3a session
        cursor.execute("""
            SELECT f.FilePath, f.FileID 
            FROM ChatSessions s
            LEFT JOIN ExcelFiles f ON s.FileID = f.FileID
            WHERE s.SessionID = ?
        """, (session_id,))
        info = cursor.fetchone()
        
        # 2. X\xc3\xb3a Session (ChatMessages s\xe1\xba\xbd t\xe1\xbb\xb1 x\xc3\xb3a nh\xe1\xbb\x9d ON DELETE CASCADE)
        cursor.execute("DELETE FROM ChatSessions WHERE SessionID = ?", (session_id,))
        
        if info:
            file_path = info[0]
            file_id = info[1]
            
            if file_id:
                # 3. X\xc3\xb3a b\xe1\xba\xa3n ghi trong Reports v\xc3\xa0 ExcelFiles
                cursor.execute("DELETE FROM Reports WHERE FileID = ?", (file_id,))
                cursor.execute("DELETE FROM ExcelFiles WHERE FileID = ?", (file_id,))
                
                # 4. X\xc3\xb3a file v\xe1\xba\xadt l\xc3\xbd tr\xc3\xaan server
                if file_path and os.path.exists(file_path):
                    try: os.remove(file_path)
                    except: pass
                
                # 5. X\xc3\xb3a bi\xe1\xbb\u0192u \xc4\u2018\xe1\xbb\u201c
                chart_file = os.path.join(os.getcwd(), 'static', 'charts', f"chart_{file_id}.png")
                if os.path.exists(chart_file):
                    try: os.remove(chart_file)
                    except: pass

        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "\u0110\xe3 x\xf3a s\u1ea1ch phi\xean chat v\xe0 c\xe1c t\u1ec7p li\xean quan!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- CH\xe1\xbb\xa8C N\xc4\u201aNG XEM CHI TI\xe1\xba\xbeT PHI\xc3\u0160N CHAT ---
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

# --- CH\xe1\xbb\xa8C N\xc4\u201aNG TH\xe1\xbb\x90NG K\xc3\u0160 (API) ---
@admin_bp.route('/stats_data')
def stats_data():
    if session.get('role') != 'Admin':
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Th\xe1\xbb\u2018ng k\xc3\xaa ng\xc6\xb0\xe1\xbb\x9di d\xc3\xb9ng m\xe1\xbb\u203ai trong 7 ng\xc3\xa0y qua
        user_stats = []
        for i in range(6, -1, -1):
            date_obj = datetime.now() - timedelta(days=i)
            date_str = date_obj.strftime('%Y-%m-%d')
            try:
                # Group by date of CreatedAt (gi\xe1\xba\xa3 \xc4\u2018\xe1\xbb\u2039nh c\xc3\xb3 c\xe1\xbb\u2122t CreatedAt)
                cursor.execute("""
                    SELECT COUNT(*) FROM Users 
                    WHERE CAST(CreatedAt AS DATE) = ?
                """, (date_str,))
                count = cursor.fetchone()[0]
            except:
                count = 0
            user_stats.append({"date": date_obj.strftime('%d/%m'), "count": count})

        # 2. Th\xe1\xbb\u2018ng k\xc3\xaa tr\xe1\xba\xa1ng th\xc3\xa1i x\xe1\xbb\xad l\xc3\xbd file Excel (Success vs Failed)
        cursor.execute("SELECT Status, COUNT(*) FROM ExcelFiles GROUP BY Status")
        file_rows = cursor.fetchall()
        file_stats = [{"status": str(row[0]), "count": row[1]} for row in file_rows]

        conn.close()
        return jsonify({
            "users": user_stats,
            "files": file_stats
        })
    except Exception as e:
        print(f"L\xe1\xbb\u2014i stats_data: {e}")
        return jsonify({"error": str(e)}), 500

def _internal_delete_file(cursor, file_id):
    """H\xc3\xa0m n\xe1\xbb\u2122i b\xe1\xbb\u2122 \xc4\u2018\xe1\xbb\u0192 x\xc3\xb3a file v\xc3\xa0 d\xe1\xbb\xaf li\xe1\xbb\u2021u li\xc3\xaan quan, d\xc3\xb9ng cho c\xe1\xba\xa3 x\xc3\xb3a \xc4\u2018\xc6\xa1n v\xc3\xa0 x\xc3\xb3a nhi\xe1\xbb\x81u"""
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

# --- CH\xe1\xbb\xa8C N\xc4\u201aNG X\xc3\u201cA FILE H\xe1\xbb\u2020 TH\xe1\xbb\x90NG ---
@admin_bp.route('/delete_file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    if session.get('role') != 'Admin': return jsonify({"error": "Forbidden"}), 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if _internal_delete_file(cursor, file_id):
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "message": "\u0110\xe3 x\xf3a file th\xe0nh c\xf4ng!"})
        conn.close()
        return jsonify({"status": "error", "message": "Kh\xf4ng t\xecm th\u1ea5y file!"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- CH\xe1\xbb\xa8C N\xc4\u201aNG X\xc3\u201cA NHI\xe1\xbb\u20acU FILE ---
@admin_bp.route('/bulk_delete_files', methods=['POST'])
def bulk_delete_files():
    if session.get('role') != 'Admin': return jsonify({"error": "Forbidden"}), 403
    try:
        data = request.json
        file_ids = data.get('file_ids', [])
        if not file_ids:
            return jsonify({"status": "error", "message": "Kh\xf4ng c\xf3 file n\xe0o \u0111\u01b0\u1ee3c ch\u1ecdn!"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        success_count = 0
        for fid in file_ids:
            if _internal_delete_file(cursor, int(fid)):
                success_count += 1
        
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"\xc4\x90\xc3\xa3 x\xc3\xb3a th\xc3\xa0nh c\xc3\xb4ng {success_count} t\u1ec7p tin!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Trang quản lý phản hồi của người dùng ---
@admin_bp.route('/feedbacks')
def feedbacks():
    """Trang quản lý phản hồi của người dùng"""
    if session.get('role') != 'Admin':
        return redirect(url_for('auth.index'))
    from database import get_all_feedbacks, get_feedback_stats
    status_filter = request.args.get('status', '')
    all_feedbacks = get_all_feedbacks(status_filter if status_filter else None)
    stats = get_feedback_stats()
    return render_template('admin_feedbacks.html',
                           feedbacks=all_feedbacks,
                           stats=stats,
                           current_filter=status_filter)

@admin_bp.route('/feedback/update/<int:feedback_id>', methods=['POST'])
def update_feedback(feedback_id):
    """Admin cập nhật trạng thái phản hồi"""
    if session.get('role') != 'Admin':
        return jsonify({"error": "Forbidden"}), 403
    data = request.json
    status = data.get('status', 'DaXem')
    admin_note = data.get('admin_note', '')
    from database import update_feedback_status
    ok = update_feedback_status(feedback_id, status, admin_note)
    if ok:
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Cập nhật thất bại"}), 500

@admin_bp.route('/feedback/delete/<int:feedback_id>', methods=['DELETE'])
def delete_feedback_route(feedback_id):
    """Admin xóa một phản hồi"""
    if session.get('role') != 'Admin':
        return jsonify({"error": "Forbidden"}), 403
    from database import delete_feedback
    ok = delete_feedback(feedback_id)
    if ok:
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Xuất thất bại"}), 500

@admin_bp.route('/feedback/stats_api')
def feedback_stats_api():
    """API trả về thống kê phản hồi dạng JSON"""
    if session.get('role') != 'Admin':
        return jsonify({"error": "Forbidden"}), 403
    from database import get_feedback_stats
    return jsonify(get_feedback_stats())
