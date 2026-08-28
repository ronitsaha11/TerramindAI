class NLQException(Exception):
    """Base class for natural-language query failures."""


class InterpreterUnavailableError(NLQException):
    """The Claude API is not configured, or the call could not be completed.

    Raised so the router can degrade to 503 while every other endpoint keeps
    working - the same posture raster endpoints take when rasterio is missing.
    """


class InterpretationError(NLQException):
    """Claude did not produce a structure that satisfies SpatialIntent.

    This is a hard stop: an intent that fails schema validation is never
    resolved and never executed.
    """
