"""Golden-set checks against the real Claude API.

Deselected by default (see `addopts` in pyproject.toml) and never run in CI:
they need credentials, cost money, and are nondeterministic. Run deliberately:

    pytest -m live

These are the only tests that prove the prompt actually produces the intents we
expect. Everything else stubs the interpreter, which verifies the pipeline but
says nothing about whether interpretation is any good.
"""

import os

import pytest

from src.nlq.interpreter import ClaudeInterpreter
from src.nlq.models import DatasetSummary, ProjectCatalogue

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY is not set",
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
    from anthropic import AsyncAnthropic

    return ClaudeInterpreter(AsyncAnthropic())


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

    # The resolver refuses anything outside the catalogue anyway; what matters
    # here is that the model does not silently relabel "airports" as one of the
    # categories that does exist, which would turn a refusal into a wrong answer.
    assert intent.target_category not in {"hospital", "park", "station"}
