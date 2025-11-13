"""
Request History Plugin - Stores all requests and responses for analysis

This plugin captures every request/response and stores it in SQLite for:
- Request history viewing
- Cost analytics
- Pattern analysis
- Cache effectiveness tracking
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from src.core.plugin import BasePlugin
from src.core.context import RequestContext
from src.core.costs import calculate_completion_cost


class RequestHistoryPlugin(BasePlugin):
    """Plugin that stores all requests and responses in SQLite database."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        priority: int = 50,
    ):
        super().__init__(name, config, enabled, priority)
        self.db_path = Path(self.config.get("db_path", "./data/history.db"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
    
    async def on_startup(self) -> None:
        """Create database and tables on startup."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Create requests table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE NOT NULL,
                timestamp DATETIME NOT NULL,
                
                -- Request data
                model TEXT NOT NULL,
                messages TEXT NOT NULL,  -- JSON array
                temperature REAL,
                max_tokens INTEGER,
                
                -- Response data
                response_text TEXT,
                finish_reason TEXT,
                
                -- Metrics
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                latency_ms INTEGER,
                
                -- Cost tracking (will be calculated by CostMonitorPlugin later)
                estimated_cost REAL DEFAULT 0.0,
                embedding_tokens INTEGER DEFAULT 0,
                embedding_cost REAL DEFAULT 0.0,
                total_cost REAL DEFAULT 0.0,
                
                -- Cache info
                cached BOOLEAN DEFAULT 0,
                cache_key TEXT,
                
                -- Metadata (JSON for extensibility)
                metadata TEXT,  -- JSON object with app_label, user_label, etc.
                
                -- Error tracking
                error TEXT,
                error_type TEXT,
                avoided_cost REAL DEFAULT 0.0,
                cache_type TEXT DEFAULT 'api',
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for common queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_requests_timestamp 
            ON requests(timestamp DESC)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_requests_model 
            ON requests(model)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_requests_cached 
            ON requests(cached)
        """)
        
        self._ensure_column("avoided_cost", "REAL DEFAULT 0.0")
        self._ensure_column("cache_type", "TEXT DEFAULT 'api'")
        self._ensure_column("embedding_tokens", "INTEGER DEFAULT 0")
        self._ensure_column("embedding_cost", "REAL DEFAULT 0.0")
        self._ensure_column("total_cost", "REAL DEFAULT 0.0")
        self._ensure_re_re_tables()

        self.conn.commit()
        self.logger.info(f"Request history database initialized at {self.db_path}")
    
    async def on_shutdown(self) -> None:
        """Close database connection on shutdown."""
        if self.conn:
            self.conn.close()
            self.logger.info("Request history database connection closed")
    
    async def after_response(self, ctx: RequestContext) -> None:
        """Store request/response data after processing."""
        if not self.conn:
            self.logger.warning("Database not initialized, skipping history storage")
            return
        
        try:
            # Generate unique request ID
            request_id = self._generate_request_id(ctx)
            
            # Extract data from context
            request_data = ctx.request
            response_data = ctx.response if ctx.response else {}
            metadata = ctx.metadata
            
            # Extract messages (handle both dict and Pydantic model)
            messages = []
            if hasattr(request_data, "messages"):
                # Pydantic model
                messages = [
                    {"role": msg.role, "content": msg.content}
                    for msg in request_data.messages
                ]
            elif isinstance(request_data, dict) and "messages" in request_data:
                # Dict
                messages = request_data["messages"]
            
            # Extract response text
            response_text = None
            finish_reason = None
            if response_data and "choices" in response_data:
                if len(response_data["choices"]) > 0:
                    choice = response_data["choices"][0]
                    if "message" in choice:
                        response_text = choice["message"].get("content", "")
                    finish_reason = choice.get("finish_reason")
            
            # Extract token usage
            prompt_tokens = None
            completion_tokens = None
            total_tokens = None
            if response_data and "usage" in response_data:
                usage = response_data["usage"]
                prompt_tokens = usage.get("prompt_tokens")
                completion_tokens = usage.get("completion_tokens")
                total_tokens = usage.get("total_tokens")
            
            # Get model - handle both Pydantic models and dicts
            if isinstance(request_data, dict):
                model = request_data.get("model")
                temperature = request_data.get("temperature")
                max_tokens = request_data.get("max_tokens")
            else:
                model = getattr(request_data, "model", None)
                temperature = getattr(request_data, "temperature", None)
                max_tokens = getattr(request_data, "max_tokens", None)
            
            # Check if cached
            cached = metadata.get("cached", False)
            cache_key = metadata.get("cache_key")
            
            # Get latency
            latency_ms = metadata.get("latency_ms")

            # Get error info
            error = metadata.get("error")
            error_type = metadata.get("error_type")

            cost_summary = ctx.metadata.get("cost_summary", {})
            estimated_cost = cost_summary.get("completion_cost", 0.0)
            embedding_tokens = cost_summary.get("embedding_tokens", 0)
            embedding_cost = cost_summary.get("embedding_cost", 0.0)
            total_cost = cost_summary.get("total_cost", estimated_cost + embedding_cost)

            avoided_cost = 0.0
            if model and prompt_tokens and completion_tokens and cached:
                avoided_cost = calculate_completion_cost(model, prompt_tokens, completion_tokens)
                self.logger.debug(
                    "Avoided completion cost for %s: $%.6f", model, avoided_cost
                )

            cache_type = metadata.get("cache_type")
            if not cache_type:
                cache_type = "verbatim" if cached else "api"

            # Store custom metadata (app labels, user labels, etc.)
            custom_metadata = {
                "app_label": metadata.get("app_label"),
                "user_label": metadata.get("user_label"),
                "environment": metadata.get("environment"),
                "source_ip": metadata.get("source_ip"),
            }

            # Insert into database
            self.conn.execute("""
                INSERT INTO requests (
                    request_id, timestamp, model, messages, temperature, max_tokens,
                    response_text, finish_reason,
                    prompt_tokens, completion_tokens, total_tokens, latency_ms,
                    estimated_cost, avoided_cost, cached, cache_key, metadata, error, error_type,
                    cache_type, embedding_tokens, embedding_cost, total_cost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_id,
                datetime.now(timezone.utc).isoformat(),
                model,
                json.dumps(messages),
                temperature,
                max_tokens,
                response_text,
                finish_reason,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                latency_ms,
                estimated_cost,
                avoided_cost,
                1 if cached else 0,
                cache_key,
                json.dumps(custom_metadata),
                error,
                error_type,
                cache_type,
                embedding_tokens,
                embedding_cost,
                total_cost,
            ))
            
            self.conn.commit()
            self.logger.debug(f"Stored request {request_id} in history")
            
        except Exception as e:
            self.logger.error(f"Failed to store request in history: {e}", exc_info=True)
    
    def _generate_request_id(self, ctx: RequestContext) -> str:
        """Generate a unique request ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        content = str(ctx.request)
        hash_input = f"{timestamp}:{content}".encode()
        return hashlib.sha256(hash_input).hexdigest()[:16]
    
    def get_requests(
        self,
        limit: int = 50,
        offset: int = 0,
        model: Optional[str] = None,
        cached: Optional[bool] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search: Optional[str] = None,
        cache_type: Optional[str] = None,
    ) -> list:
        """Query requests with filters and pagination."""
        if not self.conn:
            return []
        
        query = "SELECT * FROM requests WHERE 1=1"
        params = []
        
        if model:
            query += " AND model = ?"
            params.append(model)
        
        if cached is not None:
            query += " AND cached = ?"
            params.append(1 if cached else 0)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        if search:
            query += " AND (messages LIKE ? OR response_text LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])

        if cache_type:
            query += " AND cache_type = ?"
            params.append(cache_type)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_request_by_id(self, request_id: str) -> Optional[Dict]:
        """Get a single request by ID."""
        if not self.conn:
            return None
        
        cursor = self.conn.execute(
            "SELECT * FROM requests WHERE request_id = ?",
            (request_id,)
        )
        row = cursor.fetchone()
        
        return dict(row) if row else None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get summary statistics including cost aggregations."""
        if not self.conn:
            return {}

        # Get overall statistics
        cursor = self.conn.execute("""
            SELECT
                COUNT(*) as total_requests,
                SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as cached_requests,
                AVG(latency_ms) as avg_latency_ms,
                SUM(total_tokens) as total_tokens,
                COUNT(DISTINCT model) as unique_models,
                SUM(estimated_cost) as total_cost,
                SUM(embedding_cost) as embedding_cost_total,
                SUM(total_cost) as net_cost_total,
                SUM(avoided_cost) as avoided_cost_total,
                AVG(estimated_cost) as avg_cost_per_request
            FROM requests
        """)

        row = cursor.fetchone()
        stats = dict(row) if row else {}

        total_requests = stats.get("total_requests") or 0
        cached_requests = stats.get("cached_requests") or 0
        avoided_cost_total = stats.get("avoided_cost_total") or 0.0
        embedding_cost_total = stats.get("embedding_cost_total") or 0.0
        net_cost_total = stats.get("net_cost_total") or 0.0

        hit_rate = (cached_requests / total_requests) if total_requests else 0.0
        stats["cache_hit_rate"] = hit_rate
        stats["avoided_cost_total"] = avoided_cost_total
        stats["embedding_cost_total"] = embedding_cost_total
        stats["net_cost_total"] = net_cost_total
        stats["non_cached_requests"] = total_requests - cached_requests

        stats["cache_summary"] = {
            "cached_requests": cached_requests,
            "non_cached_requests": total_requests - cached_requests,
            "hit_rate": hit_rate,
            "avoided_cost_total": avoided_cost_total,
            "embedding_cost_total": embedding_cost_total,
            "net_cost_total": net_cost_total,
        }

        # Get cost breakdown by model
        cursor = self.conn.execute("""
            SELECT
                model,
                COUNT(*) as request_count,
                SUM(estimated_cost) as total_cost,
                AVG(estimated_cost) as avg_cost
            FROM requests
            GROUP BY model
            ORDER BY total_cost DESC
        """)

        cost_by_model = [dict(row) for row in cursor.fetchall()]
        stats["cost_by_model"] = cost_by_model

        return stats

    def _ensure_column(self, column_name: str, column_def: str) -> None:
        """Ensure a column exists on the requests table."""
        if not self.conn:
            return

        cursor = self.conn.execute("PRAGMA table_info(requests)")
        columns = {row["name"] for row in cursor.fetchall()}

        if column_name not in columns:
            self.logger.info("Adding missing column '%s' to requests table", column_name)
            self.conn.execute(f"ALTER TABLE requests ADD COLUMN {column_name} {column_def}")
            self.conn.commit()

    def _ensure_re_re_tables(self) -> None:
        """Provision auxiliary tables for Re^Re telemetry snapshots."""

        if not self.conn:
            return

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS re_re_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                thread_id TEXT,
                intent TEXT,
                phase TEXT,
                status TEXT,
                step_index INTEGER,
                node TEXT,
                tool TEXT,
                budget_used REAL,
                remaining_budget REAL,
                quality_score REAL,
                reasoning_tokens INTEGER,
                state_snapshot TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_re_re_events_thread
            ON re_re_events(thread_id, created_at DESC)
            """
        )
        self.conn.commit()

        cursor = self.conn.execute("PRAGMA table_info(re_re_events)")
        columns = {row["name"] for row in cursor.fetchall()}
        if "state_snapshot" not in columns:
            self.logger.info("Adding state_snapshot column to re_re_events table")
            self.conn.execute("ALTER TABLE re_re_events ADD COLUMN state_snapshot TEXT")
            self.conn.commit()
