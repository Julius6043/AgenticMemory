#!/usr/bin/env python3
"""
Comprehensive test for memory retrieval and chat functionality.
"""

import requests
import json
import time


def test_memory_retrieval():
    base_url = "http://localhost:5000"

    print("🧠 Testing Memory Retrieval and Chat Functionality")
    print("=" * 60)

    # Test user
    user_id = "comprehensive-test-user"
    session_id = f"session-{int(time.time())}"

    # Step 1: Add some memories for the user
    print("\n📝 Step 1: Adding memories...")

    memories_to_add = [
        {
            "content": "I love playing guitar and music production",
            "context": "Personal Interests",
            "category": "Hobby",
            "user_id": user_id,
        },
        {
            "content": "I work as a Python developer at a startup",
            "context": "Professional Life",
            "category": "Career",
            "user_id": user_id,
        },
        {
            "content": "My favorite food is Italian cuisine, especially pasta",
            "context": "Food Preferences",
            "category": "Personal",
            "user_id": user_id,
        },
    ]

    memory_ids = []
    for memory_data in memories_to_add:
        response = requests.post(f"{base_url}/memory/add", json=memory_data)
        if response.status_code == 200:
            result = response.json()
            memory_ids.append(result["memory_id"])
            print(f"✅ Added memory: {memory_data['content'][:50]}...")
        else:
            print(f"❌ Failed to add memory: {response.text}")

    print(f"\n📊 Added {len(memory_ids)} memories")

    # Step 2: Test memory search
    print("\n🔍 Step 2: Testing memory search...")

    search_queries = ["guitar music", "Python programming", "Italian food pasta"]

    for query in search_queries:
        search_data = {"query": query, "user_id": user_id, "limit": 5}

        response = requests.post(f"{base_url}/memory/search", json=search_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Search '{query}': Found {result['count']} memories")
            for memory in result.get("results", []):
                print(f"   - {memory['content'][:60]}...")
        else:
            print(f"❌ Search failed for '{query}': {response.text}")

    # Step 3: Test chat with memory retrieval
    print("\n💬 Step 3: Testing chat with memory retrieval...")

    chat_messages = [
        "Hello! What do you know about my hobbies?",
        "What's my job?",
        "Tell me about my food preferences",
        "Can you summarize what you know about me?",
    ]

    for message in chat_messages:
        chat_data = {"message": message, "user_id": user_id, "session_id": session_id}

        print(f"\n🗨️ User: {message}")

        response = requests.post(f"{base_url}/chat", json=chat_data)
        if response.status_code == 200:
            result = response.json()
            print(f"🤖 Assistant: {result['response'][:150]}...")
            print(f"📊 Related memories: {result['related_memories_count']}")

            if result.get("related_memories"):
                print("🧠 Retrieved memories:")
                for memory in result["related_memories"]:
                    print(f"   - {memory['content'][:50]}...")
        else:
            print(f"❌ Chat failed: {response.text}")

        time.sleep(1)  # Small delay between messages

    # Step 4: Test session history
    print(f"\n📜 Step 4: Testing session history...")

    response = requests.get(f"{base_url}/session/{session_id}/history")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Session history: {result['count']} messages")
        for message in result.get("messages", [])[:3]:  # Show first 3
            print(f"   {message['message_type']}: {message['content'][:50]}...")
    else:
        print(f"❌ Failed to get session history: {response.text}")

    print("\n🎉 Comprehensive test completed!")


if __name__ == "__main__":
    test_memory_retrieval()
