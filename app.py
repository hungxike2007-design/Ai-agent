import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. Cấu hình Gemini (Dán Key của bạn vào chỗ '...' nhé)
genai.configure(api_key="AQ.Ab8RN6LFaJJh_vzZUiBhWp0iGFf-VsGrbXYSTEKZezhDcuGFBg") # THAY MÃ CỦA BẠN VÀO ĐÂY
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Thêm cấu hình này để AI không bị chặn trả lời
generation_config = {
  "temperature": 0.9,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}
st.set_page_config(page_title="AI Agent Phân Tích", layout="wide")
st.title("🤖 AI Agent - Phân Tích Dữ Liệu Excel")

# 2. Giao diện Sidebar để Upload file
st.sidebar.header("Cấu hình")
uploaded_file = st.sidebar.file_uploader("Chọn file dữ liệu (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    # Đọc file Excel thành bảng dữ liệu (DataFrame)
    df = pd.read_excel(uploaded_file)
    st.success("Đã tải dữ liệu thành công!")
    
    # Hiển thị bảng dữ liệu lên màn hình
    st.write("### Xem trước dữ liệu:")
    st.dataframe(df.head(10))

    st.divider()
    
    # 3. Khu vực Hỏi - Đáp với AI
    st.write("### 💬 Hỏi đáp về dữ liệu này")
    user_question = st.text_input("Nhập câu hỏi của bạn (VD: Nhóm nào có điểm cao nhất?):")

    if user_question:
        with st.spinner("AI đang suy nghĩ..."):
            try:
                # Chuyển bảng dữ liệu thành văn bản để gửi cho AI đọc
                data_context = df.to_string()
                
                # Tạo mẫu yêu cầu gửi cho AI (Prompt)
                prompt = f"""
                Bạn là một chuyên gia phân tích dữ liệu. 
                Đây là dữ liệu của tôi:
                {data_context}
                
                Hãy trả lời câu hỏi sau dựa trên dữ liệu trên: {user_question}
                Trả lời ngắn gọn, chính xác bằng tiếng Việt.
                """
                
                # Gọi bộ não Gemini Pro
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                
                # Hiển thị câu trả lời của AI
                st.write("#### 🤖 Trả lời:")
                st.info(response.text)
                
            except Exception as e:
                st.error(f"Có lỗi xảy ra: {e}")
else:
    st.info("Vui lòng upload file Excel ở thanh bên trái để bắt đầu.")