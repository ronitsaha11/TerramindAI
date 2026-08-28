import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# The complete set of spatial operations the language model may select. These
# map one-to-one onto the verified primitives in DatasetFeatureRepository; there
# is deliberately no escape hatch for anything else.
Operation = Literal["nearby", "contains", "intersects"]

# Upper bound on a requested radius. ST_DWithin casts to ::geography, so this is
# real metres; the cap keeps a mis-parsed "2 km" from turning into a whole-planet
# scan that would return the entire dataset.
MAX_DISTANCE_METERS = 50_000.0


class SpatialIntent(BaseModel):
    """The only structure Claude is permitted to emit.

    Every field is a *name* or a number - never an identifier. Claude cannot
    address a row, because it is never shown one: resolving these names to
    dataset and feature UUIDs is done afterwards, in Python, against the live
    registry. `extra="forbid"` makes an invented field a validation failure
    rather than something that is silently carried along.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    operation: Operation = Field(
        ..., description="Which spatial operation answers the question."
    )
    reference_place: str | None = Field(
        default=None,
        description=(
            "Name of the place the query is anchored to, exactly as the user "
            "wrote it (for example 'Lalbagh'). Do not expand or correct it."
        ),
    )
    target_category: str | None = Field(
        default=None,
        description=(
            "Category of feature the user wants back, singular (for example "
            "'hospital'). Omit when the user asks for everything nearby."
        ),
    )
    target_dataset: str | None = Field(
        default=None,
        description=(
            "Name of the dataset to search, only when the user names one. "
            "Omit to search the dataset the reference place belongs to."
        ),
    )
    distance_meters: float | None = Field(
        default=None,
        gt=0,
        le=MAX_DISTANCE_METERS,
        description="Search radius in metres. Required for 'nearby'.",
    )

    @model_validator(mode="after")
    def _require_fields_per_operation(self) -> "SpatialIntent":
        if not self.reference_place:
            raise ValueError(
                f"operation '{self.operation}' requires a reference_place."
            )
        if self.operation == "nearby" and self.distance_meters is None:
            raise ValueError("operation 'nearby' requires distance_meters.")
        if self.operation == "intersects" and not self.target_dataset:
            raise ValueError(
                "operation 'intersects' requires target_dataset - the dataset "
                "to test against the reference feature."
            )
        return self


class DatasetSummary(BaseModel):
    """One dataset as described to Claude. Names and categories only."""

    model_config = ConfigDict(frozen=True)

    name: str
    feature_count: int
    categories: list[str] = Field(default_factory=list)


class ProjectCatalogue(BaseModel):
    """Everything Claude is told about a project's data.

    No geometry, no coordinates, no identifiers, no feature rows - only the
    vocabulary needed to choose an operation and name a target.
    """

    model_config = ConfigDict(frozen=True)

    datasets: list[DatasetSummary] = Field(default_factory=list)

    def category_values(self) -> set[str]:
        return {c for d in self.datasets for c in d.categories}

    def dataset_names(self) -> set[str]:
        return {d.name for d in self.datasets}


class PlaceCandidate(BaseModel):
    """A feature that matched a reference place name."""

    model_config = ConfigDict(frozen=True)

    feature_id: uuid.UUID
    feature_name: str
    dataset_id: uuid.UUID
    dataset_name: str
    category: str | None = None
    geometry_type: str
    lon: float
    lat: float


class NaturalQueryResult(BaseModel):
    """What the service returns for any natural-language question.

    `status` distinguishes the three real outcomes. "ambiguous" is a first-class
    result, not an error: when a place name matches several features the caller
    is asked which one, because guessing would return a confident answer to a
    question nobody asked.
    """

    model_config = ConfigDict(frozen=True)

    status: Literal["ok", "ambiguous", "unresolved"]
    query: str
    answer: str
    interpretation: SpatialIntent | None = None
    # A GeoJSON FeatureCollection in exactly the shape the map already renders.
    result: dict[str, Any] | None = None
    # Point the map should centre on - the resolved reference place.
    focus: dict[str, float] | None = None
    candidates: list[PlaceCandidate] = Field(default_factory=list)


class NaturalQueryRequest(BaseModel):
    """Inbound request body."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The user's question in plain language.",
    )
