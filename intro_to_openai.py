"""Ví dụ CLI tối giản để gọi OpenAI Chat Completions."""

from app_utils import load_openai_settings, request_chat_completion


def main() -> None:
    """Kiểm tra cấu hình ngay khi khởi động rồi nhận câu hỏi liên tục từ terminal."""
    # Fail fast: thiếu cấu hình thì in lỗi và thoát (exit code 1) trước khi hiện prompt.
    try:
        load_openai_settings()
    except RuntimeError as error:
        raise SystemExit(f"Lỗi cấu hình: {error}")

    while True:
        # Ctrl+C tại prompt hoặc hết stdin (EOF khi pipe/redirect) đều kết thúc êm.
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
            # Ctrl+C rơi đúng lúc đang chờ API cũng thoát êm như trên.
            print("\nĐã dừng phiên CLI.")
            return
        except Exception as error:
            # Lỗi API/mạng chỉ in ra rồi hỏi tiếp, không làm chết phiên.
            print(f"Không thể tạo câu trả lời: {error}")


if __name__ == "__main__":
    main()
