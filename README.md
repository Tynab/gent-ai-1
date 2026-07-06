# Gen AI Playground

Repo này chứa 3 ví dụ Python nhỏ để học cách gọi OpenAI API bằng CLI và Streamlit. Mã nguồn được tối ưu lại theo hướng tách logic dùng chung, kiểm tra cấu hình sớm, và giữ cho từng file có một trách nhiệm rõ ràng.

## Tổng quan kỹ thuật

- `app_utils.py`: lớp helper dùng chung cho cấu hình OpenAI, tạo payload `messages`, và đọc/ghi lịch sử chat JSON.
- `intro_to_openai.py`: script CLI tối giản, nhận câu hỏi liên tục từ terminal và in câu trả lời.
- `openai_with_ui.py`: giao diện Streamlit không lưu ngữ cảnh hỏi đáp.
- `openai_with_context.py`: giao diện Streamlit có lưu lịch sử chat vào `chat_history.json`.
- `.env.example`: mẫu cấu hình môi trường.

## Yêu cầu môi trường

- Windows PowerShell hoặc terminal bất kỳ có Python 3.11+
- Virtual environment `.venv`
- Biến môi trường `OPENAI_API_KEY`
- Biến môi trường `OPENAI_MODEL` là bắt buộc.

## Cài đặt

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Tạo file `.env` từ `.env.example`:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=your_model_name_here
```

## Cách chạy

Chạy bản CLI:

```powershell
python .\intro_to_openai.py
```

Nhấn `Ctrl + C` để dừng phiên CLI.

Chạy Streamlit UI không lưu ngữ cảnh:

```powershell
python -m streamlit run .\openai_with_ui.py
```

Chạy Streamlit UI có lưu ngữ cảnh:

```powershell
python -m streamlit run .\openai_with_context.py
```

## Luồng xử lý chính

1. `load_dotenv()` nạp biến môi trường từ file `.env`.
2. `app_utils.load_openai_settings()` xác thực `OPENAI_API_KEY` và model.
3. `app_utils.request_chat_completion()` tạo OpenAI client, lập payload `messages`, gửi request, và trả về nội dung đã rút gọn.
4. Riêng `openai_with_context.py` đọc/ghi `chat_history.json` để giữ lịch sử hỏi đáp.

## Những điểm đã được clean up

- Bỏ lặp logic kết nối OpenAI giữa 3 file entrypoint.
- Chuẩn hóa kiểm tra lỗi cấu hình thay vì để crash không rõ nguyên nhân.
- Tách phần đọc/ghi lịch sử chat ra khỏi Streamlit để dễ bảo trì.
- Sửa luồng render chat trong Streamlit để block `assistant` không bị lồng bên trong block `user`.
- Bổ sung module docstring và comment mô tả bằng tiếng Việt cho phần code tự viết.
- Kiểm tra cấu hình ngay khi khởi động (fail fast) ở cả CLI lẫn Streamlit thay vì đợi request đầu tiên.
- CLI thoát êm bằng `Ctrl + C`/EOF và nhắc nhập lại khi câu hỏi rỗng thay vì crash.
- Ghi `chat_history.json` kiểu atomic (file tạm + replace) và sao lưu file hỏng sang `.bak` thay vì ghi đè mất dữ liệu.
- Thống nhất message lỗi sang tiếng Việt và bỏ trùng lặp câu hỏi hiện tại trong payload gửi OpenAI.

## Gợi ý mở rộng tiếp theo

- Bổ sung lại test tự động cho luồng gọi API và xử lý session Streamlit khi cần CI/CD.
- Bổ sung nút `Xóa lịch sử chat` trong bản có ngữ cảnh nếu muốn reset nhanh.

