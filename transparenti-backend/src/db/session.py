from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from src.core.config import settings

url = make_url(settings.database_url)
if url.get_backend_name() == "sqlite" and url.database and url.database != ":memory:":
    Path(url.database).resolve().parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(url, connect_args={"check_same_thread": False} if url.get_backend_name() == "sqlite" else {})

if url.get_backend_name() == "sqlite":
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
