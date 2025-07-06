"""
Test script for the enhanced Supabase AgenticMemory system.

This script demonstrates the improved memory system with:
- Enhanced memory evolution from Ground_version
- Memory linking functionality
- Robust error handling
- Supabase backend integration
"""

import os
import sys
from datetime import datetime

# Add src to path
current_dir = os.path.dirname(__file__)
src_path = os.path.join(current_dir, "src")
sys.path.insert(0, src_path)
sys.path.insert(0, current_dir)

try:
    from src.database.supabase_memory_adapter import SupabaseAgenticMemorySystem
    from src.database.supabase_client import SupabaseMemoryClient
    from src.database.supabase_config import SupabaseConfigManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Available paths:", sys.path[:3])
    print("Current directory:", os.getcwd())
    print("Script directory:", os.path.dirname(__file__))
    # Try alternative import paths
    try:
        from database.supabase_memory_adapter import SupabaseAgenticMemorySystem
        from database.supabase_client import SupabaseMemoryClient
        from database.supabase_config import SupabaseConfigManager

        print("✅ Successfully imported with alternative path")
    except ImportError as e2:
        print(f"All import attempts failed:")
        print(f"  - src import: {e}")
        print(f"  - direct import: {e2}")
        sys.exit(1)


def test_enhanced_memory_system():
    """Test the enhanced memory system functionality."""

    print("🚀 Testing Enhanced Supabase AgenticMemory System")
    print("=" * 60)

    # Debug environment variables
    print("\n🔍 Environment Variable Debug:")
    print("-" * 40)

    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "OPENAI_API_KEY",
    ]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if "KEY" in var:
                print(
                    f"✅ {var}: {'*' * 8}...{value[-4:] if len(value) > 4 else '****'}"
                )
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n❌ Missing required environment variables: {missing_vars}")
        print("\nPlease set these environment variables before running the test.")
        print("\nExample for PowerShell:")
        for var in missing_vars:
            print(f'$env:{var}="your_value_here"')
        return False

    try:
        # Initialize the enhanced memory system
        print("\n1. Initializing enhanced memory system...")

        memory_system = SupabaseAgenticMemorySystem(
            model_name="all-MiniLM-L6-v2",
            llm_backend="openai",
            llm_model="gpt-4o-mini",
            evo_threshold=3,  # Low threshold for testing
            user_id="test_user_enhanced",
        )

        print("   ✅ Memory system initialized successfully")

        # Test 1: Add first memory
        print("\n2. Adding first memory...")

        memory1_id = memory_system.add_note(
            content="Artificial Intelligence is transforming how we interact with technology and process information.",
            category="Technology",
        )

        print(f"   ✅ Memory 1 created with ID: {memory1_id}")

        # Test 2: Add related memory to trigger evolution
        print("\n3. Adding related memory to trigger evolution...")

        memory2_id = memory_system.add_note(
            content="Machine learning algorithms enable computers to learn patterns from data without explicit programming.",
            category="Technology",
        )

        print(f"   ✅ Memory 2 created with ID: {memory2_id}")

        # Test 3: Add third memory to test linking
        print("\n4. Adding third memory to test memory linking...")

        memory3_id = memory_system.add_note(
            content="Deep learning neural networks are particularly effective for image recognition and natural language processing.",
            category="AI/ML",
        )

        print(f"   ✅ Memory 3 created with ID: {memory3_id}")

        # Test 4: Search for related memories
        print("\n5. Testing memory search functionality...")

        search_results = memory_system.search(
            "artificial intelligence machine learning", k=3
        )

        print(f"   ✅ Found {len(search_results)} related memories:")
        for i, result in enumerate(search_results):
            print(f"      {i+1}. {result['content'][:50]}...")
            print(f"         Tags: {result.get('tags', [])}")
            print(f"         Context: {result.get('context', 'N/A')}")

        # Test 5: Get specific memory with links
        print("\n6. Testing memory retrieval with links...")

        retrieved_memory = memory_system.read(memory1_id)
        if retrieved_memory:
            print(f"   ✅ Retrieved memory: {retrieved_memory.content[:50]}...")
            print(f"      Links: {retrieved_memory.links}")
            print(f"      Tags: {retrieved_memory.tags}")
            print(f"      Context: {retrieved_memory.context}")
        else:
            print("   ❌ Failed to retrieve memory")

        # Test 6: Test memory evolution tracking
        print("\n7. Testing evolution tracking...")

        # Add a few more memories to trigger evolution
        for i in range(3):
            memory_system.add_note(
                content=f"This is test memory {i+4} about AI and technology trends in 2025.",
                category="Technology",
            )

        print("   ✅ Added additional memories to trigger evolution")

        # Test 7: Test memory links creation
        print("\n8. Testing memory links functionality...")

        # Try to get linked memories
        linked_memories = memory_system.supabase_client.get_linked_memories(memory1_id)
        print(f"   ✅ Found {len(linked_memories)} linked memories for memory 1")

        # Test 8: Test memory update
        print("\n9. Testing memory update functionality...")

        update_success = memory_system.update(
            memory1_id,
            {"tags": ["AI", "Technology", "Updated"], "importance_score": 2.0},
        )

        if update_success:
            print("   ✅ Memory updated successfully")
            updated_memory = memory_system.read(memory1_id)
            if updated_memory:
                print(f"      New tags: {updated_memory.tags}")
                print(f"      New importance: {updated_memory.importance_score}")
        else:
            print("   ❌ Failed to update memory")

        # Test 9: Test memory statistics
        print("\n10. Getting memory statistics...")

        try:
            stats = memory_system.supabase_client.get_memory_statistics()
            if stats:
                print("   ✅ Memory statistics retrieved:")
                print(f"      Total memories: {stats.get('total_memories', 0)}")
                print(f"      Total retrievals: {stats.get('total_retrievals', 0)}")
                print(f"      Categories: {list(stats.get('categories', {}).keys())}")
        except Exception as e:
            print(f"   ⚠️ Statistics not available: {e}")

        print("\n" + "=" * 60)
        print("🎉 Enhanced AgenticMemory System Test Completed Successfully!")
        print("=" * 60)

        # Summary
        print(f"\nSummary:")
        print(f"- Memories created: {len([memory1_id, memory2_id, memory3_id]) + 3}")
        print(f"- Search results: {len(search_results)}")
        print(f"- Memory links: {len(linked_memories)}")
        print(f"- Evolution threshold: {memory_system.evo_threshold}")
        print(f"- Evolution count: {memory_system.evo_cnt}")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


