"""Ví dụ CLI tối giản để gọi OpenAI Chat Completions."""

from dotenv import load_dotenv
from app_utils import request_chat_completion


def main() -> None:
    """Nạp cấu hình, nhận input từ terminal và in câu trả lời ra màn hình."""
    load_dotenv()

    try:
        user_input = input("Nhập câu hỏi: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("Đã hủy thao tác.")
        return

    if not user_input:
        raise RuntimeError("Câu hỏi không được để trống")

    response = request_chat_completion(user_input)
    print(response)


if __name__ == "__main__":
    while True:
        main()
