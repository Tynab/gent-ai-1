# Test Runner + Đánh Bóng Tại Chỗ + Viết Lại Docs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm pytest với unit test phủ toàn bộ `app_utils.py`, áp 2 cải tiến hành vi có chủ đích (cache client OpenAI, neo `chat_history.json`), dọn nhẹ + comment tiếng Việt chọn lọc, và viết lại 4 file docs/config + đồng bộ CLAUDE.md.

**Architecture:** Repo phẳng 4 file Python: `app_utils.py` chứa toàn bộ logic (env, client, messages, lịch sử JSON); 3 entry point (`intro_to_openai.py` CLI, `openai_with_ui.py`, `openai_with_context.py` Streamlit) chỉ làm I/O + UI. Thêm duy nhất `tests/` + `conftest.py` rỗng ở root. Không tạo module logic mới.

**Tech Stack:** Python 3.11 (venv tại `.venv`), openai==2.44.0 (SDK 2.x, `client.chat.completions.create`), python-dotenv==1.2.2, streamlit==1.58.0, pytest (cài mới, pin `==`).

## Global Constraints

- Spec gốc: `docs/superpowers/specs/2026-07-07-test-runner-polish-docs-design.md` — đọc trước khi làm.
- Làm việc tại repo root `d:\Education\AI\Gen\gent-ai-1`; shell là PowerShell; Python của venv: `.\.venv\Scripts\python.exe`.
- Docstring, comment, chuỗi UI, message lỗi: **tiếng Việt**. Comment chọn lọc — chỉ đoạn logic đáng giải thích, không comment code hiển nhiên.
- Dependency pin chính xác `==`; KHÔNG nâng/hạ 3 pin runtime hiện có (`openai==2.44.0`, `python-dotenv==1.2.2`, `streamlit==1.58.0`).
- Test không gọi mạng, không cần API key thật.
- Line ending LF cho mọi file tạo/sửa (trừ `.bat/.cmd/.ps1` — repo không có).
- KHÔNG commit `chat_history.json`, `.env`, file `.tmp`/`.bak`; không đụng `.venv/`, `__pycache__/`.
- Chỉ 2 thay đổi hành vi được phép: cache client (Task 3) và neo đường dẫn lịch sử (Task 4). Mọi thứ khác giữ nguyên hành vi.

---

### Task 0: Commit baseline các thay đổi đang chờ

Working tree đang có sẵn các sửa đổi đã được review + kiểm chứng ở phiên trước (fail-fast config, ghi atomic, message tiếng Việt, sửa trùng payload) nhưng chưa commit. Commit chúng thành baseline để các task sau có diff sạch.

**Files:**
- Modify: không sửa gì — chỉ commit trạng thái hiện có.

**Interfaces:**
- Consumes: working tree hiện tại (đã pass review đối kháng).
- Produces: HEAD sạch làm nền cho các task sau; `git status --porcelain` chỉ còn file untracked ngoài scope (nếu có).

- [ ] **Step 1: Xem lại diff đang chờ**

Run: `git status --porcelain; git diff --stat`
Expected: 6 file modified (`app_utils.py`, `intro_to_openai.py`, `openai_with_ui.py`, `openai_with_context.py`, `README.md`, `.gitignore`) + `CLAUDE.md` untracked.

- [ ] **Step 2: Commit baseline**

```powershell
git add app_utils.py intro_to_openai.py openai_with_ui.py openai_with_context.py README.md .gitignore CLAUDE.md
git commit -m @'
Harden CLI and persistence, fail-fast config, Vietnamese messages

- CLI thoát êm bằng Ctrl+C/EOF, nhập rỗng được nhắc lại, fail-fast cấu hình
- Ghi chat_history.json kiểu atomic, sao lưu file hỏng sang .bak
- Sửa trùng câu hỏi hiện tại trong payload gửi OpenAI
- Thống nhất message lỗi tiếng Việt; đồng bộ README/CLAUDE.md/.gitignore

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

Run: `git status --porcelain`
Expected: rỗng (sạch).

---

### Task 1: Cài pytest, khung test + test `load_openai_settings`

**Files:**
- Modify: `requirements.txt` (thêm dòng pin pytest)
- Create: `conftest.py` (root, gần như rỗng), `tests/test_app_utils.py`

**Interfaces:**
- Consumes: `app_utils.load_openai_settings() -> tuple[str, str]` (raise `RuntimeError` khi thiếu env).
- Produces: file `tests/test_app_utils.py` với fixture autouse `isolate_env` — các task sau **append** test vào file này và Task 3 sẽ **sửa** fixture. Lệnh chạy test chuẩn của repo: `.\.venv\Scripts\python.exe -m pytest` (dạng `python -m` để CWD vào `sys.path`, giúp `import app_utils` hoạt động).

- [ ] **Step 1: Cài pytest vào venv và lấy version chính xác**

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pip freeze | Select-String -Pattern '^pytest=='
```

