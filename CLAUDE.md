# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Kiến trúc

Playground gồm 3 ví dụ gọi OpenAI Chat Completions API (SDK openai 2.x — `client.chat.completions.create`). Toàn bộ logic OpenAI nằm trong `app_utils.py`; 3 entry point chỉ làm I/O và UI:

- `app_utils.py` — `load_openai_settings` validate env, gọi fail-fast lúc khởi động ở cả 3 entry point; `load_dotenv(override=False)` nên sửa `.env` giữa chừng phải restart. Client OpenAI được cache cho cả tiến trình (`build_openai_client` bọc `lru_cache(maxsize=1)`; test reset bằng `cache_clear()`). `build_messages` ghép system prompt + lịch sử đã lọc (bỏ role lạ, content rỗng) + câu hỏi hiện tại; `load_chat_history` đọc strict (raise `ValueError` nếu sai cấu trúc, chỉ nhận role `user`/`assistant`); `save_chat_history` ghi atomic (file tạm `.tmp` + replace). Alias kiểu: `ChatMessage`/`ChatHistory`.
- `intro_to_openai.py` — CLI, không gửi lịch sử. `openai_with_ui.py` — Streamlit, không lưu state.
- `openai_with_context.py` — nạp lịch sử vào `st.session_state` một lần mỗi session; chỉ append cặp user/assistant và lưu file **sau khi** request thành công (API lỗi thì không đổi gì); file lịch sử hỏng được sao lưu sang `chat_history.json.bak` rồi reset về `[]`.

`CHAT_HISTORY_FILE` neo theo thư mục chứa `app_utils.py` (đường dẫn tuyệt đối) — chạy app từ thư mục nào cũng dùng đúng một file lịch sử tại repo root.

## Lệnh

Cần `.env` (chép từ `.env.example`) có đủ **cả** `OPENAI_API_KEY` lẫn `OPENAI_MODEL` — không có model mặc định. Thiếu env thì cả 3 app báo "Lỗi cấu hình" ngay khi khởi động (CLI thoát exit code 1; Streamlit `st.error` + `st.stop`). Venv hiện tại là Python 3.11 (sàn thực tế 3.10 do pin streamlit/python-dotenv).

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python .\intro_to_openai.py                        # CLI — thoát bằng Ctrl+C hoặc EOF
python -m streamlit run .\openai_with_ui.py        # Streamlit, không ngữ cảnh
python -m streamlit run .\openai_with_context.py   # Streamlit, lưu lịch sử

python -m pytest                                   # test (mock hoàn toàn, không cần API key)
```

Test nằm ở `tests/test_app_utils.py`; dùng dạng `python -m pytest` từ repo root (CWD vào `sys.path` để import `app_utils`; `conftest.py` rỗng ở root hỗ trợ chạy `pytest` trần). Fixture autouse đặt env `""` để chặn `.env` thật (delenv không đủ vì `load_dotenv` sẽ nạp lại) và `cache_clear()` client giữa các test. Không có linter hay CI.

## Coding convention

- Docstring, chuỗi UI, message lỗi và comment viết bằng tiếng Việt; comment chọn lọc, không comment code hiển nhiên.
- Dependency pin chính xác bằng `==` trong `requirements.txt` — thêm mới theo cùng quy ước.
- `.gitattributes` ép LF cho source/docs, CRLF chỉ cho `.bat/.cmd/.ps1` — tạo file mới theo đúng quy ước.

## Quy tắc khi sửa code

- Logic dùng chung mới đặt vào `app_utils.py`, không lặp lại giữa các entry point.
- Validation lịch sử bất đối xứng có chủ đích (có comment tại chỗ): `load_chat_history` raise khi gặp entry hỏng, còn `build_messages` lọc êm — nếu đổi một phía, cân nhắc cả hai.
- Sửa logic thì chạy `python -m pytest` trước khi báo xong; thêm hành vi mới thì thêm test tương ứng.

## Không tự ý thay đổi

- Không commit `chat_history.json` (kể cả `.tmp`/`.bak`), `.env`, `.streamlit/` — đã gitignore; không gỡ các rule này khỏi `.gitignore`.
- Không nâng/hạ phiên bản dependency hoặc đổi kiểu API SDK (2.x client-based) khi chưa được yêu cầu.
- Không đổi chính sách line-ending trong `.gitattributes`.
