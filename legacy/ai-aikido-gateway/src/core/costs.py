"""Cost calculation helpers for completions and embeddings."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

PRICE_SCALE = 1_000_000  # costs are defined per 1M tokens

# Pricing sourced from the OpenAI pricing page as of Nov 2025
EMBEDDING_PRICING_PER_MILLION: Dict[str, float] = {
    # $0.0001 / 1K tokens
    "text-embedding-ada-002": 0.10,
    # $0.02 / 1K tokens
    "text-embedding-3-small": 20.0,
    # $0.13 / 1K tokens
    "text-embedding-3-large": 130.0,
}


def get_completion_pricing(model_id: str) -> Optional[Dict[str, float]]:
    """Look up pricing for a completion model from MODEL_REGISTRY."""
    from src.api.routes import MODEL_REGISTRY  # avoid circular import at module import

    model_info = MODEL_REGISTRY.get(model_id, {})
    pricing = model_info.get("pricing")
    if not pricing:
        return None
    return pricing


def calculate_completion_cost(
    model_id: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Calculate completion cost for a model."""
    if not prompt_tokens or not completion_tokens:
        return 0.0

    pricing = get_completion_pricing(model_id)
    if not pricing:
        return 0.0

    input_cost = (prompt_tokens / PRICE_SCALE) * pricing.get("input", 0.0)
    output_cost = (completion_tokens / PRICE_SCALE) * pricing.get("output", 0.0)
    return round(input_cost + output_cost, 6)


def calculate_embedding_cost(model_id: str, prompt_tokens: int) -> float:
    """Calculate embedding cost for a given model."""
    if not prompt_tokens:
        return 0.0

    price_per_million = EMBEDDING_PRICING_PER_MILLION.get(model_id)
    if not price_per_million:
        return 0.0

    return round((prompt_tokens / PRICE_SCALE) * price_per_million, 6)
