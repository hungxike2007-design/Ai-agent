from flask import Blueprint, render_template, request, jsonify, session, send_file, make_response
import google.generativeai as genai
import pandas as pd
import io
from docx import Document
# Giữ nguyên các import service của Hùng
from services.data_processor import get_cleaning_suggestions
from services.report_service import get_report_prompt

ai_bp = Blueprint('ai', __name__)

# 1. Cấu hình Gemini - HÙNG LƯU Ý: Phải dùng Key bắt đầu bằng AIza...
# Mã cũ của Hùng (AQ.Ab8...) là mã token ngắn hạn nên sẽ bị lỗi 401
API_KEY = "AQ.Ab8RN6LFaJJh_vzZUiBhWp0iGFf-VsGrbXYSTEKZezhDcuGFBg" # <--- THAY KEY CHUẨN VÀO ĐÂY
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# Dùng session thay vì dict toàn cục để tránh lẫn lộn dữ liệu giữa các người dùng
@ai_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@ai_bp.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    style = request.form.get('style_preference', 'Kỹ thuật')

    if not file: return "Chưa chọn file!"

    try:
        df = pd.read_excel(file)
        cleaning_hints = get_cleaning_suggestions(df)
        
        df_display = df.fillna("")
        session['excel_data'] = df_display.to_string()
        
        prompt = get_report_prompt(session['excel_data'], style)
        response = model.generate_content(prompt)
        
        # Lưu kết quả vào session để các hàm export lấy ra dùng
        session['last_response'] = response.text
        
        return render_template('dashboard.html', 
                               table_html=df_display.head(10).to_html(classes='table table-hover', index=False),
                               ai_response=response.text,
                               cleaning_hints=cleaning_hints,
                               selected_style=style)
    except Exception as e:
        if "401" in str(e):
            return "Lỗi: API Key Gemini không hợp lệ hoặc đã hết hạn (401)."
        return f"Lỗi hệ thống: {e}"

@ai_bp.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get("question")
    context = session.get('excel_data')
    if not context: return jsonify({"answer": "Thiếu dữ liệu!"})
    
    response = model.generate_content(f"Dữ liệu: {context}\nCâu hỏi: {user_input}")
    session['last_response'] = response.text # Cập nhật lại cache khi hỏi đáp
    return jsonify({"answer": response.text})

# SỬA LẠI ROUTE EXPORT ĐỂ KHÔNG BỊ 404
@ai_bp.route('/export_report/<fmt>')
def export_report(fmt):
    content = session.get('last_response', "")
    if not content:
        return "Không có dữ liệu báo cáo để xuất!", 400

    if fmt == 'word':
        doc = Document()
        doc.add_heading('BÁO CÁO PHÂN TÍCH DỮ LIỆU', 0)
        doc.add_paragraph(content)
        
        stream = io.BytesIO()
        doc.save(stream)
        stream.seek(0)
        return send_file(stream, 
                         as_attachment=True, 
                         download_name="Bao_cao_AI.docx",
                         mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    
    elif fmt == 'pdf':
        # Vì xuất PDF cần thư viện nặng, tạm thời xuất ra file HTML 
        # nhưng trình duyệt sẽ hiểu là tải về file để Hùng nộp đồ án trước
        html = f"""
        <html>
            <head><meta charset="utf-8"></head>
            <body style='font-family: Arial, sans-serif; padding: 40px;'>
                <h1 style='color: #10a37f;'>Báo cáo AI Agent</h1>
                <hr>
                <div style='white-space: pre-wrap;'>{content}</div>
            </body>
        </html>
        """
        return make_response((html, 200, {
            'Content-Type': 'text/html',
            'Content-Disposition': 'attachment; filename=Bao_cao_AI.html'
        }))

    return "Định dạng không hỗ trợ", 400