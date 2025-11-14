"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import duckdb
import logging
from pathlib import Path

from .config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy setup for usage logs
engine = create_engine(settings.SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def run_migrations():
    """Run database migrations using Alembic."""
    try:
        from alembic.config import Config
        from alembic import command

        # Get the gateway directory (parent of app/)
        gateway_dir = Path(__file__).resolve().parent.parent
        alembic_ini = gateway_dir / "alembic.ini"

        if not alembic_ini.exists():
            logger.warning(f"Alembic configuration not found at {alembic_ini}")
            return

        # Create Alembic configuration
        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option("script_location", str(gateway_dir / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.SQLITE_URL)

        # Run migrations to the latest version
        logger.info("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")

    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        logger.warning("Falling back to create_all()")
        # Fall back to creating all tables if migrations fail
        Base.metadata.create_all(bind=engine)


def init_db():
    """Initialize database tables."""
    # First create any missing tables
    Base.metadata.create_all(bind=engine)
    # Then run migrations to update schema
    run_migrations()


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
