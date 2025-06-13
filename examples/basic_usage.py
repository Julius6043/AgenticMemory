"""
Test and example usage of the AgenticMemory system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import AgenticMemorySystem, MemoryNote


def run_tests():
    """Run system tests and demonstrations."""
    print("Starting Memory System Tests...")

    # Initialize memory system with OpenAI backend
    memory_system = AgenticMemorySystem(
        model_name="all-MiniLM-L6-v2", llm_backend="openai", llm_model="gpt-4o-mini"
    )

    print("\nAdding test memories...")

    # Add test memories - only content is required
    memory_ids = []
    memory_ids.append(
        memory_system.add_note(
            "Neural networks are composed of layers of neurons that process information."
        )
    )

    memory_ids.append(
        memory_system.add_note(
            "Data preprocessing involves cleaning and transforming raw data for model training."
        )
    )

    print("\nQuerying for related memories...")

    # Create a query memory note for demonstration
    query = MemoryNote(
        content="How do neural networks process data?",
        llm_controller=memory_system.llm_controller,
    )

    # Search for related memories
    related = memory_system.get_related_memories(query.content, k=2)
    print(f"Found {len(related)} related memories:")

    print("\nResults:")
    for i, memory in enumerate(related, 1):
        print(f"\n{i}. Memory:")
        print(f"Content: {memory.content}")
        print(f"Category: {memory.category}")
        print(f"Keywords: {memory.keywords}")
        print(f"Tags: {memory.tags}")
        print(f"Context: {memory.context}")
        print("-" * 50)


def run_advanced_demo():
    """Run advanced demonstration with more complex scenarios."""
    print("\n" + "=" * 60)
    print("ADVANCED DEMONSTRATION")
    print("=" * 60)

    # Initialize with different settings
    memory_system = AgenticMemorySystem(
        model_name="all-MiniLM-L6-v2",
        llm_backend="openai",
        llm_model="gpt-4o-mini",
        evo_threshold=3,  # Lower threshold for demo
    )

    # Add a variety of memories
    memories = [
        "Machine learning algorithms learn patterns from data to make predictions.",
        "Deep learning uses neural networks with multiple hidden layers.",
        "Supervised learning requires labeled training data.",
        "Reinforcement learning agents learn through interaction with an environment.",
        "Natural language processing enables computers to understand human language.",
        "Computer vision allows machines to interpret and analyze visual information.",
    ]

    print(f"\nAdding {len(memories)} diverse memories...")
    for i, content in enumerate(memories, 1):
        memory_id = memory_system.add_note(content)
        print(f"Added memory {i}: {memory_id[:8]}...")

    # Test various queries
    queries = [
        "What is machine learning?",
        "How do neural networks work?",
        "What types of learning exist in AI?",
        "How do computers understand images?",
    ]

    print(f"\nTesting {len(queries)} different queries...")
    for query in queries:
        print(f"\nQuery: '{query}'")
        related = memory_system.get_related_memories(query, k=3)
        for i, memory in enumerate(related, 1):
            print(f"  {i}. {memory.content[:60]}...")
            print(f"     Tags: {memory.tags}")


if __name__ == "__main__":
    # Run basic tests
    run_tests()

    # Uncomment for advanced demonstration
    # run_advanced_demo()
