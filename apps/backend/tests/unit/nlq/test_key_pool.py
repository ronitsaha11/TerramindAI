"""Tests for Gemini key rotation.

All hermetic: no network, no key, no SDK. Rotation is the part that only ever
runs when something has already gone wrong in production, so it has to be
provable without waiting for a real quota refusal.
"""

import logging

import pytest

from src.nlq.key_pool import GeminiKeyPool, is_quota_error, redact


class _Err(Exception):
    """Stands in for google.genai.errors.APIError, which carries code/status."""

    def __init__(self, code=None, status=None):
        super().__init__(f"{code} {status}")
        if code is not None:
            self.code = code
        if status is not None:
            self.status = status


# ── which failures rotate ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "exc",
    [
        _Err(code=429, status="RESOURCE_EXHAUSTED"),
        _Err(code=429),
        _Err(status="RESOURCE_EXHAUSTED"),
        _Err(status="resource_exhausted"),
    ],
)
def test_quota_refusals_rotate(exc):
    assert is_quota_error(exc) is True


@pytest.mark.parametrize(
    "exc",
    [
        _Err(code=400, status="INVALID_ARGUMENT"),  # malformed request
        _Err(code=401, status="UNAUTHENTICATED"),  # bad key - rotation hides it
        _Err(code=403, status="PERMISSION_DENIED"),  # config error
        _Err(code=404, status="NOT_FOUND"),  # retired model
        _Err(code=500, status="INTERNAL"),  # upstream bug
        _Err(code=503, status="UNAVAILABLE"),  # busy, not out of quota
        ValueError("application bug"),
        RuntimeError("no attributes at all"),
    ],
)
def test_everything_else_does_not_rotate(exc):
    """Rotating on these would burn every key on a fault no key can fix."""
    assert is_quota_error(exc) is False


def test_message_text_alone_never_triggers_rotation():
    """The message can contain the user's own question; only fields count."""
    assert is_quota_error(Exception("429 RESOURCE_EXHAUSTED")) is False


# ── the pool ─────────────────────────────────────────────────────────────


def test_first_key_is_used_normally():
    pool = GeminiKeyPool(["k1", "k2", "k3"])
    assert pool.current() == (1, "k1")
    assert pool.current_slot == 1
    assert pool.slot_count == 3


def test_retiring_a_slot_advances_to_the_next():
    pool = GeminiKeyPool(["k1", "k2", "k3"])
    assert pool.retire(1) is True
    assert pool.current() == (2, "k2")
    assert pool.retire(2) is True
    assert pool.current() == (3, "k3")


def test_rotation_persists_across_calls():
    """A key retired by one request must stay retired for the next."""
    pool = GeminiKeyPool(["k1", "k2"])
    pool.retire(1)
    assert pool.current() == (2, "k2")
    assert pool.current() == (2, "k2")


def test_retiring_a_stale_slot_is_ignored():
    """Concurrent requests that all fail on key 1 must advance it once."""
    pool = GeminiKeyPool(["k1", "k2", "k3"])
    pool.retire(1)
    pool.retire(1)  # a second request that also held slot 1
    pool.retire(1)
    assert pool.current() == (2, "k2")


def test_cursor_wraps_so_a_daily_quota_reset_is_reachable():
    """Forward-only would leave the endpoint dead until the process restarted."""
    pool = GeminiKeyPool(["k1", "k2"])
    pool.retire(1)
    pool.retire(2)
    assert pool.current() == (1, "k1")


def test_single_key_reports_no_alternative():
    pool = GeminiKeyPool(["only"])
    assert pool.retire(1) is False


def test_duplicates_collapse_so_rotation_is_not_wasted():
    pool = GeminiKeyPool(["k1", "k1", "k2"])
    assert pool.slot_count == 2


def test_blank_entries_are_dropped():
    pool = GeminiKeyPool(["", "  ", "k1", "\n"])
    assert pool.slot_count == 1
    assert pool.current() == (1, "k1")


def test_whitespace_is_stripped():
    assert GeminiKeyPool(["  k1  "]).current() == (1, "k1")


def test_empty_pool_reports_zero_and_refuses_to_hand_out_a_key():
    pool = GeminiKeyPool([])
    assert pool.slot_count == 0
    assert pool.retire(1) is False
    with pytest.raises(RuntimeError):
        pool.current()


# ── secrets never reach the logs ─────────────────────────────────────────


def test_rotation_log_names_the_slot_and_not_the_key(caplog):
    pool = GeminiKeyPool(["super-secret-1", "super-secret-2"])
    with caplog.at_level(logging.WARNING):
        pool.retire(1)

    text = caplog.text
    assert "key 1" in text
    assert "super-secret-1" not in text
    assert "super-secret-2" not in text


def test_redact_removes_every_configured_key():
    keys = ["abc123", "def456"]
    dirty = "failed for abc123 and also def456"
    clean = redact(dirty, keys)
    assert "abc123" not in clean
    assert "def456" not in clean
    assert "***" in clean


def test_redact_leaves_unrelated_text_alone():
    assert redact("429 RESOURCE_EXHAUSTED", ["abc123"]) == "429 RESOURCE_EXHAUSTED"


def test_redact_tolerates_blank_entries():
    assert redact("anything", ["", "  "]) == "anything"
