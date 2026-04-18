from flask import Flask
from controllers.auth_controller import auth_bp, oauth  
from controllers.ai_controller import ai_bp
from controllers.api_controller import api_bp
from controllers.admin_controller import admin_bp


app = Flask(__name__)


app.secret_key = "hung_store_key_bi_mat"

# --- KHỞI TẠO OAUTH ---
# Dòng này cực kỳ quan trọng để kết nối thư viện Authlib với ứng dụng Flask của Hùng
oauth.init_app(app)

# Đăng ký các Blueprint (Controller)
# Lưu ý: Nếu trang chủ là trang đăng nhập, ta để url_prefix của auth là '/'
app.register_blueprint(auth_bp, url_prefix='/')
app.register_blueprint(ai_bp, url_prefix='/ai')
app.register_blueprint(api_bp, url_prefix='/api/v1')
app.register_blueprint(admin_bp, url_prefix='/admin')

if __name__ == '__main__':
    print("🚀 Đồ án đang chạy tại: http://127.0.0.1:5000")
    app.run(debug=True, port=5000, use_reloader=False)