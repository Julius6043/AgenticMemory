"""
Enhanced Supabase Memory Adapter for AgenticMemory System.

This module provides an improved adapter that integrates Supabase database
with the AgenticMemory system, incorporating lessons from the Ground_version
and adding robust memory linking and evolution capabilities.
"""

import json
import uuid
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import numpy as np

# Import AgenticMemory components
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.memory import MemoryNote
from src.llm_controllers import LLMController
from sentence_transformers import SentenceTransformer

# Import Supabase components
from src.database.supabase_client import SupabaseMemoryClient
from src.database.supabase_config import SupabaseConfigManager

logger = logging.getLogger(__name__)


class SupabaseMemoryNote(MemoryNote):
    """Enhanced MemoryNote that works with Supabase storage and includes full metadata."""

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
            links=supabase_data.get(
                "linked_memory_ids", []
            ),  # Use linked_memory_ids from DB
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
        self.evolution_count = supabase_data.get("evolution_count", 0)


class SupabaseRetriever:
    """Enhanced retriever that uses Supabase for memory search."""

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

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar memories and return structured results.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of memory dictionaries
        """
        # Generate embedding for the query
        query_embedding = self.embedding_model.encode([query])[0].tolist()

        # Search using hybrid search
        results = self.client.search_similar_memories(
            embedding=query_embedding, limit=k, user_id=self.user_id
        )

        return results

    def add_documents(self, documents: List[str]):
        """Add documents to the retriever (no-op for Supabase)."""
        # Documents are added directly through create_memory
        pass


class SupabaseAgenticMemorySystem:
    """Enhanced AgenticMemory system with Supabase backend and improved evolution."""

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
        self.model_name = model_name

        # Initialize Supabase client
        self.supabase_client = supabase_client or SupabaseMemoryClient()

        # Test connection
        if not self.supabase_client.test_connection():
            raise ConnectionError("Failed to connect to Supabase")

        # Initialize retriever
        self.retriever = SupabaseRetriever(
            self.supabase_client, self.embedding_model, user_id
        )

        # Memory cache for performance (similar to Ground_version approach)
        self.memories: Dict[str, SupabaseMemoryNote] = {}

        # Evolution settings
        self.evo_cnt = 0
        self.evo_threshold = evo_threshold

        # Enhanced evolution system prompt from Ground_version
        self._evolution_system_prompt = """
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
            "suggested_connections": ["neighbor_memory_ids"],
            "tags_to_update": ["tag_1",...,"tag_n"], 
            "new_context_neighborhood": ["new context",...,"new context"],
            "new_tags_neighborhood": [["tag_1",...,"tag_n"],...["tag_1",...,"tag_n"]],
        }}
        """

    def analyze_content(self, content: str) -> Dict:
        """Analyze content using LLM to extract semantic metadata.

        Args:
            content (str): The text content to analyze

        Returns:
            Dict: Contains extracted metadata with keys:
                - keywords: List[str]
                - context: str
                - tags: List[str]
        """
        prompt = (
            """Generate a structured analysis of the following content by:
            1. Identifying the most salient keywords (focus on nouns, verbs, and key concepts)
            2. Extracting core themes and contextual elements
            3. Creating relevant categorical tags

            Format the response as a JSON object:
            {
                "keywords": [
                    // several specific, distinct keywords that capture key concepts and terminology
                    // Order from most to least important
                    // Don't include keywords that are the name of the speaker or time
                    // At least three keywords, but don't be too redundant.
                ],
                "context": 
                    // one sentence summarizing:
                    // - Main topic/domain
                    // - Key arguments/points
                    // - Intended audience/purpose
                ,
                "tags": [
                    // several broad categories/themes for classification
                    // Include domain, format, and type tags
                    // At least three tags, but don't be too redundant.
                ]
            }

            Content for analysis:
            """
            + content
        )
        try:
            response = self.llm_controller.llm.get_completion(
                prompt,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "response",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "keywords": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "context": {
                                    "type": "string",
                                },
                                "tags": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                },
            )
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return {"keywords": [], "context": "General", "tags": []}

    def add_note(self, content: str, time: str = None, **kwargs) -> str:
        """Add a new memory note"""
        # Create MemoryNote without llm_controller first
        if time is not None:
            kwargs["timestamp"] = time

        # Analyze content first
        analysis = self.analyze_content(content)

        # Merge analysis results with kwargs, giving priority to explicitly passed kwargs
        # Remove context from kwargs if it exists to avoid conflicts
        explicit_context = kwargs.pop("context", None)
        explicit_keywords = kwargs.pop("keywords", None)
        explicit_tags = kwargs.pop("tags", None)

        # Create note with analysis results, using explicit values when provided
        note = MemoryNote(
            content=content,
            keywords=explicit_keywords or analysis.get("keywords", []),
            context=explicit_context or analysis.get("context", "General"),
            tags=explicit_tags or analysis.get("tags", []),
            **kwargs,
        )

        # Process memory evolution
        evo_label, note = self.process_memory(note)

        # Generate embedding
        embedding = self.embedding_model.encode([content])[0].tolist()

        # Prepare memory data for Supabase
        memory_data = {
            "content": note.content,
            "context": note.context,
            "category": note.category,
            "keywords": note.keywords,
            "tags": note.tags,
            "importance_score": note.importance_score,
            "user_id": self.user_id,
            "embedding": embedding,
            "linked_memory_ids": note.links,  # Store links in the database
            "evolution_count": len(note.evolution_history),
        }

        # Create memory in Supabase
        result = self.supabase_client.create_memory(memory_data)
        if result:
            memory_id = str(result.get("id"))
            note.id = memory_id

            # Create SupabaseMemoryNote and cache it
            supabase_note = SupabaseMemoryNote({**memory_data, "id": memory_id})
            self.memories[memory_id] = supabase_note

            # Create memory links in database
            if note.links:
                for target_id in note.links:
                    try:
                        self.supabase_client.create_memory_link(memory_id, target_id)
                    except Exception as e:
                        logger.warning(
                            f"Failed to create memory link from {memory_id} to {target_id}: {e}"
                        )

            # Check if consolidation is needed
            if evo_label:
                self.evo_cnt += 1
                if self.evo_cnt % self.evo_threshold == 0:
                    self.consolidate_memories()

            return memory_id

        raise Exception("Failed to create memory in Supabase")

    def read(self, memory_id: str) -> Optional[SupabaseMemoryNote]:
        """Retrieve a specific memory by ID.

        Args:
            memory_id: ID of the memory to retrieve

        Returns:
            SupabaseMemoryNote object or None if not found
        """
        try:
            # Check cache first
            if memory_id in self.memories:
                memory = self.memories[memory_id]
                # Update last accessed time
                self.supabase_client.update_memory(
                    memory_id, {"last_accessed": datetime.now().isoformat()}
                )
                return memory

            # Retrieve from database
            memory_data = self.supabase_client.get_memory(memory_id)
            if memory_data:
                memory = SupabaseMemoryNote(memory_data)
                # Cache the memory
                self.memories[memory_id] = memory

                # Update last accessed time
                self.supabase_client.update_memory(
                    memory_id, {"last_accessed": datetime.now().isoformat()}
                )

                return memory
            return None
        except Exception as e:
            logger.error(f"Error reading memory {memory_id}: {e}")
            return None

    def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory with new data.

        Args:
            memory_id: ID of the memory to update
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update in database
            success = self.supabase_client.update_memory(memory_id, updates)

            if success:
                # Update cache if memory exists
                if memory_id in self.memories:
                    memory = self.memories[memory_id]
                    for key, value in updates.items():
                        if hasattr(memory, key):
                            setattr(memory, key, value)

                return True
            return False
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            return False

    def delete(self, memory_id: str) -> bool:
        """Delete a memory from the system.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from database
            success = self.supabase_client.delete_memory(memory_id)

            if success:
                # Remove from cache
                if memory_id in self.memories:
                    del self.memories[memory_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return False

    def consolidate_memories(self):
        """Consolidate memories (placeholder for future implementation)."""
        try:
            # Reset evolution counter
            self.evo_cnt = 0
            logger.info("Memory consolidation completed")
        except Exception as e:
            logger.error(f"Error in consolidation: {e}")

    def find_related_memories(self, query: str, k: int = 5) -> Tuple[str, List[str]]:
        """Find related memories and return formatted string with IDs.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            Tuple of (formatted_memory_string, memory_ids)
        """
        try:
            results = self.retriever.search(query, k)
            memory_str = ""
            memory_ids = []

            for i, result in enumerate(results):
                memory_id = str(result.get("id", ""))
                content = result.get("content", "")[:100]
                context = result.get("context", "")

                memory_str += f"Memory {i}: {content}... Context: {context}\n"
                memory_ids.append(memory_id)

            return memory_str, memory_ids
        except Exception as e:
            logger.error(f"Error in find_related_memories: {e}")
            return "", []

    def process_memory(self, note: MemoryNote) -> Tuple[bool, MemoryNote]:
        """Process a memory note and determine if it should evolve.

        Args:
            note: The memory note to process

        Returns:
            Tuple[bool, MemoryNote]: (should_evolve, processed_note)
        """
        try:
            # For first few memories, don't trigger evolution
            if len(self.memories) < 2:
                return False, note

            # Find related memories for evolution analysis
            query = f"{note.context} {' '.join(note.keywords)}"
            nearest_neighbors_memories, neighbor_ids = self.find_related_memories(
                query, k=3
            )

            if not neighbor_ids:
                return False, note

            # Use LLM to determine evolution with simplified prompt
            try:
                simplified_prompt = f"""
                Analyze this new memory and its relationship to existing memories.
                
                New memory:
                Content: {note.content}
                Keywords: {', '.join(note.keywords)}
                Context: {note.context}
                
                Related memories:
                {nearest_neighbors_memories}
                
                Should this memory be linked to any of the related memories? 
                Respond with a JSON object:
                {{
                    "should_evolve": true/false,
                    "suggested_links": [0, 1, 2],  // indices of memories to link to (0-2)
                    "updated_tags": ["tag1", "tag2"]  // updated tags for the new memory
                }}
                """

                response = self.llm_controller.llm.get_completion(simplified_prompt)

                try:
                    # Try to parse JSON response
                    import re

                    json_match = re.search(r"\{.*\}", response, re.DOTALL)
                    if json_match:
                        response_json = json.loads(json_match.group())

                        should_evolve = response_json.get("should_evolve", False)

                        if should_evolve:
                            self.evo_cnt += 1

                            # Handle links
                            suggested_links = response_json.get("suggested_links", [])
                            valid_connections = []

                            for link_index in suggested_links:
                                try:
                                    if isinstance(
                                        link_index, int
                                    ) and 0 <= link_index < len(neighbor_ids):
                                        valid_connections.append(
                                            neighbor_ids[link_index]
                                        )
                                except (ValueError, IndexError):
                                    continue

                            note.links.extend(valid_connections)

                            # Handle updated tags
                            updated_tags = response_json.get("updated_tags", note.tags)
                            if updated_tags:
                                note.tags = updated_tags

                            # Record evolution in history
                            note.evolution_history.append(
                                {
                                    "timestamp": datetime.now().isoformat(),
                                    "action": "simplified_evolution",
                                    "links_added": len(valid_connections),
                                    "tags_updated": len(updated_tags),
                                }
                            )

                        return should_evolve, note

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse evolution response: {e}")
                    return False, note

            except Exception as e:
                logger.error(f"Error in evolution analysis: {e}")
                return False, note

        except Exception as e:
            logger.error(f"Error in process_memory: {e}")
            return False, note

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for memories using Supabase retrieval."""
        try:
            results = self.retriever.search(query, k)
            memories = []

            for result in results:
                memory_dict = {
                    "id": str(result.get("id")),
                    "content": result.get("content", ""),
                    "context": result.get("context", ""),
                    "keywords": result.get("keywords", []),
                    "tags": result.get("tags", []),
                    "timestamp": result.get("created_at", ""),
                    "category": result.get("category", "Uncategorized"),
                    "similarity": result.get("similarity", 0.0),
                }
                memories.append(memory_dict)

            return memories
        except Exception as e:
            logger.error(f"Error in search: {str(e)}")
            return []

    def get_related_memories(self, query: str, k: int = 5) -> List[SupabaseMemoryNote]:
        """Find related memories and return SupabaseMemoryNote objects.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of related SupabaseMemoryNote objects
        """
        try:
            results = self.retriever.search(query, k)
            related_memories = []

            for result in results:
                memory_note = SupabaseMemoryNote(result)
                # Cache the memory
                self.memories[memory_note.id] = memory_note
                related_memories.append(memory_note)

            return related_memories
        except Exception as e:
            logger.error(f"Error getting related memories: {e}")
            return []

    def get_memory(self, memory_id: str) -> Optional[SupabaseMemoryNote]:
        """Get a specific memory by ID.

        Args:
            memory_id: ID of the memory to retrieve

        Returns:
            SupabaseMemoryNote object or None if not found
        """
        try:
            # Check cache first
            if memory_id in self.memories:
                return self.memories[memory_id]

            # Get from database
            memory_data = self.supabase_client.get_memory(memory_id)
            if memory_data:
                memory_note = SupabaseMemoryNote(memory_data)
                # Cache the memory
                self.memories[memory_id] = memory_note
                return memory_note

            return None
        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {e}")
            return None

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about the memory system.

        Returns:
            Dictionary containing memory statistics
        """
        try:
            return self.supabase_client.get_memory_statistics()
        except Exception as e:
            logger.error(f"Error getting memory statistics: {e}")
            return {
                "total_memories": 0,
                "categories": {},
                "users": {},
            }
