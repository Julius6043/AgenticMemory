"""
Supabase client for AgenticMemory system.

This module provides a comprehensive interface for interacting with
Supabase database for memory storage, retrieval, and management.
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from dataclasses import asdict

try:
    from supabase import create_client, Client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Supabase client not available. Install with: pip install supabase")

from .supabase_config import SupabaseConfigManager, SupabaseConfig


class SupabaseMemoryClient:
    """Client for interacting with Supabase database for memory storage."""

    def __init__(self, config: Optional[SupabaseConfig] = None):
        """Initialize Supabase client.

        Args:
            config: Supabase configuration. If None, loads from environment.
        """
        if not SUPABASE_AVAILABLE:
            raise ImportError(
                "Supabase client not available. Install with: pip install supabase"
            )

        self.config = config or SupabaseConfigManager.get_config()
        self.client: Client = create_client(self.config.url, self.config.key)

        # Table names
        self.memories_table = SupabaseConfigManager.MEMORIES_TABLE
        self.memory_links_table = SupabaseConfigManager.MEMORY_LINKS_TABLE
        self.chat_sessions_table = SupabaseConfigManager.CHAT_SESSIONS_TABLE
        self.chat_messages_table = SupabaseConfigManager.CHAT_MESSAGES_TABLE
        self.memory_stats_table = SupabaseConfigManager.MEMORY_STATS_TABLE

    def test_connection(self) -> bool:
        """Test connection to Supabase.

        Returns:
            bool: True if connection successful
        """
        try:
            # Try to fetch one record from memories table
            result = (
                self.client.table(self.memories_table)
                .select("id")
                .range(0, 0)
                .execute()
            )
            return True
        except Exception as e:
            print(f"Supabase connection test failed: {e}")
            return False

    # =============================================================================
    # MEMORY OPERATIONS
    # =============================================================================

    def create_memory(self, memory_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new memory in Supabase.

        Args:
            memory_data: Dictionary containing memory data

        Returns:
            Dict with memory data including ID if successful, None otherwise
        """
        # Prepare the data for insertion
        prepared_data = {
            "content": memory_data.get("content", ""),
            "context": memory_data.get("context", "General"),
            "category": memory_data.get("category", "Uncategorized"),
            "keywords": memory_data.get("keywords", []),
            "tags": memory_data.get("tags", []),
            "importance_score": memory_data.get("importance_score", 1.0),
            "user_id": memory_data.get("user_id"),
            "session_id": memory_data.get("session_id"),
            "linked_memory_ids": memory_data.get("linked_memory_ids", []),
            "evolution_count": memory_data.get("evolution_count", 0),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
        }

        # Handle embedding conversion
        embedding = memory_data.get("embedding")
        if embedding:
            try:
                if isinstance(embedding, list):
                    prepared_data["embedding"] = embedding
                elif isinstance(embedding, np.ndarray):
                    prepared_data["embedding"] = embedding.tolist()
                else:
                    prepared_data["embedding"] = embedding
            except Exception as e:
                print(f"Warning: Failed to set embedding: {e}")

        try:
            result = (
                self.client.table(self.memories_table).insert(prepared_data).execute()
            )

            if result.data:
                return result.data[0]
            else:
                print("Failed to create memory: No data returned")
                return None

        except Exception as e:
            print(f"Failed to create memory: {e}")
            return None

    def get_memory(
        self, memory_id: str, increment_count: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get a memory by ID.

        Args:
            memory_id: Memory ID
            increment_count: Whether to increment retrieval count

        Returns:
            Dict or None: Memory data
        """
        try:
            result = (
                self.client.table(self.memories_table)
                .select("*")
                .eq("id", memory_id)
                .execute()
            )

            if result.data:
                # Only increment retrieval count if explicitly requested
                if increment_count:
                    self.increment_retrieval_count(memory_id)
                return result.data[0]
            return None

        except Exception as e:
            print(f"Failed to get memory {memory_id}: {e}")
            return None

    def _get_memory_without_count(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a memory by ID without incrementing retrieval count (for internal use).

        Args:
            memory_id: Memory ID

        Returns:
            Dict or None: Memory data
        """
        return self.get_memory(memory_id, increment_count=False)

    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory.

        Args:
            memory_id: Memory ID
            updates: Dictionary of updates

        Returns:
            bool: True if successful
        """
        try:
            # Add updated timestamp
            updates["updated_at"] = datetime.now().isoformat()

            result = (
                self.client.table(self.memories_table)
                .update(updates)
                .eq("id", memory_id)
                .execute()
            )

            return bool(result.data)

        except Exception as e:
            print(f"Failed to update memory {memory_id}: {e}")
            return False

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory.

        Args:
            memory_id: Memory ID

        Returns:
            bool: True if successful
        """
        try:
            result = (
                self.client.table(self.memories_table)
                .delete()
                .eq("id", memory_id)
                .execute()
            )
            return bool(result.data)

        except Exception as e:
            print(f"Failed to delete memory {memory_id}: {e}")
            return False

    def search_memories_by_text(
        self, query: str, limit: int = 10, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search memories using full-text search.

        Args:
            query: Search query
            limit: Maximum number of results
            user_id: Filter by user ID

        Returns:
            List of memory dictionaries
        """
        try:
            # Build query
            query_builder = self.client.table(self.memories_table).select("*")

            # Add text search if query is provided
            if query.strip():
                # Use ilike for simple text search (fallback if tsvector fails)
                query_builder = query_builder.ilike("content", f"%{query}%")

            # Filter by user if provided
            if user_id:
                query_builder = query_builder.eq("user_id", user_id)

            # Execute with limit
            result = query_builder.range(0, limit - 1).execute()

            # Don't increment retrieval counts for search operations - only for explicit gets
            return result.data or []

        except Exception as e:
            print(f"Failed to search memories by text: {e}")
            return []

    def search_memories_by_embedding(
        self,
        embedding: List[float],
        similarity_threshold: float = 0.5,
        limit: int = 10,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search memories using vector similarity.

        Args:
            embedding: Query embedding vector
            similarity_threshold: Minimum similarity threshold
            limit: Maximum number of results
            user_id: Filter by user ID

        Returns:
            List of memory dictionaries with similarity scores
        """
        try:
            # Convert embedding to PostgreSQL vector format
            embedding_str = f"[{','.join(map(str, embedding))}]"

            # Use direct SQL query through RPC or fall back to text search
            try:
                result = self.client.rpc(
                    "search_similar_memories",
                    {
                        "query_embedding": embedding_str,
                        "similarity_threshold": similarity_threshold,
                        "max_results": limit,
                        "filter_user_id": user_id,
                    },
                ).execute()
            except Exception:
                # Fallback to simple text search if RPC fails
                print("RPC search failed, falling back to text search")
                return self.search_memories_by_text("", limit=limit, user_id=user_id)

            # No need to filter by user anymore since it's done in SQL
            # Don't increment retrieval counts for embedding search operations
            return result.data or []

        except Exception as e:
            print(f"Failed to search memories by embedding: {e}")
            # Fallback to text search
            return self.search_memories_by_text("", limit=limit, user_id=user_id)

    def hybrid_search_memories(
        self,
        query: str,
        embedding: Optional[List[float]] = None,
        limit: int = 10,
        semantic_weight: float = 0.5,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Hybrid search combining text and semantic search.

        Args:
            query: Search query text
            embedding: Query embedding vector
            limit: Maximum number of results
            semantic_weight: Weight for semantic vs text search (0-1)
            user_id: Filter by user ID

        Returns:
            List of memory dictionaries with combined scores
        """
        try:
            # Try RPC function first
            embedding_str = None
            if embedding:
                embedding_str = f"[{','.join(map(str, embedding))}]"

            try:
                result = self.client.rpc(
                    "hybrid_search_memories",
                    {
                        "search_query": query,
                        "query_embedding": embedding_str,
                        "max_results": limit,
                        "semantic_weight": semantic_weight,
                        "filter_user_id": user_id,
                    },
                ).execute()
            except Exception:
                # Fallback to text search if RPC fails
                print("RPC hybrid search failed, falling back to text search")
                return self.search_memories_by_text(query, limit=limit, user_id=user_id)

            # No need to filter by user anymore since it's done in SQL
            # Don't increment retrieval counts for hybrid search operations
            return result.data or []

        except Exception as e:
            print(f"Failed to hybrid search memories: {e}")
            # Fallback to text search
            return self.search_memories_by_text(query, limit=limit, user_id=user_id)

    def search_similar_memories(
        self,
        embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.5,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar memories using embedding vector.

        This is a convenience method that wraps search_memories_by_embedding
        to match the interface expected by the SupabaseRetriever.

        Args:
            embedding: Query embedding vector
            limit: Maximum number of results
            similarity_threshold: Minimum similarity threshold
            user_id: Filter by user ID

        Returns:
            List of memory dictionaries with similarity scores
        """
        return self.search_memories_by_embedding(
            embedding=embedding,
            similarity_threshold=similarity_threshold,
            limit=limit,
            user_id=user_id,
        )

    def get_memories_by_category(
        self, category: str, limit: int = 50, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get memories by category.

        Args:
            category: Memory category
            limit: Maximum number of results
            user_id: Filter by user ID

        Returns:
            List of memory dictionaries
        """
        try:
            query_builder = (
                self.client.table(self.memories_table)
                .select("*")
                .eq("category", category)
            )

            if user_id:
                query_builder = query_builder.eq("user_id", user_id)

            result = query_builder.range(0, limit - 1).execute()
            return result.data or []

        except Exception as e:
            print(f"Failed to get memories by category: {e}")
            return []

    def get_memories_by_tags(
        self,
        tags: List[str],
        match_all: bool = False,
        limit: int = 50,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get memories by tags.

        Args:
            tags: List of tags to search for
            match_all: If True, memory must have all tags. If False, any tag.
            limit: Maximum number of results
            user_id: Filter by user ID

        Returns:
            List of memory dictionaries
        """
        try:
            query_builder = self.client.table(self.memories_table).select("*")

            if match_all:
                # Memory must contain all tags
                query_builder = query_builder.contains("tags", tags)
            else:
                # Memory must contain at least one tag
                query_builder = query_builder.overlaps("tags", tags)

            if user_id:
                query_builder = query_builder.eq("user_id", user_id)

            result = query_builder.range(0, limit - 1).execute()
            return result.data or []

        except Exception as e:
            print(f"Failed to get memories by tags: {e}")
            return []

    def increment_retrieval_count(self, memory_id: str) -> bool:
        """Increment retrieval count for a memory.

        Args:
            memory_id: Memory ID

        Returns:
            bool: True if successful
        """
        try:
            # Try RPC function first
            try:
                result = self.client.rpc(
                    "increment_retrieval_count", {"memory_id": memory_id}
                ).execute()
                return True
            except Exception:
                # Fallback to direct update if RPC fails
                pass

            # Fallback: Get current count, increment, and update
            memory = self._get_memory_without_count(memory_id)
            if memory:
                new_count = memory.get("retrieval_count", 0) + 1
                current_time = datetime.now().isoformat()

                result = (
                    self.client.table(self.memories_table)
                    .update(
                        {"retrieval_count": new_count, "last_accessed": current_time}
                    )
                    .eq("id", memory_id)
                    .execute()
                )

                return bool(result.data)

            return False

        except Exception as e:
            print(f"Failed to increment retrieval count: {e}")
            return False

    # =============================================================================
    # MEMORY LINK OPERATIONS
    # =============================================================================

    def create_memory_link(
        self,
        source_memory_id: str,
        target_memory_id: str,
        link_type: str = "related",
        strength: float = 1.0,
    ) -> Optional[str]:
        """Create a link between two memories.

        Args:
            source_memory_id: ID of the source memory
            target_memory_id: ID of the target memory
            link_type: Type of relationship
            strength: Strength of the relationship

        Returns:
            Link ID if successful, None otherwise
        """
        try:
            link_data = {
                "source_memory_id": source_memory_id,
                "target_memory_id": target_memory_id,
                "link_type": link_type,
                "strength": strength,
            }

            result = (
                self.client.table(self.memory_links_table).insert(link_data).execute()
            )

            if result.data:
                link_id = result.data[0]["id"]

                # Update the linked_memory_ids array in both memories
                self._update_linked_memory_ids(source_memory_id, target_memory_id)
                self._update_linked_memory_ids(target_memory_id, source_memory_id)

                return str(link_id)
            return None

        except Exception as e:
            print(f"Error creating memory link: {e}")
            return None

    def _update_linked_memory_ids(self, memory_id: str, linked_id: str):
        """Update the linked_memory_ids array in a memory.

        Args:
            memory_id: ID of the memory to update
            linked_id: ID of the memory to link to
        """
        try:
            # Get current memory to access existing links
            current_memory = self.get_memory(memory_id)
            if current_memory:
                current_links = current_memory.get("linked_memory_ids", [])
                if linked_id not in current_links:
                    current_links.append(linked_id)

                    # Update the memory with new links
                    self.client.table(self.memories_table).update(
                        {"linked_memory_ids": current_links}
                    ).eq("id", memory_id).execute()

        except Exception as e:
            print(f"Error updating linked memory IDs: {e}")

    def get_memory_links(self, memory_id: str) -> List[Dict[str, Any]]:
        """Get all links for a specific memory.

        Args:
            memory_id: Memory ID

        Returns:
            List of memory links
        """
        try:
            # Get links where this memory is the source
            outgoing_links = (
                self.client.table(self.memory_links_table)
                .select("*")
                .eq("source_memory_id", memory_id)
                .execute()
            )

            # Get links where this memory is the target
            incoming_links = (
                self.client.table(self.memory_links_table)
                .select("*")
                .eq("target_memory_id", memory_id)
                .execute()
            )

            all_links = []
            if outgoing_links.data:
                all_links.extend(outgoing_links.data)
            if incoming_links.data:
                all_links.extend(incoming_links.data)

            return all_links

        except Exception as e:
            print(f"Error getting memory links: {e}")
            return []

    def delete_memory_link(self, link_id: str) -> bool:
        """Delete a memory link.

        Args:
            link_id: Link ID to delete

        Returns:
            True if successful
        """
        try:
            # Get the link first to update linked_memory_ids
            link_result = (
                self.client.table(self.memory_links_table)
                .select("*")
                .eq("id", link_id)
                .execute()
            )

            if link_result.data:
                link = link_result.data[0]
                source_id = link["source_memory_id"]
                target_id = link["target_memory_id"]

                # Remove from linked_memory_ids arrays
                self._remove_linked_memory_id(source_id, target_id)
                self._remove_linked_memory_id(target_id, source_id)

            # Delete the link
            result = (
                self.client.table(self.memory_links_table)
                .delete()
                .eq("id", link_id)
                .execute()
            )
            return True

        except Exception as e:
            print(f"Error deleting memory link: {e}")
            return False

    def _remove_linked_memory_id(self, memory_id: str, linked_id: str):
        """Remove a linked memory ID from a memory's linked_memory_ids array.

        Args:
            memory_id: ID of the memory to update
            linked_id: ID of the memory to unlink
        """
        try:
            # Get current memory to access existing links
            current_memory = self.get_memory(memory_id)
            if current_memory:
                current_links = current_memory.get("linked_memory_ids", [])
                if linked_id in current_links:
                    current_links.remove(linked_id)

                    # Update the memory with new links
                    self.client.table(self.memories_table).update(
                        {"linked_memory_ids": current_links}
                    ).eq("id", memory_id).execute()

        except Exception as e:
            print(f"Error removing linked memory ID: {e}")

    def get_linked_memories(
        self, memory_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get all memories linked to a specific memory.

        Args:
            memory_id: Memory ID
            limit: Maximum number of linked memories to return

        Returns:
            List of linked memories
        """
        try:
            # Get the memory to access its linked_memory_ids
            memory = self.get_memory(memory_id)
            if not memory or not memory.get("linked_memory_ids"):
                return []

            linked_ids = memory["linked_memory_ids"][:limit]

            # Fetch the linked memories
            linked_memories = []
            for linked_id in linked_ids:
                linked_memory = self.get_memory(linked_id)
                if linked_memory:
                    linked_memories.append(linked_memory)

            return linked_memories

        except Exception as e:
            print(f"Error getting linked memories: {e}")
            return []

    # =============================================================================
    # CHAT OPERATIONS
    # =============================================================================

    def create_chat_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create a new chat session or ensure it exists.

        Args:
            session_id: Session identifier
            user_id: User identifier
            metadata: Additional metadata

        Returns:
            bool: True if successful or session already exists
        """
        try:
            # Check if session already exists
            existing = (
                self.client.table(self.chat_sessions_table)
                .select("id")
                .eq("session_id", session_id)
                .execute()
            )

            if existing.data:
                # Session already exists, return success
                return True

            # Create new session
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "metadata": metadata or {},
            }

            result = (
                self.client.table(self.chat_sessions_table)
                .insert(session_data)
                .execute()
            )
            return bool(result.data)

        except Exception as e:
            print(f"Failed to create chat session: {e}")
            return False

    def add_chat_message(
        self,
        session_id: str,
        message_type: str,
        content: str,
        memory_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add a message to a chat session.

        Args:
            session_id: Session identifier
            message_type: Type of message ('user', 'assistant', 'system')
            content: Message content
            memory_ids: Related memory IDs
            metadata: Additional metadata

        Returns:
            bool: True if successful
        """
        try:
            message_data = {
                "session_id": session_id,
                "message_type": message_type,
                "content": content,
                "memory_ids": memory_ids or [],
                "metadata": metadata or {},
            }

            result = (
                self.client.table(self.chat_messages_table)
                .insert(message_data)
                .execute()
            )
            return bool(result.data)

        except Exception as e:
            print(f"Failed to add chat message: {e}")
            return False

    def get_chat_history(
        self, session_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get chat history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages

        Returns:
            List of message dictionaries
        """
        try:
            result = (
                self.client.table(self.chat_messages_table)
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=False)
                .range(0, limit - 1)
                .execute()
            )

            return result.data

        except Exception as e:
            print(f"Failed to get chat history: {e}")
            return []

    def get_chat_sessions(
        self, user_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get chat sessions.

        Args:
            user_id: Filter by user ID
            limit: Maximum number of sessions

        Returns:
            List of session dictionaries
        """
        try:
            query_builder = self.client.table(self.chat_sessions_table).select("*")

            if user_id:
                query_builder = query_builder.eq("user_id", user_id)

            result = (
                query_builder.order("updated_at", desc=True)
                .range(0, limit - 1)
                .execute()
            )
            return result.data

        except Exception as e:
            print(f"Failed to get chat sessions: {e}")
            return []

    # =============================================================================
    # STATISTICS AND ANALYTICS
    # =============================================================================

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics.

        Returns:
            Dict: Statistics dictionary
        """
        try:
            # Get total count
            total_result = (
                self.client.table(self.memories_table)
                .select("id", count="exact")
                .execute()
            )
            total_memories = total_result.count or 0

            # Get count by category
            category_result = (
                self.client.table(self.memories_table).select("category").execute()
            )

            categories = {}
            for memory in category_result.data:
                category = (
                    memory.get("category") or "Uncategorized"
                )  # Handle None values
                categories[category] = categories.get(category, 0) + 1

            # Get count by user
            user_result = (
                self.client.table(self.memories_table).select("user_id").execute()
            )

            users = {}
            for memory in user_result.data:
                user_id = memory.get("user_id") or "anonymous"  # Handle None values
                users[user_id] = users.get(user_id, 0) + 1

            return {
                "total_memories": total_memories,
                "categories": categories,
                "users": users,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            print(f"Failed to get memory statistics: {e}")
            # Return default stats
            return {
                "total_memories": 0,
                "categories": {},
                "users": {},
                "timestamp": datetime.now().isoformat(),
            }

    def get_user_memory_count(self, user_id: str) -> int:
        """Get memory count for a user.

        Args:
            user_id: User identifier

        Returns:
            int: Memory count
        """
        try:
            result = (
                self.client.table(self.memories_table)
                .select("id", count="exact")
                .eq("user_id", user_id)
                .execute()
            )

            return result.count or 0

        except Exception as e:
            print(f"Failed to get user memory count: {e}")
            return 0

    def get_popular_memories(
        self, limit: int = 10, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get most retrieved memories.

        Args:
            limit: Maximum number of results
            user_id: Filter by user ID

        Returns:
            List of memory dictionaries
        """
        try:
            query_builder = self.client.table(self.memories_table).select("*")

            if user_id:
                query_builder = query_builder.eq("user_id", user_id)

            result = (
                query_builder.order("retrieval_count", desc=True)
                .range(0, limit - 1)
                .execute()
            )
            return result.data

        except Exception as e:
            print(f"Failed to get popular memories: {e}")
            return []

    # =============================================================================
    # UTILITY METHODS
    # =============================================================================

    def bulk_create_memories(self, memories: List[Dict[str, Any]]) -> List[str]:
        """Create multiple memories in bulk.

        Args:
            memories: List of memory dictionaries

        Returns:
            List of created memory IDs
        """
        try:
            # Add timestamps to all memories
            for memory in memories:
                memory.setdefault("created_at", datetime.now().isoformat())
                memory.setdefault("updated_at", datetime.now().isoformat())
                memory.setdefault("last_accessed", datetime.now().isoformat())

            result = self.client.table(self.memories_table).insert(memories).execute()

            if result.data:
                return [str(mem["id"]) for mem in result.data]
            return []

        except Exception as e:
            print(f"Failed to bulk create memories: {e}")
            return []

    def cleanup_old_memories(
        self, days_old: int = 365, min_retrieval_count: int = 0
    ) -> int:
        """Clean up old, unused memories.

        Args:
            days_old: Delete memories older than this many days
            min_retrieval_count: Only delete if retrieval count is below this

        Returns:
            int: Number of memories deleted
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()

            # Delete old memories with low retrieval count
            result = (
                self.client.table(self.memories_table)
                .delete()
                .lt("created_at", cutoff_iso)
                .lte("retrieval_count", min_retrieval_count)
                .execute()
            )

            return len(result.data) if result.data else 0

        except Exception as e:
            print(f"Failed to cleanup old memories: {e}")
            return 0
