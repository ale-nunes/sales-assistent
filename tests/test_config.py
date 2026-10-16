"""Tests for safe configuration defaults."""

from researchmind.config import Settings


def test_settings_have_safe_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.max_critic_iterations == 3
    assert settings.gmail_read_only is True
    assert settings.gmail_allow_draft_creation is False
    assert settings.gemini_api_key is None


def test_allowed_telegram_ids_are_parsed() -> None:
    settings = Settings(_env_file=None, telegram_allowed_user_ids="123, 456")
    assert settings.allowed_telegram_user_ids == {123, 456}


def test_critic_iteration_limit_cannot_exceed_three() -> None:
    try:
        Settings(_env_file=None, max_critic_iterations=4)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected validation to reject more than three iterations.")
