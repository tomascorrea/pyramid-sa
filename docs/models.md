# Base & Models

pyramid-sa provides two base classes for your models: `Base` and `Model`. Both include utility methods from `ORMClass`.

## Base

`Base` is a SQLAlchemy `DeclarativeBase` with consistent naming conventions and utility methods:

```python
from pyramid_sa import Base
```

All models inheriting from `Base` get:

- **Naming conventions** for indexes, constraints, and foreign keys (compatible with Alembic autogenerate)
- **`as_dict()`** and **`copy_with()`** utility methods via `ORMClass`

Use `Base` when you want a plain model without audit or soft-delete columns.

### Naming conventions

| Type | Pattern | Example |
|---|---|---|
| Primary key | `pk_%(table_name)s` | `pk_items` |
| Unique constraint | `uq_%(table_name)s_%(column_0_name)s` | `uq_items_uuid` |
| Index | `ix_%(column_0_label)s` | `ix_items_name` |
| Foreign key | `fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s` | `fk_orders_user_id_users` |
| Check constraint | `ck_%(table_name)s_%(constraint_name)s` | `ck_items_positive_price` |

## Model

`Model` is a convenience base class that combines `AuditMixin` + `SoftDeleteMixin` + `Base`:

```python
from pyramid_sa import Model


class Article(Model):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
```

This gives your model audit columns (`created_at`, `updated_at`, etc.) and soft-delete columns (`deleted_at`, `deleted_by`, `deleted_ip`) automatically. See [Audit Trail](audit.md) and [Soft Delete](soft-delete.md) for details.

## When to use `Base` vs `Model`

| Scenario | Use |
|---|---|
| Model needs both audit tracking and soft-delete | `Model` |
| Model needs only audit columns | `Base` + `AuditMixin` |
| Model needs only soft-delete columns | `Base` + `SoftDeleteMixin` |
| Plain model with no extras | `Base` |

Example with selective mixins:

```python
from pyramid_sa import Base
from pyramid_sa.audit import AuditMixin


class LogEntry(AuditMixin, Base):
    """Audited but not soft-deletable."""

    __tablename__ = "log_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    message: Mapped[str] = mapped_column(String(500))
```

## ORMClass utilities

Every model inheriting from `Base` (or `Model`) gets these methods from `ORMClass`.

### `as_dict()`

Convert a model instance to a dictionary:

```python
item = dbsession.get(Item, 1)
data = item.as_dict()
```

Parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hide_internal_fields` | `bool` | `True` | Removes `id`, renames `uuid` to `id` |
| `convert_to_camel` | `bool` | `True` | Converts snake_case keys to camelCase |
| `exclude` | `list[str] \| None` | `None` | Column names to exclude |

With defaults, `as_dict()` produces API-friendly output:

```python
item.as_dict()
# {"id": "550e8400-...", "name": "Widget", "createdAt": "2024-01-15T...", ...}

item.as_dict(hide_internal_fields=False, convert_to_camel=False)
# {"id": 1, "uuid": "550e8400-...", "name": "Widget", "created_at": "2024-01-15T...", ...}
```

### `copy_with()`

Create a detached copy of a model instance with optional field overrides:

```python
original = dbsession.get(Item, 1)
clone = original.copy_with(name="Widget v2")
dbsession.add(clone)
```

The copy excludes `id`, `uuid`, `created_at`, and `updated_at` — the new instance gets fresh values for these.

## `generate_uuid()`

A convenience function that returns a new `uuid.UUID` (v4), useful as a column default:

```python
from pyramid_sa import Base, generate_uuid


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid.UUID] = mapped_column(default=generate_uuid, unique=True)
```
