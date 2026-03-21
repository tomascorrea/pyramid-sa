"""JSON renderer with adapters for common types."""

import datetime
from uuid import UUID

from pyramid.renderers import JSON


def configure_json_renderer(config):
    """Register a JSON renderer with adapters for datetime, date, and UUID."""
    renderer = JSON()
    renderer.add_adapter(datetime.datetime, lambda obj, req: obj.isoformat())
    renderer.add_adapter(datetime.date, lambda obj, req: obj.isoformat())
    renderer.add_adapter(UUID, lambda obj, req: str(obj))
    config.add_renderer("json", renderer)