Expected: dòng dạng `pytest==X.Y.Z`. Ghi nhớ version này cho Step 2.

- [ ] **Step 2: Thêm pin pytest vào `requirements.txt`**

Nội dung mới của `requirements.txt` (thay `X.Y.Z` bằng version từ Step 1, giữ nguyên 3 dòng đầu):

```
openai==2.44.0
python-dotenv==1.2.2
streamlit==1.58.0
pytest==X.Y.Z
```

- [ ] **Step 3: Tạo `conftest.py` ở root**

```python
"""File đánh dấu rootdir cho pytest.

Để trống có chủ đích: sự tồn tại của file này ở repo root giúp pytest
thêm root vào sys.path, nhờ đó tests/ import được app_utils dù chạy
bằng `pytest` trần hay `python -m pytest`.
"""
```

- [ ] **Step 4: Tạo `tests/test_app_utils.py` với fixture cách ly + test settings**

```python
"""Unit test cho app_utils.py — mock hoàn toàn, không gọi mạng, không cần API key."""

import json

import pytest

import app_utils
from app_utils import (
    DEFAULT_SYSTEM_PROMPT,
    build_messages,
    load_chat_history,
    load_openai_settings,
    save_chat_history,
)


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    """Chặn .env thật của repo lọt vào test.

    load_dotenv(override=False) không ghi đè biến ĐÃ CÓ trong môi trường,
    kể cả khi giá trị là chuỗi rỗng — nên đặt sẵn "" là đủ để vô hiệu .env.
    (delenv KHÔNG đủ: load_dotenv sẽ nạp lại giá trị thật từ file.)
    """
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_MODEL", "")


class TestLoadOpenaiSettings:
    def test_thieu_api_key_bao_loi(self):
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            load_openai_settings()

    def test_co_key_nhung_thieu_model_bao_loi(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        with pytest.raises(RuntimeError, match="OPENAI_MODEL"):
            load_openai_settings()

    def test_du_ca_hai_tra_ve_dung_gia_tri(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
        assert load_openai_settings() == ("sk-test", "gpt-test")
```

- [ ] **Step 5: Chạy test, xác nhận pass**

Run: `.\.venv\Scripts\python.exe -m pytest -v`
Expected: `3 passed` (test khóa hành vi hiện có nên pass ngay; nếu ImportError xem lại Step 3).

- [ ] **Step 6: Commit**

