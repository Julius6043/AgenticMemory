#!/usr/bin/env python3
"""
Debug script for Supabase integration issues.

This script helps identify and debug specific problems with the Supabase integration.
"""

import os
import sys
import traceback
from typing import Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.database.supabase_config import SupabaseConfigManager
from src.database.supabase_client import SupabaseMemoryClient
from src.database.supabase_memory_adapter import SupabaseAgenticMemorySystem


def test_supabase_config():
    """Test Supabase configuration."""
    print("=" * 60)
    print("Testing Supabase Configuration")
    print("=" * 60)

    try:
        # Check environment variables
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        print(
            f"SUPABASE_URL: {'✓' if url else '✗'} {url[:30]}..." if url else "✗ Not set"
        )
        print(
            f"SUPABASE_ANON_KEY: {'✓' if key else '✗'} {key[:30]}..."
            if key
            else "✗ Not set"
        )
        print(
            f"SUPABASE_SERVICE_ROLE_KEY: {'✓' if service_key else '✗'} {service_key[:30]}..."
            if service_key
            else "✗ Not set"
        )

        # Test config manager
        config = SupabaseConfigManager.get_config()
        print(f"Configuration loaded: ✓")
        print(f"URL: {config.url}")
        print(f"Key length: {len(config.key)}")

        return True

    except Exception as e:
        print(f"Configuration error: {e}")
        return False


def test_supabase_connection():
    """Test basic Supabase connection."""
    print("\n" + "=" * 60)
    print("Testing Supabase Connection")
    print("=" * 60)

    try:
        client = SupabaseMemoryClient()
        connection_ok = client.test_connection()
        print(f"Connection test: {'✓' if connection_ok else '✗'}")
        return connection_ok

    except Exception as e:
        print(f"Connection error: {e}")
        traceback.print_exc()
        return False


def test_memory_creation():
    """Test memory creation with detailed output."""
    print("\n" + "=" * 60)
    print("Testing Memory Creation")
    print("=" * 60)

    try:
        client = SupabaseMemoryClient()

        # Test simple memory creation
        memory_id = client.create_memory(
            content="This is a test memory for debugging purposes.",
            context="Debug Test",
            category="Test",
            keywords=["test", "debug"],
            tags=["debugging", "test"],
            user_id="debug_user",
        )

        print(f"Memory created: {'✓' if memory_id else '✗'}")
        if memory_id:
            print(f"Memory ID: {memory_id}")

            # Try to retrieve it
            retrieved = client.get_memory(memory_id)
            print(f"Memory retrieved: {'✓' if retrieved else '✗'}")
            if retrieved:
                print(f"Content: {retrieved.get('content', 'N/A')}")
                print(f"Embedding: {'✓' if retrieved.get('embedding') else '✗'}")

        return memory_id is not None

    except Exception as e:
        print(f"Memory creation error: {e}")
        traceback.print_exc()
        return False


def test_embedding_system():
    """Test the full memory system with embeddings."""
    print("\n" + "=" * 60)
    print("Testing Memory System with Embeddings")
    print("=" * 60)

    try:
        memory_system = SupabaseAgenticMemorySystem(user_id="debug_user")

        # Test adding a note
        memory_id = memory_system.add_note(
            content="Python is a high-level programming language known for its simplicity.",
            context="Programming Knowledge",
            category="Technology",
        )

        print(f"Memory added via system: {'✓' if memory_id else '✗'}")
        if memory_id:
            print(f"Memory ID: {memory_id}")

            # Test search
            related = memory_system.get_related_memories("Python programming", k=3)
            print(f"Related memories found: {len(related)}")

            for i, mem in enumerate(related):
                print(f"  {i+1}. {mem.content[:50]}...")
                print(f"      Embedding: {'✓' if mem.embedding else '✗'}")

        return memory_id is not None

    except Exception as e:
        print(f"Memory system error: {e}")
        traceback.print_exc()
        return False


def test_search_functions():
    """Test different search methods."""
    print("\n" + "=" * 60)
    print("Testing Search Functions")
    print("=" * 60)

    try:
        client = SupabaseMemoryClient()

        # Test text search
        text_results = client.search_memories_by_text("test", limit=5)
        print(f"Text search results: {len(text_results)}")

        # Test embedding search (with dummy embedding)
        dummy_embedding = [0.1] * 384  # Dummy 384-dimensional vector
        embedding_results = client.search_memories_by_embedding(
            dummy_embedding, limit=5
        )
        print(f"Embedding search results: {len(embedding_results)}")

        # Test hybrid search
        hybrid_results = client.hybrid_search_memories("test", dummy_embedding, limit=5)
        print(f"Hybrid search results: {len(hybrid_results)}")

        return True

    except Exception as e:
        print(f"Search functions error: {e}")
        traceback.print_exc()
        return False


def test_statistics():
    """Test statistics function."""
    print("\n" + "=" * 60)
    print("Testing Statistics Function")
    print("=" * 60)

    try:
        client = SupabaseMemoryClient()
        stats = client.get_memory_statistics()

        print(f"Statistics retrieved: {'✓' if stats else '✗'}")
        if stats:
            print(f"Total memories: {stats.get('total_memories', 'N/A')}")
            print(f"Categories: {stats.get('categories', {})}")
            print(f"Users: {stats.get('users', {})}")

        return bool(stats)

    except Exception as e:
        print(f"Statistics error: {e}")
        traceback.print_exc()
        return False


def main():
    """Main debugging function."""
    print("Supabase Integration Debug Script")
    print("=" * 60)

    tests = [
        ("Configuration", test_supabase_config),
        ("Connection", test_supabase_connection),
        ("Memory Creation", test_memory_creation),
        ("Embedding System", test_embedding_system),
        ("Search Functions", test_search_functions),
        ("Statistics", test_statistics),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"Test {test_name} crashed: {e}")
            traceback.print_exc()
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("Debug Summary")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All debug tests passed! Supabase integration should work.")
    else:
        print("❌ Some debug tests failed. Check the errors above.")

    return results


if __name__ == "__main__":
    main()
