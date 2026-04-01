"""Shared utility helpers."""

import uuid
from datetime import UTC, datetime


def _now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime.

    Uses ``datetime.UTC`` (Python 3.11+).  The returned ``tzinfo`` is
    ``datetime.timezone.utc``, which compares equal to ``pytz.UTC`` for
    equality checks but produces a different ``repr``.  Projects migrating
    from naive datetimes (PostgreSQL ``TIMESTAMP WITHOUT TIME ZONE``) should
    ensure their column types match — use ``TIMESTAMP(timezone=True)`` or
    cast existing data to avoid mixed-offset comparisons.
    """
    return datetime.now(UTC)


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()
