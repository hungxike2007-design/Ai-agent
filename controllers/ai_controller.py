from flask import Blueprint, render_template, request, jsonify, session, send_file, make_response
import google.generativeai as genai
import pandas as pd
import io
from docx import Document
from services.data_processor import get_cleaning_suggestions
from services.report_service import get_report_prompt

ai_bp = Blueprint('ai', __name__)

# Cấu hình Gemini [cite: 160]
genai.configure(api_key="AQ.Ab8RN6IIXu_L9VBElwSKbafO6R6DO4qA9rW-3orT9NGDGSFPtA")
model = genai.GenerativeModel('gemini-flash-latest')

# Cache lưu trữ phản hồi AI mới nhất để xuất báo cáo [cite: 9]
report_cache = {"last_response": ""}

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
        # Chức năng gợi ý lỗi 
        cleaning_hints = get_cleaning_suggestions(df)
        
        # Tiền xử lý và lưu vào session [cite: 6]
        df_display = df.fillna("")
        session['excel_data'] = df_display.to_string()
        
        # Sinh báo cáo tự động theo phong cách 
        prompt = get_report_prompt(session['excel_data'], style)
        response = model.generate_content(prompt)
        report_cache["last_response"] = response.text
        
        return render_template('dashboard.html', 
                               table_html=df_display.head(10).to_html(classes='table table-hover', index=False),
                               ai_response=response.text,
                               cleaning_hints=cleaning_hints,
                               selected_style=style)
    except Exception as e:
        return f"Lỗi hệ thống: {e}"

@ai_bp.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get("question")
    context = session.get('excel_data')
    if not context: return jsonify({"answer": "Thiếu dữ liệu!"})
    
    response = model.generate_content(f"Dữ liệu: {context}\nCâu hỏi: {user_input}")
    report_cache["last_response"] = response.text
    return jsonify({"answer": response.text})

@ai_bp.route('/export/<format>')
def export_report(format):
    content = report_cache["last_response"]
    if format == 'word':
        doc = Document(); doc.add_heading('Báo cáo AI Agent', 0); doc.add_paragraph(content)
        stream = io.BytesIO(); doc.save(stream); stream.seek(0)
        return send_file(stream, as_attachment=True, download_name="Bao_cao.docx")
    
    # Xuất PDF đơn giản qua HTML 
    html = f"<html><body style='font-family:sans-serif;'><h1>Báo cáo</h1><p>{content}</p></body></html>"
    res = make_response(html); res.headers['Content-Disposition'] = 'attachment; filename=Bao_cao.html'
    return res