"""
Supabase Memory Adapter for AgenticMemory System.

This module provides an adapter that integrates Supabase database
with the existing AgenticMemory system, replacing local storage
with persistent cloud storage.
"""

import json
import uuid
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import numpy as np

# Import AgenticMemory components
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from memory import MemoryNote, AgenticMemorySystem
from retrievers import SimpleEmbeddingRetriever
from llm_controllers import LLMController
from sentence_transformers import SentenceTransformer

# Import Supabase components
from .supabase_client import SupabaseMemoryClient
from .supabase_config import SupabaseConfigManager


class SupabaseMemoryNote(MemoryNote):
    """Extended MemoryNote that works with Supabase storage."""

    def __init__(self, supabase_data: Dict[str, Any], **kwargs):
        """Initialize from Supabase data.

        Args:
            supabase_data: Dictionary from Supabase database
            **kwargs: Additional parameters
        """
        # Convert Supabase data to MemoryNote format
        super().__init__(
            content=supabase_data.get("content", ""),
            id=str(supabase_data.get("id", str(uuid.uuid4()))),
            keywords=supabase_data.get("keywords", []),
            links=supabase_data.get("links", []),
            importance_score=supabase_data.get("importance_score", 1.0),
            retrieval_count=supabase_data.get("retrieval_count", 0),
            timestamp=supabase_data.get("created_at", datetime.now().isoformat()),
            last_accessed=supabase_data.get(
                "last_accessed", datetime.now().isoformat()
            ),
            context=supabase_data.get("context", "General"),
            evolution_history=supabase_data.get("evolution_history", []),
            category=supabase_data.get("category", "Uncategorized"),
            tags=supabase_data.get("tags", []),
            **kwargs,
        )

        # Store additional Supabase-specific data
        self.supabase_data = supabase_data
        self.embedding = supabase_data.get("embedding")
        self.user_id = supabase_data.get("user_id")
        self.session_id = supabase_data.get("session_id")
        self.updated_at = supabase_data.get("updated_at")


class SupabaseRetriever:
    """Retriever that uses Supabase for memory search."""

    def __init__(
        self,
        supabase_client: SupabaseMemoryClient,
        embedding_model: Optional[SentenceTransformer] = None,
        user_id: Optional[str] = None,
    ):
        """Initialize Supabase retriever.

        Args:
            supabase_client: Supabase client instance
            embedding_model: SentenceTransformer for generating embeddings
            user_id: User ID for filtering
        """
        self.client = supabase_client
        self.user_id = user_id
        self.embedding_model = embedding_model or SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    def search(self, query: str, k: int = 5) -> List[int]:
        """Search for similar memories.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of memory indices (for compatibility)
        """
        # Generate embedding for the query
        query_embedding = self.embedding_model.encode([query])[0].tolist()

        # Search using hybrid search
        results = self.client.hybrid_search_memories(
            query=query, embedding=query_embedding, limit=k, user_id=self.user_id
        )

        # Return indices (for compatibility with existing code)
        return list(range(len(results)))

    def add_documents(self, documents: List[str]):
        """Add documents to the retriever (no-op for Supabase)."""
        # Documents are added directly through create_memory
        pass


