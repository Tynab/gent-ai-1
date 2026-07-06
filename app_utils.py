"""Tiện ích dùng chung cho các ví dụ OpenAI trong repo.

Module này tập trung phần cấu hình, tạo request và đọc/ghi lịch sử chat
để các script giao diện và CLI không bị lặp logic.
"""

from __future__ import annotations

import json
import os

from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

DEFAULT_SYSTEM_PROMPT = (
    "Bạn là một trợ lý AI hữu ích, thân thiện và thông minh. "
    "Hãy trả lời câu hỏi của người dùng một cách chi tiết và dễ hiểu."
)
CHAT_HISTORY_FILE = Path("chat_history.json")
VALID_CHAT_ROLES = {"user", "assistant"}


def load_openai_settings() -> tuple[str, str]:
    """Đọc cấu hình OpenAI từ biến môi trường và kiểm tra giá trị bắt buộc."""
    load_dotenv(override=False)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Thiếu biến môi trường OPENAI_API_KEY")

    model_name = os.getenv("OPENAI_MODEL", "").strip()
    if not model_name:
        raise RuntimeError("Thiếu biến môi trường OPENAI_MODEL")

    return api_key, model_name


def build_openai_client() -> tuple[OpenAI, str]:
    """Trả về OpenAI client cùng model đang được cấu hình."""
    api_key, model_name = load_openai_settings()
    return OpenAI(api_key=api_key), model_name


def build_messages(
    user_input: str,
    chat_history: list[dict[str, str]] | None = None,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> list[dict[str, str]]:
    """Ghép system prompt, lịch sử chat hợp lệ và câu hỏi hiện tại thành payload."""
    messages = [{"role": "system", "content": system_prompt}]

    for message in chat_history or []:
        role = message.get("role")
        content = message.get("content")
        if role in VALID_CHAT_ROLES and isinstance(content, str) and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_input})
    return messages


def request_chat_completion(
    user_input: str,
    chat_history: list[dict[str, str]] | None = None,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> str:
    """Gửi request tới OpenAI và trả về nội dung câu trả lời đã được rút gọn."""
    client, model_name = build_openai_client()
    response = client.chat.completions.create(
        model=model_name,
        messages=build_messages(user_input, chat_history, system_prompt),
    )
    return response.choices[0].message.content or ""


def load_chat_history(file_path: Path = CHAT_HISTORY_FILE) -> list[dict[str, str]]:
    """Đọc lịch sử chat từ file JSON, raise ValueError nếu dữ liệu sai cấu trúc."""
    if not file_path.exists():
        return []

    with file_path.open("r", encoding="utf-8") as file:
        raw_history = json.load(file)

    if not isinstance(raw_history, list):
        raise ValueError("Lịch sử chat phải là một danh sách")

    normalized_history: list[dict[str, str]] = []
    for message in raw_history:
        if not isinstance(message, dict):
            raise ValueError("Mỗi mục trong lịch sử chat phải là một object")

        role = message.get("role")
        content = message.get("content")
        if role not in VALID_CHAT_ROLES or not isinstance(content, str):
            raise ValueError("Mục lịch sử chat phải có role hợp lệ và content là chuỗi")

        normalized_history.append({"role": role, "content": content})

    return normalized_history


def save_chat_history(history: list[dict[str, str]], file_path: Path = CHAT_HISTORY_FILE) -> None:
    """Lưu lịch sử chat ra file JSON kiểu atomic (ghi file tạm rồi thay thế) để tránh file cụt."""
    temp_path = file_path.with_name(file_path.name + ".tmp")
    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)
    temp_path.replace(file_path)
