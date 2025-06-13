"""
Advanced examples demonstrating sophisticated AgenticMemory usage.
"""

import json
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import AgenticMemorySystem, MemoryNote


class MemoryPersistence:
    """Utility class for saving and loading memory systems."""

    @staticmethod
    def save_memories(memory_system: AgenticMemorySystem, filepath: str):
        """Save memory system to JSON file."""
        data = {
            "memories": {},
            "config": {
                "evo_threshold": memory_system.evo_threshold,
                "evo_cnt": memory_system.evo_cnt,
            },
        }

        for mem_id, memory in memory_system.memories.items():
            data["memories"][mem_id] = {
                "content": memory.content,
                "keywords": memory.keywords,
                "links": memory.links,
                "importance_score": memory.importance_score,
                "retrieval_count": memory.retrieval_count,
                "timestamp": memory.timestamp,
                "last_accessed": memory.last_accessed,
                "context": memory.context,
                "evolution_history": memory.evolution_history,
                "category": memory.category,
                "tags": memory.tags,
            }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(data['memories'])} memories to {filepath}")

    @staticmethod
    def load_memories(
        filepath: str, llm_backend: str = "openai"
    ) -> AgenticMemorySystem:
        """Load memory system from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Create new memory system
        memory_system = AgenticMemorySystem(
            llm_backend=llm_backend,
            evo_threshold=data["config"].get("evo_threshold", 100),
        )
        memory_system.evo_cnt = data["config"].get("evo_cnt", 0)

        # Restore memories
        for mem_id, mem_data in data["memories"].items():
            memory = MemoryNote(
                content=mem_data["content"],
                id=mem_id,
                keywords=mem_data.get("keywords", []),
                links=mem_data.get("links", []),
                importance_score=mem_data.get("importance_score", 1.0),
                retrieval_count=mem_data.get("retrieval_count", 0),
                timestamp=mem_data.get("timestamp"),
                last_accessed=mem_data.get("last_accessed"),
                context=mem_data.get("context", "General"),
                evolution_history=mem_data.get("evolution_history", []),
                category=mem_data.get("category", "Uncategorized"),
                tags=mem_data.get("tags", []),
            )
            memory_system.memories[mem_id] = memory

        # Rebuild retriever
        memory_system.consolidate_memories()

        print(f"Loaded {len(memory_system.memories)} memories from {filepath}")
        return memory_system


def demonstrate_knowledge_base():
    """Demonstrate building a knowledge base with evolution."""
    print("=" * 60)
    print("KNOWLEDGE BASE DEMONSTRATION")
    print("=" * 60)

    memory_system = AgenticMemorySystem(llm_backend="openai", evo_threshold=5)

    # AI/ML Knowledge Base
    knowledge_items = [
        "Artificial Intelligence is the simulation of human intelligence in machines.",
        "Machine Learning is a subset of AI that learns from data without explicit programming.",
        "Deep Learning uses artificial neural networks with multiple layers.",
        "Supervised learning uses labeled data to train models.",
        "Unsupervised learning finds patterns in data without labels.",
        "Reinforcement learning learns through rewards and penalties.",
        "Neural networks are inspired by biological neural networks in brains.",
        "Backpropagation is the algorithm used to train neural networks.",
        "Gradient descent optimizes neural network weights.",
        "Overfitting occurs when a model learns the training data too specifically.",
    ]

    print(f"\nBuilding knowledge base with {len(knowledge_items)} items...")

    for i, item in enumerate(knowledge_items, 1):
        memory_id = memory_system.add_note(item)
        print(f"Added item {i}: {memory_id[:8]}...")

    # Demonstrate queries
    queries = [
        "What is the difference between AI and machine learning?",
        "How do neural networks learn?",
        "What are the types of machine learning?",
        "What problems can occur during training?",
    ]

    print(f"\nTesting knowledge retrieval with {len(queries)} queries...")

    for query in queries:
        print(f"\nQuery: '{query}'")
        related = memory_system.get_related_memories(query, k=3)

        for i, memory in enumerate(related, 1):
            print(f"  {i}. {memory.content}")
            print(f"     Context: {memory.context}")
            print(f"     Tags: {memory.tags}")
            print()

    # Save the knowledge base
    save_path = "examples/ai_knowledge_base.json"
    MemoryPersistence.save_memories(memory_system, save_path)

    return memory_system


def demonstrate_conversation_memory():
    """Demonstrate conversation-based memory with temporal aspects."""
    print("=" * 60)
    print("CONVERSATION MEMORY DEMONSTRATION")
    print("=" * 60)

    memory_system = AgenticMemorySystem(llm_backend="openai", evo_threshold=3)

    # Simulate a conversation about a project
    conversation = [
        (
            "2024-01-01 09:00",
            "We need to start planning the new AI project for customer analytics.",
        ),
        (
            "2024-01-01 09:15",
            "The project should focus on predictive customer behavior modeling.",
        ),
        (
            "2024-01-01 10:30",
            "We'll need a team of 3 data scientists and 2 ML engineers.",
        ),
        (
            "2024-01-02 14:00",
            "First milestone is data collection and preprocessing by end of month.",
        ),
        (
            "2024-01-02 14:30",
            "We have access to customer transaction data from the past 2 years.",
        ),
        (
            "2024-01-03 11:00",
            "Initial data analysis shows seasonal purchasing patterns.",
        ),
        (
            "2024-01-03 16:45",
            "We should implement feature engineering for customer segmentation.",
        ),
        (
            "2024-01-04 09:30",
            "Team decided to use Python with scikit-learn and TensorFlow.",
        ),
    ]

    print(f"\nAdding {len(conversation)} conversation memories...")

    for timestamp, content in conversation:
        memory_id = memory_system.add_note(content, time=timestamp)
        print(f"Added: {timestamp} - {content[:50]}...")

    # Query the conversation memory
    queries = [
        "What is the project about?",
        "Who is on the team?",
        "What are the milestones?",
        "What technology stack are we using?",
    ]

    print(f"\nQuerying conversation memory...")

    for query in queries:
        print(f"\nQuery: '{query}'")
        related = memory_system.get_related_memories(query, k=2)

        for memory in related:
            print(f"  Time: {memory.timestamp}")
            print(f"  Content: {memory.content}")
            print(f"  Tags: {memory.tags}")
            print()


def demonstrate_memory_evolution():
    """Demonstrate how memories evolve and form connections."""
    print("=" * 60)
    print("MEMORY EVOLUTION DEMONSTRATION")
    print("=" * 60)

    memory_system = AgenticMemorySystem(
        llm_backend="openai",
        evo_threshold=2,  # Very low threshold to see evolution quickly
    )

    # Add related memories that should form connections
    related_memories = [
        "Python is a high-level programming language.",
        "Python has extensive libraries for data science and machine learning.",
        "Pandas is a powerful Python library for data manipulation.",
        "NumPy provides support for large arrays and matrices in Python.",
        "Scikit-learn is a Python library for machine learning algorithms.",
        "TensorFlow is a Python framework for deep learning.",
    ]

    print(f"\nAdding {len(related_memories)} related memories to observe evolution...")

    for i, content in enumerate(related_memories, 1):
        print(f"\nAdding memory {i}: {content}")
        memory_id = memory_system.add_note(content)

        # Show the state after each addition
        memory = memory_system.memories[memory_id]
        print(f"  Tags: {memory.tags}")
        print(f"  Links: {memory.links}")
        print(f"  Context: {memory.context}")

    print(f"\nFinal memory system state:")
    print(f"Total memories: {len(memory_system.memories)}")
    print(f"Evolution count: {memory_system.evo_cnt}")

    # Show all memories and their connections
    for mem_id, memory in memory_system.memories.items():
        print(f"\nMemory {mem_id[:8]}:")
        print(f"  Content: {memory.content[:60]}...")
        print(f"  Tags: {memory.tags}")
        print(f"  Links: {memory.links}")


if __name__ == "__main__":
    # Run demonstrations
    print("Choose a demonstration:")
    print("1. Knowledge Base")
    print("2. Conversation Memory")
    print("3. Memory Evolution")
    print("4. All demonstrations")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice == "1":
        demonstrate_knowledge_base()
    elif choice == "2":
        demonstrate_conversation_memory()
    elif choice == "3":
        demonstrate_memory_evolution()
    elif choice == "4":
        demonstrate_knowledge_base()
        print("\n" + "=" * 60 + "\n")
        demonstrate_conversation_memory()
        print("\n" + "=" * 60 + "\n")
        demonstrate_memory_evolution()
    else:
        print("Invalid choice. Running all demonstrations...")
        demonstrate_knowledge_base()
        demonstrate_conversation_memory()
        demonstrate_memory_evolution()
