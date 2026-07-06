# Thiết kế: Test runner + đánh bóng tại chỗ + viết lại docs

- Ngày: 2026-07-07
- Trạng thái: Đã được user duyệt (design trình bày trong session, trả lời "approve")
- Phạm vi: repo `gent-ai-1` (playground OpenAI Chat Completions, Python + Streamlit)

## Bối cảnh và mục tiêu

Repo gồm 1 module logic (`app_utils.py`) và 3 entry point (`intro_to_openai.py` CLI, `openai_with_ui.py` Streamlit không ngữ cảnh, `openai_with_context.py` Streamlit có lịch sử). Code vừa được refactor và kiểm chứng đối kháng trong cùng session (fail-fast config, ghi atomic, sửa trùng payload, message tiếng Việt). Đợt này gồm 3 việc:

1. Thêm test runner (pytest) với unit test cho `app_utils.py`.
2. Đánh bóng tại chỗ: 2 cải tiến hành vi có chủ đích + dọn nhẹ + comment/summary tiếng Việt chọn lọc.
3. Viết lại `README.md`, `requirements.txt`, `.gitattributes`, `.gitignore` (và đồng bộ `CLAUDE.md`).

## Quyết định đã chốt qua Q&A

| Câu hỏi | Quyết định |
|---|---|
| Phạm vi test | Chỉ unit test `app_utils.py` (mock hoàn toàn, không mạng, không API key) |
| Mật độ comment | Vừa phải, có chọn lọc — chỉ comment đoạn logic đáng giải thích |
| Tổ chức dependency | Một file `requirements.txt` duy nhất, thêm pytest vào |
| Độ sâu refactor | "Sâu hơn nếu đáng", nhưng hướng tổng thể chọn "Đánh bóng tại chỗ": không tạo module mới, giữ nguyên 4 file |

## Ngoài phạm vi (không làm)

- Không test Streamlit (AppTest) hay CLI; không CI/CD.
- Không gộp 2 app Streamlit; không tạo `ui_utils.py`.
- Không thêm tính năng mới (nút xóa lịch sử, chọn model trong UI...).
- Không nâng/hạ phiên bản 3 dependency runtime hiện có.
- Không đụng phần sinh tự động (`.venv/`, `__pycache__/`).

## Kiến trúc

Giữ nguyên cấu trúc phẳng 4 file + thêm `tests/`:

```
app_utils.py            — logic thuần (env, client cache, messages, lịch sử); không import streamlit
intro_to_openai.py      — CLI (chỉ dùng app_utils)
openai_with_ui.py       — Streamlit không ngữ cảnh (chấp nhận vài dòng glue lặp)
openai_with_context.py  — Streamlit có lịch sử (chấp nhận vài dòng glue lặp)
tests/test_app_utils.py — pytest, mock OpenAI, tmp_path
```

## Thay đổi hành vi có chủ đích (2 điểm)

1. **Cache client OpenAI**: bọc `build_openai_client` bằng `functools.lru_cache(maxsize=1)`. Client và model chỉ được tạo/đọc một lần cho cả tiến trình, các request sau tái sử dụng. Tính đúng không đổi vì env đã bất biến trong tiến trình (`load_dotenv(override=False)`); guard cấu hình vẫn là bước fail-fast lúc khởi động ở cả 3 entry point. Test dùng `build_openai_client.cache_clear()` (fixture autouse reset cache giữa các test).
2. **Neo `chat_history.json` vào thư mục chứa module**: `CHAT_HISTORY_FILE = Path(__file__).resolve().parent / "chat_history.json"`. Chạy app từ bất kỳ thư mục làm việc nào cũng dùng đúng một file lịch sử tại repo root. File hiện có vốn nằm ở repo root nên không cần migration. File `.tmp`/`.bak` đi kèm cũng theo vị trí neo này.

## Dọn nhẹ không đổi hành vi

- Bỏ đối số `system_prompt=DEFAULT_SYSTEM_PROMPT` tại các call site (trùng giá trị default); bỏ import `DEFAULT_SYSTEM_PROMPT` không còn dùng.
- Inline 2 wrapper `generate_response` một-dòng: gọi thẳng `request_chat_completion(...)` tại chỗ.
- Thêm type alias trong `app_utils.py`: `ChatMessage = dict[str, str]`, `ChatHistory = list[ChatMessage]`; dùng trong chữ ký hàm.

## Test (pytest)

