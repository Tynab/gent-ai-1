"""Giao diện Streamlit có nhớ ngữ cảnh và lưu lịch sử chat vào file JSON."""

import streamlit as st

from dotenv import load_dotenv
from app_utils import (
    CHAT_HISTORY_FILE,
    DEFAULT_SYSTEM_PROMPT,
    load_chat_history,
    request_chat_completion,
    save_chat_history,
)


load_dotenv()


def generate_response(user_input: str) -> str:
    """Sinh câu trả lời dựa trên lịch sử chat trong session hiện tại."""
    return request_chat_completion(
        user_input,
        chat_history=st.session_state.chat_history,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
    )


def initialize_chat_history() -> None:
    """Nạp lịch sử chat từ file vào session state một lần cho mỗi session Streamlit."""
    if "chat_history" in st.session_state:
        return

    try:
        st.session_state.chat_history = load_chat_history(CHAT_HISTORY_FILE)
    except Exception as error:
        st.warning(f"Không thể tải lịch sử chat: {error}. Sẽ khởi tạo lịch sử mới.")
        st.session_state.chat_history = []


st.set_page_config(page_title="Trợ lý AI có ngữ cảnh", layout="wide")
initialize_chat_history()

st.title("Trợ lý AI có lưu ngữ cảnh")
st.caption("Ứng dụng Streamlit này tải lại lịch sử từ file JSON để giữ mạch hỏi đáp giữa các lần refresh.")

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Nhập câu hỏi của bạn:")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        response = generate_response(user_input)
    except Exception as error:
        st.error(f"Không thể tạo câu trả lời: {error}")
        st.session_state.chat_history.pop()
    else:
        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state.chat_history.append({"role": "assistant", "content": response})
        save_chat_history(st.session_state.chat_history, CHAT_HISTORY_FILE)
