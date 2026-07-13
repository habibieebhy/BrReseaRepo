from __future__ import annotations

from core.exceptions import ValidationError


PERMANENT_EXCEPTION_NAMES = {
    "DataError",
    "IntegrityError",
    "ProgrammingError",
    "UndefinedColumn",
    "UndefinedTable",
}


def is_retryable_exception(exc: Exception) -> bool:
    """Return whether repeating the same task could plausibly succeed."""

    if isinstance(
        exc,
        (
            ValidationError,
            ValueError,
            TypeError,
            KeyError,
            FileNotFoundError,
            PermissionError,
            NotImplementedError,
        ),
    ):
        return False
    if exc.__class__.__name__ in PERMANENT_EXCEPTION_NAMES:
        return False
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int) and 400 <= status_code < 500:
        return False
    return True