```powershell
git add requirements.txt conftest.py tests/test_app_utils.py
git commit -m @'
Add pytest runner and settings tests

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 2: Test khóa hành vi `build_messages` + `load/save_chat_history`

**Files:**
- Modify: `tests/test_app_utils.py` (append 2 class test vào cuối file)

**Interfaces:**
- Consumes: `build_messages(user_input, chat_history=None, system_prompt=DEFAULT_SYSTEM_PROMPT) -> list[dict[str, str]]`; `load_chat_history(file_path) -> list[dict[str, str]]` (missing file → `[]`, sai cấu trúc → `ValueError`); `save_chat_history(history, file_path)` (atomic qua file `.tmp`).
- Produces: lưới an toàn hành vi cho Task 3–5.

- [ ] **Step 1: Append 2 class test sau `TestLoadOpenaiSettings`**

```python
class TestBuildMessages:
    def test_mac_dinh_gom_system_va_cau_hoi(self):
        assert build_messages("Xin chào") == [
            {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
            {"role": "user", "content": "Xin chào"},
        ]

    def test_system_prompt_tuy_chinh_nam_dau(self):
        messages = build_messages("Hi", system_prompt="Bạn là bot.")
        assert messages[0] == {"role": "system", "content": "Bạn là bot."}

    def test_loc_em_cac_entry_khong_hop_le(self):
        history = [
            {"role": "user", "content": "hợp lệ"},
            {"role": "assistant", "content": "hợp lệ 2"},
            {"role": "system", "content": "role lạ - bị bỏ"},
            {"role": "user", "content": ""},
            {"role": "user", "content": 123},
            {"content": "thiếu role - bị bỏ"},
        ]
        messages = build_messages("câu hỏi", chat_history=history)
        assert messages[1:] == [
            {"role": "user", "content": "hợp lệ"},
            {"role": "assistant", "content": "hợp lệ 2"},
            {"role": "user", "content": "câu hỏi"},
        ]


class TestChatHistoryIO:
    def test_file_khong_ton_tai_tra_ve_rong(self, tmp_path):
        assert load_chat_history(tmp_path / "khong_co.json") == []

    def test_doc_file_hop_le(self, tmp_path):
        file_path = tmp_path / "history.json"
        file_path.write_text(
            json.dumps([{"role": "user", "content": "câu hỏi tiếng Việt"}], ensure_ascii=False),
            encoding="utf-8",
        )
        assert load_chat_history(file_path) == [{"role": "user", "content": "câu hỏi tiếng Việt"}]

    def test_root_khong_phai_list_bao_loi(self, tmp_path):
        file_path = tmp_path / "history.json"
        file_path.write_text('{"role": "user"}', encoding="utf-8")
        with pytest.raises(ValueError):
            load_chat_history(file_path)

    def test_phan_tu_khong_phai_dict_bao_loi(self, tmp_path):
        file_path = tmp_path / "history.json"
        file_path.write_text('["chuỗi trần"]', encoding="utf-8")
        with pytest.raises(ValueError):
            load_chat_history(file_path)

    def test_role_ngoai_danh_sach_bao_loi(self, tmp_path):
        file_path = tmp_path / "history.json"
        file_path.write_text(json.dumps([{"role": "system", "content": "x"}]), encoding="utf-8")
        with pytest.raises(ValueError):
            load_chat_history(file_path)

    def test_luu_roi_doc_lai_giu_nguyen_tieng_viet(self, tmp_path):
        file_path = tmp_path / "history.json"
        history = [{"role": "user", "content": "Tiếng Việt có dấu: ăn ổi"}]
        save_chat_history(history, file_path)
        assert load_chat_history(file_path) == history
        # ensure_ascii=False: ký tự có dấu nằm nguyên trên đĩa, không bị escape
        assert "ăn ổi" in file_path.read_text(encoding="utf-8")

    def test_ghi_atomic_khong_sot_file_tam(self, tmp_path):
        file_path = tmp_path / "history.json"
        save_chat_history([{"role": "user", "content": "a"}], file_path)
        assert file_path.exists()
        assert not (tmp_path / "history.json.tmp").exists()

    def test_ghi_de_duoc_file_cu(self, tmp_path):
        file_path = tmp_path / "history.json"
        save_chat_history([{"role": "user", "content": "cũ"}], file_path)
        save_chat_history([{"role": "user", "content": "mới"}], file_path)
        assert load_chat_history(file_path) == [{"role": "user", "content": "mới"}]
```

- [ ] **Step 2: Chạy test, xác nhận pass toàn bộ**

Run: `.\.venv\Scripts\python.exe -m pytest -v`
Expected: `14 passed` (3 cũ + 11 mới; tất cả khóa hành vi hiện có).

- [ ] **Step 3: Commit**

```powershell
git add tests/test_app_utils.py
git commit -m @'
Add behavior-locking tests for messages and history IO

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 3: Cache client OpenAI (TDD) + test `request_chat_completion`

**Files:**
- Modify: `app_utils.py` (thêm `lru_cache` cho `build_openai_client`), `tests/test_app_utils.py` (sửa fixture + append 2 class test)

**Interfaces:**
- Consumes: `build_openai_client() -> tuple[OpenAI, str]` hiện tại (tạo mới mỗi lần gọi).
- Produces: `build_openai_client` bọc `functools.lru_cache(maxsize=1)` — có thêm `.cache_clear()`; hành vi mới: cùng một object client cho mọi lần gọi trong tiến trình. `request_chat_completion` không đổi chữ ký.

- [ ] **Step 1: Append 2 class test (viết TRƯỚC khi sửa code) vào cuối `tests/test_app_utils.py`**

Thêm import ở đầu file (sau `import pytest`): `from types import SimpleNamespace`, và thêm `build_openai_client`, `request_chat_completion` vào danh sách `from app_utils import (...)`.

```python
def make_fake_client(content):
    """Tạo client giả: ghi lại kwargs của lần gọi create() và trả response cố định."""
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
    completions = SimpleNamespace(last_kwargs=None)

    def create(**kwargs):
        completions.last_kwargs = kwargs
        return response

    completions.create = create
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


class TestBuildOpenaiClientCache:
    def test_hai_lan_goi_tra_ve_cung_client(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
        client1, model1 = build_openai_client()
        client2, model2 = build_openai_client()
        assert client1 is client2
        assert model1 == model2 == "gpt-test"

    def test_cache_clear_tao_client_moi(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
        client1, _ = build_openai_client()
        build_openai_client.cache_clear()
        client2, _ = build_openai_client()
        assert client1 is not client2


class TestRequestChatCompletion:
    def test_gui_dung_model_va_messages(self, monkeypatch):
        fake_client = make_fake_client("trả lời")
        monkeypatch.setattr(app_utils, "build_openai_client", lambda: (fake_client, "gpt-test"))
        assert request_chat_completion("câu hỏi") == "trả lời"
        sent = fake_client.chat.completions.last_kwargs
        assert sent["model"] == "gpt-test"
        assert sent["messages"][0]["role"] == "system"
        assert sent["messages"][-1] == {"role": "user", "content": "câu hỏi"}

    def test_content_none_chuan_hoa_thanh_chuoi_rong(self, monkeypatch):
        fake_client = make_fake_client(None)
        monkeypatch.setattr(app_utils, "build_openai_client", lambda: (fake_client, "gpt-test"))
        assert request_chat_completion("câu hỏi") == ""
```

- [ ] **Step 2: Chạy test, xác nhận 2 test cache FAIL đúng kiểu**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_app_utils.py -v -k "Cache"`
Expected: `test_hai_lan_goi_tra_ve_cung_client` FAIL (assert client1 is client2 — hiện mỗi lần gọi tạo client mới); `test_cache_clear_tao_client_moi` FAIL với `AttributeError: 'function' object has no attribute 'cache_clear'`.

- [ ] **Step 3: Bọc `build_openai_client` bằng `lru_cache` trong `app_utils.py`**

Thêm vào khối import: `from functools import lru_cache`. Sửa hàm thành:

```python
@lru_cache(maxsize=1)
def build_openai_client() -> tuple[OpenAI, str]:
    """Trả về OpenAI client cùng model đang cấu hình, cache cho cả tiến trình.

    Client chỉ tạo một lần: env đã bất biến trong tiến trình (override=False)
    nên tạo lại mỗi request là thừa. Test reset bằng build_openai_client.cache_clear().
    """
    api_key, model_name = load_openai_settings()
    return OpenAI(api_key=api_key), model_name
```

- [ ] **Step 4: Cập nhật fixture `isolate_env` để reset cache giữa các test**

Thay toàn bộ fixture trong `tests/test_app_utils.py` bằng:

```python
@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    """Chặn .env thật của repo lọt vào test và reset cache client.

    load_dotenv(override=False) không ghi đè biến ĐÃ CÓ trong môi trường,
    kể cả khi giá trị là chuỗi rỗng — nên đặt sẵn "" là đủ để vô hiệu .env.
    (delenv KHÔNG đủ: load_dotenv sẽ nạp lại giá trị thật từ file.)
    """
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_MODEL", "")
    build_openai_client.cache_clear()
    yield
    build_openai_client.cache_clear()
```

- [ ] **Step 5: Chạy toàn bộ test, xác nhận pass**

Run: `.\.venv\Scripts\python.exe -m pytest -v`
Expected: `18 passed`.

- [ ] **Step 6: Commit**

```powershell
git add app_utils.py tests/test_app_utils.py
git commit -m @'
Cache OpenAI client across requests with lru_cache

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 4: Neo `CHAT_HISTORY_FILE` vào thư mục module (TDD)

**Files:**
- Modify: `app_utils.py` (1 hằng số), `tests/test_app_utils.py` (append 1 class test + 1 import)

**Interfaces:**
- Consumes: `CHAT_HISTORY_FILE` hiện tại = `Path("chat_history.json")` (tương đối theo CWD).
- Produces: `CHAT_HISTORY_FILE` = đường dẫn TUYỆT ĐỐI `<thư mục chứa app_utils.py>/chat_history.json`. `openai_with_context.py` import hằng số này nên tự nhận thay đổi, không phải sửa.

- [ ] **Step 1: Append test (viết TRƯỚC) vào cuối `tests/test_app_utils.py`**

Thêm import ở đầu file (cạnh `import json`): `from pathlib import Path`.

```python
class TestChatHistoryFileConstant:
    def test_neo_theo_thu_muc_chua_module(self):
        expected = Path(app_utils.__file__).resolve().parent / "chat_history.json"
        assert app_utils.CHAT_HISTORY_FILE == expected
        assert app_utils.CHAT_HISTORY_FILE.is_absolute()
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_app_utils.py -v -k "Constant"`
Expected: FAIL — `Path('chat_history.json')` không bằng đường dẫn tuyệt đối và `is_absolute()` là False.

- [ ] **Step 3: Sửa hằng số trong `app_utils.py`**

```python
# Neo file lịch sử theo thư mục chứa module: chạy app từ thư mục nào
# cũng dùng đúng một file tại repo root (tránh "mất lịch sử" khi chạy sai chỗ).
CHAT_HISTORY_FILE = Path(__file__).resolve().parent / "chat_history.json"
```

- [ ] **Step 4: Chạy toàn bộ test, xác nhận pass**

Run: `.\.venv\Scripts\python.exe -m pytest -v`
Expected: `19 passed`.

- [ ] **Step 5: Commit**

```powershell
git add app_utils.py tests/test_app_utils.py
git commit -m @'
Anchor chat_history.json to module directory

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 5: Dọn nhẹ entry points + type alias + comment tiếng Việt chọn lọc

**Files:**
- Modify: `app_utils.py`, `intro_to_openai.py`, `openai_with_ui.py`, `openai_with_context.py`

**Interfaces:**
- Consumes: API `app_utils` sau Task 3–4.
- Produces: alias `ChatMessage = dict[str, str]`, `ChatHistory = list[ChatMessage]` export từ `app_utils`; chữ ký hàm dùng alias nhưng KHÔNG đổi kiểu thực tế. `openai_with_ui.py`/`openai_with_context.py` không còn hàm `generate_response` và không còn import `DEFAULT_SYSTEM_PROMPT`.

- [ ] **Step 1: Viết lại `app_utils.py` thành nội dung cuối cùng**

```python
"""Tiện ích dùng chung cho các ví dụ OpenAI trong repo.

Module này gom phần cấu hình, khởi tạo client, tạo payload messages và
đọc/ghi lịch sử chat để các entry point (CLI lẫn Streamlit) không lặp logic.
"""

from __future__ import annotations

import json
import os

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
    # Ghi ra file tạm rồi replace (atomic trên cùng ổ đĩa): tiến trình có bị
    # ngắt giữa lúc ghi thì file lịch sử gốc vẫn nguyên vẹn.
    temp_path = file_path.with_name(file_path.name + ".tmp")
    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)
    temp_path.replace(file_path)
