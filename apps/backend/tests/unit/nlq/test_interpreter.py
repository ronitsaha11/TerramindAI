"""Tests for the Gemini interpreter: the schema it sends, and key fallback.

Gemini's `response_schema` accepts a subset of JSON Schema, and SpatialIntent
does not fit it: `distance_meters` is declared `gt=0`, which Pydantic emits as
`exclusiveMinimum`, and Gemini rejects that outright with a ValidationError on
the request. The fix must never be to relax SpatialIntent - the radius bound is
a security control - so the schema is sanitised for transport while the model
stays the authority on what is acceptable.

The fallback tests drive the retry loop with fake clients, so quota exhaustion
is provable without burning a real key.
"""

import logging

import pytest

from src.nlq.exceptions import InterpretationError, InterpreterUnavailableError
from src.nlq.interpreter import (
    SYSTEM_PROMPT,
    GeminiInterpreter,
    build_intent_json,
    gemini_response_schema,
)
from src.nlq.key_pool import GeminiKeyPool
from src.nlq.models import (
    MAX_DISTANCE_METERS,
    DatasetSummary,
    ProjectCatalogue,
    SpatialIntent,
)

UNSUPPORTED = {
    "additionalProperties",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "const",
    "$schema",
    "discriminator",
}

CATALOGUE = ProjectCatalogue(
    datasets=[
        DatasetSummary(
            name="bangalore osm",
            feature_count=1188,
            categories=["hospital", "park", "station"],
        )
    ]
)

VALID_JSON = (
    '{"operation":"nearby","reference_place":"Lalbagh",'
    '"target_category":"hospital","distance_meters":2000}'
)


def _walk(node):
    """Yield every key in a nested schema."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


# ── the schema handed to Gemini ──────────────────────────────────────────


def test_schema_carries_no_keyword_gemini_rejects():
    """The regression guard. Gemini 400s on any of these, killing every query."""
    assert not (set(_walk(gemini_response_schema())) & UNSUPPORTED)


def test_raw_pydantic_schema_would_still_be_rejected():
    """Proves the sanitiser is load-bearing rather than decorative."""
    assert "exclusiveMinimum" in set(_walk(SpatialIntent.model_json_schema()))


def test_schema_still_describes_every_field():
    properties = gemini_response_schema()["properties"]
    assert set(properties) == {
        "operation",
        "reference_place",
        "target_category",
        "target_dataset",
        "distance_meters",
    }


def test_optional_fields_become_nullable_not_anyof():
    place = gemini_response_schema()["properties"]["reference_place"]
    assert place.get("nullable") is True
    assert "anyOf" not in place


def test_operation_stays_a_closed_enum():
    operation = gemini_response_schema()["properties"]["operation"]
    assert set(operation["enum"]) == {"nearby", "contains", "intersects"}


# ── SpatialIntent stays the authority ────────────────────────────────────


@pytest.mark.parametrize("distance", [0, -5, MAX_DISTANCE_METERS + 1])
def test_radius_bound_is_enforced_even_though_the_schema_cannot_express_it(distance):
    payload = (
        '{"operation":"nearby","reference_place":"Lalbagh",'
        f'"distance_meters":{distance}}}'
    )
    with pytest.raises(InterpretationError):
        build_intent_json(payload)


def test_invented_field_is_rejected():
    """extra="forbid" must survive the JSON round trip."""
    payload = (
        '{"operation":"nearby","reference_place":"Lalbagh",'
        '"distance_meters":2000,"sql":"DROP TABLE datasets"}'
    )
    with pytest.raises(InterpretationError):
        build_intent_json(payload)


def test_malformed_json_is_an_interpretation_error_not_a_crash():
    with pytest.raises(InterpretationError):
        build_intent_json("not json at all")


def test_valid_payload_round_trips():
    assert build_intent_json(VALID_JSON) == SpatialIntent(
        operation="nearby",
        reference_place="Lalbagh",
        target_category="hospital",
        distance_meters=2000,
    )


# ── an unsupported category must survive to the resolver ─────────────────


def test_prompt_forbids_dropping_an_unavailable_category():
    """The airport case: omitting the category silently removes the filter.

    "show airports within 3 km" once returned every feature in the radius with
    HTTP 200, because the model dropped the unavailable category and the
    service reads a null category as "no filter". The refusal exists in the
    resolver; the prompt has to let it be reached.
    """
    prompt = SYSTEM_PROMPT.lower()
    assert "copy it even when it is not in the list" in prompt
    assert "never leave target_category" in prompt


def test_unavailable_category_is_carried_through_not_nulled():
    intent = build_intent_json(
        '{"operation":"nearby","reference_place":"Lalbagh",'
        '"target_category":"airport","distance_meters":3000}'
    )
    # The resolver refuses this; what matters here is that it arrives at all.
    assert intent.target_category == "airport"


# ── fakes for the retry loop ─────────────────────────────────────────────


class _QuotaError(Exception):
    code = 429
    status = "RESOURCE_EXHAUSTED"


class _BadRequest(Exception):
    code = 400
    status = "INVALID_ARGUMENT"


class _Models:
    def __init__(self, outcome):
        self._outcome = outcome
        self.calls = 0

    async def generate_content(self, **kwargs):
        self.calls += 1
        self.kwargs = kwargs
        if isinstance(self._outcome, Exception):
            raise self._outcome
        return self._outcome


class _FakeClient:
    """Mimics genai.Client's `client.aio.models.generate_content` shape."""

    def __init__(self, outcome):
        self.models = _Models(outcome)
        self.aio = self

    @property
    def text(self):  # pragma: no cover - never used
        raise AssertionError


