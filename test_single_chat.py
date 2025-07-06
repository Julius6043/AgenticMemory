"""
Test single chat message to see detailed logging output.
"""

import os
import requests
import json
import time

# API Configuration
API_BASE_URL = "http://localhost:5000"
TEST_USER_ID = "test_user_detailed_log"
TEST_SESSION_ID = f"detailed_test_session_{int(time.time())}"


def test_single_chat():
    """Test a single chat message to see detailed logging."""
    print("🚀 Testing single chat message with detailed logging...")
    print(f"👤 User ID: {TEST_USER_ID}")
    print(f"💬 Session ID: {TEST_SESSION_ID}")

    # Test message
    test_message = (
        "What are the main benefits of using Python for machine learning projects?"
    )

    print(f"📝 Message: {test_message}")
    print("-" * 80)

    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "message": test_message,
                "user_id": TEST_USER_ID,
                "session_id": TEST_SESSION_ID,
            },
            timeout=60,
        )

        print(f"📡 Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print("-" * 80)
            print("📊 Response Summary:")
            print(f"   Response Length: {len(result.get('response', ''))}")
            print(f"   Memory IDs Created: {result.get('memory_ids', [])}")
            print(f"   Context Memory IDs: {result.get('context_memory_ids', [])}")
            print(
                f"   Related Memories Count: {result.get('related_memories_count', 0)}"
            )

            if "processing_details" in result:
                details = result["processing_details"]
                print("🔍 Processing Details:")
                print(
                    f"   - Memories Retrieved: {details.get('memories_retrieved', 'N/A')}"
                )
                print(
                    f"   - Memories Used for Context: {details.get('memories_used_for_context', 'N/A')}"
                )
                print(
                    f"   - LLM Prompt Length: {details.get('llm_prompt_length', 'N/A')}"
                )
                print(
                    f"   - LLM Response Length: {details.get('llm_response_length', 'N/A')}"
                )

            print("-" * 80)
            print("🤖 Assistant Response:")
            print(result.get("response", "No response"))

            if result.get("context_memory_ids"):
                print("-" * 80)
                print("🧠 Context Memory IDs Used:")
                for i, memory_id in enumerate(result.get("context_memory_ids", []), 1):
                    print(f"   {i}. {memory_id}")

        else:
            print(f"❌ Error: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {str(e)}")


if __name__ == "__main__":
    test_single_chat()
