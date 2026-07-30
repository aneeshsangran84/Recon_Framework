from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from pathlib import Path
from recon.config.settings import Settings

engine = None
Session = None

def init_db(settings: Settings, project_path: Path) -> None:
    global engine, Session
    db_path = project_path / "recon.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Session = scoped_session(sessionmaker(bind=engine))
    from recon.data.models import Base
    Base.metadata.create_all(engine)

def get_session():
    return Session()