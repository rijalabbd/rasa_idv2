from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=15,
    max_overflow=25,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session to FastAPI routes.
    Automatically closes the session after the request is complete.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
