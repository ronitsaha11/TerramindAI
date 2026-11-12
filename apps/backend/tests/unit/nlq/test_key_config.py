"""How GEMINI_API_KEY_1..N is read into rotation order.

Slot order is operator-visible behaviour: "Gemini key 2 exhausted" in a log is
only meaningful if slot 2 is the key the operator put in GEMINI_API_KEY_2.
"""

import pytest

from src.core.config import Settings


@pytest.fixture
def env(monkeypatch, tmp_path):
    """A Settings pointed at an empty env file, so only os.environ matters."""
    for name in list(__import__("os").environ):
        if name.startswith("GEMINI_API_KEY"):
            monkeypatch.delenv(name, raising=False)

    empty = tmp_path / "empty.env"
    empty.write_text("", encoding="utf-8")

    def build(**values):
        for name, value in values.items():
            monkeypatch.setenv(name, value)
        settings = Settings(_env_file=str(empty))
        settings.model_config["env_file"] = str(empty)
        return settings

    return build


def test_numbered_keys_are_ordered_by_slot(env):
    settings = env(
        GEMINI_API_KEY_2="second",
        GEMINI_API_KEY_1="first",
        GEMINI_API_KEY_3="third",
    )
    assert settings.gemini_api_keys() == ["first", "second", "third"]


def test_double_digit_slots_sort_numerically_not_alphabetically(env):
    settings = env(
        GEMINI_API_KEY_10="tenth",
        GEMINI_API_KEY_2="second",
    )
    assert settings.gemini_api_keys() == ["second", "tenth"]


def test_gaps_in_numbering_are_tolerated(env):
    settings = env(GEMINI_API_KEY_1="first", GEMINI_API_KEY_7="seventh")
    assert settings.gemini_api_keys() == ["first", "seventh"]


def test_blank_slots_are_skipped(env):
    settings = env(
        GEMINI_API_KEY_1="first",
        GEMINI_API_KEY_2="   ",
        GEMINI_API_KEY_3="third",
    )
    assert settings.gemini_api_keys() == ["first", "third"]


def test_whitespace_around_a_key_is_stripped(env):
    settings = env(GEMINI_API_KEY_1="  padded  ")
    assert settings.gemini_api_keys() == ["padded"]


def test_a_lone_unnumbered_key_still_works(env):
    """Existing single-key deployments must not need reconfiguring."""
    settings = env(GEMINI_API_KEY="legacy")
    assert settings.gemini_api_keys() == ["legacy"]


def test_unnumbered_key_is_appended_after_the_numbered_ones(env):
    settings = env(GEMINI_API_KEY="legacy", GEMINI_API_KEY_1="first")
    assert settings.gemini_api_keys() == ["first", "legacy"]


def test_unnumbered_key_is_not_duplicated_when_it_repeats_a_slot(env):
    settings = env(GEMINI_API_KEY="same", GEMINI_API_KEY_1="same")
    assert settings.gemini_api_keys() == ["same"]


def test_no_keys_configured_returns_empty(env):
    assert env().gemini_api_keys() == []


def test_similarly_named_variables_are_ignored(env):
    """Only the exact GEMINI_API_KEY_<n> shape counts."""
    settings = env(
        GEMINI_API_KEY_1="first",
        GEMINI_API_KEY_BACKUP="not a slot",
        GEMINI_API_KEY_1_OLD="not a slot either",
        MY_GEMINI_API_KEY_2="nor this",
    )
    assert settings.gemini_api_keys() == ["first"]


def test_keys_can_come_from_the_env_file(tmp_path, monkeypatch):
    """Native runs put keys in apps/backend/.env rather than the environment."""
    for name in list(__import__("os").environ):
        if name.startswith("GEMINI_API_KEY"):
            monkeypatch.delenv(name, raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "GEMINI_API_KEY_1=from-file-one\nGEMINI_API_KEY_2=from-file-two\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=str(env_file))
    settings.model_config["env_file"] = str(env_file)

    assert settings.gemini_api_keys() == ["from-file-one", "from-file-two"]


def test_real_environment_wins_over_the_env_file(tmp_path, monkeypatch):
    """Matches pydantic-settings' own precedence, and how Docker passes keys."""
    for name in list(__import__("os").environ):
        if name.startswith("GEMINI_API_KEY"):
            monkeypatch.delenv(name, raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY_1=from-file\n", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY_1", "from-environment")

    settings = Settings(_env_file=str(env_file))
    settings.model_config["env_file"] = str(env_file)

    assert settings.gemini_api_keys() == ["from-environment"]
