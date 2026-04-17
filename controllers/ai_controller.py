from flask import Blueprint, render_template, request, jsonify, session, send_file, make_response
import google.generativeai as genai
import pandas as pd
import io
import os
from docx import Document
from services.data_processor import get_cleaning_suggestions
from services.report_service import get_report_prompt
from database import get_connection

ai_bp = Blueprint('ai', __name__)

# --- CẤU HÌNH GEMINI --- 
API_KEY = "AQ.Ab8RN6KdpiL6uhDBziFvxmSKBTobtzicrQ7qTJXo7o1uX_BaCg"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

report_cache = {"last_response": ""}

@ai_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@ai_bp.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    style = request.form.get('style_preference', 'Kỹ thuật')
    user_id = session.get('user_id')

    if not file: return "Chưa chọn file!"
    if not user_id: return "Vui lòng đăng nhập lại!"

    try:
        # 1. Đọc và xử lý Excel
        df = pd.read_excel(file)
        filename = file.filename
        cleaning_hints = get_cleaning_suggestions(df)
        df_display = df.fillna("")
        session['excel_data'] = df_display.to_string()
        
        # 2. LƯU FILE VÀO DATABASE (Bảng ExcelFiles)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ExcelFiles (UserID, FileName, FilePath, UploadDate, Status) 
            OUTPUT INSERTED.FileID 
            VALUES (?, ?, ?, GETDATE(), 'Success')""", 
            (user_id, filename, f"uploads/{filename}"))
        file_id = cursor.fetchone()[0]
        
        # 3. TẠO PHIÊN CHAT MỚI VỚI TIÊU ĐỀ RÚT GỌN BẰNG AI
        try:
            # Nhờ AI đặt tên ngắn gọn dựa trên 5 dòng đầu của dữ liệu để tiết kiệm token
            name_prompt = f"Dựa trên dữ liệu này, hãy đặt 1 tiêu đề cực ngắn (tối đa 5 từ) để mô tả nội dung file '{filename}':\n{df.head(5).to_string()}"
            name_response = model.generate_content(name_prompt)
            short_title = name_response.text.strip().replace("*", "").replace('"', '')
        except:
            # Nếu AI lỗi, dùng mặc định nhưng ngắn gọn hơn
            short_title = f"File: {filename[:20]}"

        cursor.execute("""
            INSERT INTO ChatSessions (UserID, FileID, StartTime, SessionTitle) 
            OUTPUT INSERTED.SessionID 
            VALUES (?, ?, GETDATE(), ?)""", 
            (user_id, file_id, short_title))
        session_id = cursor.fetchone()[0]
        session['current_session_id'] = session_id 
        conn.commit()

        # 4. GỌI AI TẠO BÁO CÁO BAN ĐẦU
        prompt = get_report_prompt(session['excel_data'], style)
        response = model.generate_content(prompt)
        report_content = response.text
        report_cache["last_response"] = report_content

        # 5. LƯU NỘI DUNG BÁO CÁO VÀO BẢNG REPORTS
        try:
            summary_text = report_content[:200] + "..." if len(report_content) > 200 else report_content
            
            sql_report = """
                INSERT INTO Reports (FileID, [Content], CreatedDate, Summary) 
                VALUES (?, ?, GETDATE(), ?)
            """
            cursor.execute(sql_report, (file_id, report_content, summary_text))
            conn.commit()
        except Exception as db_err:
            print(f"Lỗi khi lưu vào bảng Reports: {db_err}")

        conn.close()
        
        return render_template('dashboard.html', 
                               table_html=df_display.head(10).to_html(classes='table table-hover', index=False),
                               ai_response=report_content,
                               cleaning_hints=cleaning_hints,
                               selected_style=style)
    except Exception as e:
        return f"Lỗi hệ thống: {e}"

@ai_bp.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question')
    excel_data = session.get('excel_data', "Không có dữ liệu bảng.")
    session_id = session.get('current_session_id') # Lấy ID phiên từ lúc upload

    try:
        user_id = int(session.get('user_id'))
    except:
        return jsonify({"answer": "Vui lòng đăng nhập lại."}), 400

    # Nếu chưa có session_id (người dùng chưa upload file mà đã hỏi), tạo mới
    if not session_id:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ChatSessions (UserID, StartTime, SessionTitle) OUTPUT INSERTED.SessionID VALUES (?, GETDATE(), ?)", 
                       (user_id, question[:50]))
        session_id = cursor.fetchone()[0]
        session['current_session_id'] = session_id
        conn.commit()
        conn.close()

    try:
        # 1. Tạo tiêu đề bằng AI
        try:
            title_prompt = f"Tóm tắt ngắn gọn câu hỏi này làm tiêu đề lịch sử (max 5 từ): '{question}'"
            title_response = model.generate_content(title_prompt)
            title = title_response.text.strip().replace("*", "").replace('"', '')
        except:
            title = question[:50]

        # 2. Gọi AI phân tích dữ liệu
        full_prompt = f"Dữ liệu: {excel_data}\n\nCâu hỏi: {question}\n\nTrả lời ngắn gọn, chính xác."
        response = model.generate_content(full_prompt)
        answer = response.text
        
        # 3. LƯU VÀO DATABASE (Cả SessionTitle và ChatMessages)
        conn = get_connection()
        cursor = conn.cursor()
        
        # Cập nhật lại tiêu đề phiên chat cho hay hơn (nếu cần)
        cursor.execute("UPDATE ChatSessions SET SessionTitle = ? WHERE SessionID = ?", (title, session_id))
        
        # Lưu tin nhắn của Người dùng và AI (Quan trọng để hiện lịch sử)
        # Sử dụng [Content] vì đây là từ khóa trong SQL
        cursor.execute("INSERT INTO ChatMessages (SessionID, Role, [Content], CreatedAt) VALUES (?, 'user', ?, GETDATE())", (session_id, question))
        cursor.execute("INSERT INTO ChatMessages (SessionID, Role, [Content], CreatedAt) VALUES (?, 'assistant', ?, GETDATE())", (session_id, answer))
        
        conn.commit()
        conn.close()
        
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"answer": f"Lỗi: {str(e)}"}), 500

@ai_bp.route('/history')
def history():
    user_id = session.get('user_id')
    # Nếu không có user_id trong session (chưa đăng nhập), trả về danh sách trống
    if not user_id: 
        return jsonify([])
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # CHỐT chặn quan trọng: Chỉ lấy những phiên chat mà UserID khớp với người đang đăng nhập
        sql = """
            SELECT SessionID, SessionTitle 
            FROM ChatSessions 
            WHERE UserID = ? 
            ORDER BY StartTime DESC
        """
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return jsonify([{"id": row[0], "title": row[1]} for row in rows])
    except Exception as e:
        print(f"Lỗi history: {e}")
        return jsonify([])

@ai_bp.route('/export_report') # Sửa tên route để hết lỗi 404
def export_report():
    format_type = request.args.get('format', 'word')
    session_id = request.args.get('session_id')
    
    content = ""

    # 1. Nếu có session_id (từ lịch sử), ưu tiên lấy nội dung từ Database
    if session_id:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            # Join bảng ChatSessions và Reports để lấy đúng nội dung báo cáo của file đó
            sql = """
                SELECT r.[Content] 
                FROM Reports r
                JOIN ChatSessions s ON r.FileID = s.FileID
                WHERE s.SessionID = ?
            """
            cursor.execute(sql, (session_id,))
            row = cursor.fetchone()
            if row:
                content = row[0]
            conn.close()
        except Exception as e:
            print(f"Lỗi DB khi xuất file: {e}")

    # 2. Nếu không tìm thấy trong DB (hoặc không có session_id), mới dùng cache
    if not content:
        content = report_cache.get("last_response", "")

    # 3. Kiểm tra dữ liệu cuối cùng
    if not content: 
        return "Không có dữ liệu để xuất! Hãy chọn một phiên chat có dữ liệu."

    # --- TIẾN HÀNH XUẤT FILE ---
    if format_type == 'word':
        doc = Document()
        doc.add_heading('BÁO CÁO PHÂN TÍCH DỮ LIỆU', 0)
        doc.add_paragraph(content)
        stream = io.BytesIO()
        doc.save(stream)
        stream.seek(0)
        return send_file(stream, as_attachment=True, download_name="Bao_cao_AI.docx")
    
    # Xuất PDF (Dạng HTML)
    html = f"""
    <html>
        <head><meta charset="utf-8"></head>
        <body style='font-family:sans-serif; padding:20px; line-height:1.6;'>
            <h1 style='color:#2c3e50;'>Báo cáo phân tích</h1>
            <hr>
            <div style='white-space: pre-wrap;'>{content}</div>
        </body>
    </html>
    """
    res = make_response(html)
    res.headers['Content-Disposition'] = 'attachment; filename=Bao_cao_AI.html'
    return res

# --- CÁC HÀM CŨ ĐỂ TƯƠNG THÍCH (NẾU CẦN) ---
def save_chat_session(user_id, title, file_id=None):
    # Hàm này giờ đã được tích hợp trực tiếp vào luồng /ask để tối ưu hơn
    pass

def get_user_chat_history(user_id):
    # Hàm này đã được tích hợp vào luồng /history
    pass

@ai_bp.route('/get_session/<int:session_id>')
def get_session(session_id):
    user_id = session.get('user_id')
    if not user_id: 
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Lấy FilePath từ bảng ExcelFiles thông qua ChatSessions
        sql_file = """
            SELECT f.FilePath, f.FileName 
            FROM ChatSessions s
            JOIN ExcelFiles f ON s.FileID = f.FileID
            WHERE s.SessionID = ? AND s.UserID = ?
        """
        cursor.execute(sql_file, (session_id, user_id))
        file_data = cursor.fetchone()

        # 2. Lấy danh sách tin nhắn
        cursor.execute("SELECT Role, [Content] FROM ChatMessages WHERE SessionID = ? ORDER BY CreatedAt ASC", (session_id,))
        messages = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]

        # 3. Đọc dữ liệu Excel để hiển thị lại bảng
        table_html = ""
        if file_data and os.path.exists(file_data[0]):
            df = pd.read_excel(file_data[0])
            table_html = df.head(10).to_html(classes='table table-hover', index=False)
            # Cập nhật lại dữ liệu vào session để người dùng có thể chat tiếp với file này
            session['excel_data'] = df.fillna("").to_string()
        
        session['current_session_id'] = session_id
        conn.close()

        return jsonify({
            "messages": messages,
            "table_html": table_html,
            "filename": file_data[1] if file_data else "Unknown"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500