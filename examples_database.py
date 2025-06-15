#!/usr/bin/env python3
"""
Example script demonstrating Supabase database functionality.

This script shows how to use the Supabase database components
for various real-world scenarios and use cases.
"""

import os
import sys
import uuid
import time
import json
from datetime import datetime
from typing import List, Dict, Any

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.database.supabase_client import SupabaseMemoryClient
from src.database.supabase_memory_adapter import SupabaseAgenticMemorySystem
from src.database.supabase_config import SupabaseConfigManager
from src.database.supabase_utils import (
    SupabaseMigrationTool,
    SupabaseMaintenanceTool,
    SupabaseBackupTool,
)


class SupabaseDatabaseExamples:
    """Examples of using Supabase database components."""

    def __init__(self):
        """Initialize the examples with demo data."""
        self.user_id = f"demo_user_{uuid.uuid4().hex[:8]}"
        self.client = None
        self.memory_system = None

    def setup(self):
        """Set up the example environment."""
        print("🔧 Setting up example environment...")

        try:
            # Initialize client
            self.client = SupabaseMemoryClient()

            # Test connection
            if not self.client.test_connection():
                print("❌ Cannot connect to Supabase. Please check your configuration.")
                return False

            # Initialize memory system
            self.memory_system = SupabaseAgenticMemorySystem(
                user_id=self.user_id,
                model_name="all-MiniLM-L6-v2",
                llm_backend="openai",
                llm_model="gpt-4o-mini",
            )

            print(f"✅ Connected to Supabase with user ID: {self.user_id}")
            return True

        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    def example_1_basic_memory_operations(self):
        """Example 1: Basic memory operations."""
        print("\n" + "=" * 60)
        print("📝 EXAMPLE 1: Basic Memory Operations")
        print("=" * 60)

        print("\n1. Creating memories...")

        # Create some example memories
        memories_to_create = [
            {
                "content": "Python is a high-level programming language known for its simplicity and readability.",
                "context": "Programming Knowledge",
                "category": "Technology",
                "keywords": ["python", "programming", "language"],
                "tags": ["coding", "development"],
                "importance_score": 0.9,
            },
            {
                "content": "Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
                "context": "AI Knowledge",
                "category": "Technology",
                "keywords": ["machine learning", "AI", "data"],
                "tags": ["artificial intelligence", "ml"],
                "importance_score": 0.8,
            },
            {
                "content": "Supabase is an open-source Firebase alternative with a PostgreSQL database.",
                "context": "Database Knowledge",
                "category": "Technology",
                "keywords": ["supabase", "database", "postgresql"],
                "tags": ["backend", "database"],
                "importance_score": 0.7,
            },
        ]

        created_ids = []
        for i, memory_data in enumerate(memories_to_create, 1):
            try:
                memory_id = self.client.create_memory(
                    user_id=self.user_id, **memory_data
                )
                created_ids.append(memory_id)
                print(f"   ✅ Memory {i} created: {memory_id}")
                print(f"      Content: {memory_data['content'][:50]}...")

            except Exception as e:
                print(f"   ❌ Failed to create memory {i}: {e}")

        print(f"\n📊 Created {len(created_ids)} memories total")

        # Retrieve a memory
        if created_ids:
            print(f"\n2. Retrieving memory {created_ids[0]}...")
            try:
                memory = self.client.get_memory(created_ids[0])
                if memory:
                    print(f"   ✅ Retrieved memory:")
                    print(f"      Content: {memory['content']}")
                    print(f"      Category: {memory['category']}")
                    print(f"      Keywords: {memory['keywords']}")
                else:
                    print("   ❌ Memory not found")

            except Exception as e:
                print(f"   ❌ Failed to retrieve memory: {e}")

        # Update a memory
        if created_ids:
            print(f"\n3. Updating memory {created_ids[0]}...")
            try:
                updated = self.client.update_memory(
                    created_ids[0],
                    {
                        "importance_score": 1.0,
                        "tags": ["python", "programming", "updated"],
                    },
                )
                if updated:
                    print("   ✅ Memory updated successfully")
                else:
                    print("   ❌ Failed to update memory")

            except Exception as e:
                print(f"   ❌ Update failed: {e}")

        return created_ids

    def example_2_search_and_retrieval(self):
        """Example 2: Search and retrieval operations."""
        print("\n" + "=" * 60)
        print("🔍 EXAMPLE 2: Search and Retrieval")
        print("=" * 60)

        # Text search
        print("\n1. Text-based search...")
        search_queries = ["Python programming", "machine learning", "database"]

        for query in search_queries:
            try:
                results = self.client.search_memories_by_text(
                    query=query, limit=3, user_id=self.user_id
                )

                print(f"\n   🔍 Search for '{query}':")
                if results:
                    print(f"      Found {len(results)} results:")
                    for i, result in enumerate(results, 1):
                        print(f"         {i}. {result['content'][:60]}...")
                else:
                    print("      No results found")

            except Exception as e:
                print(f"   ❌ Search failed: {e}")

        # Category-based search
        print("\n2. Category-based search...")
        try:
            tech_memories = self.client.get_memories_by_category(
                category="Technology", limit=10, user_id=self.user_id
            )

            print(f"   📁 Technology category: {len(tech_memories)} memories")
            for i, memory in enumerate(tech_memories, 1):
                print(f"      {i}. {memory['content'][:50]}...")

        except Exception as e:
            print(f"   ❌ Category search failed: {e}")

        # Tag-based search
        print("\n3. Tag-based search...")
        try:
            tagged_memories = self.client.get_memories_by_tags(
                tags=["programming", "development"],
                match_all=False,  # Match any tag
                limit=5,
                user_id=self.user_id,
            )

            print(f"   🏷️ Tagged memories: {len(tagged_memories)} found")
            for i, memory in enumerate(tagged_memories, 1):
                print(f"      {i}. {memory['content'][:50]}...")
                print(f"         Tags: {memory.get('tags', [])}")

        except Exception as e:
            print(f"   ❌ Tag search failed: {e}")

    def example_3_memory_system_usage(self):
        """Example 3: Using the AgenticMemory system."""
        print("\n" + "=" * 60)
        print("🧠 EXAMPLE 3: AgenticMemory System Usage")
        print("=" * 60)

        print("\n1. Adding notes through the memory system...")

        # Add notes using the memory system
        notes_to_add = [
            "Flask is a lightweight web framework for Python that's easy to learn and use.",
            "PostgreSQL is a powerful, open-source relational database management system.",
            "Vector embeddings are numerical representations of text that capture semantic meaning.",
            "REST APIs provide a standardized way for applications to communicate over HTTP.",
        ]

        added_notes = []
        for i, content in enumerate(notes_to_add, 1):
            try:
                note_id = self.memory_system.add_note(
                    content=content,
                    context="Technical Knowledge",
                    category="Technology",
                )
                added_notes.append(note_id)
                print(f"   ✅ Note {i} added: {note_id}")
                print(f"      Content: {content[:50]}...")

            except Exception as e:
                print(f"   ❌ Failed to add note {i}: {e}")

        print(f"\n📝 Added {len(added_notes)} notes")

        # Get related memories
        print("\n2. Finding related memories...")

        queries = [
            "web development frameworks",
            "database systems",
            "natural language processing",
        ]

        for query in queries:
            try:
                related = self.memory_system.get_related_memories(query, k=3)
                print(f"\n   🔗 Related to '{query}':")

                if related:
                    for i, memory in enumerate(related, 1):
                        print(f"      {i}. {memory.content[:60]}...")
                        print(f"         Context: {memory.context}")
                else:
                    print("      No related memories found")

            except Exception as e:
                print(f"   ❌ Related memories search failed: {e}")

        # Get memory statistics
        print("\n3. Memory system statistics...")
        try:
            stats = self.memory_system.get_memory_statistics()
            print(f"   📊 Statistics:")
            print(f"      Total memories: {stats.get('total_memories', 'N/A')}")
            print(f"      Categories: {len(stats.get('categories', {}))}")
            print(
                f"      Average importance: {stats.get('avg_importance_score', 'N/A')}"
            )

        except Exception as e:
            print(f"   ❌ Statistics failed: {e}")

    def example_4_chat_sessions(self):
        """Example 4: Chat session management."""
        print("\n" + "=" * 60)
        print("💬 EXAMPLE 4: Chat Session Management")
        print("=" * 60)

        session_id = f"demo_session_{uuid.uuid4().hex[:8]}"

        print(f"\n1. Creating chat session: {session_id}")
        try:
            session_created = self.client.create_chat_session(
                session_id=session_id,
                user_id=self.user_id,
                metadata={"demo": True, "topic": "AI Discussion"},
            )

            if session_created:
                print("   ✅ Chat session created")
            else:
                print("   ❌ Failed to create chat session")
                return

        except Exception as e:
            print(f"   ❌ Session creation failed: {e}")
            return

        print("\n2. Adding chat messages...")

        # Simulate a conversation
        messages = [
            ("user", "Hello! Can you tell me about artificial intelligence?"),
            (
                "assistant",
                "AI is a field of computer science focused on creating intelligent machines.",
            ),
            ("user", "What are some applications of AI?"),
            (
                "assistant",
                "AI is used in healthcare, finance, transportation, and many other fields.",
            ),
            ("user", "How does machine learning relate to AI?"),
            (
                "assistant",
                "Machine learning is a subset of AI that learns patterns from data.",
            ),
        ]

        for message_type, content in messages:
            try:
                added = self.client.add_chat_message(
                    session_id=session_id,
                    message_type=message_type,
                    content=content,
                    metadata={"timestamp": datetime.now().isoformat()},
                )

                if added:
                    print(f"   ✅ {message_type}: {content[:50]}...")
                else:
                    print(f"   ❌ Failed to add {message_type} message")

            except Exception as e:
                print(f"   ❌ Message addition failed: {e}")

        print("\n3. Retrieving chat history...")
        try:
            history = self.client.get_chat_history(session_id, limit=10)

            print(f"   📜 Chat history ({len(history)} messages):")
            for i, message in enumerate(history, 1):
                msg_type = message.get("message_type", "unknown")
                content = message.get("content", "")[:50]
                print(f"      {i}. [{msg_type}] {content}...")

        except Exception as e:
            print(f"   ❌ History retrieval failed: {e}")

        print("\n4. Listing chat sessions...")
        try:
            sessions = self.client.get_chat_sessions(user_id=self.user_id, limit=5)

            print(f"   📋 User sessions ({len(sessions)} found):")
            for i, session in enumerate(sessions, 1):
                session_id_short = session.get("session_id", "")[:20]
                created_at = session.get("created_at", "")
                print(f"      {i}. {session_id_short}... (created: {created_at})")

        except Exception as e:
            print(f"   ❌ Session listing failed: {e}")

    def example_5_utilities_and_maintenance(self):
        """Example 5: Utilities and maintenance operations."""
        print("\n" + "=" * 60)
        print("🛠️ EXAMPLE 5: Utilities and Maintenance")
        print("=" * 60)

        print("\n1. Database statistics...")
        try:
            maintenance_tool = SupabaseMaintenanceTool(self.client)
            db_stats = maintenance_tool.get_database_statistics()

            print("   📊 Database statistics:")
            for key, value in db_stats.items():
                print(f"      {key}: {value}")

        except Exception as e:
            print(f"   ❌ Database statistics failed: {e}")

        print("\n2. Memory analytics...")
        try:
            stats = self.client.get_memory_statistics()

            print("   📈 Memory analytics:")
            print(f"      Total memories: {stats.get('total_memories', 0)}")
            print(
                f"      Average importance: {stats.get('avg_importance_score', 0):.2f}"
            )

            categories = stats.get("categories", {})
            if categories:
                print("      Categories:")
                for category, count in categories.items():
                    print(f"         {category}: {count}")

        except Exception as e:
            print(f"   ❌ Memory analytics failed: {e}")

        print("\n3. Backup operations (demo)...")
        try:
            backup_tool = SupabaseBackupTool(self.client)

            # For demo purposes, we'll just show that the tool can be initialized
            print("   💾 Backup tool initialized successfully")
            print("      (In a real scenario, you would call create_backup())")

        except Exception as e:
            print(f"   ❌ Backup tool failed: {e}")

    def example_6_advanced_search(self):
        """Example 6: Advanced search capabilities."""
        print("\n" + "=" * 60)
        print("🔍 EXAMPLE 6: Advanced Search Capabilities")
        print("=" * 60)

        # Create some specialized memories for search demonstration
        print("\n1. Creating specialized memories for search demo...")

        specialized_memories = [
            {
                "content": "Neural networks are computing systems inspired by biological neural networks.",
                "context": "Deep Learning",
                "category": "AI",
                "keywords": ["neural networks", "deep learning", "AI"],
                "tags": ["machine learning", "neural", "artificial intelligence"],
                "importance_score": 0.9,
            },
            {
                "content": "Transformers revolutionized natural language processing with attention mechanisms.",
                "context": "NLP Research",
                "category": "AI",
                "keywords": ["transformers", "NLP", "attention"],
                "tags": ["language models", "attention", "transformer"],
                "importance_score": 0.95,
            },
            {
                "content": "Docker containers provide lightweight virtualization for application deployment.",
                "context": "DevOps",
                "category": "Technology",
                "keywords": ["docker", "containers", "deployment"],
                "tags": ["devops", "virtualization", "deployment"],
                "importance_score": 0.8,
            },
        ]

        search_memory_ids = []
        for i, memory_data in enumerate(specialized_memories, 1):
            try:
                memory_id = self.client.create_memory(
                    user_id=self.user_id, **memory_data
                )
                search_memory_ids.append(memory_id)
                print(f"   ✅ Search demo memory {i} created")

            except Exception as e:
                print(f"   ❌ Failed to create search demo memory {i}: {e}")

        # Wait a moment for indexing
        print("\n   ⏳ Waiting for indexing...")
        time.sleep(2)

        print("\n2. Performing advanced searches...")

        # Hybrid search (combines text and semantic search)
        print("\n   🔍 Hybrid search for 'artificial intelligence':")
        try:
            hybrid_results = self.client.hybrid_search_memories(
                query="artificial intelligence",
                limit=5,
                semantic_weight=0.7,  # 70% semantic, 30% text
                user_id=self.user_id,
            )

            if hybrid_results:
                for i, result in enumerate(hybrid_results, 1):
                    print(f"      {i}. {result['content'][:60]}...")
                    print(
                        f"         Score: {result.get('similarity_score', 'N/A'):.3f}"
                    )
            else:
                print("      No results found")

        except Exception as e:
            print(f"   ❌ Hybrid search failed: {e}")

        # Similarity threshold search
        print("\n   🎯 High similarity search (threshold > 0.8):")
        try:
            # First get an embedding for comparison
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("all-MiniLM-L6-v2")
            query_embedding = model.encode(["machine learning algorithms"]).tolist()[0]

            similar_results = self.client.search_memories_by_embedding(
                embedding=query_embedding,
                similarity_threshold=0.1,  # Lower threshold for demo
                limit=3,
                user_id=self.user_id,
            )

            if similar_results:
                for i, result in enumerate(similar_results, 1):
                    print(f"      {i}. {result['content'][:60]}...")
                    print(f"         Similarity: {result.get('similarity', 'N/A'):.3f}")
            else:
                print("      No high-similarity results found")

        except Exception as e:
            print(f"   ❌ Similarity search failed: {e}")

        # Multi-tag search
        print("\n   🏷️ Multi-tag search (AI + machine learning):")
        try:
            tag_results = self.client.get_memories_by_tags(
                tags=["artificial intelligence", "machine learning"],
                match_all=False,  # Match any of the tags
                limit=5,
                user_id=self.user_id,
            )

            if tag_results:
                for i, result in enumerate(tag_results, 1):
                    print(f"      {i}. {result['content'][:60]}...")
                    print(f"         Tags: {result.get('tags', [])}")
            else:
                print("      No tagged results found")

        except Exception as e:
            print(f"   ❌ Multi-tag search failed: {e}")

    def cleanup_demo_data(self):
        """Clean up the demo data."""
        print("\n🧹 Cleaning up demo data...")

        try:
            # Get all memories for this user
            all_memories = self.client.search_memories_by_text(
                query="", limit=100, user_id=self.user_id  # Empty query to get all
            )

            deleted_count = 0
            for memory in all_memories:
                if self.client.delete_memory(memory["id"]):
                    deleted_count += 1

            print(f"   ✅ Cleaned up {deleted_count} demo memories")

        except Exception as e:
            print(f"   ❌ Cleanup failed: {e}")

    def run_all_examples(self):
        """Run all examples."""
        print("=" * 70)
        print("  SUPABASE DATABASE EXAMPLES")
        print("=" * 70)
        print(f"Demo User ID: {self.user_id}")
        print("This will demonstrate various Supabase database operations.")

        if not self.setup():
            print("❌ Setup failed. Cannot run examples.")
            return False

        try:
            # Run all examples
            self.example_1_basic_memory_operations()
            self.example_2_search_and_retrieval()
            self.example_3_memory_system_usage()
            self.example_4_chat_sessions()
            self.example_5_utilities_and_maintenance()
            self.example_6_advanced_search()

        except KeyboardInterrupt:
            print("\n\n⏹️ Examples interrupted by user")
        except Exception as e:
            print(f"\n❌ Example failed: {e}")
        finally:
            # Always try to clean up
            self.cleanup_demo_data()

        print("\n" + "=" * 70)
        print("✨ Examples completed!")
        print("=" * 70)
        print("\nThese examples show how to:")
        print("• Create and manage memories in Supabase")
        print("• Perform various types of searches")
        print("• Use the AgenticMemory system with Supabase")
        print("• Manage chat sessions and messages")
        print("• Use utility and maintenance tools")
        print("• Perform advanced search operations")

        return True


def main():
    """Main function to run the examples."""
    print("Supabase Database Examples")
    print("This will demonstrate how to use the Supabase database components.")
    print("\nMake sure your environment is configured:")
    print("- SUPABASE_URL, SUPABASE_ANON_KEY, OPENAI_API_KEY")
    print("- Database schema has been applied")
    print("- All dependencies are installed")

    choice = input("\nDo you want to run the examples? (y/n): ").lower().strip()

    if choice in ["y", "yes"]:
        examples = SupabaseDatabaseExamples()
        examples.run_all_examples()
    else:
        print("Examples cancelled.")


if __name__ == "__main__":
    main()
