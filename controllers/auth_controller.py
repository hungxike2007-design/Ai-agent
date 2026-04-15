from flask import Blueprint, render_template, request, redirect, url_for
import database as db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('index.html')

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
        return redirect(url_for('ai.dashboard')) # Chuyển hướng sang blueprint ai
    return "<h1>Sai tài khoản!</h1><a href='/'>Thử lại</a>"