def test_memory_evolution_detailed():
    """Test detailed memory evolution functionality."""

    print("\n🧠 Testing Detailed Memory Evolution")
    print("=" * 50)

    try:
        memory_system = SupabaseAgenticMemorySystem(
            llm_backend="openai",
            llm_model="gpt-4o-mini",
            evo_threshold=2,  # Very low for testing
            user_id="test_evolution_user",
        )

        # Create memories that should trigger evolution
        print("1. Creating memories to trigger evolution...")

        memories = [
            "Python is a popular programming language for data science and machine learning.",
            "Data scientists use Python libraries like pandas and scikit-learn for analysis.",
            "Machine learning models in Python can be deployed using frameworks like Flask or FastAPI.",
        ]

        memory_ids = []
        for i, content in enumerate(memories):
            memory_id = memory_system.add_note(content, category="Programming")
            memory_ids.append(memory_id)
            print(f"   Memory {i+1}: {memory_id}")

            # Check for evolution after each addition
            if memory_system.evo_cnt > 0:
                print(f"   🔄 Evolution triggered! Count: {memory_system.evo_cnt}")

        print("\n2. Testing memory relationships...")

        for memory_id in memory_ids:
            memory = memory_system.read(memory_id)
            if memory and memory.links:
                print(f"   Memory {memory_id} has {len(memory.links)} links")
                linked_memories = memory_system.supabase_client.get_linked_memories(
                    memory_id
                )
                print(f"   Linked to: {[m.get('id') for m in linked_memories]}")

        print("\n✅ Evolution testing completed!")

    except Exception as e:
        print(f"\n❌ Evolution test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run tests with proper environment variable checking built-in
    print("🔍 Starting Enhanced Memory System Tests...")

    # Run basic test
    success = test_enhanced_memory_system()

    if success is not False:  # If basic test passed or returned None
        print("\n" + "=" * 60)
        print("🔄 Running detailed evolution test...")
        test_memory_evolution_detailed()
    else:
        print(
            "❌ Basic test failed due to environment issues. Skipping evolution test."
        )
        sys.exit(1)
