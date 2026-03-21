# Domain Concepts

Key domain concepts, terminology, and mental models for this project.

## Glossary

| Term | Definition |
|---|---|
| includeme | Pyramid convention: a function that receives a Configurator and registers components |
| AuditMixin | Mixin class adding created_at/updated_at/created_by/updated_by/created_ip/updated_ip to models |
| Tween | Pyramid middleware-like layer that wraps request handling (used for exception mapping) |
| pyramid_tm | Pyramid plugin that manages a transaction per request via the transaction package |
| zope.sqlalchemy | Bridges SQLAlchemy sessions with the transaction package for automatic commit/rollback |
| Reified property | A Pyramid request property computed once and cached for the request lifetime |

## Mental Models

- **Session lifecycle**: Each request gets one SQLAlchemy session. pyramid_tm commits on success, aborts on exception. zope.sqlalchemy registers the session with the transaction manager.
- **Test isolation**: Tests use a doomed transaction manager — the transaction is always aborted after each test, rolling back all changes without needing cleanup.
- **Audit trail**: Event listeners on `before_insert` and `before_update` pull `authenticated_userid` and `client_addr` from the request stored in `session.info["request"]`.

## Invariants

- `request.dbsession` is always transaction-managed (never a standalone session)
- `Base` always includes `AuditMixin` — all models get audit columns
- The exception tween sits below `excview_tween_factory` so HTTP exceptions still work normally
