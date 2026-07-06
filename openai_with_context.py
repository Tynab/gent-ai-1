"""Giao diện Streamlit có nhớ ngữ cảnh và lưu lịch sử chat vào file JSON."""

import streamlit as st

from app_utils import (
    CHAT_HISTORY_FILE,
    load_chat_history,
    load_openai_settings,
    request_chat_completion,
    save_chat_history,
)


def initialize_chat_history() -> None:
    """Nạp lịch sử chat từ file vào session state một lần cho mỗi session Streamlit."""
    if "chat_history" in st.session_state:
        return

    try:
        st.session_state.chat_history = load_chat_history(CHAT_HISTORY_FILE)
    except Exception as error:
        # File hỏng: sao lưu sang .bak để không ghi đè mất dữ liệu, rồi làm lại từ đầu.
        notice = f"Không thể tải lịch sử chat: {error}."
        if CHAT_HISTORY_FILE.exists():
            backup_path = CHAT_HISTORY_FILE.with_name(CHAT_HISTORY_FILE.name + ".bak")
            CHAT_HISTORY_FILE.replace(backup_path)
            notice += f" File cũ đã được sao lưu sang {backup_path.name}."
        st.warning(f"{notice} Phiên này bắt đầu với lịch sử mới.")
        st.session_state.chat_history = []


st.set_page_config(page_title="Trợ lý AI có ngữ cảnh", layout="wide")

# Fail fast: thiếu cấu hình thì báo lỗi ngay khi mở trang và dừng render.
try:
    load_openai_settings()
except RuntimeError as error:
    st.error(f"Lỗi cấu hình: {error}")
    st.stop()

initialize_chat_history()

st.title("Trợ lý AI có lưu ngữ cảnh")
st.caption("Ứng dụng Streamlit này tải lại lịch sử từ file JSON để giữ mạch hỏi đáp giữa các lần refresh.")

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Nhập câu hỏi của bạn:")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        # Lịch sử trong session lúc này CHƯA gồm câu hỏi hiện tại —
        # build_messages sẽ tự append, nhờ đó câu hỏi chỉ lên API đúng một lần.
        response = request_chat_completion(
            user_input, chat_history=st.session_state.chat_history
        )
    except Exception as error:
        st.error(f"Không thể tạo câu trả lời: {error}")
    else:
        with st.chat_message("assistant"):
            st.markdown(response)

        # Chỉ ghi nhận cặp hỏi-đáp sau khi thành công: API lỗi thì cả session
        # lẫn file đều không đổi, không cần rollback.
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        save_chat_history(st.session_state.chat_history, CHAT_HISTORY_FILE)
