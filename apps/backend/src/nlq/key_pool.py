"""Rotation across several Gemini API keys.

Gemini's free tier caps requests per day *per project per model*, so a single
key stops answering long before the day is out. Configuring several keys lets a
request that hits that ceiling be retried on the next one rather than surfaced
to the user as an outage.

Two things are deliberately kept out of this module: the SDK, so the rotation
logic can be tested without a network or a key, and the key material itself,
which is never logged - slots are identified by their 1-based number only.
"""

import logging
from collections.abc import Sequence

logger = logging.getLogger(__name__)


def is_quota_error(exc: BaseException) -> bool:
    """True only for a quota or rate-limit refusal, which another key may serve.

    Matched on the SDK's structured fields rather than on message text. The
    message can contain the user's own question, so substring matching would
    let a question mentioning "429" trigger rotation - and, worse, would rotate
    on failures a different key cannot fix.

    Everything else - malformed requests, an invalid or unauthorised key, a
    missing model, an application bug - is *not* a quota problem. Rotating on
    those would burn every configured key on a fault none of them can fix, and
    would hide a misconfiguration behind an apparently working system.
    """
    for attribute in ("code", "status_code"):
        if getattr(exc, attribute, None) == 429:
            return True

    status = getattr(exc, "status", None)
    return isinstance(status, str) and status.upper() == "RESOURCE_EXHAUSTED"


def redact(text: str, secrets: Sequence[str]) -> str:
    """Replace any configured key that appears in *text*.

    Nothing in the SDK is expected to echo a key back - it travels in a header,
    not the URL - but this is the one place a key could reach a log file, and an
    assumption about a third party's error formatting is a poor thing to rest a
    secret on.
    """
    for secret in secrets:
        if secret and secret in text:
            text = text.replace(secret, "***")
    return text


class GeminiKeyPool:
    """An ordered set of API keys with a rotating cursor.

    The cursor is process-level state, so a key retired by one request stays
    retired for the next one - rotation happens without a restart. It wraps:
    after the last key it returns to the first, because a daily quota resets on
    its own and a forward-only cursor would leave the endpoint dead until the
    process was bounced. Callers bound their own retries by `slot_count` so a
    single request can never loop over an exhausted ring.
    """

    def __init__(self, keys: Sequence[str]) -> None:
        seen: set[str] = set()
        ordered: list[str] = []
        for key in keys:
            cleaned = key.strip()
            # A duplicate would waste a rotation step on a key already known to
            # be exhausted, so identical entries collapse to one slot.
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                ordered.append(cleaned)

        self._keys = tuple(ordered)
        self._index = 0

    @property
    def slot_count(self) -> int:
        return len(self._keys)

    @property
    def current_slot(self) -> int:
        """1-based number of the active slot, for logs and diagnostics."""
        return self._index + 1

    @property
    def secrets(self) -> tuple[str, ...]:
        """Every configured key, for redaction. Never log this."""
        return self._keys

    def current(self) -> tuple[int, str]:
        """The active slot number and its key."""
        if not self._keys:
            raise RuntimeError("No Gemini API keys are configured.")
        return self._index + 1, self._keys[self._index]

    def retire(self, slot: int) -> bool:
        """Advance past *slot* because it is out of quota.

        Idempotent with respect to the slot: concurrent requests that all fail
        on the same key advance the cursor once between them, rather than each
        skipping a key that was never tried.

        Returns True when another slot is available to try.
        """
        if not self._keys:
            return False

        if slot == self.current_slot:
            self._index = (self._index + 1) % len(self._keys)
            logger.warning(
                "Gemini key %d exhausted (quota/rate limit); rotating to key %d of %d.",
                slot,
                self.current_slot,
                len(self._keys),
            )

        return len(self._keys) > 1
