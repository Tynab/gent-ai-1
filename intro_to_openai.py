"""Ví dụ CLI tối giản để gọi OpenAI Chat Completions."""

from app_utils import load_openai_settings, request_chat_completion


def main() -> None:
    """Kiểm tra cấu hình ngay khi khởi động rồi nhận câu hỏi liên tục từ terminal."""
    try:
        load_openai_settings()
    except RuntimeError as error:
        raise SystemExit(f"Lỗi cấu hình: {error}")

    while True:
        try:
            user_input = input("Nhập câu hỏi: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nĐã dừng phiên CLI.")
            return

        if not user_input:
            print("Câu hỏi không được để trống, vui lòng nhập lại.")
            continue

        try:
            print(request_chat_completion(user_input))
        except KeyboardInterrupt:
            print("\nĐã dừng phiên CLI.")
            return
        except Exception as error:
            print(f"Không thể tạo câu trả lời: {error}")


if __name__ == "__main__":
    main()
