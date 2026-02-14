"""
Database engine and session factory.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


def get_engine(database_url: str):
    return create_engine(
        database_url,
        pool_pre_ping=True,
        echo=False,
    )


def get_session_factory(engine):
    return sessionmaker(engine, autocommit=False, autoflush=False, class_=Session)


def init_db(engine) -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
