#!/usr/bin/env python3
"""
Test the search functionality specifically.
"""

import requests
import json


def test_search_function():
    base_url = "http://localhost:5000"

    # Test memory search with different scenarios
    test_cases = [
        {
            "name": "Valid search query",
            "data": {
                "query": "Python programming",
                "user_id": "test-search-user",
                "limit": 5,
            },
            "should_succeed": True,
        },
        {
            "name": "Empty query",
            "data": {"query": "", "user_id": "test-search-user", "limit": 5},
            "should_succeed": False,
        },
        {
            "name": "Only whitespace query",
            "data": {"query": "   ", "user_id": "test-search-user", "limit": 5},
            "should_succeed": False,
        },
        {"name": "No data sent", "data": None, "should_succeed": False},
        {
            "name": "Missing query field",
            "data": {"user_id": "test-search-user", "limit": 5},
            "should_succeed": False,
        },
    ]

    print("🔍 Testing Search Functionality")
    print("=" * 50)

    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")

        try:
            if test_case["data"] is None:
                # Test with no data
                response = requests.post(f"{base_url}/memory/search")
            else:
                response = requests.post(
                    f"{base_url}/memory/search",
                    json=test_case["data"],
                    headers={"Content-Type": "application/json"},
                )

            print(f"Status: {response.status_code}")

            if test_case["should_succeed"]:
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ SUCCESS - Found {result.get('count', 0)} memories")
                    if result.get("results"):
                        print(
                            f"   First result: {result['results'][0]['content'][:50]}..."
                        )
                else:
                    print(f"❌ FAILED - Expected 200, got {response.status_code}")
                    print(f"   Response: {response.text}")
            else:
                if response.status_code == 400:
                    result = response.json()
                    print(
                        f"✅ CORRECTLY REJECTED - {result.get('error', 'Bad request')}"
                    )
                else:
                    print(f"❌ UNEXPECTED - Expected 400, got {response.status_code}")
                    print(f"   Response: {response.text}")

        except Exception as e:
            print(f"❌ ERROR: {e}")


if __name__ == "__main__":
    test_search_function()
