# Gen AI Playground

Ba ví dụ Python nhỏ để học cách gọi OpenAI Chat Completions API (SDK openai 2.x) qua CLI và Streamlit. Logic dùng chung nằm trong `app_utils.py`; mỗi entry point giữ một trách nhiệm rõ ràng.

## Cấu trúc

- `app_utils.py` — cấu hình, client OpenAI (cache), payload `messages`, đọc/ghi lịch sử chat.
- `intro_to_openai.py` — CLI hỏi đáp liên tục, không lưu ngữ cảnh.
- `openai_with_ui.py` — giao diện Streamlit, không lưu ngữ cảnh.
- `openai_with_context.py` — giao diện Streamlit, lưu lịch sử vào `chat_history.json`.
- `tests/test_app_utils.py` — unit test cho toàn bộ logic dùng chung.

## Yêu cầu

- Python 3.10+ (khuyến nghị 3.11)
- API key của OpenAI

## Cài đặt

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Tạo file `.env` từ `.env.example` — cả hai biến đều bắt buộc, không có model mặc định:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=your_model_name_here
```

## Cách chạy

```powershell
python .\intro_to_openai.py                        # CLI
python -m streamlit run .\openai_with_ui.py        # Streamlit, không ngữ cảnh
python -m streamlit run .\openai_with_context.py   # Streamlit, có lưu lịch sử
```

## Chạy test

```powershell
python -m pytest
```

Test mock toàn bộ lệnh gọi OpenAI — không cần API key, không tốn phí, không gọi mạng.

## Ghi chú hành vi

- Thiếu biến môi trường: cả 3 app báo "Lỗi cấu hình" ngay khi khởi động (CLI thoát với exit code 1; Streamlit hiện lỗi và dừng trang).
- CLI: thoát bằng `Ctrl + C` hoặc EOF; nhập rỗng sẽ được nhắc nhập lại; lỗi API chỉ in ra rồi hỏi tiếp.
- `chat_history.json` luôn nằm cạnh `app_utils.py` (repo root) bất kể chạy từ thư mục nào; file hỏng được tự sao lưu sang `.bak` thay vì ghi đè.
- Sửa `.env` khi app đang chạy không có tác dụng — cần restart tiến trình (biến môi trường có sẵn trong shell luôn thắng `.env`).
