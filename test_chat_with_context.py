#!/usr/bin/env python3
"""
Test script to verify that the chat API correctly retrieves and uses memories for context.
Tests the improved logging and context memory ID return.
"""

import requests
import json
import time


def test_chat_with_memory_context():
    """Test that chat correctly retrieves and uses existing memories."""

    base_url = "http://localhost:5000"
    user_id = "demo-user-agentic-memory-2024"
    session_id = f"test-session-{int(time.time())}"

    print("🧪 Testing Chat API with Memory Context")
    print("=" * 60)

    # First, let's check the memory stats for this user
    print("📊 Checking memory stats for user...")
    try:
        stats_response = requests.get(
            f"{base_url}/memory/stats", params={"user_id": user_id}
        )
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"✅ User has {stats.get('total_memories', 0)} memories")
        else:
            print(f"❌ Failed to get stats: {stats_response.status_code}")
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

    print("-" * 60)

    # Now test chat with a query that should match existing memories
    print("💬 Testing chat message that should find related memories...")

    # Use a German message that should match existing content
    test_message = (
        "Hallo, wie geht es dir? Was kannst du über Machine Learning erzählen?"
    )

    chat_data = {"message": test_message, "session_id": session_id, "user_id": user_id}

    print(f"📝 Message: {test_message}")
    print(f"👤 User ID: {user_id}")
    print(f"📱 Session ID: {session_id}")
    print("-" * 60)

    try:
        print("🚀 Sending chat request...")
        response = requests.post(f"{base_url}/chat", json=chat_data)

        if response.status_code == 200:
            result = response.json()

            print("✅ Chat Response Received!")
            print(f"📝 Response: {result.get('response', 'No response')[:200]}...")
            print()

            # Check for context memory IDs
            context_memory_ids = result.get("context_memory_ids", [])
            print(f"🧠 Context Memory IDs: {context_memory_ids}")
            print(f"📊 Number of context memories used: {len(context_memory_ids)}")

            # Check related memories
            related_memories = result.get("related_memories", [])
            print(f"🔗 Related memories found: {len(related_memories)}")

            if related_memories:
                print("\n📋 Related Memories Details:")
                for i, mem in enumerate(related_memories):
                    print(f"  {i+1}. ID: {mem.get('id')}")
                    print(f"     Content: {mem.get('content', '')[:100]}...")
                    print(f"     Category: {mem.get('category', 'N/A')}")
                    print(f"     Context: {mem.get('context', 'N/A')}")
                    print("     " + "-" * 50)

            # Check processing details
            processing_details = result.get("processing_details", {})
            print(f"\n🔧 Processing Details:")
            for key, value in processing_details.items():
                print(f"  {key}: {value}")

            # New memory IDs created
            memory_ids = result.get("memory_ids", [])
            print(f"\n💾 New Memory IDs Created: {memory_ids}")

            # Test success criteria
            print("\n🎯 Test Results:")
            if context_memory_ids:
                print("✅ SUCCESS: Context memories were retrieved and used!")
            else:
                print("❌ ISSUE: No context memories were found/used")

            if len(related_memories) > 0:
                print("✅ SUCCESS: Related memories were found!")
            else:
                print("❌ ISSUE: No related memories were found")

        else:
            print(f"❌ Chat request failed: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Error during chat request: {e}")


if __name__ == "__main__":
    test_chat_with_memory_context()