class _Response:
    def __init__(self, text):
        self.text = text


def _factory(outcomes):
    """Build a client factory mapping each key to its scripted outcome."""
    clients = {key: _FakeClient(outcome) for key, outcome in outcomes.items()}
    used: list[str] = []

    def factory(api_key):
        used.append(api_key)
        return clients[api_key]

    factory.clients = clients  # type: ignore[attr-defined]
    factory.used = used  # type: ignore[attr-defined]
    return factory


def _interpreter(outcomes, keys=None):
    keys = keys or list(outcomes)
    factory = _factory(outcomes)
    return GeminiInterpreter(factory, GeminiKeyPool(keys)), factory


# ── key rotation and quota fallback ──────────────────────────────────────


async def test_first_key_is_used_when_it_works():
    outcomes = {"k1": _Response(VALID_JSON), "k2": _Response(VALID_JSON)}
    interpreter, factory = _interpreter(outcomes)

    intent = await interpreter.interpret("hospitals near Lalbagh", CATALOGUE)

    assert intent.operation == "nearby"
    assert factory.used == ["k1"], "key 2 must not be touched while key 1 works"


async def test_quota_failure_retries_the_same_question_on_the_next_key():
    outcomes = {"k1": _QuotaError(), "k2": _Response(VALID_JSON)}
    interpreter, factory = _interpreter(outcomes)

    intent = await interpreter.interpret("hospitals near Lalbagh", CATALOGUE)

    assert intent.target_category == "hospital"
    assert factory.used == ["k1", "k2"]
    assert factory.clients["k2"].models.calls == 1


async def test_rotation_walks_through_several_exhausted_keys():
    outcomes = {
        "k1": _QuotaError(),
        "k2": _QuotaError(),
        "k3": _Response(VALID_JSON),
    }
    interpreter, factory = _interpreter(outcomes)

    await interpreter.interpret("hospitals near Lalbagh", CATALOGUE)

    assert factory.used == ["k1", "k2", "k3"]


async def test_rotation_is_remembered_for_the_next_request():
    """Rotation must survive between requests without restarting the server."""
    outcomes = {"k1": _QuotaError(), "k2": _Response(VALID_JSON)}
    interpreter, factory = _interpreter(outcomes)

    await interpreter.interpret("first", CATALOGUE)
    await interpreter.interpret("second", CATALOGUE)

    # k1 is tried once, then skipped entirely on the second question.
    assert factory.used == ["k1", "k2", "k2"]


