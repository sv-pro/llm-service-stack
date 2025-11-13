"""Cost tracking for LLM usage."""

from typing import Dict, Any
from datetime import datetime, timedelta


class CostTracker:
    """Track and calculate costs for LLM usage."""
    
    # Pricing per 1K tokens (approximate, should be configured)
    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-32k": {"input": 0.06, "output": 0.12},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "claude-2": {"input": 0.008, "output": 0.024},
        "claude-instant": {"input": 0.0008, "output": 0.0024},
    }
    
    def __init__(self):
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "by_model": {}
        }
    
    def calculate_cost(self, model: str, response: Dict[Any, Any]) -> float:
        """Calculate cost for a single request."""
        usage = response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        if model not in self.PRICING:
            # Default pricing if model not found
            model = "gpt-3.5-turbo"
        
        pricing = self.PRICING[model]
        cost = (
            (prompt_tokens / 1000) * pricing["input"] +
            (completion_tokens / 1000) * pricing["output"]
        )
        
        # Update stats
        self.stats["total_requests"] += 1
        self.stats["total_tokens"] += prompt_tokens + completion_tokens
        self.stats["total_cost"] += cost
        
        if model not in self.stats["by_model"]:
            self.stats["by_model"][model] = {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0
            }
        
        self.stats["by_model"][model]["requests"] += 1
        self.stats["by_model"][model]["tokens"] += prompt_tokens + completion_tokens
        self.stats["by_model"][model]["cost"] += cost
        
        return cost
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return self.stats
