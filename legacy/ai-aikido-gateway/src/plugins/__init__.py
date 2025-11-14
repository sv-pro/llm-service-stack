"""AI Aikido Gateway plugins."""

from src.plugins.anthropic_proxy import AnthropicProxyPlugin
from src.plugins.cache import CachePlugin
from src.plugins.example import ExampleLoggerPlugin
from src.plugins.history import RequestHistoryPlugin
from src.plugins.normalization import NormalizationPlugin
from src.plugins.openai_proxy import OpenAIProxyPlugin
from src.plugins.semantic_cache import SemanticCachePlugin
from src.plugins.transparency import TransparencyPlugin

__all__ = [
    "ExampleLoggerPlugin",
    "NormalizationPlugin",
    "CachePlugin",
    "SemanticCachePlugin",
    "RequestHistoryPlugin",
    "TransparencyPlugin",
    "OpenAIProxyPlugin",
    "AnthropicProxyPlugin",
]
