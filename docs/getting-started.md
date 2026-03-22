# Getting Started

## Installation

```bash
pip install pyramid-sa
```

For test fixtures (dev only):

```bash
pip install pyramid-sa-testing
```

## App factory

In your Pyramid application factory, include `pyramid_sa` and scan your model modules:

```python
from pyramid.config import Configurator


def create_app(global_config=None, dbengine=None, **settings):
    config = Configurator(settings=settings)

    if dbengine is not None:
        config.registry["dbengine"] = dbengine

    config.include("pyramid_sa")
    config.sa_scan_models("myapp.models")

    config.scan(".views")
    return config.make_wsgi_app()
```

`sa_scan_models` accepts one or more dotted module paths. It imports each module (registering models with `Base`) and calls `configure_mappers()` so all relationships are resolved.

## What `config.include("pyramid_sa")` does

1. Includes `pyramid_tm` (transaction management)
2. Creates the SQLAlchemy engine from `sqlalchemy.url` in settings (or uses `config.registry["dbengine"]` if pre-set)
3. Registers a session factory and adds `request.dbsession` as a reified property
4. Adds an exception tween (`NoResultFound` → 404, `IntegrityError` → 409)
5. Configures a JSON renderer with adapters for `datetime`, `date`, and `UUID`
6. Registers directives on the Configurator:
    - `sa_scan_models` — import model modules and configure mappers
    - `sa_enable_audit` — activate [audit trail](audit.md) event listeners
    - `sa_enable_soft_delete` — activate [soft-delete](soft-delete.md) behavior
    - `sa_error_formatter` — customize [error response bodies](error-handling.md)

## First model

All models should inherit from `pyramid_sa.Base`:

```python
import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from pyramid_sa import Base, generate_uuid


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid.UUID] = mapped_column(default=generate_uuid, unique=True)
    name: Mapped[str] = mapped_column(String(255))
```

`Base` includes `ORMClass`, which gives every model `as_dict()` and `copy_with()` methods. See [Base & Models](models.md) for details.

For models that need audit columns and soft-delete support, use `Model` instead:

```python
from pyramid_sa import Model


class Article(Model):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
```

`Model` combines `AuditMixin` + `SoftDeleteMixin` + `Base` for the common case. See [Base & Models](models.md) for guidance on when to use each.

## Enabling optional features

After `config.include("pyramid_sa")`, activate the features your app needs:

```python
config.include("pyramid_sa")
config.sa_enable_audit()          # populate audit fields from request
config.sa_enable_soft_delete()    # intercept deletes, filter queries
config.sa_scan_models("myapp.models")
```

Each directive is opt-in — your app only gets the behavior it asks for.