```

- [ ] **Step 2: Viết lại `intro_to_openai.py`**

```python
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
```

- [ ] **Step 3: Viết lại `openai_with_ui.py`**

```python
"""Giao diện Streamlit cơ bản cho trợ lý AI không lưu ngữ cảnh hỏi đáp."""

import streamlit as st

from app_utils import load_openai_settings, request_chat_completion

st.set_page_config(page_title="Trợ lý AI", layout="wide")

# Fail fast: thiếu cấu hình thì báo lỗi ngay khi mở trang và dừng render.
try:
    load_openai_settings()
except RuntimeError as error:
    st.error(f"Lỗi cấu hình: {error}")
    st.stop()

st.title("Trợ lý AI")
st.caption("Giao diện hỏi đáp cơ bản, phù hợp để thử nhanh model và prompt hệ thống.")

user_input = st.chat_input("Nhập câu hỏi của bạn:")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        response = request_chat_completion(user_input)
    except Exception as error:
        st.error(f"Không thể tạo câu trả lời: {error}")
    else:
        with st.chat_message("assistant"):
            st.markdown(response)
```

- [ ] **Step 4: Viết lại `openai_with_context.py`**

```python
"""Giao diện Streamlit có nhớ ngữ cảnh và lưu lịch sử chat vào file JSON."""

