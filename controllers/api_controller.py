from flask import Blueprint, jsonify, request
import database as db

api_bp = Blueprint('api', __name__)

# API 1: Lấy danh sách báo cáo của người dùng (Dạng JSON)
@api_bp.route('/reports/<int:user_id>', methods=['GET'])
def get_reports(user_id):
    reports_data = db.get_user_reports(user_id)
    # Chuyển đổi dữ liệu từ SQL (tuple) sang List các Dictionary để gửi đi
    result = []
    for r in reports_data:
        result.append({
            "id": r[0],
            "title": r[2],
            "content": r[4],
            "date": r[6].strftime("%Y-%m-%d %H:%M:%S") if r[6] else None
        })
    return jsonify(result)

# API 2: API dành cho AI Agent xử lý dữ liệu từ xa
@api_bp.route('/ai/process', methods=['POST'])
def process_ai():
    data = request.get_json()
    prompt = data.get('prompt')
    user_id = data.get('user_id')
    
    # Giả lập gọi đến bộ não AI
    ai_response = f"AI Agent đã xử lý yêu cầu: {prompt}"
    
    # Lưu vào database thông qua API
    db.save_report(user_id, "API Request", prompt, ai_response)
    
    return jsonify({
        "status": "success",
        "response": ai_response
    })