async def test_all_keys_exhausted_degrades_to_unavailable():
    outcomes = {"k1": _QuotaError(), "k2": _QuotaError()}
    interpreter, factory = _interpreter(outcomes)

    with pytest.raises(InterpreterUnavailableError):
        await interpreter.interpret("hospitals near Lalbagh", CATALOGUE)

    assert factory.used == ["k1", "k2"], "each key tried exactly once, no looping"


async def test_non_quota_failure_does_not_burn_the_other_keys():
    """A malformed request is not fixed by another key, so do not spend one."""
    outcomes = {"k1": _BadRequest(), "k2": _Response(VALID_JSON)}
    interpreter, factory = _interpreter(outcomes)

    with pytest.raises(InterpreterUnavailableError):
        await interpreter.interpret("hospitals near Lalbagh", CATALOGUE)

    assert factory.used == ["k1"]


async def test_single_key_still_works_without_rotation():
    interpreter, factory = _interpreter({"solo": _Response(VALID_JSON)})
    intent = await interpreter.interpret("hospitals near Lalbagh", CATALOGUE)
    assert intent.operation == "nearby"


async def test_single_exhausted_key_reports_unavailable_once():
    interpreter, factory = _interpreter({"solo": _QuotaError()})
    with pytest.raises(InterpreterUnavailableError):
        await interpreter.interpret("hospitals near Lalbagh", CATALOGUE)
    assert factory.used == ["solo"]


async def test_no_key_material_is_logged_during_rotation(caplog):
    outcomes = {"secret-key-one": _QuotaError(), "secret-key-two": _QuotaError()}
    interpreter, _ = _interpreter(outcomes)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(InterpreterUnavailableError):
            await interpreter.interpret("hospitals near Lalbagh", CATALOGUE)

    assert "secret-key-one" not in caplog.text
    assert "secret-key-two" not in caplog.text
    assert "key 1" in caplog.text


async def test_a_key_echoed_in_an_error_is_redacted_from_the_log(caplog):
    """Defence in depth: nothing should echo a key, but if it did, not to disk."""
    outcomes = {"leaky-secret": _BadRequest()}
    outcomes["leaky-secret"].args = ("400 for key=leaky-secret",)
    interpreter, _ = _interpreter(outcomes)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(InterpreterUnavailableError):
            await interpreter.interpret("q", CATALOGUE)

    assert "leaky-secret" not in caplog.text
    assert "***" in caplog.text


# ── reply handling ───────────────────────────────────────────────────────


async def test_empty_reply_is_refused_rather_than_guessed():
    interpreter, _ = _interpreter({"k1": _Response("")})
    with pytest.raises(InterpretationError):
        await interpreter.interpret("hospitals near X", CATALOGUE)


async def test_reply_is_validated_against_spatial_intent():
    """Constrained decoding is not trusted on its own."""
    interpreter, _ = _interpreter(
        {"k1": _Response('{"operation":"teleport","reference_place":"X"}')}
    )
    with pytest.raises(InterpretationError):
        await interpreter.interpret("teleport me", CATALOGUE)


async def test_an_invalid_reply_is_not_retried_on_another_key():
    """A bad reply is the model's answer, not a quota problem."""
    outcomes = {
        "k1": _Response('{"operation":"teleport","reference_place":"X"}'),
        "k2": _Response(VALID_JSON),
    }
    interpreter, factory = _interpreter(outcomes)

    with pytest.raises(InterpretationError):
        await interpreter.interpret("teleport me", CATALOGUE)

    assert factory.used == ["k1"]


async def test_catalogue_reaches_the_model_as_vocabulary_only():
    """The prompt must carry names and counts - never rows, ids or geometry."""
    interpreter, factory = _interpreter({"k1": _Response(VALID_JSON)})
    await interpreter.interpret("hospitals within 2km of Lalbagh", CATALOGUE)

    system = factory.clients["k1"].models.kwargs["config"].system_instruction
    assert "bangalore osm" in system
    assert "hospital" in system
    for leak in ("geometry", "coordinates", "SELECT", "uuid"):
        assert leak not in system
