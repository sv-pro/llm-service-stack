"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import duckdb

from .config import settings

# SQLAlchemy setup for usage logs
engine = create_engine(settings.SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DuckDBConnection:
    """DuckDB connection for analytics queries."""
    
    def __init__(self):
        self.conn = None
    
    def connect(self):
        """Create DuckDB connection."""
        if not self.conn:
            self.conn = duckdb.connect(settings.DATABASE_URL.replace("duckdb:///", ""))
        return self.conn
    
    def execute(self, query: str):
        """Execute query and return results."""
        conn = self.connect()
        return conn.execute(query).fetchall()


duckdb_conn = DuckDBConnection()
