"""PostgreSQL database connection with asyncpg for template storage."""

import asyncpg
import logging
from typing import Optional
from contextlib import asynccontextmanager

from .config import settings

logger = logging.getLogger(__name__)


class PostgresConnection:
    """PostgreSQL connection pool manager."""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create connection pool."""
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(
                    settings.POSTGRES_URL,
                    min_size=1,
                    max_size=10,
                    command_timeout=60
                )
                logger.info("PostgreSQL connection pool created")

                # Initialize pgvector extension
                async with self.pool.acquire() as conn:
                    await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
                    logger.info("pgvector extension initialized")

            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                raise

        return self.pool

    async def disconnect(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed")

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            yield conn

    async def init_tables(self):
        """Initialize template tables."""
        async with self.acquire() as conn:
            # Create templates table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,

                    -- Prompt templates
                    system_template TEXT NOT NULL,
                    user_template TEXT NOT NULL,

                    -- Arguments (stored as JSONB)
                    required_args JSONB DEFAULT '[]'::jsonb,
                    optional_args JSONB DEFAULT '[]'::jsonb,

                    -- Semantic matching
                    embedding vector(1536),  -- OpenAI embedding dimension
                    keywords TEXT[],

                    -- Statistics
                    usage_count INTEGER DEFAULT 0,
                    avg_cost FLOAT DEFAULT 0.0,
                    avg_latency_ms FLOAT DEFAULT 0.0,
                    success_rate FLOAT DEFAULT 1.0,

                    -- Metadata
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    created_by TEXT,
                    category TEXT,
                    tags TEXT[],

                    -- Index for semantic search
                    CONSTRAINT valid_category CHECK (category IN (
                        'code_review', 'code_generation', 'content_writing',
                        'data_analysis', 'debugging', 'api_design', 'documentation',
                        'testing', 'architecture', 'general'
                    ))
                )
            ''')

            # Create index on embedding for fast similarity search
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS templates_embedding_idx
                ON templates USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            ''')

            # Create indexes for filtering
            await conn.execute('CREATE INDEX IF NOT EXISTS templates_category_idx ON templates(category)')
            await conn.execute('CREATE INDEX IF NOT EXISTS templates_created_at_idx ON templates(created_at DESC)')
            await conn.execute('CREATE INDEX IF NOT EXISTS templates_usage_count_idx ON templates(usage_count DESC)')

            # Create template usage logs table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS template_usage (
                    id SERIAL PRIMARY KEY,
                    template_id TEXT REFERENCES templates(id) ON DELETE CASCADE,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    user_id TEXT,
                    extracted_args JSONB,
                    cost FLOAT,
                    latency_ms FLOAT,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT
                )
            ''')

            await conn.execute('CREATE INDEX IF NOT EXISTS template_usage_template_id_idx ON template_usage(template_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS template_usage_timestamp_idx ON template_usage(timestamp DESC)')

            logger.info("Template tables initialized")


# Global PostgreSQL connection instance
postgres_conn = PostgresConnection()