class SupabaseAgenticMemorySystem(AgenticMemorySystem):
    """AgenticMemory system with Supabase backend."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        llm_backend: str = "openai",
        llm_model: str = "gpt-4o-mini",
        evo_threshold: int = 100,
        api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        supabase_client: Optional[SupabaseMemoryClient] = None,
    ):
        """Initialize Supabase-backed memory system.

        Args:
            model_name: Sentence transformer model name
            llm_backend: LLM backend ("openai" or "ollama")
            llm_model: Specific model name
            evo_threshold: Number of evolutions before consolidation
            api_key: API key for LLM backend
            user_id: User ID for memory isolation
            supabase_client: Optional Supabase client instance
        """
        # Initialize base components
        self.llm_controller = LLMController(llm_backend, llm_model, api_key)
        self.embedding_model = SentenceTransformer(model_name)
        self.user_id = user_id

        # Initialize Supabase client
        self.supabase_client = supabase_client or SupabaseMemoryClient()

        # Test connection
        if not self.supabase_client.test_connection():
            raise ConnectionError("Failed to connect to Supabase")

        # Initialize retriever
        self.retriever = SupabaseRetriever(
            self.supabase_client, self.embedding_model, user_id
        )

        # Memory cache for performance
        self.memory_cache: Dict[str, SupabaseMemoryNote] = {}

        # Evolution settings
        self.evo_cnt = 0
        self.evo_threshold = evo_threshold
        self.evolution_system_prompt = """
        You are an AI memory evolution agent responsible for managing and evolving a knowledge base.
        Analyze the new memory note according to keywords and context, also with their several nearest neighbors memory.
        Make decisions about its evolution.  

        The new memory context:
        {context}
        content: {content}
        keywords: {keywords}

        The nearest neighbors memories:
        {nearest_neighbors_memories}

        Based on this information, determine:
        1. Should this memory be evolved? Consider its relationships with other memories.
        2. What specific actions should be taken (strengthen, update_neighbor)?
           2.1 If choose to strengthen the connection, which memory should it be connected to? Can you give the updated tags of this memory?
           2.2 If choose to update_neighbor, you can update the context and tags of these memories based on the understanding of these memories. If the context and the tags are not updated, the new context and tags should be the same as the original ones. Generate the new context and tags in the sequential order of the input neighbors.
        Tags should be determined by the content of these characteristic of these memories, which can be used to retrieve them later and categorize them.
        Note that the length of new_tags_neighborhood must equal the number of input neighbors, and the length of new_context_neighborhood must equal the number of input neighbors.
        The number of neighbors is {neighbor_number}.
        Return your decision in JSON format with the following structure:
        {{
            "should_evolve": true or false,
            "actions": ["strengthen", "update_neighbor"],
            "suggested_connections": [neighbor_memory_indices],
            "tags_to_update": ["tag_1",...,"tag_n"], 
            "new_context_neighborhood": ["new context",...,"new context"],
            "new_tags_neighborhood": [["tag_1",...,"tag_n"],...["tag_1",...,"tag_n"]],
        }}
        """

    @property
    def memories(self) -> Dict[str, SupabaseMemoryNote]:
        """Get memories dictionary (for compatibility)."""
        return self.memory_cache

    def add_note(self, content: str, time: str = None, **kwargs) -> str:
        """Add a new memory note to Supabase.

        Args:
            content: Main content of the memory
            time: Timestamp (auto-generated if None)
            **kwargs: Additional memory note parameters

        Returns:
            String ID of the created memory note
        """
        # Generate metadata using LLM if not provided
        context = kwargs.get("context")
        category = kwargs.get("category")
        keywords = kwargs.get("keywords")
        tags = kwargs.get("tags")

        if any(param is None for param in [context, category, keywords, tags]):
            try:
                metadata = MemoryNote.analyze_content(content, self.llm_controller)
                context = context or metadata.get("context", "General")
                category = category or metadata.get("category", "Uncategorized")
                keywords = keywords or metadata.get("keywords", [])
                tags = tags or metadata.get("tags", [])
            except Exception as e:
                print(f"Failed to analyze content with LLM: {e}")
                # Use defaults
                context = context or "General"
                category = category or "Uncategorized"
                keywords = keywords or []
                tags = tags or []

        # Generate embedding
        embedding = self.embedding_model.encode([content])[0].tolist()

        # Create memory in Supabase
        memory_id = self.supabase_client.create_memory(
            content=content,
            embedding=embedding,
            context=context,
            category=category,
            keywords=keywords,
            tags=tags,
            user_id=self.user_id,
            **kwargs,
        )

        # Load memory into cache
        memory_data = self.supabase_client.get_memory(memory_id)
        if memory_data:
            memory_note = SupabaseMemoryNote(memory_data)
            self.memory_cache[memory_id] = memory_note

            # Process evolution
            try:
                evo_label, updated_note = self.process_memory(memory_note)
                if evo_label:
                    self.evo_cnt += 1
                    if self.evo_cnt >= self.evo_threshold:
                        self.consolidate_memories()
                        self.evo_cnt = 0
            except Exception as e:
                print(f"Evolution processing failed: {e}")

        return memory_id

    def get_memory(self, memory_id: str) -> Optional[SupabaseMemoryNote]:
        """Get a memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            SupabaseMemoryNote or None
        """
        # Check cache first
        if memory_id in self.memory_cache:
            return self.memory_cache[memory_id]

        # Load from Supabase
        memory_data = self.supabase_client.get_memory(memory_id)
        if memory_data:
            memory_note = SupabaseMemoryNote(memory_data)
            self.memory_cache[memory_id] = memory_note
            return memory_note

        return None

    def get_related_memories(self, query: str, k: int = 5) -> List[SupabaseMemoryNote]:
        """Get related memories using Supabase search.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of SupabaseMemoryNote objects
        """
        # Generate embedding for query
        query_embedding = self.embedding_model.encode([query])[0].tolist()

        # Search using hybrid search
        results = self.supabase_client.hybrid_search_memories(
            query=query, embedding=query_embedding, limit=k, user_id=self.user_id
        )

        # Convert to SupabaseMemoryNote objects
        memory_notes = []
        for result in results:
            memory_note = SupabaseMemoryNote(result)
            # Cache the memory
            self.memory_cache[memory_note.id] = memory_note
            memory_notes.append(memory_note)

        return memory_notes

    def find_related_memories(self, query: str, k: int = 5) -> Tuple[str, List[int]]:
        """Find related memories and return formatted string.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            Tuple of (formatted_string, indices_list)
        """
        related_memories = self.get_related_memories(query, k)

        # Format memories for display
        formatted_memories = []
        indices = []

        for i, memory in enumerate(related_memories):
            formatted_memory = f"Memory {i+1}:\nContent: {memory.content}\nContext: {memory.context}\nKeywords: {', '.join(memory.keywords)}\nTags: {', '.join(memory.tags)}\n"
            formatted_memories.append(formatted_memory)
            indices.append(i)

        return "\n".join(formatted_memories), indices

    def process_memory(
        self, note: SupabaseMemoryNote
    ) -> Tuple[bool, SupabaseMemoryNote]:
        """Process a memory note and determine evolution actions.

        Args:
            note: Memory note to process

        Returns:
            Tuple of (should_evolve, processed_note)
        """
        try:
            neighbor_memory, indices = self.find_related_memories(note.content, k=5)
            prompt_memory = self.evolution_system_prompt.format(
                context=note.context,
                content=note.content,
                keywords=note.keywords,
                nearest_neighbors_memories=neighbor_memory,
                neighbor_number=len(indices),
            )

            response = self.llm_controller.llm.get_completion(
                prompt_memory,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "response",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "should_evolve": {"type": "boolean"},
                                "actions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "suggested_connections": {
                                    "type": "array",
                                    "items": {"type": "integer"},
                                },
                                "new_context_neighborhood": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "tags_to_update": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "new_tags_neighborhood": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                            },
                            "required": [
                                "should_evolve",
                                "actions",
                                "suggested_connections",
                                "tags_to_update",
                                "new_context_neighborhood",
                                "new_tags_neighborhood",
                            ],
                            "additionalProperties": False,
                        },
                        "strict": True,
                    },
                },
            )

            try:
                response_json = json.loads(response)
            except json.JSONDecodeError:
                print("Failed to parse evolution response as JSON")
                return False, note

            should_evolve = response_json.get("should_evolve", False)

            if should_evolve:
                # Process evolution actions
                actions = response_json.get("actions", [])

                if "strengthen" in actions:
                    # Update memory tags
                    new_tags = response_json.get("tags_to_update", note.tags)
                    updates = {"tags": new_tags}
                    self.supabase_client.update_memory(note.id, updates)
                    note.tags = new_tags

                if "update_neighbor" in actions:
                    # Update neighbor memories
                    related_memories = self.get_related_memories(note.content, k=5)
                    new_contexts = response_json.get("new_context_neighborhood", [])
                    new_tags_list = response_json.get("new_tags_neighborhood", [])

                    for i, memory in enumerate(related_memories[: len(new_contexts)]):
                        if i < len(new_contexts) and i < len(new_tags_list):
                            updates = {
                                "context": new_contexts[i],
                                "tags": new_tags_list[i],
                            }
                            self.supabase_client.update_memory(memory.id, updates)

                            # Update cache
                            if memory.id in self.memory_cache:
                                self.memory_cache[memory.id].context = new_contexts[i]
                                self.memory_cache[memory.id].tags = new_tags_list[i]

                # Create memory links
                suggested_connections = response_json.get("suggested_connections", [])
                related_memories = self.get_related_memories(note.content, k=5)

                for conn_idx in suggested_connections:
                    if 0 <= conn_idx < len(related_memories):
                        target_memory = related_memories[conn_idx]
                        self.supabase_client.create_memory_link(
                            note.id, target_memory.id, "evolved_connection"
                        )

            return should_evolve, note

        except Exception as e:
            print(f"Error in process_memory: {e}")
            return False, note

    def consolidate_memories(self):
        """Consolidate memories (clear cache to force refresh)."""
        print("Consolidating memories - clearing cache")
        self.memory_cache.clear()

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics from Supabase.

        Returns:
            Dict: Statistics dictionary
        """
        return self.supabase_client.get_memory_statistics()

    def search_memories(self, query: str, k: int = 5) -> List[SupabaseMemoryNote]:
        """Search memories by text query.

        Args:
            query: Search query
            k: Number of results

        Returns:
            List of SupabaseMemoryNote objects
        """
        results = self.supabase_client.search_memories_by_text(
            query=query, limit=k, user_id=self.user_id
        )

        memory_notes = []
        for result in results:
            memory_note = SupabaseMemoryNote(result)
            self.memory_cache[memory_note.id] = memory_note
            memory_notes.append(memory_note)

        return memory_notes

    def get_memories_by_category(
        self, category: str, limit: int = 50
    ) -> List[SupabaseMemoryNote]:
        """Get memories by category.

        Args:
            category: Memory category
            limit: Maximum results

        Returns:
            List of SupabaseMemoryNote objects
        """
        results = self.supabase_client.get_memories_by_category(
            category=category, limit=limit, user_id=self.user_id
        )

        memory_notes = []
        for result in results:
            memory_note = SupabaseMemoryNote(result)
            self.memory_cache[memory_note.id] = memory_note
            memory_notes.append(memory_note)

        return memory_notes

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory.

        Args:
            memory_id: Memory ID

        Returns:
            bool: True if successful
        """
        success = self.supabase_client.delete_memory(memory_id)
        if success and memory_id in self.memory_cache:
            del self.memory_cache[memory_id]
        return success
