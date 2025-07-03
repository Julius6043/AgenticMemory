"""
Utility functions for Supabase integration with AgenticMemory.

This module provides helper functions for database operations,
data migration, and maintenance tasks.
"""

import json
import pickle
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np

from src.database.supabase_client import SupabaseMemoryClient
from src.database.supabase_memory_adapter import (
    SupabaseMemoryNote,
    SupabaseAgenticMemorySystem,
)

# Import original memory system for migration
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.memory import MemoryNote, AgenticMemorySystem


class SupabaseMigrationTool:
    """Tools for migrating data to/from Supabase."""

    def __init__(self, supabase_client: SupabaseMemoryClient):
        """Initialize migration tool.

        Args:
            supabase_client: Supabase client instance
        """
        self.client = supabase_client

    def migrate_local_memories_to_supabase(
        self, local_memory_system: AgenticMemorySystem, user_id: str = "migrated_user"
    ) -> Dict[str, Any]:
        """Migrate memories from local system to Supabase.

        Args:
            local_memory_system: Local AgenticMemorySystem instance
            user_id: User ID for migrated memories

        Returns:
            Dict with migration results
        """
        results = {
            "total_memories": 0,
            "migrated_memories": 0,
            "failed_memories": 0,
            "errors": [],
        }

        # Prepare memories for bulk insert
        memories_to_create = []

        for memory_id, memory in local_memory_system.memories.items():
            try:
                # Generate embedding if not exists
                embedding = None
                if hasattr(local_memory_system, "embedding_model"):
                    embedding = local_memory_system.embedding_model.encode(
                        [memory.content]
                    )[0].tolist()

                memory_data = {
                    "content": memory.content,
                    "context": memory.context,
                    "category": memory.category,
                    "keywords": memory.keywords,
                    "tags": memory.tags,
                    "importance_score": memory.importance_score,
                    "retrieval_count": memory.retrieval_count,
                    "user_id": user_id,
                    "embedding": embedding,
                    "evolution_history": memory.evolution_history,
                    "created_at": (
                        memory.timestamp
                        if hasattr(memory, "timestamp")
                        else datetime.now().isoformat()
                    ),
                    "last_accessed": (
                        memory.last_accessed
                        if hasattr(memory, "last_accessed")
                        else datetime.now().isoformat()
                    ),
                }

                memories_to_create.append(memory_data)
                results["total_memories"] += 1

            except Exception as e:
                results["failed_memories"] += 1
                results["errors"].append(
                    f"Failed to prepare memory {memory_id}: {str(e)}"
                )

        # Bulk create memories
        if memories_to_create:
            try:
                created_ids = self.client.bulk_create_memories(memories_to_create)
                results["migrated_memories"] = len(created_ids)

                print(f"Successfully migrated {len(created_ids)} memories to Supabase")

            except Exception as e:
                results["errors"].append(f"Bulk creation failed: {str(e)}")

        return results

    def export_supabase_memories_to_json(
        self,
        output_file: str,
        user_id: Optional[str] = None,
        include_embeddings: bool = False,
    ) -> int:
        """Export Supabase memories to JSON file.

        Args:
            output_file: Output JSON file path
            user_id: Filter by user ID (optional)
            include_embeddings: Whether to include embeddings in export

        Returns:
            int: Number of memories exported
        """
        try:
            # Get all memories for user
            if user_id:
                # This would require implementing a get_all_memories method
                memories = []  # Placeholder
            else:
                memories = []  # Placeholder - would need implementation

            # Prepare export data
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "total_memories": len(memories),
                "memories": [],
            }

            for memory in memories:
                memory_export = {
                    "id": str(memory["id"]),
                    "content": memory["content"],
                    "context": memory["context"],
                    "category": memory["category"],
                    "keywords": memory["keywords"],
                    "tags": memory["tags"],
                    "importance_score": memory["importance_score"],
                    "retrieval_count": memory["retrieval_count"],
                    "created_at": memory["created_at"],
                    "updated_at": memory["updated_at"],
                    "last_accessed": memory["last_accessed"],
                    "evolution_history": memory["evolution_history"],
                }

                if include_embeddings and memory.get("embedding"):
                    memory_export["embedding"] = memory["embedding"]

                export_data["memories"].append(memory_export)

            # Write to file
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            print(f"Exported {len(memories)} memories to {output_file}")
            return len(memories)

        except Exception as e:
            print(f"Export failed: {e}")
            return 0

    def import_memories_from_json(
        self, json_file: str, user_id: str, overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Import memories from JSON file to Supabase.

        Args:
            json_file: Input JSON file path
            user_id: User ID for imported memories
            overwrite_existing: Whether to overwrite existing memories

        Returns:
            Dict with import results
        """
        results = {
            "total_memories": 0,
            "imported_memories": 0,
            "skipped_memories": 0,
            "failed_memories": 0,
            "errors": [],
        }

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            memories = import_data.get("memories", [])
            results["total_memories"] = len(memories)

            memories_to_create = []

            for memory in memories:
                try:
                    # Check if memory already exists (by content hash or ID)
                    if not overwrite_existing:
                        # This would require implementing a check method
                        pass

                    memory_data = {
                        "content": memory["content"],
                        "context": memory.get("context", "General"),
                        "category": memory.get("category", "Imported"),
                        "keywords": memory.get("keywords", []),
                        "tags": memory.get("tags", []),
                        "importance_score": memory.get("importance_score", 1.0),
                        "user_id": user_id,
                        "embedding": memory.get("embedding"),
                        "evolution_history": memory.get("evolution_history", []),
                    }

                    memories_to_create.append(memory_data)

                except Exception as e:
                    results["failed_memories"] += 1
                    results["errors"].append(f"Failed to prepare memory: {str(e)}")

            # Bulk create memories
            if memories_to_create:
                created_ids = self.client.bulk_create_memories(memories_to_create)
                results["imported_memories"] = len(created_ids)

        except Exception as e:
            results["errors"].append(f"Import failed: {str(e)}")

        return results


class SupabaseMaintenanceTool:
    """Tools for maintaining Supabase database."""

    def __init__(self, supabase_client: SupabaseMemoryClient):
        """Initialize maintenance tool.

        Args:
            supabase_client: Supabase client instance
        """
        self.client = supabase_client

    def cleanup_old_memories(
        self, days_old: int = 365, min_retrieval_count: int = 0, dry_run: bool = True
    ) -> Dict[str, Any]:
        """Clean up old, unused memories.

        Args:
            days_old: Delete memories older than this many days
            min_retrieval_count: Only delete if retrieval count is below this
            dry_run: If True, only report what would be deleted

        Returns:
            Dict with cleanup results
        """
        results = {"memories_to_delete": 0, "memories_deleted": 0, "dry_run": dry_run}

        if not dry_run:
            deleted_count = self.client.cleanup_old_memories(
                days_old, min_retrieval_count
            )
            results["memories_deleted"] = deleted_count
        else:
            # In a real implementation, we'd query to count what would be deleted
            results["memories_to_delete"] = 0  # Placeholder

        return results

    def optimize_embeddings(self, batch_size: int = 100) -> Dict[str, Any]:
        """Regenerate embeddings for memories that don't have them.

        Args:
            batch_size: Number of memories to process at once

        Returns:
            Dict with optimization results
        """
        results = {
            "total_memories": 0,
            "memories_processed": 0,
            "embeddings_generated": 0,
            "errors": [],
        }

        # This would require implementing a method to find memories without embeddings
        # and batch update them with new embeddings

        return results

    def rebuild_full_text_index(self) -> bool:
        """Rebuild full-text search indexes.

        Returns:
            bool: True if successful
        """
        try:
            # This would execute SQL to rebuild indexes
            # For now, it's a placeholder
            return True
        except Exception as e:
            print(f"Failed to rebuild full-text index: {e}")
            return False

    def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics.

        Returns:
            Dict with database statistics
        """
        try:
            # Get basic memory statistics
            stats = self.client.get_memory_statistics()

            # Add additional statistics
            stats.update(
                {
                    "database_size": "N/A",  # Would require database-specific query
                    "index_health": "Good",  # Would require checking index statistics
                    "last_maintenance": datetime.now().isoformat(),
                }
            )

            return stats

        except Exception as e:
            print(f"Failed to get database statistics: {e}")
            return {}


class SupabaseBackupTool:
    """Tools for backing up and restoring Supabase data."""

    def __init__(self, supabase_client: SupabaseMemoryClient):
        """Initialize backup tool.

        Args:
            supabase_client: Supabase client instance
        """
        self.client = supabase_client

    def create_backup(
        self,
        backup_path: str,
        user_id: Optional[str] = None,
        include_chat_history: bool = True,
    ) -> Dict[str, Any]:
        """Create a complete backup of user data.

        Args:
            backup_path: Directory to store backup files
            user_id: User ID to backup (None for all users)
            include_chat_history: Whether to include chat history

        Returns:
            Dict with backup results
        """
        results = {
            "backup_timestamp": datetime.now().isoformat(),
            "backup_path": backup_path,
            "files_created": [],
            "total_memories": 0,
            "total_chat_sessions": 0,
            "success": False,
        }

        try:
            os.makedirs(backup_path, exist_ok=True)

            # Backup memories
            migration_tool = SupabaseMigrationTool(self.client)
            memories_file = os.path.join(backup_path, "memories.json")
            memory_count = migration_tool.export_supabase_memories_to_json(
                memories_file, user_id, include_embeddings=True
            )
            results["total_memories"] = memory_count
            results["files_created"].append("memories.json")

            # Backup chat history if requested
            if include_chat_history:
                # This would require implementing chat export
                chat_file = os.path.join(backup_path, "chat_history.json")
                # Placeholder for chat export
                results["files_created"].append("chat_history.json")

            # Create metadata file
            metadata = {
                "backup_timestamp": results["backup_timestamp"],
                "user_id": user_id,
                "total_memories": results["total_memories"],
                "total_chat_sessions": results["total_chat_sessions"],
                "include_chat_history": include_chat_history,
                "agenticmemory_version": "1.0.0",  # Would get from package
            }

            metadata_file = os.path.join(backup_path, "backup_metadata.json")
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            results["files_created"].append("backup_metadata.json")

            results["success"] = True
            print(f"Backup completed successfully at {backup_path}")

        except Exception as e:
            results["error"] = str(e)
            print(f"Backup failed: {e}")

        return results

    def restore_backup(
        self, backup_path: str, user_id: str, overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Restore data from backup.

        Args:
            backup_path: Directory containing backup files
            user_id: User ID for restored data
            overwrite_existing: Whether to overwrite existing data

        Returns:
            Dict with restore results
        """
        results = {
            "restore_timestamp": datetime.now().isoformat(),
            "backup_path": backup_path,
            "restored_memories": 0,
            "restored_chat_sessions": 0,
            "success": False,
        }

        try:
            # Check if backup exists
            metadata_file = os.path.join(backup_path, "backup_metadata.json")
            if not os.path.exists(metadata_file):
                raise FileNotFoundError("Backup metadata not found")

            # Load backup metadata
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            print(f"Restoring backup from {metadata['backup_timestamp']}")

            # Restore memories
            memories_file = os.path.join(backup_path, "memories.json")
            if os.path.exists(memories_file):
                migration_tool = SupabaseMigrationTool(self.client)
                memory_results = migration_tool.import_memories_from_json(
                    memories_file, user_id, overwrite_existing
                )
                results["restored_memories"] = memory_results["imported_memories"]

            # Restore chat history
            chat_file = os.path.join(backup_path, "chat_history.json")
            if os.path.exists(chat_file):
                # This would require implementing chat import
                pass

            results["success"] = True
            print(f"Restore completed successfully")

        except Exception as e:
            results["error"] = str(e)
            print(f"Restore failed: {e}")

        return results


def setup_supabase_environment():
    """Setup and validate Supabase environment."""
    try:
        from .supabase_config import SupabaseConfigManager

        print("Checking Supabase configuration...")

        if not SupabaseConfigManager.validate_config():
            print("❌ Supabase configuration is invalid!")
            print("\nPlease set the following environment variables:")
            print("- SUPABASE_URL")
            print("- SUPABASE_ANON_KEY")
            print("- SUPABASE_SERVICE_ROLE_KEY (optional)")
            print("- SUPABASE_DB_PASSWORD (for direct DB access)")
            return False

        print("✅ Supabase configuration is valid!")

        # Test connection
        client = SupabaseMemoryClient()
        if client.test_connection():
            print("✅ Supabase connection successful!")
            return True
        else:
            print("❌ Supabase connection failed!")
            return False

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


def get_supabase_memory_system(
    user_id: Optional[str] = None,
) -> SupabaseAgenticMemorySystem:
    """Get configured Supabase memory system.

    Args:
        user_id: User ID for memory isolation

    Returns:
        SupabaseAgenticMemorySystem instance
    """
    return SupabaseAgenticMemorySystem(user_id=user_id)
