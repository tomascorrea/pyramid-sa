# Error Handling

pyramid-sa includes an exception tween that translates common SQLAlchemy exceptions into HTTP error responses with JSON bodies. The tween is registered automatically when you call `config.include("pyramid_sa")`.

## Default behavior

| Exception | HTTP Status | Default body |
|---|---|---|
| `sqlalchemy.orm.exc.NoResultFound` | 404 Not Found | `{"error": "not_found", "message": "Resource not found."}` |
| `sqlalchemy.exc.IntegrityError` | 409 Conflict | `{"error": "conflict", "message": "Operation violates a uniqueness constraint."}` |

The tween sits below `excview_tween_factory` so normal Pyramid HTTP exceptions still work as expected. Any exception not listed above propagates unchanged.

## Custom error formatters

To match your API's error schema, override the default bodies with `sa_error_formatter`:

```python
def my_not_found(request):
    return {"code": "NOT_FOUND", "detail": "The requested resource does not exist."}


def my_conflict(request):
    return {"code": "CONFLICT", "detail": "A record with this value already exists."}


config.include("pyramid_sa")
config.sa_error_formatter(not_found=my_not_found, conflict=my_conflict)
```

Each formatter is a callable with signature `(request) -> dict`. The returned dict becomes the `json_body` of the HTTP error response.

### Partial overrides

Both arguments are optional. You can override just one:

```python
config.sa_error_formatter(not_found=my_not_found)
# conflict keeps the default body
```

### Access to request context

Since formatters receive the current request, you can use any request-scoped data:

```python
def localized_not_found(request):
    return {
        "error": "not_found",
        "message": request.localizer.translate("Resource not found."),
    }
```
