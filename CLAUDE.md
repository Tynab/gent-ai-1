# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Kiến trúc

Playground gồm 3 ví dụ gọi OpenAI Chat Completions API (SDK openai 2.x — `client.chat.completions.create`). Toàn bộ logic OpenAI nằm trong `app_utils.py`; 3 entry point chỉ làm I/O và UI:

- `app_utils.py` — `load_openai_settings` validate env: được gọi fail-fast lúc khởi động ở cả 3 entry point và gọi lại cho mỗi request; luôn `load_dotenv(override=False)` nên sửa `.env` giữa chừng phải restart mới có tác dụng. Client OpenAI được tạo mới cho mỗi request; `build_messages` ghép system prompt + lịch sử đã lọc (bỏ role lạ, content rỗng) + câu hỏi hiện tại; `load_chat_history` đọc strict (raise `ValueError` nếu sai cấu trúc, chỉ nhận role `user`/`assistant`); `save_chat_history` ghi atomic (file tạm `.tmp` + replace), không validate nội dung.
- `intro_to_openai.py` — CLI, không gửi lịch sử. `openai_with_ui.py` — Streamlit, không lưu state.
- `openai_with_context.py` — nạp lịch sử vào `st.session_state` một lần mỗi session; chỉ append cặp user/assistant và lưu file **sau khi** request thành công (API lỗi thì lịch sử không đổi); file lịch sử hỏng được sao lưu sang `chat_history.json.bak` rồi reset về `[]`.

`chat_history.json` resolve theo thư mục làm việc lúc chạy — luôn chạy lệnh từ repo root, nếu không lịch sử "biến mất".

## Lệnh

Cần `.env` (chép từ `.env.example`) có đủ **cả** `OPENAI_API_KEY` lẫn `OPENAI_MODEL` — không có model mặc định. Thiếu env thì cả 3 app báo "Lỗi cấu hình" ngay khi khởi động (CLI in lỗi và thoát với exit code 1; Streamlit hiện `st.error` rồi `st.stop`). Venv hiện tại là Python 3.11 (sàn thực tế 3.10 do pin streamlit/python-dotenv).

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python .\intro_to_openai.py                        # CLI — thoát bằng Ctrl+C hoặc EOF
python -m streamlit run .\openai_with_ui.py        # Streamlit, không ngữ cảnh
python -m streamlit run .\openai_with_context.py   # Streamlit, lưu lịch sử
```

Không có test, linter hay CI — xác minh thay đổi bằng cách chạy tay các entry point (cần API key thật).

## Coding convention

- Docstring, chuỗi UI và message lỗi viết bằng tiếng Việt.
- Dependency pin chính xác bằng `==` trong `requirements.txt` — thêm mới theo cùng quy ước.
- `.gitattributes` ép LF cho source/docs, CRLF chỉ cho `.bat/.cmd/.ps1` — tạo file mới theo đúng quy ước.

## Quy tắc khi sửa code

- Logic dùng chung mới đặt vào `app_utils.py`, không lặp lại giữa các entry point.
- Validation lịch sử hiện bất đối xứng có chủ đích: `load_chat_history` raise khi gặp entry hỏng, còn `build_messages` lọc êm — nếu đổi một phía, cân nhắc cả hai.

## Không tự ý thay đổi

- Không commit `chat_history.json` (kể cả file `.tmp`/`.bak` của nó), `.env`, `.streamlit/` — đã gitignore; không gỡ các rule này khỏi `.gitignore`.
- Không nâng/hạ phiên bản dependency hoặc đổi kiểu API SDK (2.x client-based) khi chưa được yêu cầu.
- Không đổi chính sách line-ending trong `.gitattributes`.
