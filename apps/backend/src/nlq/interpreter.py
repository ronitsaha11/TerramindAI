import copy
import logging
from collections.abc import Callable
from typing import Any, Protocol

from pydantic import ValidationError

from src.nlq.exceptions import InterpretationError, InterpreterUnavailableError
from src.nlq.key_pool import GeminiKeyPool, is_quota_error, redact
from src.nlq.models import ProjectCatalogue, SpatialIntent

logger = logging.getLogger(__name__)

# Bounded extraction: the reply is a handful of short fields, never prose.
MAX_TOKENS = 1024

SYSTEM_PROMPT = """\
You turn questions about geographic data into one structured query.

TerraMind computes the geography itself, using a spatial database. Your only \
job is to choose an operation and name what the user is asking about. You do \
not see the data, you do not compute the answer, and you do not write queries.

Operations:
- "nearby": features within a radius of a place. Needs reference_place and \
distance_meters.
- "contains": features located inside a named area. Needs reference_place.
- "intersects": features of one dataset that overlap a named feature. Needs \
reference_place and target_dataset.

{catalogue}

Rules:
- Copy reference_place exactly as the user wrote it. Do not expand it, correct \
its spelling, or resolve which specific place is meant - several places may \
share a name, and choosing between them is not your decision.
- target_category is the kind of feature the user asked for, in the singular. \
Copy it even when it is not in the list above: TerraMind checks it against the \
real data and tells the user when it does not exist. Never substitute a \
different category for one that is missing, and never leave target_category \
out because the category is unavailable - omitting it means "the user asked \
for everything", which is a different question and would return a confident \
answer to something nobody asked.
- Omit target_category only when the user genuinely wants every feature, as in \
"what is inside the park".
- target_dataset must be one of the dataset names listed above. Omit it unless \
the user named a dataset or the operation is "intersects".
- Convert distances to metres: "2 km" is 2000.
- Never invent a dataset or a place that is not in the question or the list \
above.
"""

# Gemini's response_schema is a subset of JSON Schema. These keywords are
# rejected outright, and `exclusiveMinimum` is not optional for us: SpatialIntent
# declares `distance_meters` as `gt=0`, which Pydantic emits as exactly that.
#
# The resolution is deliberate. The schema handed to Gemini is a *generation
# hint*; SpatialIntent remains the authority, and every reply is validated
# against the real model afterwards. Loosening the model to fit the transport
# would turn a security control into a formatting preference.
_UNSUPPORTED_SCHEMA_KEYS = (
    "additionalProperties",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "const",
    "$schema",
    "discriminator",
)


def _sanitise(node: Any) -> Any:
    """Recursively drop schema keywords Gemini's Schema type rejects."""
    if isinstance(node, list):
        return [_sanitise(item) for item in node]
    if not isinstance(node, dict):
        return node

    cleaned = {
        key: _sanitise(value)
        for key, value in node.items()
        if key not in _UNSUPPORTED_SCHEMA_KEYS
    }

    # Pydantic renders `str | None` as an anyOf against a null branch; Gemini
    # expects `nullable` on the single real variant instead.
    variants = cleaned.get("anyOf")
    if isinstance(variants, list):
        real = [v for v in variants if isinstance(v, dict) and v.get("type") != "null"]
        if len(real) == 1 and len(variants) > 1:
            merged = dict(real[0])
            merged["nullable"] = True
            for carried in ("description", "title"):
                if carried in cleaned:
                    merged.setdefault(carried, cleaned[carried])
            return merged

    return cleaned


def gemini_response_schema() -> dict[str, Any]:
    """SpatialIntent rendered in the schema subset Gemini accepts."""
    return _sanitise(copy.deepcopy(SpatialIntent.model_json_schema()))


def _render_catalogue(catalogue: ProjectCatalogue) -> str:
    if not catalogue.datasets:
        return "This project currently has no datasets."

    lines = ["Available data in this project:"]
    for dataset in catalogue.datasets:
        categories = ", ".join(sorted(dataset.categories)) or "none"
        lines.append(
            f'- dataset "{dataset.name}": {dataset.feature_count} features; '
            f"categories: {categories}"
        )
    return "\n".join(lines)


