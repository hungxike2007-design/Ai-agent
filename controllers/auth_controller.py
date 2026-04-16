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

# --- LOGIC ĐĂNG NHẬP TRUYỀN THỐNG ---
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
        # Lưu thông tin user vào session
        session['user_id'] = user[0] 
        session['username'] = user[2]
        return redirect(url_for('ai.dashboard'))
    return "<h1>Sai tài khoản!</h1><a href='/'>Thử lại</a>"

# --- LOGIC ĐĂNG NHẬP GOOGLE (MỚI) ---

@auth_bp.route('/login/google')
def google_login():
    # Hùng dùng hẳn đường dẫn tuyệt đối này để không sợ Blueprint làm lệch URL
    redirect_uri = 'http://127.0.0.1:5000/google/callback' 
    return google.authorize_redirect(redirect_uri)

@auth_bp.route('/google/callback')
def google_callback():
    # Bước 2: Google trả mã xác thực về, ứng dụng đổi lấy thông tin user
    token = google.authorize_access_token()
    user_info = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
    
    if user_info:
        # Bước 3: Lưu thông tin vào Session (Khớp với Sequence Diagram của Nhóm 7)
        session['user_id'] = user_info.get('sub') # ID định danh của Google
        session['username'] = user_info.get('name')
        session['email'] = user_info.get('email')
        session['avatar'] = user_info.get('picture')
        
        return redirect(url_for('ai.dashboard'))
    
    return "<h1>Lỗi xác thực Google!</h1><a href='/'>Thử lại</a>"

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))