import streamlit as st

from app_utils import (
    CHAT_HISTORY_FILE,
    load_chat_history,
    load_openai_settings,
    request_chat_completion,
    save_chat_history,
)


def initialize_chat_history() -> None:
    """Nạp lịch sử chat từ file vào session state một lần cho mỗi session Streamlit."""
    if "chat_history" in st.session_state:
        return

    try:
        st.session_state.chat_history = load_chat_history(CHAT_HISTORY_FILE)
    except Exception as error:
        # File hỏng: sao lưu sang .bak để không ghi đè mất dữ liệu, rồi làm lại từ đầu.
        notice = f"Không thể tải lịch sử chat: {error}."
        if CHAT_HISTORY_FILE.exists():
            backup_path = CHAT_HISTORY_FILE.with_name(CHAT_HISTORY_FILE.name + ".bak")
            CHAT_HISTORY_FILE.replace(backup_path)
            notice += f" File cũ đã được sao lưu sang {backup_path.name}."
        st.warning(f"{notice} Phiên này bắt đầu với lịch sử mới.")
        st.session_state.chat_history = []


st.set_page_config(page_title="Trợ lý AI có ngữ cảnh", layout="wide")

# Fail fast: thiếu cấu hình thì báo lỗi ngay khi mở trang và dừng render.
try:
    load_openai_settings()
