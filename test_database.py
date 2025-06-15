#!/usr/bin/env python3
"""
Test script for Supabase database components.

This script tests the core Supabase database functionality without using the Flask API.
It directly tests the database client, memory adapter, and utilities.
"""

import os
import sys
import uuid
import time
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


class SupabaseDatabaseTester:
    """Comprehensive test suite for Supabase database components."""

    def __init__(self):
        """Initialize the tester with test data."""
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        self.test_session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        self.client = None
        self.memory_system = None
        self.created_memory_ids = []

    def setup(self):
        """Set up the test environment."""
        print("🔧 Setting up test environment...")

        try:
            # Test configuration
            print("   - Testing configuration...")
            if not SupabaseConfigManager.validate_config():
                print("   ❌ Configuration validation failed")
                return False

            # Initialize client
            print("   - Initializing Supabase client...")
            self.client = SupabaseMemoryClient()

            # Test connection
            print("   - Testing connection...")
            if not self.client.test_connection():
                print("   ❌ Connection test failed")
                return False

            # Initialize memory system
            print("   - Initializing memory system...")
            self.memory_system = SupabaseAgenticMemorySystem(
                user_id=self.test_user_id,
                model_name="all-MiniLM-L6-v2",
                llm_backend="openai",
                llm_model="gpt-4o-mini",
            )

            print("   ✅ Setup completed successfully")
            return True

        except Exception as e:
            print(f"   ❌ Setup failed: {e}")
            return False

    def test_supabase_client(self):
        """Test the Supabase client functionality."""
        print("\n📊 Testing Supabase Client...")

        test_results = {
            "create_memory": False,
            "get_memory": False,
            "update_memory": False,
            "search_memories": False,
            "chat_operations": False,
            "statistics": False,
        }

        try:
            # Test 1: Create memory
            print("   1. Testing memory creation...")
            memory_id = self.client.create_memory(
                content="Python is a high-level programming language known for its simplicity and readability.",
                context="Programming Knowledge",
                category="Technology",
                keywords=["python", "programming", "language"],
                tags=["coding", "development"],
                importance_score=0.8,
                user_id=self.test_user_id,
            )

            if memory_id:
                self.created_memory_ids.append(memory_id)
                print(f"      ✅ Memory created: {memory_id}")
                test_results["create_memory"] = True
            else:
                print("      ❌ Failed to create memory")

        except Exception as e:
            print(f"      ❌ Memory creation failed: {e}")

        try:
            # Test 2: Get memory
            print("   2. Testing memory retrieval...")
            if self.created_memory_ids:
                memory = self.client.get_memory(self.created_memory_ids[0])
                if memory and memory.get("content"):
                    print(f"      ✅ Memory retrieved: {memory['content'][:50]}...")
                    test_results["get_memory"] = True
                else:
                    print("      ❌ Failed to retrieve memory")
            else:
                print("      ⏭️ Skipped (no memory ID available)")

        except Exception as e:
            print(f"      ❌ Memory retrieval failed: {e}")

        try:
            # Test 3: Update memory
            print("   3. Testing memory update...")
            if self.created_memory_ids:
                updated = self.client.update_memory(
                    self.created_memory_ids[0],
                    {
                        "importance_score": 0.9,
                        "tags": ["coding", "development", "updated"],
                    },
                )
                if updated:
                    print("      ✅ Memory updated successfully")
                    test_results["update_memory"] = True
                else:
                    print("      ❌ Failed to update memory")
            else:
                print("      ⏭️ Skipped (no memory ID available)")

        except Exception as e:
            print(f"      ❌ Memory update failed: {e}")

        try:
            # Test 4: Search memories
            print("   4. Testing memory search...")

            # Text search
            text_results = self.client.search_memories_by_text(
                query="Python programming", limit=5, user_id=self.test_user_id
            )

            if text_results:
                print(f"      ✅ Text search found {len(text_results)} results")
                test_results["search_memories"] = True
            else:
                print("      ❌ Text search returned no results")

        except Exception as e:
            print(f"      ❌ Memory search failed: {e}")

        try:
            # Test 5: Chat operations
            print("   5. Testing chat operations...")

            # Create chat session
            session_created = self.client.create_chat_session(
                session_id=self.test_session_id,
                user_id=self.test_user_id,
                metadata={"test": True},
            )

            if session_created:
                # Add chat message
                message_added = self.client.add_chat_message(
                    session_id=self.test_session_id,
                    message_type="user",
                    content="Hello, this is a test message",
                )

                if message_added:
                    print("      ✅ Chat operations successful")
                    test_results["chat_operations"] = True
                else:
                    print("      ❌ Failed to add chat message")
            else:
                print("      ❌ Failed to create chat session")

        except Exception as e:
            print(f"      ❌ Chat operations failed: {e}")

        try:
            # Test 6: Statistics
            print("   6. Testing statistics...")
            stats = self.client.get_memory_statistics()

            if stats and "total_memories" in stats:
                print(
                    f"      ✅ Statistics retrieved: {stats['total_memories']} total memories"
                )
                test_results["statistics"] = True
            else:
                print("      ❌ Failed to get statistics")

        except Exception as e:
            print(f"      ❌ Statistics failed: {e}")

        return test_results

    def test_memory_adapter(self):
        """Test the Supabase memory adapter."""
        print("\n🧠 Testing Memory Adapter...")

        test_results = {
            "add_note": False,
            "get_related_memories": False,
            "search_memories": False,
            "get_statistics": False,
        }

        try:
            # Test 1: Add note
            print("   1. Testing add note...")
            note_id = self.memory_system.add_note(
                content="Machine learning is a subset of artificial intelligence that focuses on algorithms.",
                context="AI Knowledge",
                category="Technology",
            )

            if note_id:
                self.created_memory_ids.append(note_id)
                print(f"      ✅ Note added: {note_id}")
                test_results["add_note"] = True
            else:
                print("      ❌ Failed to add note")

        except Exception as e:
            print(f"      ❌ Add note failed: {e}")

        try:
            # Test 2: Get related memories
            print("   2. Testing related memories...")
            related = self.memory_system.get_related_memories(
                "programming languages", k=3
            )

            if related:
                print(f"      ✅ Found {len(related)} related memories")
                test_results["get_related_memories"] = True
            else:
                print("      ❌ No related memories found")

        except Exception as e:
            print(f"      ❌ Related memories failed: {e}")

        try:
            # Test 3: Search memories
            print("   3. Testing memory search...")
            search_results = self.memory_system.search_memories(
                "artificial intelligence", k=5
            )

            if search_results:
                print(f"      ✅ Search found {len(search_results)} results")
                test_results["search_memories"] = True
            else:
                print("      ❌ Search returned no results")

        except Exception as e:
            print(f"      ❌ Memory search failed: {e}")

        try:
            # Test 4: Get statistics
            print("   4. Testing statistics...")
            stats = self.memory_system.get_memory_statistics()

            if stats and "total_memories" in stats:
                print(f"      ✅ Statistics: {stats}")
                test_results["get_statistics"] = True
            else:
                print("      ❌ Failed to get statistics")

        except Exception as e:
            print(f"      ❌ Statistics failed: {e}")

        return test_results

    def test_utilities(self):
        """Test the utility functions."""
        print("\n🛠️ Testing Utilities...")

        test_results = {
            "backup_tool": False,
            "maintenance_tool": False,
            "migration_tool": False,
        }

        try:
            # Test 1: Backup tool
            print("   1. Testing backup tool...")
            backup_tool = SupabaseBackupTool(self.client)

            # We'll just test initialization for now
            if backup_tool:
                print("      ✅ Backup tool initialized")
                test_results["backup_tool"] = True
            else:
                print("      ❌ Failed to initialize backup tool")

        except Exception as e:
            print(f"      ❌ Backup tool failed: {e}")

        try:
            # Test 2: Maintenance tool
            print("   2. Testing maintenance tool...")
            maintenance_tool = SupabaseMaintenanceTool(self.client)

            # Test database statistics
            db_stats = maintenance_tool.get_database_statistics()
            if db_stats:
                print(f"      ✅ Database statistics: {len(db_stats)} metrics")
                test_results["maintenance_tool"] = True
            else:
                print("      ❌ Failed to get database statistics")

        except Exception as e:
            print(f"      ❌ Maintenance tool failed: {e}")

        try:
            # Test 3: Migration tool
            print("   3. Testing migration tool...")
            migration_tool = SupabaseMigrationTool(self.client)

            if migration_tool:
                print("      ✅ Migration tool initialized")
                test_results["migration_tool"] = True
            else:
                print("      ❌ Failed to initialize migration tool")

        except Exception as e:
            print(f"      ❌ Migration tool failed: {e}")

        return test_results

    def cleanup(self):
        """Clean up test data."""
        print("\n🧹 Cleaning up test data...")

        try:
            # Delete created memories
            deleted_count = 0
            for memory_id in self.created_memory_ids:
                if self.client.delete_memory(memory_id):
                    deleted_count += 1

            print(
                f"   ✅ Deleted {deleted_count}/{len(self.created_memory_ids)} test memories"
            )

        except Exception as e:
            print(f"   ❌ Cleanup failed: {e}")

    def run_all_tests(self):
        """Run the complete test suite."""
        print("=" * 70)
        print("  SUPABASE DATABASE COMPONENTS TEST SUITE")
        print("=" * 70)

        # Setup
        if not self.setup():
            print("❌ Setup failed. Cannot continue with tests.")
            return False

        all_results = {}

        # Run tests
        print(f"\n👤 Testing with user ID: {self.test_user_id}")

        # Test Supabase client
        client_results = self.test_supabase_client()
        all_results.update(client_results)

        # Test memory adapter
        adapter_results = self.test_memory_adapter()
        all_results.update(adapter_results)

        # Test utilities
        utility_results = self.test_utilities()
        all_results.update(utility_results)

        # Cleanup
        self.cleanup()

        # Summary
        print("\n" + "=" * 70)
        print("  TEST RESULTS SUMMARY")
        print("=" * 70)

        passed = 0
        total = len(all_results)

        print("\n📊 Supabase Client:")
        for test in [
            "create_memory",
            "get_memory",
            "update_memory",
            "search_memories",
            "chat_operations",
            "statistics",
        ]:
            if test in all_results:
                status = "✅ PASS" if all_results[test] else "❌ FAIL"
                print(f"   {test:20} : {status}")
                if all_results[test]:
                    passed += 1

        print("\n🧠 Memory Adapter:")
        for test in [
            "add_note",
            "get_related_memories",
            "search_memories",
            "get_statistics",
        ]:
            if test in all_results:
                status = "✅ PASS" if all_results[test] else "❌ FAIL"
                print(f"   {test:20} : {status}")
                if all_results[test]:
                    passed += 1

        print("\n🛠️ Utilities:")
        for test in ["backup_tool", "maintenance_tool", "migration_tool"]:
            if test in all_results:
                status = "✅ PASS" if all_results[test] else "❌ FAIL"
                print(f"   {test:20} : {status}")
                if all_results[test]:
                    passed += 1

        print(f"\n🎯 Overall Result: {passed}/{total} tests passed")

        if passed == total:
            print(
                "🎉 All tests passed! Supabase database integration is working correctly."
            )
            return True
        else:
            print(
                "❌ Some tests failed. Please check the configuration and database setup."
            )
            return False


def main():
    """Main function to run the test suite."""
    print("Supabase Database Components Test Suite")
    print("This will test the database functionality without using the Flask API.")
    print("\nMake sure your Supabase configuration is set up correctly:")
    print("- SUPABASE_URL")
    print("- SUPABASE_ANON_KEY")
    print("- OPENAI_API_KEY")
    print("- Database schema has been applied")

    input("\nPress Enter to start the tests...")

    tester = SupabaseDatabaseTester()
    success = tester.run_all_tests()

    if success:
        print("\n✨ Database components are ready for use!")
    else:
        print("\n🔧 Please fix the issues before proceeding.")

    return success


if __name__ == "__main__":
    main()
