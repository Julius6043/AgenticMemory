"""
Test script for debugging the AgenticMemory API.

This script tests all API endpoints and helps identify issues.
"""

import os
import sys
import json
import requests
import time
from datetime import datetime

# Add src to path
current_dir = os.path.dirname(__file__)
src_path = os.path.join(current_dir, "src")
sys.path.insert(0, src_path)
sys.path.insert(0, current_dir)

# API Configuration
API_BASE_URL = "http://localhost:5000"
TEST_USER_ID = "test_user_debug"
TEST_SESSION_ID = f"test_session_{int(time.time())}"


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)


def print_step(step, description):
    """Print a test step."""
    print(f"\n{step}. {description}")
    print("-" * 40)


def test_api_endpoint(method, endpoint, data=None, params=None):
    """Test an API endpoint and return the response."""
    url = f"{API_BASE_URL}{endpoint}"

    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            print(f"❌ Unsupported method: {method}")
            return None

        print(f"📡 {method.upper()} {endpoint}")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {json.dumps(result, indent=2)[:200]}...")
            return result
        else:
            print(f"❌ Error: {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: API server not running at {API_BASE_URL}")
        return None
    except requests.exceptions.Timeout:
        print(f"❌ Timeout: Request took too long")
        return None
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None


def test_health_check():
    """Test the health check endpoint."""
    print_step(1, "Testing Health Check")
    result = test_api_endpoint("GET", "/health")
    return result is not None and result.get("status") == "healthy"


def test_add_memory():
    """Test adding memory directly."""
    print_step(2, "Testing Add Memory")

    test_memories = [
        {
            "content": "Python is a powerful programming language for AI and data science",
            "context": "Programming Knowledge",
            "category": "Technology",
            "keywords": ["Python", "programming", "AI", "data science"],
            "tags": ["Programming", "Technology", "AI"],
            "user_id": TEST_USER_ID,
        },
        {
            "content": "Machine learning algorithms can learn patterns from data without explicit programming",
            "context": "AI Knowledge",
            "category": "AI/ML",
            "keywords": ["machine learning", "algorithms", "data", "patterns"],
            "tags": ["AI", "Machine Learning", "Technology"],
            "user_id": TEST_USER_ID,
        },
    ]

    memory_ids = []
    for i, memory_data in enumerate(test_memories):
        print(f"\n  Adding memory {i+1}...")
        result = test_api_endpoint("POST", "/memory/add", memory_data)
        if result and "memory_id" in result:
            memory_ids.append(result["memory_id"])
            print(f"  ✅ Memory ID: {result['memory_id']}")
        else:
            print(f"  ❌ Failed to add memory {i+1}")

    # Return True if at least one memory was added successfully
    return len(memory_ids) > 0


def test_search_memories():
    """Test memory search functionality."""
    print_step(3, "Testing Memory Search")

    search_queries = [
        "Python programming language",
        "machine learning algorithms",
        "artificial intelligence",
    ]

    all_successful = True
    for query in search_queries:
        print(f"\n  Searching for: '{query}'")
        result = test_api_endpoint(
            "POST",
            "/memory/search",
            {"query": query, "user_id": TEST_USER_ID, "limit": 3},
        )

        if result and "results" in result:
            print(f"  ✅ Found {len(result['results'])} results")
        else:
            print(f"  ❌ Search failed")
            all_successful = False

    return all_successful


def test_chat_functionality():
    """Test the chat endpoint."""
    print_step(4, "Testing Chat Functionality")

    chat_messages = [
        "Hello! What do you know about Python programming?",
        "Can you tell me about machine learning algorithms?",
        "How are Python and machine learning related?",
    ]

    all_successful = True
    for i, message in enumerate(chat_messages):
        print(f"\n  Chat message {i+1}: '{message}'")
        result = test_api_endpoint(
            "POST",
            "/chat",
            {
                "message": message,
                "user_id": TEST_USER_ID,
                "session_id": TEST_SESSION_ID,
            },
        )

        if result and "response" in result and not result.get("error"):
            print(f"  ✅ Response: {result['response'][:100]}...")
            print(f"  📊 Related memories: {result.get('related_memories_count', 0)}")
        else:
            print(f"  ❌ Chat failed")
            all_successful = False

        # Small delay between messages
        time.sleep(1)

    return all_successful


def test_session_history():
    """Test session history retrieval."""
    print_step(5, "Testing Session History")

    result = test_api_endpoint("GET", f"/session/{TEST_SESSION_ID}/history")

    if result and "messages" in result:
        print(f"  ✅ Found {len(result['messages'])} messages in session")
        return True
    else:
        print(f"  ❌ Failed to get session history")
        return False


def test_memory_stats():
    """Test memory statistics."""
    print_step(6, "Testing Memory Statistics")

    result = test_api_endpoint("GET", "/memory/stats", params={"user_id": TEST_USER_ID})

    if result and "total_memories" in result:
        print(f"  ✅ Total memories: {result['total_memories']}")
        print(f"  📊 Categories: {result.get('categories', {})}")
        return True
    else:
        print(f"  ❌ Failed to get memory statistics")
        return False


def run_comprehensive_api_test():
    """Run comprehensive API testing."""
    print_header("AgenticMemory API Debug Test")

    print("🚀 Starting comprehensive API testing...")
    print(f"📍 API Base URL: {API_BASE_URL}")
    print(f"👤 Test User ID: {TEST_USER_ID}")
    print(f"💬 Test Session ID: {TEST_SESSION_ID}")

    # Check environment variables
    print("\n🔍 Environment Check:")
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "OPENAI_API_KEY"]
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            if "KEY" in var:
                print(f"  ✅ {var}: {'*' * 20}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: NOT SET")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n❌ Missing environment variables: {missing_vars}")
        print("Please set these before running the API server.")
        return

    # Test sequence
    tests = [
        test_health_check,
        test_add_memory,
        test_search_memories,
        test_chat_functionality,
        test_session_history,
        test_memory_stats,
    ]

    results = {}
    for test_func in tests:
        try:
            result = test_func()
            results[test_func.__name__] = bool(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            results[test_func.__name__] = False

    # Summary
    print_header("Test Summary")

    passed = sum(1 for success in results.values() if success)
    total = len(results)

    print(f"📊 Test Results: {passed}/{total} passed")

    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")

    if passed == total:
        print("\n🎉 All tests passed! API is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the logs above for details.")

    print("\nTesting completed.")


if __name__ == "__main__":
    run_comprehensive_api_test()
