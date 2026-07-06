"""Giao diện Streamlit cơ bản cho trợ lý AI không lưu ngữ cảnh hỏi đáp."""

import streamlit as st

from app_utils import DEFAULT_SYSTEM_PROMPT, load_openai_settings, request_chat_completion


def generate_response(user_input: str) -> str:
    """Gửi câu hỏi hiện tại lên model và trả về phản hồi văn bản."""
    return request_chat_completion(user_input, system_prompt=DEFAULT_SYSTEM_PROMPT)


st.set_page_config(page_title="Trợ lý AI", layout="wide")

try:
    load_openai_settings()
except RuntimeError as error:
    st.error(f"Lỗi cấu hình: {error}")
    st.stop()

st.title("Trợ lý AI")
st.caption("Giao diện hỏi đáp cơ bản, phù hợp để thử nhanh model và prompt hệ thống.")

user_input = st.chat_input("Nhập câu hỏi của bạn:")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        response = generate_response(user_input)
    except Exception as error:
        st.error(f"Không thể tạo câu trả lời: {error}")
    else:
        with st.chat_message("assistant"):
            st.markdown(response)
