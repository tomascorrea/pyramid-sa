# Audit Trail

`AuditMixin` adds columns to track who created and updated each record and when. The columns are always present on models that use the mixin; the *behavior* (auto-populating fields from the request) is activated separately via a Pyramid directive.

## Columns

| Column | Type | Set on |
|---|---|---|
| `created_at` | `DateTime` | Insert (default: `datetime.now(UTC)`) |
| `updated_at` | `DateTime` | Update (via `onupdate`) |
| `created_by` | `String(40)` | Insert (from `request.authenticated_userid`) |
| `updated_by` | `String(40)` | Update (from `request.authenticated_userid`) |
| `created_ip` | `String(40)` | Insert (from `request.client_addr`) |
| `updated_ip` | `String(40)` | Update (from `request.client_addr`) |

## Usage

### Adding audit columns to a model

Use `AuditMixin` directly or inherit from `Model` (which includes it):

```python
from pyramid_sa import Base
from pyramid_sa.models.audit import AuditMixin


class Item(AuditMixin, Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
```

Or use `Model` which bundles `AuditMixin` + `SoftDeleteMixin` + `Base`:

```python
from pyramid_sa import Model


class Item(Model):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
```

### Activating automatic field population

The columns exist on the model regardless, but to have `created_by`, `updated_by`, `created_ip`, and `updated_ip` populated automatically from the request, call the directive in your app factory:

```python
config.include("pyramid_sa")
config.sa_enable_audit()
```

This registers `before_insert` and `before_update` event listeners on the SQLAlchemy mapper. The listeners:

1. Check if the target model is an `AuditMixin` instance
2. Read `request.authenticated_userid` from the session's `info["request"]`
3. Set `created_by`/`updated_by` (truncated to 40 chars) and `created_ip`/`updated_ip`

## Columns vs behavior

Mixins provide **columns** at import time. Directives activate **behavior** at app startup.

A model can have `AuditMixin` columns without calling `sa_enable_audit()`. In that case, `created_at` and `updated_at` still work (they use SQLAlchemy's `default` and `onupdate`), but `created_by`, `updated_by`, `created_ip`, and `updated_ip` will remain `NULL` unless you set them manually.

This separation is intentional — it allows shared schemas where some apps populate audit fields and others don't.
