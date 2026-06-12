"""
Database configuration and session management.
Provides connection pooling and session generators using SQLAlchemy.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecotrace.db")

# Create the engine. SQLite uses connect_args for multithreading compatibility in FastAPI.
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency generator function that yields database sessions.
    Guarantees session cleanup after requests finish.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
