from flask import Blueprint, render_template, request, redirect, url_for, session,flash
from authlib.integrations.flask_client import OAuth
import database as db

auth_bp = Blueprint('auth', __name__)

# --- CẤU HÌNH GOOGLE OAUTH ---
oauth = OAuth()
google = oauth.register(
    name='google',
    client_id='44095566122-91udbj167e4lf7re6g5i33t5ce5d1479.apps.googleusercontent.com',
    client_secret='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', 
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@auth_bp.route('/')
def index():
    return render_template('index.html')

# --- ĐĂNG KÝ / ĐĂNG NHẬP TRUYỀN THỐNG ---
@auth_bp.route('/register', methods=['POST'])
def register():
    fullname = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    username = email.split('@')[0]
    try:
        db.register_user(username, password, fullname, email)
        return "<h1>Đăng ký thành công!</h1><a href='/'>Quay lại</a>"
    except Exception as e:
        return f"<h1>Lỗi đăng ký:</h1><p>{e}</p>"

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    user = db.check_login(email, password)
    if user:
        session['user_id'] = user[0] 
        session['username'] = user[3] # Cột Fullname trong SQL
        session['role'] = user.Role if hasattr(user, 'Role') else 'User' # Đảm bảo có Role trong session
        return redirect(url_for('ai.dashboard'))
    return "<h1>Sai tài khoản!</h1><a href='/'>Thử lại</a>"

# --- LOGIC ĐĂNG NHẬP GOOGLE & KẾT NỐI SQL ---

@auth_bp.route('/login/google')
def google_login():
    redirect_uri = 'http://127.0.0.1:5000/google/callback' 
    return google.authorize_redirect(redirect_uri)

@auth_bp.route('/google/callback')
def google_callback():
    token = google.authorize_access_token()
    user_info = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
    
    if user_info:
        google_id = user_info.get('sub')
        email = user_info.get('email')
        fullname = user_info.get('name')
        picture = user_info.get('picture')

        # 1. Tìm trong bảng Users trước (dựa trên email)
        user = db.get_user_by_email(email)
        
        if not user:
            # Nếu chưa có account trong bảng Users -> Đăng ký mới
            username = email.split('@')[0]
            db.register_user(username, 'GOOGLE', fullname, email)
            # Lấy lại thông tin sau khi đăng ký để có UserID
            user = db.get_user_by_email(email)
            
            # Sau đó mới liên kết bảng GoogleAccounts
            db.link_google_account(google_id, user[0], email, picture)
        else:
            # Nếu đã có account Users, kiểm tra xem đã link GoogleAccounts chưa
            g_account = db.get_user_by_google_id(google_id)
            if not g_account:
                # Nếu chưa link thì link ngay để lần sau login nhanh hơn
                db.link_google_account(google_id, user[0], email, picture)

        # 2. Quan trọng nhất: Lưu UserID của bảng Users vào session
        # Điều này giúp các bảng ExcelFiles, ChatSessions (hình 12, 13) không bị lỗi Foreign Key
        session['user_id'] = user[0]   # ID từ bảng Users
        session['username'] = user[3] # FullName từ bảng Users
        session['avatar'] = picture
        
        return redirect(url_for('ai.dashboard'))
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = db.get_user_by_email(email)
        
        if user:
            # Ở đây Hùng có thể gửi email, nhưng đơn giản nhất là 
            # cho họ chuyển hướng đến trang đặt lại mật khẩu với token là email
            return redirect(url_for('auth.reset_password', email=email))
        else:
            flash("Email không tồn tại trong hệ thống!", "danger")
            
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<email>', methods=['GET', 'POST'])
def reset_password(email):
    if request.method == 'POST':
        new_password = request.form.get('password')
        # Gọi hàm cập nhật pass trong database.py
        db.update_user_password(email, new_password)
        flash("Đổi mật khẩu thành công! Vui lòng đăng nhập lại.", "success")
        return redirect(url_for('auth.index'))
        
    return render_template('reset_password.html', email=email)
   
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))