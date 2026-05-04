import sys
import io
import os

# ── BẮT BUỘC UTF-8 CHO TOÀN BỘ OUTPUT (fix lỗi charmap trên Windows) ────────
# Windows mặc định dùng cp1252 cho stdout/stderr → crash khi print tiếng Việt.
# Phải đặt TRƯỚC tất cả các import khác.
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
# Fallback cho môi trường không hỗ trợ reconfigure
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from flask import Flask
from controllers.auth_controller import auth_bp, oauth  
from controllers.ai_controller import ai_bp
from controllers.api_controller import api_bp
from controllers.admin_controller import admin_bp
from database import init_db_schema

# Tự động cập nhật cấu trúc database (nếu cần)
init_db_schema()


app = Flask(__name__)


app.secret_key = "hung_store_key_bi_mat"

# Đảm bảo JSON trả về là tiếng Việt chuẩn (không bị mã hóa \uXXXX)
app.config['JSON_AS_ASCII'] = False

@app.after_request
def enforce_utf8_charset(response):
    """Bắt buộc mọi phản hồi (HTML/JSON) đều phải có charset=utf-8 ở HTTP Header"""
    content_type = response.headers.get('Content-Type', '')
    if content_type and 'charset' not in content_type.lower():
        response.headers['Content-Type'] = f"{content_type}; charset=utf-8"
    return response

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
    print("Do an dang chay tai: http://127.0.0.1:5000")
    # Sử dụng reloader_type='stat' để tránh loop restart khi lưu biểu đồ trên Windows
    app.run(debug=True, port=5000, use_reloader=True, reloader_type='stat')