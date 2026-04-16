from flask import Blueprint, render_template, request, redirect, url_for

# Giả sử bạn đã có file database.py để xử lý DB
import database as db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('index.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Lấy dữ liệu từ Form
        fullname = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Kiểm tra nếu email có giá trị thì mới xử lý split
        if email:
            username = email.split('@')[0]
            try:
                db.register_user(username, password, fullname, email)
                return "<h1>Đăng ký thành công!</h1><a href='/login'>Đi đến Đăng nhập</a>"
            except Exception as e:
                return f"<h1>Lỗi đăng ký:</h1><p>{e}</p><a href='/register'>Thử lại</a>"
        else:
            return "<h1>Vui lòng nhập đầy đủ thông tin!</h1><a href='/register'>Quay lại</a>"
            
    # Nếu là GET (vừa vào trang), chỉ hiển thị giao diện
    return render_template('register.html') # Đảm bảo bạn có file này hoặc dùng index.html

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = db.check_login(email, password)
        if user:
            # Chuyển hướng sang trang dashboard của AI Agent
            return redirect(url_for('ai.dashboard')) 
        return "<h1>Sai tài khoản!</h1><a href='/login'>Thử lại</a>"
        
    # Nếu là GET, hiện trang đăng nhập
    return render_template('index.html') # Hoặc login.html tùy bạn đặt tên