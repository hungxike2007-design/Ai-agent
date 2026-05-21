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
    attempts = 0
    max_attempts = len(rotator._keys)
    last_err = None

    while attempts < max_attempts:
        try:
            api_key = rotator.get_current_api_key()
            
            from database import get_all_system_configs
            configs = get_all_system_configs()
            max_tokens = int(configs.get("MaxTokens", 8192))

            # Khởi tạo mô hình Chat của Langchain với Gemini
            llm = ChatGoogleGenerativeAI(
                model=target_model or GEMINI_MODEL_NAME,
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
                prefix=prefix
            )
            
            result = agent.invoke({"input": question})
            output = result.get("output", "")
            
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
            if ('not_found' in err_str or '404' in err_str) and target_model and target_model != GEMINI_MODEL_NAME:
                print(f"[PANDAS AGENT] Model '{target_model}' không tồn tại → Fallback về '{GEMINI_MODEL_NAME}'")
                target_model = None  # Lần thử tiếp sẽ dùng GEMINI_MODEL_NAME
                continue
            
            # Sử dụng phương thức kiểm tra lỗi từ rotator
            if rotator._is_rotatable_error(e):
                print(f"[PANDAS AGENT] Key #{rotator._index + 1} gặp lỗi ({str(e)[:50]}...) → Đang xoay key...")
                rotator._rotate()
                attempts += 1
            else:
                # Nếu là lỗi khác không liên quan đến key/quota thì throw luôn
                break

    print(f"[PANDAS AGENT ERROR] {last_err}")
    return f"Xin lỗi, có lỗi xảy ra khi thực thi phân tích chuyên sâu sau {attempts+1} lần thử. Lỗi: {last_err}"
