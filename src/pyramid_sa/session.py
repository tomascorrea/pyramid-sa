"""SQLAlchemy engine and session management for Pyramid."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import register

from pyramid_sa.models.soft_delete import SoftDeleteSession


def get_engine(settings: dict, prefix: str = "sqlalchemy."):
    return create_engine(settings[f"{prefix}url"])


def get_session_factory(engine) -> sessionmaker[SoftDeleteSession]:
    return sessionmaker(bind=engine, class_=SoftDeleteSession)


def get_tm_session(
    session_factory: sessionmaker[SoftDeleteSession],
    transaction_manager,
    request=None,
) -> SoftDeleteSession:
    dbsession = session_factory(info={"request": request})
    register(dbsession, transaction_manager=transaction_manager)
    return dbsession
