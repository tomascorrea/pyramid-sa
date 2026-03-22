"""Model mixins, helpers, and the convenience Model base class."""

from pyramid_sa.meta import Base
from pyramid_sa.models.audit import AuditMixin, sa_enable_audit
from pyramid_sa.models.soft_delete import (
    RestoreConflictError,
    SoftDeleteMixin,
    SoftDeleteSession,
    SoftDeleteUniqueIndex,
    sa_enable_soft_delete,
    soft_delete_mapped_column,
)


class Model(AuditMixin, SoftDeleteMixin, Base):
    """Auditable, soft-deletable base class — the common case.

    Use instead of ``Base`` when the model needs both audit columns and
    soft-delete support::

        class Article(Model):
            __tablename__ = "articles"
            ...
    """

    __abstract__ = True


__all__ = [
    "AuditMixin",
    "Model",
    "RestoreConflictError",
    "SoftDeleteMixin",
    "SoftDeleteSession",
    "SoftDeleteUniqueIndex",
    "sa_enable_audit",
    "sa_enable_soft_delete",
    "soft_delete_mapped_column",
]
