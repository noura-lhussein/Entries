"""Error payload shapes for the portal endpoints.

Ninja rendered every error as `{"detail": "..."}`. DRF renders a bare
`ValidationError("x")` as `["x"]` instead, which changes the shape a client has to
read — the portal looks for `detail`. These helpers keep the old shape so error
handling on the frontend is unaffected by the framework change.

Use them for portal routes. report_moe's own endpoints predate this and use DRF's
field-keyed validation errors, which their frontend already understands.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException, NotFound, ValidationError


def detail_error(message: str) -> ValidationError:
    """A 400 shaped like Ninja's: `{"detail": "..."}`."""
    return ValidationError({"detail": message})


def not_found(message: str = "Not found.") -> NotFound:
    return NotFound(message)


class Gone(APIException):
    """410 for routes that moved, rather than a generic failure."""

    status_code = 410

    def __init__(self, message: str):
        super().__init__({"detail": message})
