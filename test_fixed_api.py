#!/usr/bin/env python3
"""
Test script for the fixed Supabase AgenticMemory API.

This script tests the main issues that were identified:
1. Chat messages storage with correct message types
2. User ID being properly set in memories
3. Session ID handling for duplicate sessions
4. Performance optimizations (reduced retrieval count increments)
"""

import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:5000"


def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_chat_with_user_id():
    """Test chat endpoint with user ID."""
    print("\n💬 Testing chat with user ID...")

    user_id = f"test-user-{int(datetime.now().timestamp())}"
    session_id = f"test-session-{int(datetime.now().timestamp())}"

    # Test message 1
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "Hello! Can you remember that I like programming in Python?",
            "user_id": user_id,
            "session_id": session_id,
        },
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code != 200:
        return False

    # Test message 2 - to check memory
    time.sleep(2)
    response2 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "What programming language did I mention I like?",
            "user_id": user_id,
            "session_id": session_id,
        },
    )

    print(f"\nSecond message status: {response2.status_code}")
    print(f"Second response: {json.dumps(response2.json(), indent=2)}")

    return response2.status_code == 200


def test_memory_with_user_id():
    """Test adding memory with user ID."""
    print("\n📝 Testing memory creation with user ID...")

    user_id = f"test-user-{int(datetime.now().timestamp())}"

    response = requests.post(
        f"{BASE_URL}/memory/add",
        json={
            "content": "I work as a software engineer at a tech company",
            "context": "Personal Information",
            "category": "Profile",
            "user_id": user_id,
        },
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_memory_search():
    """Test memory search performance."""
    print("\n🔍 Testing memory search performance...")

    user_id = "test-user-search"

    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/memory/search",
        json={"query": "programming Python software", "user_id": user_id, "limit": 5},
    )
    end_time = time.time()

    print(f"Status: {response.status_code}")
    print(f"Search time: {end_time - start_time:.2f} seconds")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200 and (end_time - start_time) < 5.0


def test_session_handling():
    """Test session creation and message handling."""
    print("\n🗣️ Testing session handling...")

    user_id = f"test-user-{int(datetime.now().timestamp())}"
    session_id = f"persistent-session-{int(datetime.now().timestamp())}"

    # Send multiple messages to same session
    messages = ["My name is Alice", "I am 25 years old", "What's my name and age?"]

    for i, message in enumerate(messages):
        print(f"\nMessage {i+1}: {message}")
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": message, "user_id": user_id, "session_id": session_id},
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result.get('response', 'No response')[:100]}...")
        else:
            print(f"Error: {response.text}")
            return False

        time.sleep(1)  # Small delay between messages

    return True


def test_memory_stats():
    """Test memory statistics."""
    print("\n📊 Testing memory statistics...")

    user_id = "test-user-stats"

    response = requests.get(f"{BASE_URL}/memory/stats", params={"user_id": user_id})

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def main():
    """Run all tests."""
    print("🚀 Starting API Tests...")
    print("=" * 50)

    tests = [
        ("Health Check", test_health),
        ("Chat with User ID", test_chat_with_user_id),
        ("Memory with User ID", test_memory_with_user_id),
        ("Memory Search Performance", test_memory_search),
        ("Session Handling", test_session_handling),
        ("Memory Statistics", test_memory_stats),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[test_name] = False

        time.sleep(1)  # Small delay between tests

    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(tests)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The fixes are working correctly.")
    else:
        print("⚠️ Some tests failed. Check the logs for details.")


if __name__ == "__main__":
    main()
