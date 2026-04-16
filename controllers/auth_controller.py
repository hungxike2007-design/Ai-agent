from flask import Blueprint, render_template, request, redirect, url_for, session
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

        user = db.get_user_by_google_id(google_id)
        
        if not user:
            username = email.split('@')[0]
            # Đăng ký user mới vào bảng Users
            # Password Hùng để là 'GOOGLE' vì đăng nhập qua Google không cần pass
            db.register_user(username, 'GOOGLE', fullname, email)
            
            # Lấy lại UserID vừa tạo (Lúc này hàm get_user_by_email trả về 4 cột)
            new_user = db.get_user_by_email(email)
            new_user_id = new_user[0] # UserID
            
            # Lưu vào bảng GoogleAccounts (khớp với ảnh 2 của Hùng)
            db.link_google_account(google_id, new_user_id, email, picture)
            user = new_user

        # Lấy dữ liệu an toàn dựa trên hàm SELECT 4 cột ở trên:
        session['user_id'] = user[0]   # UserID
        session['username'] = user[3] # FullName (Cột thứ 4 trong lệnh SELECT)
        session['avatar'] = picture
        
        return redirect(url_for('ai.dashboard'))
    
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))