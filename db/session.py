import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///output/monitor.db")


def _get_connect_args() -> dict:
    if DATABASE_URL.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


if DATABASE_URL.startswith("sqlite"):
    Path("output").mkdir(parents=True, exist_ok=True)


engine = create_engine(
    DATABASE_URL,
    connect_args=_get_connect_args(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)


def get_database_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
