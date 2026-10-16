"""
NexusAI Python Client Example
==============================
Simple Python client to interact with the NexusAI Gateway.
"""

import requests
import time
from typing import Dict, Any

class NexusAIClient:
    """Simple client for NexusAI Gateway."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "sk-nexus-dev-demo-key"):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
    
    def infer(self, prompt: str, provider: str = "mock", **kwargs) -> Dict[str, Any]:
        """
        Execute inference with caching.
        
        Args:
            prompt: The question or prompt
            provider: LLM provider (mock, huggingface, openai)
            **kwargs: Additional parameters (model, temperature, max_tokens, etc.)
        
        Returns:
            Response dictionary with answer and metadata
        """
        data = {
            "prompt": prompt,
            "provider": provider,
            **kwargs
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/infer",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        response = requests.get(
            f"{self.base_url}/api/v1/cache/stats",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear all cached entries."""
        response = requests.delete(
            f"{self.base_url}/api/v1/cache/clear",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check gateway health."""
        response = requests.get(f"{self.base_url}/api/v1/health")
        response.raise_for_status()
        return response.json()


def main():
    """Example usage."""
    
    # Initialize client
    client = NexusAIClient()
    
    print("🚀 NexusAI Python Client Example\n")
    
    # Health check
    print("1. Health Check")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Backend: {health['backend_storage']}\n")
    
    # First query (MISS)
    print("2. First Query (Cache MISS expected)")
    query1 = "What is the capital of France?"
    result1 = client.infer(query1)
    print(f"   Query: {query1}")
    print(f"   Cache Hit: {result1['cache_hit']}")
    print(f"   Latency: {result1['latency_ms']}ms")
    print(f"   Response: {result1['response'][:80]}...\n")
    
    # Wait a moment
    time.sleep(1)
    
    # Similar query (HIT)
    print("3. Similar Query (Cache HIT expected)")
    query2 = "What's France's capital city?"
    result2 = client.infer(query2)
    print(f"   Query: {query2}")
    print(f"   Cache Hit: {result2['cache_hit']}")
    print(f"   Similarity: {result2.get('similarity_score', 0) * 100:.1f}%")
    print(f"   Latency: {result2['latency_ms']}ms")
    print(f"   Speedup: {result1['latency_ms'] / result2['latency_ms']:.1f}x faster!\n")
    
    # Volatile query (BYPASS)
    print("4. Volatile Query (Bypass expected)")
    query3 = "What is the weather today in Tokyo?"
    result3 = client.infer(query3)
    print(f"   Query: {query3}")
    print(f"   Bypassed: {result3['bypassed_due_to_volatility']}")
    print(f"   Latency: {result3['latency_ms']}ms\n")
    
    # Cache stats
    print("5. Cache Statistics")
    stats = client.get_cache_stats()
    print(f"   Total Entries: {stats['total_entries']}")
    print(f"   Cache Hits: {stats['hits']}")
    print(f"   Cache Misses: {stats['misses']}")
    print(f"   Hit Ratio: {stats['hit_ratio']}%\n")
    
    print("✅ Example completed successfully!")


if __name__ == "__main__":
    main()
