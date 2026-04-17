import streamlit as st
import pandas as pd
import google.generativeai as genai
import re # Thêm thư viện này để xử lý chuỗi an toàn

# 1. Cấu hình Gemini
# HÙNG LƯU Ý: Phải vào https://aistudio.google.com/ lấy Key bắt đầu bằng "AIza..."
API_KEY = "AQ.Ab8RN6LFaJJh_vzZUiBhWp0iGFf-VsGrbXYSTEKZezhDcuGFBg" # THAY ĐÚNG MÃ VÀO ĐÂY
genai.configure(api_key=API_KEY)

def get_ai_response(user_question, df):
    try:
        # Chuyển bảng dữ liệu thành văn bản
        data_context = df.to_string()
        
        # Tạo mẫu yêu cầu gửi cho AI (Prompt)
        prompt = f"""
        Bạn là một chuyên gia phân tích dữ liệu chuyên nghiệp. 
        Dữ liệu bảng tính:
        {data_context}
        
        Câu hỏi: {user_question}
        Yêu cầu: Trả lời ngắn gọn, chính xác bằng tiếng Việt. 
        Nếu có tiêu đề, hãy bắt đầu bằng dòng 'Tiêu đề: [Tên báo cáo]'.
        """
        
        # Gọi model
        model = genai.GenerativeModel('gemini-1.5-flash') # Dùng bản 1.5 mới nhất cho ổn định
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text
        else:
            return "AI không thể đưa ra phản hồi. Vui lòng kiểm tra lại nội dung câu hỏi."

    except Exception as e:
        # Nếu lỗi 401, thông báo cho người dùng biết là sai API Key
        if "401" in str(e):
            return "LỖI: API Key không hợp lệ (Mã 401). Vui lòng kiểm tra lại mã AIza trong cấu hình."
        return f"Có lỗi xảy ra khi gọi AI: {e}"

# --- PHẦN GIAO DIỆN STREAMLIT ---
st.set_page_config(page_title="AI Agent Phân Tích", layout="wide")
st.title("🤖 AI Agent - Phân Tích Dữ Liệu Excel")

st.sidebar.header("Cấu hình")
uploaded_file = st.sidebar.file_uploader("Chọn file dữ liệu (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("Đã tải dữ liệu thành công!")
    st.write("### Xem trước dữ liệu:")
    st.dataframe(df)

    st.divider()
    st.write("### 💬 Hỏi đáp về dữ liệu này")
    user_question = st.text_input("Nhập câu hỏi của bạn:")

    if user_question:
        with st.spinner("AI đang suy nghĩ..."):
            # Gọi hàm xử lý đã được bọc lỗi an toàn
            answer = get_ai_response(user_question, df)
            
            st.write("#### 🤖 Trả lời:")
            if "LỖI" in answer:
                st.error(answer)
            else:
                st.info(answer)
                # Lưu vào session để các hàm xuất file Word/PDF có thể lấy lại dữ liệu
                st.session_state['last_ai_response'] = answer
else:
    st.info("Vui lòng upload file Excel ở thanh bên trái để bắt đầu.")