except RuntimeError as error:
    st.error(f"Lỗi cấu hình: {error}")
    st.stop()

initialize_chat_history()

st.title("Trợ lý AI có lưu ngữ cảnh")
st.caption("Ứng dụng Streamlit này tải lại lịch sử từ file JSON để giữ mạch hỏi đáp giữa các lần refresh.")

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Nhập câu hỏi của bạn:")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        # Lịch sử trong session lúc này CHƯA gồm câu hỏi hiện tại —
        # build_messages sẽ tự append, nhờ đó câu hỏi chỉ lên API đúng một lần.
        response = request_chat_completion(
            user_input, chat_history=st.session_state.chat_history
        )
    except Exception as error:
        st.error(f"Không thể tạo câu trả lời: {error}")
    else:
        with st.chat_message("assistant"):
            st.markdown(response)

        # Chỉ ghi nhận cặp hỏi-đáp sau khi thành công: API lỗi thì cả session
        # lẫn file đều không đổi, không cần rollback.
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        save_chat_history(st.session_state.chat_history, CHAT_HISTORY_FILE)
```

- [ ] **Step 5: Compile + chạy toàn bộ test**

Run: `.\.venv\Scripts\python.exe -m py_compile app_utils.py intro_to_openai.py openai_with_ui.py openai_with_context.py tests/test_app_utils.py; .\.venv\Scripts\python.exe -m pytest -v`
Expected: compile không lỗi; `19 passed`.

- [ ] **Step 6: Commit**

```powershell
git add app_utils.py intro_to_openai.py openai_with_ui.py openai_with_context.py
git commit -m @'
Inline trivial wrappers, add type aliases, selective Vietnamese comments

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 6: Viết lại `.gitattributes` + `.gitignore`

**Files:**
- Modify: `.gitattributes`, `.gitignore` (thay toàn bộ nội dung)

**Interfaces:**
- Consumes: chính sách line-ending hiện có (LF mặc định, CRLF cho script Windows).
- Produces: 2 file gọn đúng thực tế repo; `chat_history.json*`, `.env` vẫn được ignore.

- [ ] **Step 1: Viết lại `.gitattributes`**

```
# Chuẩn hóa line ending: mặc định LF cho mọi file text.
* text=auto eol=lf

# Source và tài liệu — LF
*.py   text eol=lf
*.md   text eol=lf
*.json text eol=lf
*.yml  text eol=lf
*.yaml text eol=lf
*.toml text eol=lf
*.txt  text eol=lf
*.sh   text eol=lf

# Script Windows — CRLF
*.bat  text eol=crlf
*.cmd  text eol=crlf
*.ps1  text eol=crlf

# File nhị phân
*.png  binary
*.jpg  binary
*.jpeg binary
*.gif  binary
*.ico  binary
```

