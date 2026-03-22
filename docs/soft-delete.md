# Soft Delete

Soft delete marks rows as deleted instead of removing them from the database. pyramid-sa provides a mixin for columns, a session subclass for hard deletes, partial unique indexes for value reuse, and safe restore with conflict detection.

## Setup

### Adding soft-delete columns

Use `SoftDeleteMixin` directly or inherit from `Model` (which includes it):

```python
from pyramid_sa import Base
from pyramid_sa import SoftDeleteMixin


class Article(SoftDeleteMixin, Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
```

This adds three columns:

| Column | Type | Description |
|---|---|---|
| `deleted_at` | `DateTime` | When the row was soft-deleted (`None` = active) |
| `deleted_by` | `String(40)` | Who deleted it (from `request.authenticated_userid`) |
| `deleted_ip` | `String(40)` | Client IP at deletion time |

### Activating soft-delete behavior

The columns alone don't change how SQLAlchemy handles deletes or queries. To activate the behavior, call the directive in your app factory:

```python
config.include("pyramid_sa")
config.sa_enable_soft_delete()
config.sa_scan_models("myapp.models")
```

This registers event listeners for:

- **Delete interception** — `session.delete(obj)` sets `deleted_at` instead of issuing SQL DELETE
- **Query filtering** — SELECT queries automatically exclude rows where `deleted_at IS NOT NULL`
- **Index finalization** — `SoftDeleteUniqueIndex` and `soft_delete_mapped_column(unique=True)` are converted into partial unique indexes

## Soft-deleting a record

There are two ways to soft-delete:

### Via `session.delete()`

When `sa_enable_soft_delete()` is active, calling `session.delete()` on a `SoftDeleteMixin` model performs a soft delete:

```python
article = dbsession.get(Article, 1)
dbsession.delete(article)
# article.deleted_at is now set; the row stays in the database
```

The `deleted_by` and `deleted_ip` fields are populated from the request automatically.

### Via `soft_delete()` method

You can also call the instance method directly:

```python
article = dbsession.get(Article, 1)
article.soft_delete()
```

This sets `deleted_at`, `deleted_by`, and `deleted_ip` from the request. Unlike `session.delete()`, this is an explicit update — useful when you want to soft-delete without going through the session's delete machinery.

## Checking delete status

```python
article.is_deleted  # True if deleted_at is not None
```

## Query filtering

When `sa_enable_soft_delete()` is active, all SELECT queries automatically exclude soft-deleted rows:

```python
# Only returns articles where deleted_at IS NULL
articles = dbsession.scalars(select(Article)).all()
```

### Including deleted rows

Use the `include_deleted` execution option to bypass the filter:

```python
from sqlalchemy import select

stmt = select(Article).execution_options(include_deleted=True)
all_articles = dbsession.scalars(stmt).all()
```

## Hard delete

To permanently remove a row from the database, use `hard_delete()` on the session:

```python
article = dbsession.get(Article, 1)
dbsession.hard_delete(article)
# Row is actually deleted via SQL DELETE
```

This bypasses the soft-delete interception. The session is a `SoftDeleteSession` subclass that adds this method. Non-soft-delete models are always hard-deleted by `session.delete()`.

## Unique indexes

Soft-deleted rows can block reuse of unique values (e.g., a slug or email). pyramid-sa provides two APIs to create partial unique indexes that only constrain active rows (`WHERE deleted_at IS NULL`).

### `soft_delete_mapped_column` — single column

For single-column uniqueness at the column level:

```python
from pyramid_sa import Model, soft_delete_mapped_column


class Article(Model):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = soft_delete_mapped_column(String(255), unique=True)
    uuid: Mapped[str] = mapped_column(unique=True)  # stays globally unique
```

`soft_delete_mapped_column(unique=True)` creates a partial unique index. Regular `mapped_column(unique=True)` remains globally unique — you choose per column.

### `SoftDeleteUniqueIndex` — multi-column

For composite uniqueness in `__table_args__`:

```python
from pyramid_sa import Model, SoftDeleteUniqueIndex


class ScopedArticle(Model):
    __tablename__ = "scoped_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(40))
    slug: Mapped[str] = mapped_column(String(255))

    __table_args__ = (SoftDeleteUniqueIndex("tenant_id", "slug"),)
```

Both produce indexes named `uq_{table}_{cols}_active` with `WHERE deleted_at IS NULL`.

### Warning for plain unique constraints

When `sa_enable_soft_delete()` runs, it logs a warning if it finds a plain `UniqueConstraint` on a soft-delete model. This nudges you to choose explicitly between global uniqueness (keep `mapped_column(unique=True)`) and soft-delete-aware uniqueness (use `soft_delete_mapped_column(unique=True)` or `SoftDeleteUniqueIndex`).

## Restoring soft-deleted rows

### `restore()`

Un-delete a soft-deleted instance:

```python
stmt = select(Article).execution_options(include_deleted=True).where(Article.id == 1)
article = dbsession.scalars(stmt).one()
article.restore()
# deleted_at, deleted_by, deleted_ip are all cleared
```

If restoring would violate a partial unique constraint (another active row holds the same value), `restore()` raises `RestoreConflictError`:

```python
from pyramid_sa import RestoreConflictError

try:
    article.restore()
except RestoreConflictError as exc:
    print(exc.conflicts)  # [("slug",)] or [("tenant_id", "slug")]
    print(exc.instance)   # the article that can't be restored
```

### `can_restore()`

Check for conflicts before attempting to restore:

```python
conflicts = article.can_restore()
if not conflicts:
    article.restore()
else:
    # conflicts is a list of column-name tuples, e.g. [("slug",)]
    print(f"Cannot restore: conflicts on {conflicts}")
```

`can_restore()` queries for active rows with matching unique values. It returns an empty list when restore is safe.

## Columns vs behavior

Like [audit](audit.md), soft-delete separates columns from behavior:

- `SoftDeleteMixin` provides **columns** at import time
- `config.sa_enable_soft_delete()` activates **behavior** at app startup

A model can have the soft-delete columns without the behavior if the directive is never called. Queries won't be filtered and `session.delete()` will perform real deletes.

Soft-delete event listeners are registered on the specific `sessionmaker` instance, not the global `Session` class. This scoping prevents behavior from leaking across apps in the same process — important in test suites that create multiple Pyramid apps.
