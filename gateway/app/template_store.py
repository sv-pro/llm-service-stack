"""Template storage and retrieval with semantic search."""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from .pg_database import postgres_conn
from .cache import generate_embedding

logger = logging.getLogger(__name__)


class Template:
    """Template data model."""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        system_template: str,
        user_template: str,
        required_args: List[Dict[str, Any]],
        optional_args: List[Dict[str, Any]],
        embedding: Optional[List[float]] = None,
        keywords: Optional[List[str]] = None,
        usage_count: int = 0,
        avg_cost: float = 0.0,
        avg_latency_ms: float = 0.0,
        success_rate: float = 1.0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        category: str = "general",
        tags: Optional[List[str]] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.system_template = system_template
        self.user_template = user_template
        self.required_args = required_args or []
        self.optional_args = optional_args or []
        self.embedding = embedding
        self.keywords = keywords or []
        self.usage_count = usage_count
        self.avg_cost = avg_cost
        self.avg_latency_ms = avg_latency_ms
        self.success_rate = success_rate
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.created_by = created_by
        self.category = category
        self.tags = tags or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_template": self.system_template,
            "user_template": self.user_template,
            "required_args": self.required_args,
            "optional_args": self.optional_args,
            "keywords": self.keywords,
            "usage_count": self.usage_count,
            "avg_cost": self.avg_cost,
            "avg_latency_ms": self.avg_latency_ms,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "category": self.category,
            "tags": self.tags,
        }

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "Template":
        """Create Template from database row."""
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            system_template=row["system_template"],
            user_template=row["user_template"],
            required_args=row.get("required_args", []),
            optional_args=row.get("optional_args", []),
            embedding=row.get("embedding"),
            keywords=row.get("keywords", []),
            usage_count=row.get("usage_count", 0),
            avg_cost=row.get("avg_cost", 0.0),
            avg_latency_ms=row.get("avg_latency_ms", 0.0),
            success_rate=row.get("success_rate", 1.0),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            created_by=row.get("created_by"),
            category=row.get("category", "general"),
            tags=row.get("tags", []),
        )