class NLQInterpreter(Protocol):
    """Turns a question plus a catalogue into a validated SpatialIntent.

    A Protocol so the pipeline can be exercised end-to-end without a network
    call or an API key - the tests substitute a deterministic implementation.
    """

    async def interpret(
        self, query: str, catalogue: ProjectCatalogue
    ) -> SpatialIntent: ...


class GeminiInterpreter:
    """Interprets natural language with the Gemini API.

    This class is the entire surface through which a language model touches
    TerraMind. It receives a question and a vocabulary of names; it returns a
    SpatialIntent or raises. It has no database access and no knowledge of
    identifiers, so there is nothing here for a malicious prompt to reach.

    Constrained decoding narrows what the model can emit, but it is not trusted
    to be sufficient: the reply is parsed against SpatialIntent regardless, so
    a bound the transport could not express is still enforced here.

    A client is built per key rather than injected, because a quota refusal is
    answered by retrying the same request on the next key in the pool.
    """

    def __init__(
        self,
        client_factory: Callable[[str], Any],
        key_pool: GeminiKeyPool,
        model: str = "gemini-3.6-flash",
    ) -> None:
        self._client_factory = client_factory
        self._pool = key_pool
        self._model = model

    async def interpret(self, query: str, catalogue: ProjectCatalogue) -> SpatialIntent:
        system = SYSTEM_PROMPT.format(catalogue=_render_catalogue(catalogue))

        last_error: BaseException | None = None

        # Bounded by the number of configured keys: the pool's cursor wraps, so
        # an unbounded loop over an exhausted ring would spin forever.
        for _ in range(max(self._pool.slot_count, 1)):
            slot, api_key = self._pool.current()

            try:
                payload = await self._generate(api_key, query, system)
            except Exception as exc:
                if is_quota_error(exc):
                    # The pool logs the rotation, by slot number only.
                    last_error = exc
                    if self._pool.retire(slot):
                        continue
                    break

                # Anything that is not a quota refusal is a fault no other key
                # can fix - a bad request, a rejected key, a missing model, a
                # bug. Fail now rather than replaying it across every key.
                logger.warning(
                    "Gemini interpretation call failed on key %d: %s",
                    slot,
                    redact(str(exc), self._pool.secrets),
                )
                raise InterpreterUnavailableError(
                    "The natural-language interpreter is unavailable."
                ) from exc

            if not payload:
                # An empty body means the model produced nothing usable - a
                # safety stop or a truncated reply. Refuse rather than guess.
                raise InterpretationError(
                    "The interpreter did not return a valid spatial query."
                )
            return build_intent_json(payload)

        logger.warning(
            "Every configured Gemini key (%d) is out of quota.",
            self._pool.slot_count,
        )
        raise InterpreterUnavailableError(
            "The natural-language interpreter is unavailable: every configured "
            "Gemini key is out of quota."
        ) from last_error

    async def _generate(self, api_key: str, query: str, system: str) -> str | None:
        """One Gemini call with one key. Isolated so the retry loop stays legible."""
        from google.genai import types

        client = self._client_factory(api_key)
        response = await client.aio.models.generate_content(
            model=self._model,
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_schema=gemini_response_schema(),
                max_output_tokens=MAX_TOKENS,
                temperature=0,
                # No tools are declared, so the automatic function-calling path
                # has nothing to do; disabling it keeps the SDK from warning on
                # every call.
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )
        text: str | None = getattr(response, "text", None)
        return text


def build_intent(payload: dict) -> SpatialIntent:
    """Validate a raw intent mapping, translating failure into InterpretationError.

    Used wherever an intent arrives as loose data rather than from the SDK's
    constrained decoding.
    """
    try:
        return SpatialIntent.model_validate(payload)
    except ValidationError as exc:
        raise InterpretationError(str(exc)) from exc


def build_intent_json(payload: str) -> SpatialIntent:
    """Validate a raw JSON intent, translating failure into InterpretationError."""
    try:
        return SpatialIntent.model_validate_json(payload)
    except ValidationError as exc:
        raise InterpretationError(str(exc)) from exc
