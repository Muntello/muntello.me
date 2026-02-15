import pytest
import os
from app.config import Settings


def test_settings_has_required_fields():
    """Test that Settings has all required fields"""
    # Create test settings without loading .env
    test_settings = Settings(
        TELEGRAM_BOT_TOKEN="test_token",
        _env_file=None
    )
    assert hasattr(test_settings, 'TELEGRAM_BOT_TOKEN')
    assert hasattr(test_settings, 'SUPPORT_CHAT_ID')
    assert hasattr(test_settings, 'WEBHOOK_URL')
    assert hasattr(test_settings, 'DATABASE_URL')
    assert hasattr(test_settings, 'DEBUG')
    assert hasattr(test_settings, 'LOG_LEVEL')


def test_settings_defaults():
    """Test Settings default values"""
    test_settings = Settings(
        TELEGRAM_BOT_TOKEN="test_token",
        _env_file=None  # Don't load .env for tests
    )
    assert test_settings.SUPPORT_CHAT_ID == 5237566869
    assert test_settings.DEBUG is False
    assert test_settings.LOG_LEVEL == "INFO"
    assert test_settings.WEBHOOK_URL == "https://support.muntello.me"
    assert "sqlite" in test_settings.DATABASE_URL


def test_settings_custom_values():
    """Test Settings with custom values"""
    test_settings = Settings(
        TELEGRAM_BOT_TOKEN="custom_token",
        SUPPORT_CHAT_ID=123456789,
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        _env_file=None
    )
    assert test_settings.TELEGRAM_BOT_TOKEN == "custom_token"
    assert test_settings.SUPPORT_CHAT_ID == 123456789
    assert test_settings.DEBUG is True
    assert test_settings.LOG_LEVEL == "DEBUG"
