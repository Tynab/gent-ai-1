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
