import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.dependencies import get_natural_query_service
from src.core.config import settings
from src.main import app
from src.nlq.exceptions import InterpretationError, InterpreterUnavailableError
from src.nlq.models import NaturalQueryResult, PlaceCandidate, SpatialIntent

PROJECT_ID = uuid.uuid4()
URL = f"/api/v1/projects/{PROJECT_ID}/query/natural"


class StubService:
    def __init__(self, result=None, error=None):
        self._result = result
        self._error = error

    async def answer(self, project_id, query):
        if self._error:
            raise self._error
        return self._result


def client_for(service):
    app.dependency_overrides[get_natural_query_service] = lambda: service
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


async def test_ok_response_carries_a_feature_collection():
    """The map already renders this shape - the contract must not drift."""
    result = NaturalQueryResult(
        status="ok",
        query="hospitals within 2km of Lalbagh Botanical Gardens",
        answer="Found 1 hospital within 2 km of Lalbagh Botanical Gardens.",
        interpretation=SpatialIntent(
            operation="nearby",
            reference_place="Lalbagh Botanical Gardens",
            target_category="hospital",
            distance_meters=2000,
        ),
        result={
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": str(uuid.uuid4()),
                    "geometry": {"type": "Point", "coordinates": [77.58, 12.94]},
                    "properties": {"category": "hospital"},
                }
            ],
        },
        focus={"lon": 77.5856, "lat": 12.9486},
    )

    async with client_for(StubService(result)) as client:
        response = await client.post(URL, json={"query": "hospitals near Lalbagh"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["status"] == "ok"
    assert data["result"]["type"] == "FeatureCollection"
    assert len(data["result"]["features"]) == 1
    assert data["interpretation"]["operation"] == "nearby"
    assert data["focus"] == {"lon": 77.5856, "lat": 12.9486}


async def test_ambiguous_response_returns_candidates():
    result = NaturalQueryResult(
        status="ambiguous",
        query="hospitals near Lalbagh",
        answer="'Lalbagh' matches 3 places in this project.",
        candidates=[
            PlaceCandidate(
                feature_id=uuid.uuid4(),
                feature_name=name,
                dataset_id=uuid.uuid4(),
                dataset_name="bangalore osm",
                category=category,
                geometry_type="ST_Point",
                lon=77.58,
                lat=12.94,
            )
            for name, category in [
                ("Lalbagh", "station"),
                ("Lalbagh Nursing Home", "hospital"),
                ("Lalbagh Botanical Gardens", "park"),
            ]
        ],
    )

    async with client_for(StubService(result)) as client:
        response = await client.post(URL, json={"query": "hospitals near Lalbagh"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ambiguous"
    assert len(data["candidates"]) == 3
    assert data["result"] is None


async def test_interpreter_unavailable_maps_to_503():
    error = InterpreterUnavailableError("interpreter is unavailable")

    async with client_for(StubService(error=error)) as client:
        response = await client.post(URL, json={"query": "anything"})

    assert response.status_code == 503


async def test_uninterpretable_question_maps_to_422():
    error = InterpretationError("not a spatial question")

    async with client_for(StubService(error=error)) as client:
        response = await client.post(URL, json={"query": "what is the weather"})

    assert response.status_code == 422


@pytest.mark.parametrize("payload", [{}, {"query": ""}, {"query": "x" * 501}])
async def test_request_validation(payload):
    async with client_for(StubService(None)) as client:
        response = await client.post(URL, json=payload)

    assert response.status_code == 422


async def test_missing_api_key_degrades_to_503(monkeypatch):
    """No Claude credentials must cost exactly one endpoint, nothing else.

    This exercises the real dependency chain rather than an override, so it also
    proves resolving it touches no database.
    """
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(URL, json={"query": "hospitals near Lalbagh"})
        health = await client.get("/api/v1/health")

    assert response.status_code == 503
    assert "ANTHROPIC_API_KEY" in response.json()["error"]["message"]
    assert health.status_code == 200