- Vị trí: `tests/test_app_utils.py`. Chạy: `python -m pytest` từ repo root (venv kích hoạt).
- pytest cài vào `.venv` bằng pip, pin `==` đúng phiên bản cài được tại thời điểm thực thi (lấy từ `pip freeze`), thêm vào `requirements.txt`.
- Cách ly môi trường: fixture autouse (1) `monkeypatch.chdir(tmp_path)` để `load_dotenv` không nhặt `.env` thật của repo, (2) `monkeypatch.delenv("OPENAI_API_KEY"/"OPENAI_MODEL", raising=False)`, (3) `build_openai_client.cache_clear()`.
- Các case bắt buộc:
  - `load_openai_settings`: thiếu API key → `RuntimeError`; có key nhưng thiếu model → `RuntimeError`; đủ cả hai → trả đúng `(api_key, model)`.
  - `build_messages`: phần tử đầu là system prompt (default và custom); lịch sử bị lọc đúng (role ngoài `user`/`assistant` bị bỏ, content không phải str bị bỏ, content rỗng bị bỏ); câu hỏi hiện tại nằm cuối; `chat_history=None` → chỉ system + câu hỏi.
  - `load_chat_history`: file không tồn tại → `[]`; file hợp lệ → list chuẩn hóa; root không phải list → `ValueError`; phần tử không phải dict → `ValueError`; role/content sai → `ValueError`.
  - `save_chat_history`: roundtrip với `load_chat_history` (tiếng Việt giữ nguyên — `ensure_ascii=False`); sau khi lưu không còn file `.tmp` sót lại; ghi đè file cũ thành công.
  - `request_chat_completion`: mock client (monkeypatch `build_openai_client` hoặc `OpenAI`) → verify `model` và `messages` truyền đúng; response content `None` → trả `""`.
  - Cache client: gọi `build_openai_client` 2 lần → cùng một object; sau `cache_clear()` → object mới.

## Comment/summary tiếng Việt (chọn lọc)

- Làm giàu docstring module + hàm hiện có (đều đã là tiếng Việt) khi mô tả còn mỏng.
- Thêm inline comment tại: validate lịch sử (vì sao raise thay vì lọc), ghi atomic (`.tmp` + replace), luồng append-sau-thành-công trong `openai_with_context.py`, xử lý Ctrl+C/EOF trong CLI, lý do cache client và neo đường dẫn.
- Không comment code hiển nhiên. Test cũng có docstring/comment tiếng Việt theo cùng chuẩn.

## Viết lại docs/config (task 3)

- **README.md** (tiếng Việt, viết lại sạch): giới thiệu; bảng/danh sách cấu trúc file; yêu cầu môi trường; cài đặt (venv + pip); cấu hình `.env` (2 biến bắt buộc, không default model); cách chạy 3 app; **mục "Chạy test" mới** (`python -m pytest`); ghi chú hành vi (CLI thoát bằng Ctrl+C/EOF, nhập rỗng được nhắc lại; lịch sử neo tại repo root, file hỏng tự sao lưu `.bak`; sửa `.env` cần restart). Bỏ mục "Những điểm đã được clean up" và "Gợi ý mở rộng tiếp theo" (dạng changelog — để git giữ).
- **requirements.txt**: đúng 4 dòng pin `==`: `openai==2.44.0`, `python-dotenv==1.2.2`, `streamlit==1.58.0`, `pytest==<bản cài thực tế>`.
- **.gitattributes**: giữ nguyên chính sách, viết lại gọn: `* text=auto eol=lf`; LF tường minh cho `.py .md .json .yml .yaml .toml .sh .txt`; CRLF cho `.bat .cmd .ps1`; binary cho `.png .jpg .jpeg .gif .ico`.
- **.gitignore**: tổ chức lại theo nhóm, chỉ giữ những gì repo thực dùng: virtualenv (`.venv/`, `venv/`); secrets (`.env`, `.env.*`, `!.env.example`); cache Python/pytest (`__pycache__/`, `*.py[cod]`, `.pytest_cache/`); IDE (`.idea/`, `.vscode/`); OS (`Thumbs.db`, `.DS_Store`); app state (`chat_history.json`, `chat_history.json.*`, `.streamlit/`). Bỏ hẳn các entry tool không tồn tại trong repo (mypy/ruff/tox/nox/coverage/pyre/pytype/hypothesis, build/dist/egg-info) — khi nào repo thêm tool thì thêm lại entry tương ứng.
- **CLAUDE.md** (đồng bộ bắt buộc): cập nhật — client cached (không còn "tạo mới mỗi request"), `chat_history.json` neo repo root (bỏ cảnh báo CWD), lệnh test mới, mục "Không có test" đổi thành hướng dẫn pytest, pin pytest trong quy ước dependency.

## Xử lý lỗi

Không đổi semantics: fail-fast cấu hình lúc khởi động (CLI exit code 1, Streamlit `st.error` + `st.stop`); message lỗi tiếng Việt; `load_chat_history` raise `ValueError` khi sai cấu trúc còn `build_messages` lọc êm (bất đối xứng giữ nguyên, có comment giải thích).

## Tiêu chí nghiệm thu

1. `python -m pytest` xanh toàn bộ trong venv, không cần API key, không gọi mạng.
2. `python -m py_compile` sạch cho 4 file nguồn + file test.
3. 4 file docs/config được viết lại đúng nội dung mô tả trên; `CLAUDE.md` không còn khẳng định nào sai với code.
4. Workflow review đối kháng (theo pattern session) không còn finding thật nào.
5. Không commit code khi user chưa yêu cầu (spec doc này được commit riêng theo quy trình skill).
