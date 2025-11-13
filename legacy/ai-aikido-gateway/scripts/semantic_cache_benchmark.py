#!/usr/bin/env python
"""
Semantic cache benchmark harness.

Runs a small workload against the FAISS-backed semantic cache using either:
- On-premise sentence-transformers (default, $0 cost)
- OpenAI embeddings (requires OPENAI_API_KEY)

Useful for collecting latency and hit-rate numbers before adjusting
similarity thresholds/TTLs for production deployment.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import statistics
import sys
import time
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.cache.semantic import SemanticCacheBackend
from src.core.embeddings import OpenAIEmbeddingProvider, SentenceTransformersProvider


DEFAULT_PROMPTS = [
    "Summarize the latest gateway request in one sentence.",
    "Explain how the semantic cache reduces cost for repeated prompts.",
    "Provide a list of next steps for Phase 6 intent modeling.",
    "Describe the normalization pipeline that runs before caching.",
    "Give me a friendly greeting suitable for a customer support reply."
]


async def run_benchmark(
    prompts: List[str],
    iterations: int,
    similarity_threshold: float,
    max_entries: int,
    ttl_seconds: int,
    model: str,
    provider_type: str = "openai",
    embedding_service_url: str | None = None,
) -> None:
    # Initialize the embedding provider based on type
    if provider_type == "sentence_transformers":
        if not embedding_service_url:
            embedding_service_url = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8001")
        print(f"Using on-premise embeddings: {embedding_service_url}")
        provider = SentenceTransformersProvider(service_url=embedding_service_url, model=model)
    elif provider_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI embeddings.")
        provider = OpenAIEmbeddingProvider(api_key=api_key, model=model)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")

    backend = SemanticCacheBackend(
        dimension=provider.dimension,
        similarity_threshold=similarity_threshold,
        max_entries=max_entries,
        ttl_seconds=ttl_seconds,
    )

    embed_durations: List[float] = []
    lookup_durations: List[float] = []
    semantic_hits = 0
    embedding_tokens_total = 0
    embedding_cost_total = 0.0

    for idx in range(iterations):
        prompt = prompts[idx % len(prompts)]

        # Generate embedding (counts toward "real" perf)
        started = time.perf_counter()
        embedding_result = await provider.embed(prompt)
        embedding = embedding_result.vector
        embed_durations.append(time.perf_counter() - started)
        embedding_tokens_total += embedding_result.prompt_tokens or 0
        embedding_cost_total += embedding_result.cost or 0.0

        # Alternate between storing and looking up to simulate reuse
        metadata = {"model": model}
        if idx % 2 == 0:
            await backend.set(embedding, {"id": f"resp-{idx}", "prompt": prompt}, metadata)
        else:
            lookup_started = time.perf_counter()
            hit = await backend.get(embedding, metadata)
            lookup_durations.append(time.perf_counter() - lookup_started)
            if hit:
                semantic_hits += 1

    total_lookups = len(lookup_durations)
    hit_rate = semantic_hits / total_lookups if total_lookups else 0.0

    def percentile(values: List[float], pct: float) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        index = int((pct / 100) * (len(sorted_vals) - 1))
        return sorted_vals[index]

    print("\n=== Semantic Cache Benchmark ===")
    print(f"Provider             : {provider_type}")
    print(f"Prompts used         : {len(prompts)}")
    print(f"Iterations           : {iterations}")
    print(f"Embedding model      : {provider.model_name} ({provider.dimension} dims)")
    print(f"Similarity threshold : {similarity_threshold}")
    print(f"Semantic hits        : {semantic_hits}/{total_lookups} ({hit_rate*100:.1f}%)")
    print("\nEmbedding latency (seconds)")
    print(f"  avg: {statistics.fmean(embed_durations):.3f}  p95: {percentile(embed_durations, 95):.3f}")
    if lookup_durations:
        print("\nLookup latency (seconds)")
        print(f"  avg: {statistics.fmean(lookup_durations):.3f}  p95: {percentile(lookup_durations, 95):.3f}")
    print("\nCache stats snapshot:")
    print(backend.get_stats())
    print("\nEmbedding spend snapshot:")
    print(
        f"  tokens: {embedding_tokens_total} · "
        f"cost: ${embedding_cost_total:.6f} "
        f"(avg ${ (embedding_cost_total / iterations):.6f} per embedding)"
        if iterations
        else "  tokens: 0 · cost: $0.000000"
    )

    # Cleanup
    if hasattr(provider, "close"):
        await provider.close()


def load_prompts(path: Path | None) -> List[str]:
    if path is None:
        return DEFAULT_PROMPTS
    data = path.read_text(encoding="utf-8").strip().splitlines()
    return [line for line in data if line.strip()]


async def async_main() -> None:
    parser = argparse.ArgumentParser(description="Semantic cache benchmark harness.")
    parser.add_argument("--prompts-file", type=Path, help="Path to newline-delimited prompts.")
    parser.add_argument("--iterations", type=int, default=20, help="Total benchmark iterations (default: 20).")
    parser.add_argument("--similarity-threshold", type=float, default=0.85, help="Similarity threshold to test.")
    parser.add_argument("--max-entries", type=int, default=1000, help="Semantic cache capacity.")
    parser.add_argument("--ttl-seconds", type=int, default=3600, help="Semantic cache TTL.")
    parser.add_argument(
        "--provider",
        type=str,
        default="sentence_transformers",
        choices=["openai", "sentence_transformers"],
        help="Embedding provider (default: sentence_transformers for on-premise)"
    )
    parser.add_argument(
        "--embedding-service-url",
        type=str,
        help="URL for sentence-transformers service (default: http://localhost:8001)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Embedding model to use (default: all-MiniLM-L6-v2 for on-premise, text-embedding-ada-002 for OpenAI)"
    )
    args = parser.parse_args()

    prompts = load_prompts(args.prompts_file)
    await run_benchmark(
        prompts=prompts,
        iterations=args.iterations,
        similarity_threshold=args.similarity_threshold,
        max_entries=args.max_entries,
        ttl_seconds=args.ttl_seconds,
        model=args.model,
        provider_type=args.provider,
        embedding_service_url=args.embedding_service_url,
    )


def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nBenchmark cancelled.")


if __name__ == "__main__":
    main()
