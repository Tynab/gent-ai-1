"""Giao diện Streamlit cơ bản cho trợ lý AI không lưu ngữ cảnh hỏi đáp."""

import streamlit as st

from dotenv import load_dotenv
from app_utils import DEFAULT_SYSTEM_PROMPT, request_chat_completion


load_dotenv()


def generate_response(user_input: str) -> str:
    """Gửi câu hỏi hiện tại lên model và trả về phản hồi văn bản."""
    return request_chat_completion(user_input, system_prompt=DEFAULT_SYSTEM_PROMPT)


st.set_page_config(page_title="Trợ lý AI", layout="wide")
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
