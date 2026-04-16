from flask import Blueprint, render_template, request, jsonify, session, send_file, make_response
import google.generativeai as genai
import pandas as pd
import io
import os
from docx import Document
from dotenv import load_dotenv

# Import các dịch vụ bổ trợ
from services.data_processor import get_cleaning_suggestions
from services.report_service import get_report_prompt

# 1. Cấu hình môi trường và API
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# 2. KHỞI TẠO MODEL (Đây là dòng bạn thiếu dẫn đến lỗi 'model' is not defined)
model = genai.GenerativeModel('gemini-flash-latest')

ai_bp = Blueprint('ai', __name__)

# Cache lưu trữ phản hồi AI mới nhất để xuất báo cáo
report_cache = {"last_response": ""}

@ai_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@ai_bp.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    style = request.form.get('style_preference', 'Kỹ thuật')

    if not file: 
        return "Chưa chọn file!"

    try:
        # Đọc file Excel
        df = pd.read_excel(file)
        
        # Chức năng gợi ý lỗi làm sạch dữ liệu
        cleaning_hints = get_cleaning_suggestions(df)
        
        # Tiền xử lý dữ liệu: Thay thế NaN bằng chuỗi rỗng để không bị lỗi khi hiển thị
        df_display = df.fillna("")
        
        # Lưu dữ liệu vào session (chuyển sang string để AI có thể đọc)
        session['excel_data'] = df_display.to_string()
        
        # Sinh báo cáo tự động bằng Gemini
        prompt = get_report_prompt(session['excel_data'], style)
        response = model.generate_content(prompt)
        
        # Lưu kết quả vào cache để sau này xuất file Word/PDF
        report_cache["last_response"] = response.text
        
        return render_template('dashboard.html', 
                               table_html=df_display.head(10).to_html(classes='table table-hover', index=False),
                               ai_response=response.text,
                               cleaning_hints=cleaning_hints,
                               selected_style=style)
    except Exception as e:
        # In lỗi ra console để debug nếu cần
        print(f"DEBUG Error: {e}")
        return f"Lỗi hệ thống khi xử lý file: {e}"

@ai_bp.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get("question")
    context = session.get('excel_data')
    
    if not context: 
        return jsonify({"answer": "Vui lòng upload dữ liệu trước khi đặt câu hỏi!"})
    
    try:
        # AI trả lời dựa trên ngữ cảnh là dữ liệu Excel đã upload
        response = model.generate_content(f"Dữ liệu: {context}\nCâu hỏi: {user_input}")
        report_cache["last_response"] = response.text
        return jsonify({"answer": response.text})
    except Exception as e:
        return jsonify({"answer": f"Lỗi AI: {str(e)}"})

@ai_bp.route('/export/<format>')
def export_report(format):
    content = report_cache.get("last_response", "")
    if not content:
        return "Không có dữ liệu báo cáo để xuất!"

    if format == 'word':
        doc = Document()
        doc.add_heading('BÁO CÁO PHÂN TÍCH DỮ LIỆU', 0)
        doc.add_paragraph(content)
        
        stream = io.BytesIO()
        doc.save(stream)
        stream.seek(0)
        return send_file(stream, as_attachment=True, download_name="Bao_cao_AI.docx")
    
    # Xuất ra HTML (hoặc có thể mở rộng PDF ở đây)
    html = f"""
    <html>
        <head><meta charset='utf-8'></head>
        <body style='font-family:sans-serif; padding: 20px;'>
            <h1 style='color: #2c3e50;'>Báo cáo Phân tích từ AI Agent</h1>
            <hr>
            <div style='white-space: pre-wrap;'>{content}</div>
        </body>
    </html>
    """
    res = make_response(html)
    res.headers['Content-Disposition'] = 'attachment; filename=Bao_cao_AI.html'
    return res