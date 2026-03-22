"""Shared utility helpers."""

import uuid
from datetime import UTC, datetime


def _now() -> datetime:
    return datetime.now(UTC)


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()
