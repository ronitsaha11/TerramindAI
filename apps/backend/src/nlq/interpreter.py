import logging
from typing import Protocol

from pydantic import ValidationError

from src.nlq.exceptions import InterpretationError, InterpreterUnavailableError
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
- target_category must be one of the categories listed above, in the singular.
- target_dataset must be one of the dataset names listed above. Omit it unless \
the user named a dataset or the operation is "intersects".
- Convert distances to metres: "2 km" is 2000.
- Never invent a dataset, category, or place that is not in the question or \
the list above.
"""


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


class ClaudeInterpreter:
    """Interprets natural language with the Claude API.

    This class is the entire surface through which a language model touches
    TerraMind. It receives a question and a vocabulary of names; it returns a
    SpatialIntent or raises. It has no database access and no knowledge of
    identifiers, so there is nothing here for a malicious prompt to reach.
    """

    def __init__(
        self,
        client: object,
        model: str = "claude-opus-5",
    ) -> None:
        self._client = client
        self._model = model

    async def interpret(self, query: str, catalogue: ProjectCatalogue) -> SpatialIntent:
        system = SYSTEM_PROMPT.format(catalogue=_render_catalogue(catalogue))

        try:
            response = await self._client.messages.parse(  # type: ignore[attr-defined]
                model=self._model,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": query}],
                output_format=SpatialIntent,
            )
        except Exception as exc:  # broad on purpose - surfaced as a 503 upstream
            logger.warning("Claude interpretation call failed: %s", exc)
            raise InterpreterUnavailableError(
                "The natural-language interpreter is unavailable."
            ) from exc

        intent = getattr(response, "parsed_output", None)
        if not isinstance(intent, SpatialIntent):
            # Constrained decoding should make this unreachable; if the schema
            # is ever not honoured we refuse rather than guess at the shape.
            raise InterpretationError(
                "The interpreter did not return a valid spatial query."
            )
        return intent


def build_intent(payload: dict) -> SpatialIntent:
    """Validate a raw intent mapping, translating failure into InterpretationError.

    Used wherever an intent arrives as loose data rather than from the SDK's
    constrained decoding.
    """
    try:
        return SpatialIntent.model_validate(payload)
    except ValidationError as exc:
        raise InterpretationError(str(exc)) from exc
