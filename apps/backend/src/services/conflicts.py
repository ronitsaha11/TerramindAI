from sqlalchemy.exc import IntegrityError


def is_unique_violation(exc: IntegrityError) -> bool:
    """Return whether an IntegrityError is a PostgreSQL unique-constraint violation."""
    original = exc.orig
    return any(
        getattr(error, "sqlstate", None) == "23505"
        or getattr(error, "pgcode", None) == "23505"
        for error in (original, getattr(original, "__cause__", None))
        if error is not None
    )
