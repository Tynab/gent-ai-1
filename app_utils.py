"""Tiện ích dùng chung cho các ví dụ OpenAI trong repo.

Module này gom phần cấu hình, khởi tạo client, tạo payload messages và
đọc/ghi lịch sử chat để các entry point (CLI lẫn Streamlit) không lặp logic.
"""

from __future__ import annotations

import json
import os
import tempfile

from functools import lru_cache
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Kiểu dùng chung cho lịch sử chat: mỗi message là {"role": ..., "content": ...}.
ChatMessage = dict[str, str]
ChatHistory = list[ChatMessage]

DEFAULT_SYSTEM_PROMPT = (
    "Bạn là một trợ lý AI hữu ích, thân thiện và thông minh. "
    "Hãy trả lời câu hỏi của người dùng một cách chi tiết và dễ hiểu."
)
# Neo file lịch sử theo thư mục chứa module: chạy app từ thư mục nào
# cũng dùng đúng một file tại repo root (tránh "mất lịch sử" khi chạy sai chỗ).
CHAT_HISTORY_FILE = Path(__file__).resolve().parent / "chat_history.json"
VALID_CHAT_ROLES = {"user", "assistant"}


def load_openai_settings() -> tuple[str, str]:
    """Đọc cấu hình OpenAI từ biến môi trường, raise RuntimeError nếu thiếu.

    Được gọi fail-fast ngay khi khởi động ở cả 3 entry point. Vì
    load_dotenv(override=False), biến đã có trong môi trường luôn thắng
    file .env, và sửa .env giữa chừng cần restart mới có tác dụng.
    """
    load_dotenv(override=False)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Thiếu biến môi trường OPENAI_API_KEY")

    model_name = os.getenv("OPENAI_MODEL", "").strip()
    if not model_name:
        raise RuntimeError("Thiếu biến môi trường OPENAI_MODEL")

    return api_key, model_name


@lru_cache(maxsize=1)
def build_openai_client() -> tuple[OpenAI, str]:
    """Trả về OpenAI client cùng model đang cấu hình, cache cho cả tiến trình.

    Client chỉ tạo một lần: env đã bất biến trong tiến trình (override=False)
    nên tạo lại mỗi request là thừa. Test reset bằng build_openai_client.cache_clear().
    """
    api_key, model_name = load_openai_settings()
    return OpenAI(api_key=api_key), model_name


def build_messages(
    user_input: str,
    chat_history: ChatHistory | None = None,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> ChatHistory:
    """Ghép system prompt, lịch sử hợp lệ và câu hỏi hiện tại thành payload."""
    messages: ChatHistory = [{"role": "system", "content": system_prompt}]

    # Lọc êm entry không hợp lệ (khác load_chat_history vốn raise): lịch sử
    # trong session có thể đến từ nhiều nguồn, bỏ qua entry hỏng vẫn trả lời được.
    for message in chat_history or []:
        role = message.get("role")
        content = message.get("content")
        if role in VALID_CHAT_ROLES and isinstance(content, str) and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_input})
    return messages


def request_chat_completion(
    user_input: str,
    chat_history: ChatHistory | None = None,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> str:
    """Gửi request tới OpenAI và trả về nội dung trả lời dạng chuỗi."""
    client, model_name = build_openai_client()
    response = client.chat.completions.create(
        model=model_name,
        messages=build_messages(user_input, chat_history, system_prompt),
    )
    # Model có thể trả content None (hiếm) — chuẩn hóa về chuỗi rỗng cho UI.
    return response.choices[0].message.content or ""


def load_chat_history(file_path: Path = CHAT_HISTORY_FILE) -> ChatHistory:
    """Đọc lịch sử chat từ file JSON, raise ValueError nếu dữ liệu sai cấu trúc.

    Chủ đích raise thay vì lọc êm: để nơi gọi tự quyết cách xử lý file hỏng
    (openai_with_context.py chọn sao lưu file sang .bak rồi làm lại từ đầu).
    """
    if not file_path.exists():
        return []

    with file_path.open("r", encoding="utf-8") as file:
        raw_history = json.load(file)

    if not isinstance(raw_history, list):
        raise ValueError("Lịch sử chat phải là một danh sách")

    normalized_history: ChatHistory = []
    for message in raw_history:
        if not isinstance(message, dict):
            raise ValueError("Mỗi mục trong lịch sử chat phải là một object")

        role = message.get("role")
        content = message.get("content")
        if role not in VALID_CHAT_ROLES or not isinstance(content, str):
            raise ValueError("Mục lịch sử chat phải có role hợp lệ và content là chuỗi")

        normalized_history.append({"role": role, "content": content})

    return normalized_history


def save_chat_history(history: ChatHistory, file_path: Path = CHAT_HISTORY_FILE) -> None:
    """Lưu lịch sử chat ra file JSON kiểu atomic để tránh file cụt giữa chừng."""
    # File tạm đặt tên duy nhất (mkstemp) thay vì tên cố định: nhiều session/tiến
    # trình ghi đồng thời (vd. 2 tab Streamlit) sẽ không còn đụng độ trên cùng một
    # file tạm gây PermissionError trên Windows. Nếu ghi hoặc replace lỗi giữa
    # chừng, file tạm được dọn dẹp và file lịch sử gốc vẫn nguyên vẹn.
    fd, temp_name = tempfile.mkstemp(
        dir=file_path.parent, prefix=file_path.name + ".", suffix=".tmp"
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(history, file, ensure_ascii=False, indent=2)
        temp_path.replace(file_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
