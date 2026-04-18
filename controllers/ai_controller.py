from flask import Blueprint, render_template, request, jsonify, session, send_file, make_response
import google.generativeai as genai
import pandas as pd
import io
import os
import uuid
from docx import Document
from services.data_processor import get_cleaning_suggestions
from services.report_service import get_report_prompt
from database import get_connection

ai_bp = Blueprint('ai', __name__)

# --- CẤU HÌNH GEMINI --- 
API_KEY = "AQ.Ab8RN6LlYOyrJwj0J_NdqytUZOd2e7IJ0h0pYAQDxRCQohm2Bw"
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
    
# --- API ĐỔI TÊN PHIÊN CHAT ---
@ai_bp.route('/rename_session/<int:session_id>', methods=['POST'])
def rename_session(session_id):
    data = request.json
    new_title = data.get('new_title')
    user_id = session.get('user_id')

    if not new_title:
        return jsonify({"error": "Tiêu đề không được để trống"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Chỉ cho phép đổi tên nếu phiên chat đó thuộc về user đang đăng nhập
        cursor.execute("UPDATE ChatSessions SET SessionTitle = ? WHERE SessionID = ? AND UserID = ?", 
                       (new_title, session_id, user_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Đã đổi tên thành công"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- API CHIA SẺ PHIÊN CHAT ---
@ai_bp.route('/share_session/<int:session_id>', methods=['POST'])
def share_session(session_id):
    user_id = session.get('user_id')
    share_token = str(uuid.uuid4()) # Tạo chuỗi định danh duy nhất

    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Lấy FileID từ ChatSession
        cursor.execute("SELECT FileID FROM ChatSessions WHERE SessionID = ? AND UserID = ?", (session_id, user_id))
        row = cursor.fetchone()
        
        if not row or not row[0]:
            return jsonify({"error": "Không tìm thấy báo cáo để chia sẻ"}), 404
        
        file_id = row[0]

        # 2. Cập nhật ShareToken vào bảng Reports (hoặc tạo mới nếu chưa có)
        # Theo ERD của bạn, ShareToken nằm ở bảng Reports
        cursor.execute("UPDATE Reports SET ShareToken = ?, IsPublic = 1 WHERE FileID = ?", (share_token, file_id))
        
        conn.commit()
        conn.close()
        return jsonify({"share_url": f"/ai/view_shared/{share_token}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- API XÓA SẠCH SESSION ---
@ai_bp.route('/delete_session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    user_id = session.get('user_id')
    
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Lấy FilePath và FileID trước khi xóa để xử lý file vật lý
        sql_info = """
            SELECT f.FilePath, f.FileID 
            FROM ChatSessions s
            JOIN ExcelFiles f ON s.FileID = f.FileID
            WHERE s.SessionID = ? AND s.UserID = ?
        """
        cursor.execute(sql_info, (session_id, user_id))
        info = cursor.fetchone()

        if info:
            file_path = info[0]
            file_id = info[1]

            # 2. Xóa tin nhắn trong ChatMessages (Ràng buộc khóa ngoại)
            cursor.execute("DELETE FROM ChatMessages WHERE SessionID = ?", (session_id,))
            
            # 3. Xóa báo cáo trong Reports
            cursor.execute("DELETE FROM Reports WHERE FileID = ?", (file_id,))

            # 4. Xóa phiên chat trong ChatSessions
            cursor.execute("DELETE FROM ChatSessions WHERE SessionID = ?", (session_id,))

            # 5. Xóa file trong ExcelFiles
            cursor.execute("DELETE FROM ExcelFiles WHERE FileID = ?", (file_id,))

            # 6. Xóa file vật lý trên ổ cứng (nếu tồn tại)
            if os.path.exists(file_path):
                os.remove(file_path)

            conn.commit()
            return jsonify({"success": True, "message": "Đã xóa sạch toàn bộ dữ liệu liên quan"})
        else:
            return jsonify({"error": "Không tìm thấy phiên chat hoặc bạn không có quyền xóa"}), 404

    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@ai_bp.route('/view_shared/<token>')
def view_shared(token):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Truy vấn nội dung báo cáo và thông tin file dựa trên ShareToken
        # IsPublic = 1 để đảm bảo báo cáo này đã được người dùng cho phép chia sẻ
        sql = """
            SELECT r.[Content], f.FileName, r.CreatedDate, f.FilePath
            FROM Reports r
            JOIN ExcelFiles f ON r.FileID = f.FileID
            WHERE r.ShareToken = ? AND r.IsPublic = 1
        """
        cursor.execute(sql, (token,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return "<h3>Link chia sẻ không tồn tại hoặc đã bị gỡ bỏ.</h3>", 404

        report_content = row[0]
        filename = row[1]
        created_date = row[2]
        file_path = row[3]

        # Đọc dữ liệu Excel để hiển thị bảng xem trước (preview) cho người xem
        table_html = ""
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path)
                table_html = df.head(15).to_html(classes='table table-bordered table-striped', index=False)
            except Exception as e:
                table_html = f"<p>Không thể hiển thị bản xem trước dữ liệu: {e}</p>"

        conn.close()

        # Render ra một template riêng cho người xem (ví dụ: shared_report.html)
        # Nếu chưa có file html riêng, bạn có thể tạo nhanh hoặc dùng render_template
        return render_template('shared_view.html', 
                               content=report_content, 
                               filename=filename, 
                               date=created_date, 
                               table_preview=table_html)

    except Exception as e:
        return f"Lỗi hệ thống khi tải báo cáo: {str(e)}", 500