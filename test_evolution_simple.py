#!/usr/bin/env python3
"""
Simple test for evolution functionality.
"""

import os
import sys

# Add src to path
current_dir = os.path.dirname(__file__)
src_path = os.path.join(current_dir, "src")
sys.path.insert(0, src_path)
sys.path.insert(0, current_dir)

from src.database.supabase_memory_adapter import SupabaseAgenticMemorySystem


def test_evolution_simple():
    """Test basic evolution functionality with a few memories."""

    print("🧠 Testing Simple Memory Evolution")
    print("=" * 40)

    try:
        # Initialize system with low evolution threshold for testing
        memory_system = SupabaseAgenticMemorySystem(
            llm_backend="openai",
            llm_model="gpt-4o-mini",
            evo_threshold=2,  # Very low for testing
            user_id="test_evolution_simple",
        )

        print("✅ Memory system initialized")

        # Add some related memories
        memories = [
            "Python is a programming language used for web development.",
            "JavaScript is popular for creating interactive web applications.",
            "Web development involves both frontend and backend technologies.",
        ]

        memory_ids = []

        for i, content in enumerate(memories):
            print(f"\nAdding memory {i+1}: {content[:50]}...")
            memory_id = memory_system.add_note(content, category="Programming")
            memory_ids.append(memory_id)
            print(f"  Created with ID: {memory_id}")

            # Check for evolution
            if memory_system.evo_cnt > 0:
                print(f"  🔄 Evolution triggered! Total count: {memory_system.evo_cnt}")

        # Check final state
        print(f"\n📊 Final Statistics:")
        print(f"  Total memories: {len(memory_ids)}")
        print(f"  Evolution count: {memory_system.evo_cnt}")

        # Check for links
        for memory_id in memory_ids:
            memory = memory_system.read(memory_id)
            if memory and memory.links:
                print(f"  Memory {memory_id[:8]}... has {len(memory.links)} links")

        print("\n✅ Simple evolution test completed!")

    except Exception as e:
        print(f"\n❌ Evolution test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_evolution_simple()
