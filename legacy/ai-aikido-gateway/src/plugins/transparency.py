"""
Transparency Plugin

Provides optional transparency headers showing what normalizations
the gateway applied to requests. Useful for developers debugging
integration issues or understanding gateway behavior.

When enabled, adds response headers:
- X-Gateway-Normalizations: List of parameter changes made
- X-Gateway-Original-Model: The model requested by client
- X-Gateway-Latency-Ms: Request processing time
"""

import logging
from typing import Any, Dict, Optional
from src.core.plugin import BasePlugin
from src.core.context import RequestContext

logger = logging.getLogger(__name__)


class TransparencyPlugin(BasePlugin):
    """
    Plugin that adds transparency headers to responses.
    
    Configuration:
        enabled: bool - Whether to add transparency headers (default: False)
        show_normalizations: bool - Show parameter normalizations (default: True)
        show_model: bool - Show original model (default: True)
        show_latency: bool - Show request latency (default: True)
        show_cache_status: bool - Show cache hit/miss status (default: True)
        custom_prefix: str - Custom header prefix (default: "X-Gateway")
    
    Example config:
        transparency:
          enabled: true
          show_normalizations: true
          show_model: true
          show_latency: true
          show_cache_status: true
    """
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        enabled: bool = True,
        priority: int = 100
    ):
        super().__init__(name, config, enabled, priority)
        
        # Configuration options
        self.show_normalizations = config.get("show_normalizations", True)
        self.show_model = config.get("show_model", True)
        self.show_latency = config.get("show_latency", True)
        self.show_cache_status = config.get("show_cache_status", True)
        self.show_retry_summary = config.get("show_retry_summary", True)
        self.custom_prefix = config.get("custom_prefix", "X-Gateway")
        
        logger.info(
            f"Transparency plugin initialized: "
            f"normalizations={self.show_normalizations}, "
            f"model={self.show_model}, "
            f"latency={self.show_latency}, "
            f"cache={self.show_cache_status}"
        )
    
    async def on_startup(self):
        """Called when the plugin starts"""
        logger.info(f"Plugin '{self.name}' starting up")
        logger.info("Transparency headers will be added to all responses")
    
    async def on_shutdown(self):
        """Called when the plugin shuts down"""
        logger.info(f"Plugin '{self.name}' shutting down")
    def _format_retry_summary(self, summaries: list[dict[str, Any]]) -> str:
        parts = []
        for item in summaries:
            provider = item.get("provider", "?")
            model = item.get("model", "?")
            attempts = item.get("attempts", 0)
            failures = item.get("failures", 0)
            status = "success" if item.get("successful", False) else "error"
            suffix = "fallback" if item.get("is_fallback") else "primary"
            segment = f"{provider}:{model} attempts={attempts} failures={failures} {suffix} {status}"
            key_label = item.get("key_label")
            if key_label:
                segment += f" key={key_label}"
            parts.append(segment.strip())
        return "; ".join(parts)

    def _build_headers(self, ctx: RequestContext) -> Dict[str, str]:
        headers = {}
        
        # Add normalization information
        if self.show_normalizations and "normalizations" in ctx.metadata:
            normalizations = ctx.metadata["normalizations"]
            if normalizations:
                headers[f"{self.custom_prefix}-Normalizations"] = "; ".join(normalizations)
        
        # Add original model information
        if self.show_model and "model" in ctx.metadata:
            headers[f"{self.custom_prefix}-Original-Model"] = ctx.metadata["model"]
        
        # Add latency information
        if self.show_latency and "latency_ms" in ctx.metadata:
            latency = ctx.metadata["latency_ms"]
            headers[f"{self.custom_prefix}-Latency-Ms"] = f"{latency:.2f}"
        
        # Add cache status
        if self.show_cache_status:
            if ctx.metadata.get("cache_hit"):
                headers[f"{self.custom_prefix}-Cache-Status"] = "HIT"

                # Add cache type (verbatim vs semantic)
                cache_type = ctx.metadata.get("cache_type", "verbatim")
                headers[f"{self.custom_prefix}-Cache-Type"] = cache_type

                # Add semantic similarity score if semantic cache hit
                if cache_type == "semantic" and "similarity_score" in ctx.metadata:
                    similarity = ctx.metadata["similarity_score"]
                    headers[f"{self.custom_prefix}-Cache-Similarity"] = f"{similarity:.3f}"
            elif "cache_miss" in ctx.metadata:
                headers[f"{self.custom_prefix}-Cache-Status"] = "MISS"

        cache_type_overall = ctx.metadata.get("cache_type")
        if cache_type_overall:
            headers[f"{self.custom_prefix}-Cache-Type"] = cache_type_overall

        if self.show_retry_summary and ctx.metadata.get("retry_summary"):
            formatted = self._format_retry_summary(ctx.metadata["retry_summary"])
            if formatted:
                headers[f"{self.custom_prefix}-Retries"] = formatted

        if headers:
            exposed = {
                key
                for key in headers.keys()
                if key.lower() != "access-control-expose-headers"
            }
            existing = headers.get("Access-Control-Expose-Headers")
            if existing:
                exposed.update(
                    h.strip()
                    for h in existing.split(",")
                    if h.strip()
                )
            if exposed:
                headers["Access-Control-Expose-Headers"] = ", ".join(sorted(exposed))

        return headers

    async def after_response(self, ctx: RequestContext) -> None:
        """
        Add transparency headers to the response context.
        
        Headers are stored in ctx.metadata['transparency_headers'] and
        will be added to the HTTP response by the route handler.
        """
        if not ctx.response:
            return

        headers = self._build_headers(ctx)
        
        # Store headers in context for route handler to use
        if headers:
            ctx.metadata["transparency_headers"] = headers
            logger.debug(f"Added transparency headers: {headers}")

    async def on_error(self, ctx: RequestContext, error: Exception) -> Optional[Dict[str, Any]]:
        headers = self._build_headers(ctx)
        if headers:
            ctx.metadata["transparency_headers"] = headers
            logger.debug("Added transparency headers on error: %s", headers)
        return await super().on_error(ctx, error)
