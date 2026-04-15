from flask import Flask
from controllers.auth_controller import auth_bp
from controllers.ai_controller import ai_bp

app = Flask(__name__)
app.secret_key = "hung_store_key_bi_mat"

# Đăng ký các Blueprint (Controller)
app.register_blueprint(auth_bp)
app.register_blueprint(ai_bp)

if __name__ == '__main__':
    print("🚀 Con cac đang chạy tại: http://127.0.0.1:5000")
    app.run(debug=True, port=5000, use_reloader=False)