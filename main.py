from flask import Flask, redirect, url_for
from controllers.auth_controller import auth_bp
from controllers.ai_controller import ai_bp

# 1. Khởi tạo App trước (Bắt buộc)
app = Flask(__name__)


app.secret_key = "hung_store_key_bi_mat"

# 2. Định nghĩa trang chủ (Redirect về trang login)
@app.route('/')
def index():
    # Thường tên định danh sẽ là 'tên_blueprint.tên_hàm'
    # Bạn thử 'auth.login', nếu báo lỗi thì đổi thành 'auth_bp.login'
    return redirect(url_for('auth.login')) 

# 3. Đăng ký các Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(ai_bp)

if __name__ == '__main__':
    print("🚀 Đồ án đang chạy tại: http://127.0.0.1:5000")
    app.run(debug=True, port=5000, use_reloader=False)