- [ ] **Step 2: Viết lại `.gitignore`**

```
# Virtual environment
.venv/
venv/

# Secrets và cấu hình cục bộ
.env
.env.*
!.env.example

# Cache Python / pytest
__pycache__/
*.py[cod]
.pytest_cache/

# IDE
.idea/
.vscode/

# File hệ điều hành
Thumbs.db
.DS_Store

# Trạng thái cục bộ của app
chat_history.json
chat_history.json.*
.streamlit/
```

- [ ] **Step 3: Kiểm tra ignore vẫn đúng và không file tracked nào bị ảnh hưởng**

Run: `git check-ignore -v .env chat_history.json chat_history.json.bak .venv; git status --porcelain`
Expected: cả 4 đường dẫn đều match rule; status chỉ hiện `.gitattributes` và `.gitignore` modified (không có file tracked nào bỗng thành ignored).

- [ ] **Step 4: Commit**

```powershell
git add .gitattributes .gitignore
git commit -m @'
Rewrite gitattributes and gitignore to match repo reality

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 7: Viết lại `README.md`

**Files:**
- Modify: `README.md` (thay toàn bộ nội dung)

**Interfaces:**
- Consumes: hành vi code sau Task 3–5 (client cache, path neo, fail-fast, CLI thoát Ctrl+C/EOF).
- Produces: README tiếng Việt là nguồn hướng dẫn duy nhất cho người dùng repo.

- [ ] **Step 1: Viết lại `README.md` với nội dung sau**

````markdown
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
````

- [ ] **Step 2: Commit**

```powershell
git add README.md
git commit -m @'
Rewrite README: structure, setup, run, test, behavior notes

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 8: Đồng bộ `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md` (thay toàn bộ nội dung)

**Interfaces:**
- Consumes: mọi thay đổi từ Task 1–7.
- Produces: CLAUDE.md không còn khẳng định nào sai với code (tiêu chí nghiệm thu #3 của spec).

- [ ] **Step 1: Viết lại `CLAUDE.md` với nội dung sau**

````markdown
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
````

- [ ] **Step 2: Commit**

```powershell
git add CLAUDE.md
git commit -m @'
Sync CLAUDE.md with cached client, anchored history path, pytest

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 9: Nghiệm thu cuối

**Files:**
- Không sửa file — chỉ xác minh.

**Interfaces:**
- Consumes: toàn bộ kết quả Task 0–8.
- Produces: bằng chứng nghiệm thu theo 5 tiêu chí của spec.

- [ ] **Step 1: Chạy toàn bộ test + compile**

Run: `.\.venv\Scripts\python.exe -m pytest -v; .\.venv\Scripts\python.exe -m py_compile app_utils.py intro_to_openai.py openai_with_ui.py openai_with_context.py tests/test_app_utils.py`
Expected: `19 passed`; compile im lặng.

- [ ] **Step 2: Kiểm tra vệ sinh git**

Run: `git status --porcelain; git diff --check; git log --oneline -12`
Expected: working tree sạch (hoặc chỉ file ngoài scope); không lỗi whitespace/CRLF; thấy đủ các commit của Task 0–8.

- [ ] **Step 3: Xác minh chéo docs-code**

Đọc lại `README.md` và `CLAUDE.md`, đối chiếu từng khẳng định hành vi với code (fail-fast, cache, neo path, atomic, `.bak`, thoát CLI). Nếu phát hiện khẳng định sai → sửa doc ngay trong task này và commit `docs: fix stale claim`.
Expected: không còn khẳng định sai.

- [ ] **Step 4 (orchestrator, không giao subagent): Review đối kháng**

Orchestrator chạy workflow review đối kháng theo pattern của session (reviewer đa chiều → skeptic xác minh từng finding) trên toàn bộ diff của plan. Finding thật nào được xác nhận → sửa và commit trước khi báo cáo.
Expected: 0 finding thật.

- [ ] **Step 5: Báo cáo hoàn tất**

Tổng hợp: số test, các commit đã tạo, hành vi thay đổi (2 điểm chủ đích), file docs đã viết lại. KHÔNG push khi user chưa yêu cầu.