class TemplateStore:
    """Storage and retrieval for prompt templates with semantic search."""

    async def save(self, template: Template) -> str:
        """Save template with precomputed embedding."""
        try:
            # Generate embedding if not provided
            if not template.embedding:
                text = f"{template.name} {template.description} {template.system_template} {template.user_template}"
                template.embedding = await generate_embedding(text)

            async with postgres_conn.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO templates (
                        id, name, description, system_template, user_template,
                        required_args, optional_args, embedding, keywords,
                        usage_count, avg_cost, avg_latency_ms, success_rate,
                        created_at, updated_at, created_by, category, tags
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        system_template = EXCLUDED.system_template,
                        user_template = EXCLUDED.user_template,
                        required_args = EXCLUDED.required_args,
                        optional_args = EXCLUDED.optional_args,
                        embedding = EXCLUDED.embedding,
                        keywords = EXCLUDED.keywords,
                        updated_at = NOW(),
                        category = EXCLUDED.category,
                        tags = EXCLUDED.tags
                    """,
                    template.id,
                    template.name,
                    template.description,
                    template.system_template,
                    template.user_template,
                    json.dumps(template.required_args),
                    json.dumps(template.optional_args),
                    template.embedding,
                    template.keywords,
                    template.usage_count,
                    template.avg_cost,
                    template.avg_latency_ms,
                    template.success_rate,
                    template.created_at,
                    template.updated_at,
                    template.created_by,
                    template.category,
                    template.tags,
                )

                logger.info(f"Template saved: {template.id} - {template.name}")
                return template.id

        except Exception as e:
            logger.error(f"Error saving template: {e}")
            raise

    async def get(self, template_id: str) -> Optional[Template]:
        """Get template by ID."""
        try:
            async with postgres_conn.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM templates WHERE id = $1", template_id
                )

                if row:
                    return Template.from_row(dict(row))
                return None

        except Exception as e:
            logger.error(f"Error getting template: {e}")
            return None

    async def list(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "usage_count",
    ) -> List[Template]:
        """List templates with optional filtering."""
        try:
            async with postgres_conn.acquire() as conn:
                query = "SELECT * FROM templates"
                params = []

                if category:
                    query += " WHERE category = $1"
                    params.append(category)

                # Order by
                valid_order_fields = ["usage_count", "created_at", "avg_cost", "success_rate"]
                if order_by not in valid_order_fields:
                    order_by = "usage_count"

                query += f" ORDER BY {order_by} DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
                params.extend([limit, offset])

                rows = await conn.fetch(query, *params)
                return [Template.from_row(dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return []

    async def find_similar(
        self,
        embedding: List[float],
        top_k: int = 5,
        min_similarity: float = 0.7,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search using pgvector cosine similarity.
        Returns templates with similarity scores.
        """
        try:
            async with postgres_conn.acquire() as conn:
                query = """
                    SELECT *,
                           1 - (embedding <=> $1::vector) AS similarity
                    FROM templates
                    WHERE 1 - (embedding <=> $1::vector) >= $2
                """
                params = [embedding, min_similarity]

                if category:
                    query += " AND category = $3"
                    params.append(category)

                query += " ORDER BY similarity DESC LIMIT $" + str(len(params) + 1)
                params.append(top_k)

                rows = await conn.fetch(query, *params)

                results = []
                for row in rows:
                    row_dict = dict(row)
                    template = Template.from_row(row_dict)
                    results.append({
                        **template.to_dict(),
                        "similarity": float(row_dict["similarity"]),
                    })

                return results

        except Exception as e:
            logger.error(f"Error finding similar templates: {e}")
            return []

    async def delete(self, template_id: str) -> bool:
        """Delete template by ID."""
        try:
            async with postgres_conn.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM templates WHERE id = $1", template_id
                )
                return result == "DELETE 1"

        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return False

    async def increment_usage(
        self,
        template_id: str,
        cost: float,
        latency_ms: float,
        success: bool = True,
    ):
        """Increment usage count and update statistics."""
        try:
            async with postgres_conn.acquire() as conn:
                # Get current stats
                row = await conn.fetchrow(
                    "SELECT usage_count, avg_cost, avg_latency_ms, success_rate FROM templates WHERE id = $1",
                    template_id,
                )

                if not row:
                    return

                usage_count = row["usage_count"]
                avg_cost = row["avg_cost"]
                avg_latency_ms = row["avg_latency_ms"]
                success_rate = row["success_rate"]

                # Update running averages
                new_usage_count = usage_count + 1
                new_avg_cost = (avg_cost * usage_count + cost) / new_usage_count
                new_avg_latency_ms = (avg_latency_ms * usage_count + latency_ms) / new_usage_count
                new_success_rate = (success_rate * usage_count + (1 if success else 0)) / new_usage_count

                # Update template
                await conn.execute(
                    """
                    UPDATE templates
                    SET usage_count = $1,
                        avg_cost = $2,
                        avg_latency_ms = $3,
                        success_rate = $4,
                        updated_at = NOW()
                    WHERE id = $5
                    """,
                    new_usage_count,
                    new_avg_cost,
                    new_avg_latency_ms,
                    new_success_rate,
                    template_id,
                )

        except Exception as e:
            logger.error(f"Error incrementing template usage: {e}")

    async def log_usage(
        self,
        template_id: str,
        user_id: Optional[str],
        extracted_args: Dict[str, Any],
        cost: float,
        latency_ms: float,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """Log template usage for analytics."""
        try:
            async with postgres_conn.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO template_usage (
                        template_id, user_id, extracted_args, cost, latency_ms, success, error_message
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    template_id,
                    user_id,
                    json.dumps(extracted_args),
                    cost,
                    latency_ms,
                    success,
                    error_message,
                )

                # Update template statistics
                await self.increment_usage(template_id, cost, latency_ms, success)

        except Exception as e:
            logger.error(f"Error logging template usage: {e}")


# Global template store instance
template_store = TemplateStore()
