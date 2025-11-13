#!/usr/bin/env python3
"""
Demo script to showcase semantic cache functionality.

This script sends similar but not identical prompts to demonstrate
how semantic cache matches semantically similar requests.
"""

import json
import time
import requests
from typing import Optional

API_URL = "http://localhost:8000/v1/chat/completions"

# ANSI color codes
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
NC = "\033[0m"  # No Color


def send_request(prompt: str, label: str) -> None:
    """Send a request and display the response with cache headers."""
    print(f"{BLUE}{label}{NC}")
    print(f'Prompt: "{prompt}"')
    print()

    try:
        response = requests.post(
            API_URL,
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 50,
            },
            timeout=30,
        )

        # Extract headers
        cache_status = response.headers.get("X-Gateway-Cache-Status", "MISS")
        cache_type = response.headers.get("X-Gateway-Cache-Type")
        cache_similarity = response.headers.get("X-Gateway-Cache-Similarity")
        latency = response.headers.get("X-Gateway-Latency-Ms")

        # Extract response content
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "N/A")

        # Display results
        print(f"{GREEN}Response:{NC} {content[:100]}...")
        print()
        print(f"📊 Cache Status: {cache_status}")

        if cache_type:
            type_icon = "🎯" if cache_type == "semantic" else "📝"
            print(f"   Cache Type: {type_icon} {cache_type}")

        if cache_similarity:
            similarity_float = float(cache_similarity)
            similarity_pct = similarity_float * 100

            # Color code based on similarity
            if similarity_float >= 0.90:
                color = GREEN
                quality = "excellent"
            elif similarity_float >= 0.80:
                color = YELLOW
                quality = "good"
            else:
                color = RED
                quality = "acceptable"

            print(
                f"   {color}Similarity: {cache_similarity} ({similarity_pct:.1f}%) - {quality} match!{NC}"
            )

        if latency:
            latency_float = float(latency)
            latency_color = GREEN if latency_float < 100 else YELLOW
            print(f"   {latency_color}Latency: {latency}ms{NC}")

    except requests.exceptions.RequestException as e:
        print(f"{RED}Error: {e}{NC}")
        print(f"{YELLOW}Is the gateway running? Start it with: uvicorn src.main:app --reload{NC}")

    print()
    print("---")
    print()


def main():
    """Run the semantic cache demo."""
    print(f"{CYAN}🚀 Semantic Cache Demo - AI Aikido Gateway{NC}")
    print("=" * 50)
    print()

    # Test 1: Initial request (will be a MISS)
    print(f"{CYAN}Step 1: Initial request (will be a MISS){NC}")
    print()
    send_request("What is the capital of France?", "📝 Request 1")
    time.sleep(1)

    # Test 2: Exact same request (verbatim cache HIT)
    print(f"{CYAN}Step 2: Exact same request (verbatim cache HIT){NC}")
    print()
    send_request("What is the capital of France?", "📝 Request 2 (identical)")
    time.sleep(1)

    # Test 3: Similar wording (semantic cache HIT expected)
    print(f"{CYAN}Step 3: Similar but different wording (semantic cache HIT){NC}")
    print()
    send_request("Tell me the capital city of France", "📝 Request 3 (similar)")
    time.sleep(1)

    # Test 4: Another variation (semantic cache HIT expected)
    print(f"{CYAN}Step 4: Another variation (semantic cache HIT){NC}")
    print()
    send_request("What's the capital of France?", "📝 Request 4 (variation)")
    time.sleep(1)

    # Test 5: Related question (may or may not hit)
    print(f"{CYAN}Step 5: Related but different question{NC}")
    print()
    send_request(
        "Which city is the capital of France?", "📝 Request 5 (related)"
    )
    time.sleep(1)

    # Test 6: Very different wording but same question (should still hit)
    print(f"{CYAN}Step 6: Very different wording{NC}")
    print()
    send_request(
        "Can you name the capital city of the French Republic?",
        "📝 Request 6 (rephrased)",
    )

    # Summary
    print()
    print(f"{GREEN}✅ Demo Complete!{NC}")
    print()
    print(f"{CYAN}💡 Key Observations:{NC}")
    print("   - Request 2: Verbatim cache hit (exact match)")
    print("   - Requests 3-6: Semantic cache hits (similar meaning)")
    print("   - Check the similarity scores to see how close each match was")
    print()
    print(f"{CYAN}📈 View detailed metrics:{NC}")
    print("   - Dashboard: http://localhost:3000/cache-analytics")
    print("   - Stats API: http://localhost:8000/v1/history/stats")
    print("   - Time-series: http://localhost:8000/v1/cache/semantic/timeseries")
    print()
    print(f"{CYAN}🔧 Adjust similarity threshold:{NC}")
    print('   curl -X POST http://localhost:8000/v1/cache/semantic/threshold \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"similarity_threshold": 0.90}\'')
    print()


if __name__ == "__main__":
    main()
