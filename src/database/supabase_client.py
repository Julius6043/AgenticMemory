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
                self.client.table(self.memories_table).select("id").limit(1).execute()
            )
            return True
        except Exception as e:
            print(f"Supabase connection test failed: {e}")
            return False

    # =============================================================================
    # MEMORY OPERATIONS
    # =============================================================================

    def create_memory(
        self,
        content: str,
        embedding: Optional[List[float]] = None,
        context: str = "General",
        category: str = "Uncategorized",
        keywords: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        importance_score: float = 1.0,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Create a new memory in Supabase.

        Args:
            content: Memory content
            embedding: Vector embedding for semantic search
            context: Memory context
            category: Memory category
            keywords: List of keywords
            tags: List of tags
            importance_score: Importance score
            user_id: User identifier
            session_id: Session identifier
            **kwargs: Additional metadata

        Returns:
            str: Memory ID
        """
        memory_data = {
            "content": content,
            "context": context,
            "category": category,
            "keywords": keywords or [],
            "tags": tags or [],
            "importance_score": importance_score,
            "user_id": user_id,
            "session_id": session_id,
            "embedding": embedding,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
        }

        # Add any additional metadata
        for key, value in kwargs.items():
            if key not in memory_data:
                memory_data[key] = value

        try:
            result = (
                self.client.table(self.memories_table).insert(memory_data).execute()
            )

            if result.data:
                return str(result.data[0]["id"])
            else:
                raise Exception("Failed to create memory: No data returned")

        except Exception as e:
            raise Exception(f"Failed to create memory: {e}")

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a memory by ID.

        Args:
            memory_id: Memory ID

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
                # Increment retrieval count
                self.increment_retrieval_count(memory_id)
                return result.data[0]
            return None

        except Exception as e:
            print(f"Failed to get memory {memory_id}: {e}")
            return None

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

            # Add text search (using PostgreSQL full-text search)
            query_builder = query_builder.text_search("content_tsvector", query)

            # Filter by user if provided
            if user_id:
                query_builder = query_builder.eq("user_id", user_id)

            # Limit results
            query_builder = query_builder.limit(limit)

            result = query_builder.execute()

            # Increment retrieval counts for found memories
            for memory in result.data:
                self.increment_retrieval_count(memory["id"])

            return result.data

        except Exception as e:
            print(f"Failed to search memories: {e}")
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
            # Use RPC to call the search function
            result = self.client.rpc(
                "search_similar_memories",
                {
                    "query_embedding": embedding,
                    "similarity_threshold": similarity_threshold,
                    "max_results": limit,
                },
            ).execute()

            # Filter by user if provided
            if user_id:
                result.data = [
                    mem for mem in result.data if mem.get("user_id") == user_id
                ]

            # Increment retrieval counts for found memories
            for memory in result.data:
                self.increment_retrieval_count(memory["id"])

            return result.data

        except Exception as e:
            print(f"Failed to search memories by embedding: {e}")
            return []

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
            # Use RPC to call the hybrid search function
            result = self.client.rpc(
                "hybrid_search_memories",
                {
                    "search_query": query,
                    "query_embedding": embedding,
                    "max_results": limit,
                    "semantic_weight": semantic_weight,
                },
            ).execute()

            # Filter by user if provided
            if user_id:
                result.data = [
                    mem for mem in result.data if mem.get("user_id") == user_id
                ]

            # Increment retrieval counts for found memories
            for memory in result.data:
                self.increment_retrieval_count(memory["id"])

            return result.data

        except Exception as e:
            print(f"Failed to hybrid search memories: {e}")
            return []

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

            result = query_builder.limit(limit).execute()
            return result.data

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

            result = query_builder.limit(limit).execute()
            return result.data

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
            # Use RPC to call the increment function
            result = self.client.rpc(
                "increment_retrieval_count", {"memory_id": memory_id}
            ).execute()

            return True

        except Exception as e:
            print(f"Failed to increment retrieval count: {e}")
            return False

    # =============================================================================
    # MEMORY LINKS OPERATIONS
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
            source_memory_id: Source memory ID
            target_memory_id: Target memory ID
            link_type: Type of link
            strength: Link strength

        Returns:
            str or None: Link ID if successful
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
                return str(result.data[0]["id"])
            return None

        except Exception as e:
            print(f"Failed to create memory link: {e}")
            return None

    def get_memory_links(self, memory_id: str) -> List[Dict[str, Any]]:
        """Get all links for a memory.

        Args:
            memory_id: Memory ID

        Returns:
            List of link dictionaries
        """
        try:
            # Get outgoing links
            outgoing = (
                self.client.table(self.memory_links_table)
                .select("*")
                .eq("source_memory_id", memory_id)
                .execute()
            )

            # Get incoming links
            incoming = (
                self.client.table(self.memory_links_table)
                .select("*")
                .eq("target_memory_id", memory_id)
                .execute()
            )

            return outgoing.data + incoming.data

        except Exception as e:
            print(f"Failed to get memory links: {e}")
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
        """Create a new chat session.

        Args:
            session_id: Session identifier
            user_id: User identifier
            metadata: Additional metadata

        Returns:
            bool: True if successful
        """
        try:
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
                .limit(limit)
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

            result = query_builder.order("updated_at", desc=True).limit(limit).execute()
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
            # Use RPC to call the statistics function
            result = self.client.rpc("get_memory_statistics").execute()

            if result.data:
                return result.data[0] if isinstance(result.data, list) else result.data
            return {}

        except Exception as e:
            print(f"Failed to get memory statistics: {e}")
            return {}

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
                query_builder.order("retrieval_count", desc=True).limit(limit).execute()
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
