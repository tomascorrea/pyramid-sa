"""SQLAlchemy engine and session management for Pyramid."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from zope.sqlalchemy import register


def get_engine(settings: dict, prefix: str = "sqlalchemy."):
    return create_engine(settings[f"{prefix}url"])


def get_session_factory(engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine)


def get_tm_session(
    session_factory: sessionmaker[Session],
    transaction_manager,
    request=None,
) -> Session:
    dbsession = session_factory(info={"request": request})
    register(dbsession, transaction_manager=transaction_manager)
    return dbsession
