"""Database session management."""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

engine = None
Session = None


def init_db(settings, project_path: Path) -> None:
    """Initialize database for a project."""
    global engine, Session
    db_path = project_path / "recon.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Session = scoped_session(sessionmaker(bind=engine))
    from recon.data.models import Base
    Base.metadata.create_all(engine)


def get_session():
    """Get a new database session."""
    if Session is None:
        raise RuntimeError("Database not initialized. Call init_db first.")
    return Session()
