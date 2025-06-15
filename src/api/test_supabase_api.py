#!/usr/bin/env python3
"""
Test script for the Supabase-backed Flask API.

This script tests all the endpoints and functionalities of the chat API
with the Supabase backend to ensure proper integration.
"""

import json
import requests
import time
import uuid
from typing import Dict, Any, Optional

# Configuration
API_BASE_URL = "http://localhost:5000"
TEST_USER_ID = "test_user_123"


class SupabaseAPITester:
    """Test suite for the Supabase-backed Flask API."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session_id = str(uuid.uuid4())

    def test_health_check(self) -> bool:
        """Test the health check endpoint."""
        print("Testing health check...")
        try:
            response = requests.get(f"{self.base_url}/health")
            data = response.json()

            print(f"Health check status: {data.get('status')}")
            print(f"Memory system active: {data.get('memory_system_active')}")
            print(f"Supabase client active: {data.get('supabase_client_active')}")

            return response.status_code == 200 and data.get("status") == "healthy"
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    def test_add_memory(self) -> Optional[str]:
        """Test adding a memory note."""
        print("Testing add memory...")
        try:
            memory_data = {
                "content": "Python is a programming language known for its simplicity and readability.",
                "context": "Programming Knowledge",
                "category": "Technology",
                "user_id": TEST_USER_ID,
                "tags": ["python", "programming", "language"],
            }

            response = requests.post(f"{self.base_url}/memory/add", json=memory_data)
            data = response.json()

            if response.status_code == 200:
                memory_id = data.get("memory_id")
                print(f"Memory added successfully: {memory_id}")
                return memory_id
            else:
                print(f"Failed to add memory: {data}")
                return None

        except Exception as e:
            print(f"Add memory failed: {e}")
            return None

    def test_search_memories(self, query: str = "Python programming") -> bool:
        """Test searching for memories."""
        print(f"Testing memory search with query: {query}")
        try:
            search_data = {"query": query, "k": 3, "user_id": TEST_USER_ID}

            response = requests.post(f"{self.base_url}/memory/search", json=search_data)
            data = response.json()

            if response.status_code == 200:
                results = data.get("results", [])
                print(f"Found {len(results)} memories")
                for i, result in enumerate(results):
                    print(f"  {i+1}. {result.get('content')[:50]}...")
                return True
            else:
                print(f"Memory search failed: {data}")
                return False

        except Exception as e:
            print(f"Memory search failed: {e}")
            return False

    def test_get_memory(self, memory_id: str) -> bool:
        """Test retrieving a specific memory."""
        print(f"Testing get memory: {memory_id}")
        try:
            response = requests.get(f"{self.base_url}/memory/get/{memory_id}")
            data = response.json()

            if response.status_code == 200:
                print(f"Retrieved memory: {data.get('content', '')[:50]}...")
                return True
            else:
                print(f"Get memory failed: {data}")
                return False

        except Exception as e:
            print(f"Get memory failed: {e}")
            return False

    def test_chat(self, message: str) -> Optional[Dict[str, Any]]:
        """Test the chat functionality."""
        print(f"Testing chat with message: {message}")
        try:
            chat_data = {
                "message": message,
                "session_id": self.session_id,
                "user_id": TEST_USER_ID,
            }

            response = requests.post(f"{self.base_url}/chat", json=chat_data)
            data = response.json()

            if response.status_code == 200:
                print(f"Chat response: {data.get('response', '')[:100]}...")
                print(f"Memory IDs created: {data.get('memory_ids', [])}")
                return data
            else:
                print(f"Chat failed: {data}")
                return None

        except Exception as e:
            print(f"Chat failed: {e}")
            return None

    def test_session_history(self) -> bool:
        """Test retrieving session history."""
        print(f"Testing session history for: {self.session_id}")
        try:
            response = requests.get(
                f"{self.base_url}/session/{self.session_id}/history"
            )
            data = response.json()

            if response.status_code == 200:
                history = data.get("history", [])
                print(f"Session has {len(history)} messages")
                return True
            else:
                print(f"Session history failed: {data}")
                return False

        except Exception as e:
            print(f"Session history failed: {e}")
            return False

    def test_list_sessions(self) -> bool:
        """Test listing all sessions."""
        print("Testing list sessions...")
        try:
            params = {"user_id": TEST_USER_ID}
            response = requests.get(f"{self.base_url}/sessions", params=params)
            data = response.json()

            if response.status_code == 200:
                sessions = data.get("sessions", [])
                print(f"Found {len(sessions)} sessions")
                return True
            else:
                print(f"List sessions failed: {data}")
                return False

        except Exception as e:
            print(f"List sessions failed: {e}")
            return False

    def test_memory_stats(self) -> bool:
        """Test memory statistics."""
        print("Testing memory stats...")
        try:
            params = {"user_id": TEST_USER_ID}
            response = requests.get(f"{self.base_url}/memory/stats", params=params)
            data = response.json()

            if response.status_code == 200:
                print(f"Total memories: {data.get('total_memories', 0)}")
                print(f"Categories: {data.get('categories', {})}")
                return True
            else:
                print(f"Memory stats failed: {data}")
                return False

        except Exception as e:
            print(f"Memory stats failed: {e}")
            return False

    def run_full_test_suite(self):
        """Run the complete test suite."""
        print("=" * 60)
        print("Starting Supabase API Test Suite")
        print("=" * 60)

        test_results = {}

        # Test 1: Health Check
        test_results["health_check"] = self.test_health_check()
        print()

        # Wait a moment for system to be ready
        time.sleep(1)

        # Test 2: Add Memory
        memory_id = self.test_add_memory()
        test_results["add_memory"] = memory_id is not None
        print()

        # Test 3: Search Memories
        test_results["search_memories"] = self.test_search_memories()
        print()

        # Test 4: Get Memory (if we have a memory ID)
        if memory_id:
            test_results["get_memory"] = self.test_get_memory(memory_id)
        else:
            test_results["get_memory"] = False
            print("Skipping get memory test (no memory ID)")
        print()

        # Test 5: Chat
        chat_result = self.test_chat("Hello! Can you tell me about Python programming?")
        test_results["chat"] = chat_result is not None
        print()

        # Test 6: Session History
        test_results["session_history"] = self.test_session_history()
        print()

        # Test 7: List Sessions
        test_results["list_sessions"] = self.test_list_sessions()
        print()

        # Test 8: Memory Stats
        test_results["memory_stats"] = self.test_memory_stats()
        print()

        # Summary
        print("=" * 60)
        print("Test Results Summary")
        print("=" * 60)

        passed = 0
        total = len(test_results)

        for test_name, result in test_results.items():
            status = "PASS" if result else "FAIL"
            print(f"{test_name:20} : {status}")
            if result:
                passed += 1

        print(f"\nOverall: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! Supabase integration is working correctly.")
        else:
            print(
                "❌ Some tests failed. Please check the API and Supabase configuration."
            )

        return test_results


def main():
    """Main function to run the test suite."""
    print("Supabase API Test Suite")
    print("Make sure the Flask API server is running on http://localhost:5000")
    print("And that your Supabase configuration is set up correctly.")

    input("Press Enter to start the tests...")

    tester = SupabaseAPITester()
    results = tester.run_full_test_suite()

    return results


if __name__ == "__main__":
    main()
