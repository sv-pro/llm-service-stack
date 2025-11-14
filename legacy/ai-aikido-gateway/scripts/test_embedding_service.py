"""Test script for the embedding service prototype."""

import asyncio
import subprocess
import time
import sys

import requests


def wait_for_service(url: str, timeout: int = 30) -> bool:
    """Wait for service to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    return False


def test_embedding_service():
    """Test the embedding service."""
    print("Starting embedding service test...")

    # Start the service in background
    print("\n1. Starting embedding service...")
    process = subprocess.Popen(
        [sys.executable, "src/services/embeddings/server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Wait for service to be ready
        print("2. Waiting for service to be ready...")
        if not wait_for_service("http://localhost:8001/health", timeout=60):
            print("❌ Service failed to start within timeout")
            return False

        print("✓ Service started successfully")

        # Test health endpoint
        print("\n3. Testing health endpoint...")
        response = requests.get("http://localhost:8001/health")
        health = response.json()
        print(f"   Status: {health['status']}")
        print(f"   Model loaded: {health['model_loaded']}")
        print(f"   Model name: {health['model_name']}")

        if not health['model_loaded']:
            print("❌ Model not loaded")
            return False
        print("✓ Health check passed")

        # Test embedding endpoint
        print("\n4. Testing embedding generation...")
        test_text = "This is a test sentence for semantic similarity."
        response = requests.post(
            "http://localhost:8001/embed",
            json={"text": test_text, "model": "all-MiniLM-L6-v2"}
        )

        if response.status_code != 200:
            print(f"❌ Embedding request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        result = response.json()
        print(f"   Dimensions: {result['dimensions']}")
        print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
        print(f"   Vector sample: {result['embedding'][:5]}...")

        if result['dimensions'] != 384:  # all-MiniLM-L6-v2 produces 384-dim vectors
            print(f"❌ Unexpected dimensions: {result['dimensions']}")
            return False
        print("✓ Embedding generation successful")

        # Test multiple embeddings for consistency
        print("\n5. Testing consistency...")
        response2 = requests.post(
            "http://localhost:8001/embed",
            json={"text": test_text, "model": "all-MiniLM-L6-v2"}
        )
        result2 = response2.json()

        # Embeddings should be identical for same input
        diff = sum(abs(a - b) for a, b in zip(result['embedding'], result2['embedding']))
        if diff > 0.0001:
            print(f"❌ Embeddings not consistent: diff={diff}")
            return False
        print("✓ Embeddings are consistent")

        print("\n" + "="*50)
        print("✓ All tests passed!")
        print("="*50)
        return True

    finally:
        # Cleanup
        print("\n6. Shutting down service...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("✓ Service stopped")


if __name__ == "__main__":
    try:
        success = test_embedding_service()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
