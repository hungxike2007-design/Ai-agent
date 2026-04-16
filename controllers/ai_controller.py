<<<<<<< Updated upstream
from flask import Blueprint, render_template, request, jsonify, session, send_file, make_response
=======
from flask import Blueprint, render_template, request, jsonify, send_file, session, make_response
>>>>>>> Stashed changes
import google.generativeai as genai
import pandas as pd
import io
from docx import Document
from services.data_processor import get_cleaning_suggestions
from services.report_service import get_report_prompt

ai_bp = Blueprint('ai', __name__)

<<<<<<< Updated upstream
# Cấu hình Gemini [cite: 160]
genai.configure(api_key="AIzaSyCOYbNAyyazkuRw_p_VJHam_MpaygKBo_0")
model = genai.GenerativeModel('gemini-flash-latest')

# Cache lưu trữ phản hồi AI mới nhất để xuất báo cáo [cite: 9]
report_cache = {"last_response": ""}
=======
# Cấu hình AI
genai.configure(api_key="AQ.Ab8RN6JkolKnP0thWfKNhhqDz0CvV1sgS0_o7C9J3xSEjB3VMQ")
model = genai.GenerativeModel('gemini-flash-latest')

# Biến tạm lưu kết quả phân tích mới nhất để xuất file
data_cache = {
    "last_ai_response": ""
}
>>>>>>> Stashed changes

@ai_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@ai_bp.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
<<<<<<< Updated upstream
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
=======
    style = request.form.get('style_preference', 'Phổ thông') # Tùy chỉnh phong cách 

    if not file:
        return "Không có file!"

    try:
        df = pd.read_excel(file)
        
        # 1. Gọi chức năng Gợi ý dữ liệu lỗi (Quét dòng trống, giá trị âm) 
        cleaning_hints = get_cleaning_suggestions(df)
        
        # 2. Tiền xử lý để hiển thị và phân tích
        df_display = df.fillna("") 
        session['excel_data'] = df_display.to_string() # Lưu vào session để dùng cho /ask và /generate-report
        
        # 3. Sinh tóm tắt ban đầu dựa trên phong cách đã chọn 
        final_prompt = get_report_prompt(session['excel_data'], style)
        response = model.generate_content(final_prompt)
        data_cache["last_ai_response"] = response.text
        
        table_html = df_display.head(10).to_html(classes='data-table', index=False)
        
        return render_template('dashboard.html', 
                               table_html=table_html, 
                               ai_response=response.text,
                               cleaning_hints=cleaning_hints,
                               file_name=file.filename)
    except Exception as e:
        return f"Lỗi xử lý file: {e}"
>>>>>>> Stashed changes

@ai_bp.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get("question")
<<<<<<< Updated upstream
    context = session.get('excel_data')
    if not context: return jsonify({"answer": "Thiếu dữ liệu!"})
    
    response = model.generate_content(f"Dữ liệu: {context}\nCâu hỏi: {user_input}")
    report_cache["last_response"] = response.text
    return jsonify({"answer": response.text})

=======
    context = session.get('excel_data') # Lấy từ session cho đồng bộ
    
    if not context:
        return jsonify({"answer": "Bạn chưa tải file lên!"})
        
    prompt = f"Dựa trên dữ liệu: {context}\n\nTrả lời câu hỏi: {user_input}"
    response = model.generate_content(prompt)
    
    data_cache["last_ai_response"] = response.text
    return jsonify({"answer": response.text})

@ai_bp.route('/generate-report', methods=['POST'])
def generate_report():
    style = request.form.get('style_preference') 
    data_summary = session.get('excel_data')
    
    if not data_summary:
        return jsonify({"error": "Chưa có dữ liệu Excel"}), 400
        
    final_prompt = get_report_prompt(data_summary, style)
    response = model.generate_content(final_prompt)
    data_cache["last_ai_response"] = response.text
    
    return jsonify({"report_content": response.text})

>>>>>>> Stashed changes
@ai_bp.route('/export/<format>')
def export_report(format):
    content = report_cache["last_response"]
    if format == 'word':
<<<<<<< Updated upstream
        doc = Document(); doc.add_heading('Báo cáo AI Agent', 0); doc.add_paragraph(content)
        stream = io.BytesIO(); doc.save(stream); stream.seek(0)
        return send_file(stream, as_attachment=True, download_name="Bao_cao.docx")
    
    # Xuất PDF đơn giản qua HTML 
    html = f"<html><body style='font-family:sans-serif;'><h1>Báo cáo</h1><p>{content}</p></body></html>"
    res = make_response(html); res.headers['Content-Disposition'] = 'attachment; filename=Bao_cao.html'
    return res
=======
        doc = Document()
        doc.add_heading('BÁO CÁO PHÂN TÍCH AI', 0)
        doc.add_paragraph(content)
        
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        return send_file(file_stream, as_attachment=True, download_name="Bao_cao_Ai_Agent.docx")

    elif format == 'pdf':
        # Xuất báo cáo đa định dạng: PDF, Word 
        html_content = f"""
        <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: sans-serif; padding: 50px; }}
                    h1 {{ color: #28a745; }}
                    .content {{ white-space: pre-wrap; }}
                </style>
            </head>
            <body>
                <h1>BÁO CÁO PHÂN TÍCH DỮ LIỆU</h1>
                <div class="content">{content}</div>
            </body>
        </html>
        """
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename=Bao_cao_Ai_Agent.html'
        return response

    return "Định dạng không hỗ trợ"
>>>>>>> Stashed changes
