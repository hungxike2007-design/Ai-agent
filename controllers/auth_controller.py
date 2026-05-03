from flask import Blueprint, render_template, request, redirect, url_for, session,flash
from authlib.integrations.flask_client import OAuth
import database as db

auth_bp = Blueprint('auth', __name__)

# --- C\u1ea4U H\xccNH GOOGLE OAUTH ---
oauth = OAuth()
google = oauth.register(
    name='google',
    client_id='44095566122-91udbj167e4lf7re6g5i33t5ce5d1479.apps.googleusercontent.com',
    client_secret='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', 
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --- C\u1ea4U H\xccNH GITHUB OAUTH ---
github = oauth.register(
    name='github',
    client_id='your_github_client_id',  # Replace with your GitHub OAuth App Client ID
    client_secret='your_github_client_secret',  # Replace with your GitHub OAuth App Client Secret
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    client_kwargs={'scope': 'user:email'}
)

@auth_bp.route('/')
def index():
    return render_template('index.html')

# --- \u0110\u0102NG K\xdd / \u0110\u0102NG NH\u1eacP TRUY\u1ec0N TH\u1ed0NG ---
@auth_bp.route('/register', methods=['POST'])
def register():
    fullname = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    username = email.split('@')[0]
    try:
        db.register_user(username, password, fullname, email)
        flash("\u0110\u0103ng k\xfd th\xe0nh c\xf4ng! Vui l\xf2ng \u0111\u0103ng nh\u1eadp.", "success")
        return redirect(url_for('auth.index'))
    except Exception as e:
        flash(f"L\u1ed7i \u0111\u0103ng k\xfd: {str(e)}", "danger")
        return redirect(url_for('auth.index'))

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    user = db.check_login(email, password)
    if user:
        session['user_id'] = user[0] 
        session['username'] = user[3] # C\u1ed9t Fullname trong SQL
        session['role'] = user.Role if hasattr(user, 'Role') else 'User' # \u0110\u1ea3m b\u1ea3o c\xf3 Role trong session
        return redirect(url_for('ai.dashboard'))
    
    flash("Sai t\xe0i kho\u1ea3n ho\u1eb7c m\u1eadt kh\u1ea9u!", "danger")
    return redirect(url_for('auth.index'))

# --- LOGIC \u0110\u0102NG NH\u1eacP GOOGLE & K\u1ebeT N\u1ed0I SQL ---

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

        # 1. T\xecm trong b\u1ea3ng Users tr\u01b0\u1edbc (d\u1ef1a tr\xean email)
        user = db.get_user_by_email(email)
        
        if not user:
            # N\u1ebfu ch\u01b0a c\xf3 account trong b\u1ea3ng Users -> \u0110\u0103ng k\xfd m\u1edbi
            username = email.split('@')[0]
            db.register_user(username, 'GOOGLE', fullname, email)
            # L\u1ea5y l\u1ea1i th\xf4ng tin sau khi \u0111\u0103ng k\xfd \u0111\u1ec3 c\xf3 UserID
            user = db.get_user_by_email(email)
            
            # Sau \u0111\xf3 m\u1edbi li\xean k\u1ebft b\u1ea3ng GoogleAccounts
            db.link_google_account(google_id, user[0], email, picture)
        else:
            # N\u1ebfu \u0111\xe3 c\xf3 account Users, ki\u1ec3m tra xem \u0111\xe3 link GoogleAccounts ch\u01b0a
            g_account = db.get_user_by_google_id(google_id)
            if not g_account:
                # N\u1ebfu ch\u01b0a link th\xec link ngay \u0111\u1ec3 l\u1ea7n sau login nhanh h\u01a1n
                db.link_google_account(google_id, user[0], email, picture)

        # 2. Quan tr\u1ecdng nh\u1ea5t: L\u01b0u UserID c\u1ee7a b\u1ea3ng Users v\xe0o session
        # \u0110i\u1ec1u n\xe0y gi\xfap c\xe1c b\u1ea3ng ExcelFiles, ChatSessions (h\xecnh 12, 13) kh\xf4ng b\u1ecb l\u1ed7i Foreign Key
        session['user_id'] = user[0]   # ID t\u1eeb b\u1ea3ng Users
        session['username'] = user[3] # FullName t\u1eeb b\u1ea3ng Users
        session['avatar'] = picture
        
        return redirect(url_for('ai.dashboard'))
    
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = db.get_user_by_email(email)
        
        if user:
            # \u1ede \u0111\xe2y   c\xf3 th\u1ec3 g\u1eedi email, nh\u01b0ng \u0111\u01a1n gi\u1ea3n nh\u1ea5t l\xe0 
            # cho h\u1ecd chuy\u1ec3n h\u01b0\u1edbng \u0111\u1ebfn trang \u0111\u1eb7t l\u1ea1i m\u1eadt kh\u1ea9u v\u1edbi token l\xe0 email
            return redirect(url_for('auth.reset_password', email=email))
        else:
            flash("Email kh\xf4ng t\u1ed3n t\u1ea1i trong h\u1ec7 th\u1ed1ng!", "danger")
            
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<email>', methods=['GET', 'POST'])
def reset_password(email):
    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash("M\u1eadt kh\u1ea9u x\xe1c nh\u1eadn kh\xf4ng kh\u1edbp!", "danger")
            return render_template('reset_password.html', email=email)
        
        # G\u1ecdi h\xe0m c\u1eadp nh\u1eadt pass trong database.py
        db.update_user_password(email, new_password)
        flash("\u0110\u1ed5i m\u1eadt kh\u1ea9u th\xe0nh c\xf4ng! Vui l\xf2ng \u0111\u0103ng nh\u1eadp l\u1ea1i.", "success")
        return redirect(url_for('auth.index'))
        
    return render_template('reset_password.html', email=email)
   
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))