from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
import pyodbc

admin_bp = Blueprint('admin', __name__)

def get_db_connection():
    # Hùng dùng chuỗi kết nối của máy Hùng nhé
    conn_str = 'DRIVER={SQL Server};SERVER=TOM\SQLEXPRESS;DATABASE=QuanLyAIAgent;Trusted_Connection=yes;'
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

    # 3. Quản lý tài nguyên: Thống kê Token
    cursor.execute("SELECT SUM(TokensUsed) FROM TokenLogs")
    total_tokens = cursor.fetchone()[0] or 0

    # 4. Quản lý phân tích: Đếm số yêu cầu AI
    cursor.execute("SELECT COUNT(*) FROM TokenLogs")
    total_requests = cursor.fetchone()[0] or 0

    conn.close()
    return render_template('admin_dashboard.html', 
                           users=users, 
                           files=files, 
                           total_tokens=total_tokens,
                           total_requests=total_requests,
                           total_users=len(users))

# API Khóa/Mở hoặc Đổi quyền nhanh
@admin_bp.route('/admin/update_role', methods=['POST'])
def update_role():
    if session.get('role') == 'Admin':
        data = request.json
        user_id = data.get('user_id')
        new_role = data.get('new_role')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Users SET Role = ? WHERE UserID = ?", (new_role, user_id))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 403