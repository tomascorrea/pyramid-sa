# Domain Concepts

Key domain concepts, terminology, and mental models for this project.

## Glossary

| Term | Definition |
|---|---|
| includeme | Pyramid convention: a function that receives a Configurator and registers components |
| Base | DeclarativeBase with naming conventions and ORMClass utility methods (`as_dict`, `copy_with`) — every model inherits these |
| ORMClass | Plain Python class providing `as_dict` and `copy_with`; mixed into Base so all models get utility methods |
| Model | Convenience base class combining AuditMixin + SoftDeleteMixin + Base — the common case for most models |
| AuditMixin | Mixin adding created_at/updated_at/created_by/updated_by/created_ip/updated_ip columns |
| SoftDeleteMixin | Mixin adding deleted_at/deleted_by/deleted_ip columns plus `soft_delete()`, `restore()`, `is_deleted` |
| SoftDeleteSession | Session subclass adding `hard_delete()` for real SQL DELETE, bypassing soft-delete interception |
| sa_enable_audit | Pyramid directive that registers audit event listeners (`before_insert`, `before_update`) |
| sa_enable_soft_delete | Pyramid directive that registers soft-delete event listeners (query filtering, delete interception, unique index transformation) |
| sa_error_formatter | Pyramid directive that configures custom error body formatters (`not_found`, `conflict`) for the exception tween. Each formatter is `(request) -> dict`. |
| Tween | Pyramid middleware-like layer that wraps request handling (used for exception mapping) |
| pyramid_tm | Pyramid plugin that manages a transaction per request via the transaction package |
| zope.sqlalchemy | Bridges SQLAlchemy sessions with the transaction package for automatic commit/rollback |
| Reified property | A Pyramid request property computed once and cached for the request lifetime |

## Mental Models

- **Columns vs Behavior**: Mixins add columns at import time. Directives activate behavior at app startup. A model can have `SoftDeleteMixin` columns without soft-delete behavior if `sa_enable_soft_delete()` is never called.
- **Session lifecycle**: Each request gets one SQLAlchemy session. pyramid_tm commits on success, aborts on exception. zope.sqlalchemy registers the session with the transaction manager.
- **Soft-delete scoping**: Soft-delete event listeners are registered on the specific `sessionmaker` instance, not the global `Session` class. This ensures behavior is scoped per-app and doesn't leak across apps sharing the same process (important for tests).
- **Test isolation**: Tests use a doomed transaction manager — the transaction is always aborted after each test, rolling back all changes without needing cleanup.
- **Test structure**: Each test area has its own `app/` directory with a real Pyramid app factory and models. Tests always run against a properly configured Pyramid app, never standalone engines/sessions.
- **Test fixtures**: The conftest provides a layered hierarchy: `db_engine` → `app` (real Pyramid WSGI app) → `tm` (doomed TM) → `dbsession` → `app_request` (real request via `prepare()`) → `authenticated_request` (sets `test.userid` in environ). A `TestSecurityPolicy` reads the userid from `request.environ["test.userid"]`. All request fixtures use real Pyramid objects, never fakes.
- **Audit trail**: Event listeners on `before_insert` and `before_update` pull `authenticated_userid` and `client_addr` from the request stored in `session.info["request"]`.
- **Unique index transformation**: When `sa_enable_soft_delete()` is called, `UniqueConstraint`s on soft-delete models are replaced with filtered partial indexes (`WHERE deleted_at IS NULL`), allowing soft-deleted rows' unique values to be reused.

## Invariants

- `request.dbsession` is always transaction-managed (never a standalone session)
- `Base` always includes `ORMClass` — all models get `as_dict` and `copy_with`
- Audit columns and soft-delete columns are opt-in via mixins; their behavior is opt-in via directives
- The exception tween sits below `excview_tween_factory` so HTTP exceptions still work normally
- **Error body formatters**: The exception tween uses configurable callables `(request) -> dict` to build error response bodies. Defaults produce `{"error": ..., "message": ...}`. Apps override via `config.sa_error_formatter(not_found=fn, conflict=fn)`.
