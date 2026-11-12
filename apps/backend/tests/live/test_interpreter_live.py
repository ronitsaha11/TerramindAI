"""Golden-set checks against the real Gemini API.

Deselected by default (see `addopts` in pyproject.toml) and never run in CI:
they need credentials, cost money, and are nondeterministic. Run deliberately:

    pytest -m live

These are the only tests that prove the prompt actually produces the intents we
expect. Everything else stubs the interpreter, which verifies the pipeline but
says nothing about whether interpretation is any good.
"""

import pytest

from src.core.config import settings
from src.nlq.interpreter import GeminiInterpreter
from src.nlq.key_pool import GeminiKeyPool
from src.nlq.models import DatasetSummary, ProjectCatalogue

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not settings.gemini_api_keys(),
        reason="no GEMINI_API_KEY / GEMINI_API_KEY_1.. is configured",
    ),
]

CATALOGUE = ProjectCatalogue(
    datasets=[
        DatasetSummary(
            name="bangalore osm",
            feature_count=1188,
            categories=["hospital", "park", "station"],
        ),
        DatasetSummary(name="test data", feature_count=3, categories=[]),
    ]
)


@pytest.fixture
def interpreter():
    """Backed by every configured key, so a golden run can outlast one quota."""
    from google import genai

    clients: dict[str, object] = {}

    def client_for(api_key: str) -> object:
        if api_key not in clients:
            clients[api_key] = genai.Client(api_key=api_key)
        return clients[api_key]

    return GeminiInterpreter(
        client_for,
        GeminiKeyPool(settings.gemini_api_keys()),
        model=settings.NLQ_MODEL,
    )


@pytest.mark.parametrize(
    ("question", "operation", "category", "distance"),
    [
        ("Show hospitals within 2 km of Lalbagh", "nearby", "hospital", 2000),
        ("hospitals within 2km of Lalbagh", "nearby", "hospital", 2000),
        ("find parks within 500 m of Cubbon Park", "nearby", "park", 500),
        ("which stations are within 1.5 km of Lalbagh", "nearby", "station", 1500),
        ("what is inside Lalbagh Botanical Gardens", "contains", None, None),
    ],
)
async def test_golden_intents(interpreter, question, operation, category, distance):
    intent = await interpreter.interpret(question, CATALOGUE)

    assert intent.operation == operation
    if category:
        assert intent.target_category == category
    if distance:
        assert intent.distance_meters == distance


async def test_place_name_is_copied_not_disambiguated(interpreter):
    """Choosing between same-named places is the backend's job, not the model's."""
    intent = await interpreter.interpret(
        "Show hospitals within 2 km of Lalbagh", CATALOGUE
    )

    assert intent.reference_place == "Lalbagh"


async def test_unknown_category_is_not_invented(interpreter):
    intent = await interpreter.interpret(
        "show airports within 3 km of Lalbagh", CATALOGUE
    )

    # Two failure modes, both of which turn a refusal into a wrong answer.
    #
    # Relabelling "airports" as a category that does exist would answer a
    # different question. Dropping it entirely is worse and was a real bug: a
    # null category means "the user wanted everything", so the request returned
    # every feature in the radius with HTTP 200. The category has to survive to
    # the resolver, which is what refuses it.
    assert intent.target_category is not None, (
        "an unavailable category must be preserved, not dropped - a null "
        "category removes the filter and returns everything nearby"
    )
    assert intent.target_category not in {"hospital", "park", "station"}
    assert "airport" in intent.target_category.casefold()
