import time
import pandas as pd
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from database import get_key_rotator, GEMINI_MODEL_NAME

def ask_pandas_agent(df: pd.DataFrame, question: str, target_model: str = None) -> str:
    """
    Sử dụng LangChain Pandas Agent (Code Interpreter) để phân tích bảng dữ liệu.
    Agent sẽ tự động sinh mã Python (Pandas) chạy dưới nền để tìm câu trả lời chính xác.
    """
    rotator = get_key_rotator()
    
    models_to_try = []
    if target_model:
        models_to_try.append(target_model)
    if GEMINI_MODEL_NAME not in models_to_try:
        models_to_try.append(GEMINI_MODEL_NAME)
        
    # Danh sách model dự phòng
    fallback_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-pro-latest"]
    for m in fallback_models:
        if m not in models_to_try:
            models_to_try.append(m)

    last_err = None

    for current_model in models_to_try:
        attempts = 0
        max_attempts = len(rotator._keys)
        
        while attempts < max_attempts:
            try:
                api_key = rotator.get_current_api_key()
                
                from database import get_all_system_configs
                configs = get_all_system_configs()
                max_tokens = int(configs.get("MaxTokens", 8192))
    
                # Khởi tạo mô hình Chat của Langchain với Gemini
                llm = ChatGoogleGenerativeAI(
                    model=current_model,
                    temperature=0,
                    google_api_key=api_key,
                    max_output_tokens=max_tokens
                )
                
                prefix = (
                    "Bạn là một chuyên gia phân tích dữ liệu Excel chuyên nghiệp. "
                    "Khi xử lý dữ liệu, hãy luôn chú ý:\n"
                    "1. Kiểm tra và chuẩn hóa kiểu dữ liệu (pd.to_numeric, pd.to_datetime) trước khi tính toán.\n"
                    "2. Sử dụng Pivot Tables (pd.pivot_table) cho các câu hỏi tổng hợp đa chiều.\n"
                    "3. Tự động xử lý dữ liệu trống (fillna) hoặc trùng lặp (drop_duplicates) nếu thấy cần thiết để kết quả chính xác.\n"
                    "4. Nếu người dùng yêu cầu so sánh, hãy dùng các kỹ thuật GroupBy hoặc Merge/Join.\n"
                    "Luôn trả lời bằng tiếng Việt, ngắn gọn và trình bày bằng Markdown (bảng, danh sách)."
                )
    
                agent = create_pandas_dataframe_agent(
                    llm,
                    df,
                    verbose=False,
                    allow_dangerous_code=True,
                    agent_type="tool-calling",
                    handle_parsing_errors=True,
                    prefix=prefix,
                    max_iterations=10
                )
                
                result = agent.invoke({"input": question})
                output = result.get("output", "")
                
                # Bắt lỗi vòng lặp của LangChain Agent
                if isinstance(output, str) and "Agent stopped due to max iterations" in output:
                    return "## ⏳ Dữ liệu quá phức tạp\n\nAI đã thử nhiều cách phân tích nhưng chưa đưa ra được kết luận cuối cùng vì câu hỏi quá chung chung hoặc dữ liệu quá rắc rối.\n\n**💡 Mẹo:** Hãy chia nhỏ câu hỏi ra, hoặc sử dụng tính năng **Tạo báo cáo AI** (nút màu xanh ở trên cùng) để AI phân tích toàn diện."                
                # Xử lý nếu AI trả về list các block (thường gặp ở model flash mới)
                if isinstance(output, list):
                    clean_text = ""
                    for block in output:
                        if isinstance(block, dict) and "text" in block:
                            clean_text += block["text"]
                        else:
                            clean_text += str(block)
                    return clean_text.strip()
                    
                return str(output)
                
            except Exception as e:
                last_err = e
                err_str = str(e).lower()
                
                # Nếu model bị 404 NOT_FOUND → fallback về model mặc định
                if 'not_found' in err_str or '404' in err_str:
                    print(f"[PANDAS AGENT] Model '{current_model}' không tồn tại → Chuyển sang model dự phòng")
                    break
                
                # Sử dụng phương thức kiểm tra lỗi từ rotator
                if rotator._is_rotatable_error(e):
                    print(f"[PANDAS AGENT] Model '{current_model}' - Key #{rotator._index + 1} gặp lỗi ({str(e)[:50]}...) → Đợi 10s và xoay key...")
                    time.sleep(10)  # Nghỉ 10 giây để hạ nhiệt Rate Limit trước khi thử lại
                    rotator._rotate()
                    attempts += 1
                else:
                    # Nếu là lỗi khác không liên quan đến key/quota thì throw luôn
                    break
        
        print(f"[PANDAS AGENT] Model '{current_model}' đã thử hết các key. Đang chuyển sang model dự phòng...")

    print(f"[PANDAS AGENT ERROR] {last_err}")
    err_str = str(last_err).lower()
    if 'quota' in err_str or 'resource exhausted' in err_str or '429' in err_str:
        return "## ⚠️ Hết Hạn Mức API\n\nHệ thống đã thử xoay vòng các key nhưng đều báo hết hạn mức. Vui lòng thêm API Key mới hoặc đợi khoảng 1 phút rồi thử lại."
    elif any(k in err_str for k in ['api_key', 'invalid', 'unauthenticated']):
        return "## 🔑 API Key Không Hợp Lệ\n\nVui lòng kiểm tra lại cấu hình API Key trong hệ thống."
    else:
        return f"## ❌ Lỗi Xử Lý Dữ Liệu\n\nXin lỗi, có lỗi xảy ra khi phân tích chuyên sâu. Vui lòng đặt câu hỏi theo cách khác."
