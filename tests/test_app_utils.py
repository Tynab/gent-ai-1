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
