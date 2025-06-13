"""
Core memory management classes.

This module contains the MemoryNote class for individual memory units
and the AgenticMemorySystem for managing the entire memory network.
"""

from typing import List, Dict, Optional, Any
import json
import uuid
from datetime import datetime

from .llm_controllers import LLMController
from .retrievers import SimpleEmbeddingRetriever


class MemoryNote:
    """Basic memory unit with metadata and LLM-powered analysis."""

    def __init__(
        self,
        content: str,
        id: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        links: Optional[List] = None,
        importance_score: Optional[float] = None,
        retrieval_count: Optional[int] = None,
        timestamp: Optional[str] = None,
        last_accessed: Optional[str] = None,
        context: Optional[str] = None,
        evolution_history: Optional[List] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        llm_controller: Optional[LLMController] = None,
    ):
        """Initialize a memory note with automatic metadata generation.

        Args:
            content: The main content of the memory
            id: Unique identifier (auto-generated if None)
            keywords: Key terms extracted from content
            links: Connections to other memory notes
            importance_score: Relevance/importance rating
            retrieval_count: How often this memory has been accessed
            timestamp: Creation time
            last_accessed: Last access time
            context: Contextual summary
            evolution_history: History of changes
            category: Broad category classification
            tags: Classification tags
            llm_controller: LLM controller for metadata generation
        """
        self.content = content

        # Generate metadata using LLM if not provided and controller is available
        if llm_controller and any(
            param is None for param in [keywords, context, category, tags]
        ):
            analysis = self.analyze_content(content, llm_controller)
            print("Analysis result:", analysis)
            keywords = keywords or analysis.get("keywords", [])
            context = context or analysis.get("context", "General")
            tags = tags or analysis.get("tags", [])

        # Set default values for optional parameters
        self.id = id or str(uuid.uuid4())
        self.keywords = keywords or []
        self.links = links or []
        self.importance_score = importance_score or 1.0
        self.retrieval_count = retrieval_count or 0
        current_time = datetime.now().strftime("%Y%m%d%H%M")
        self.timestamp = timestamp or current_time
        self.last_accessed = last_accessed or current_time

        # Handle context that can be either string or list
        self.context = context or "General"
        if isinstance(self.context, list):
            self.context = " ".join(self.context)  # Convert list to string by joining

        self.evolution_history = evolution_history or []
        self.category = category or "Uncategorized"
        self.tags = tags or []

    @staticmethod
    def analyze_content(content: str, llm_controller: LLMController) -> Dict:
        """Analyze content to extract keywords, context, and other metadata.

        Args:
            content: Text content to analyze
            llm_controller: LLM controller for analysis

        Returns:
            Dictionary with extracted metadata
        """
        prompt = f"""Generate a structured analysis of the following content by:
        1. Identifying the most salient keywords (focus on nouns, verbs, and key concepts)
        2. Extracting core themes and contextual elements
        3. Creating relevant categorical tags

        Format the response as a JSON object:
        {{
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
        }}

        Content for analysis:
        {content}"""

        try:
            response = llm_controller.llm.get_completion(
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
                            "required": ["keywords", "context", "tags"],
                            "additionalProperties": False,
                        },
                        "strict": True,
                    },
                },
            )

            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                analysis = response

            return analysis

        except Exception as e:
            print(f"Error analyzing content: {str(e)}")
            return {
                "keywords": [],
                "context": "General",
                "category": "Uncategorized",
                "tags": [],
            }


class AgenticMemorySystem:
    """Memory management system with embedding-based retrieval and evolution."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        llm_backend: str = "openai",
        llm_model: str = "gpt-4o-mini",
        evo_threshold: int = 100,
        api_key: Optional[str] = None,
    ):
        """Initialize the Agentic Memory System.

        Args:
            model_name: Sentence transformer model name
            llm_backend: LLM backend ("openai" or "ollama")
            llm_model: Specific model name
            evo_threshold: Number of evolutions before consolidation
            api_key: API key for LLM backend
        """
        self.memories = {}  # id -> MemoryNote
        self.retriever = SimpleEmbeddingRetriever(model_name)
        self.llm_controller = LLMController(llm_backend, llm_model, api_key)
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
        self.evo_cnt = 0
        self.evo_threshold = evo_threshold

    def add_note(self, content: str, time: str = None, **kwargs) -> str:
        """Add a new memory note to the system.

        Args:
            content: Main content of the memory
            time: Timestamp (auto-generated if None)
            **kwargs: Additional memory note parameters

        Returns:
            String ID of the created memory note
        """
        note = MemoryNote(
            content=content,
            llm_controller=self.llm_controller,
            timestamp=time,
            **kwargs,
        )

        # Process memory evolution
        evo_label, note = self.process_memory(note)
        self.memories[note.id] = note

        # Update retriever
        self.retriever.add_documents(
            [note.context + " keywords: " + ", ".join(note.keywords)]
        )

        # Check if consolidation is needed
        if evo_label:
            self.evo_cnt += 1
            if self.evo_cnt % self.evo_threshold == 0:
                self.consolidate_memories()

        return note.id

    def consolidate_memories(self):
        """Consolidate memories by updating retriever with all current memories."""
        # Reset the retriever with the same model
        try:
            model_name = self.retriever.model.get_config_dict()["model_name"]
        except (AttributeError, KeyError):
            model_name = "all-MiniLM-L6-v2"

        self.retriever = SimpleEmbeddingRetriever(model_name)

        # Re-add all memory documents with their metadata
        for memory in self.memories.values():
            metadata_text = (
                f"{memory.context} {' '.join(memory.keywords)} {' '.join(memory.tags)}"
            )
            self.retriever.add_documents([memory.content + " , " + metadata_text])

    def process_memory(self, note: MemoryNote) -> tuple[bool, MemoryNote]:
        """Process a memory note and determine evolution actions.

        Args:
            note: Memory note to process

        Returns:
            Tuple of (should_evolve, processed_note)
        """
        neighbor_memory, indices = self.find_related_memories(note.content, k=5)
        prompt_memory = self.evolution_system_prompt.format(
            context=note.context,
            content=note.content,
            keywords=note.keywords,
            nearest_neighbors_memories=neighbor_memory,
            neighbor_number=len(indices),
        )

        print("Evolution prompt:", prompt_memory)

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
                            "actions": {"type": "array", "items": {"type": "string"}},
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
                                "items": {"type": "array", "items": {"type": "string"}},
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
            print("Evolution response:", response_json)
        except json.JSONDecodeError:
            response_json = response

        should_evolve = response_json.get("should_evolve", False)

        if should_evolve:
            actions = response_json.get("actions", [])
            for action in actions:
                if action == "strengthen":
                    suggest_connections = response_json.get("suggested_connections", [])
                    new_tags = response_json.get("tags_to_update", [])
                    note.links.extend(suggest_connections)
                    note.tags = new_tags
                elif action == "update_neighbor":
                    new_context_neighborhood = response_json.get(
                        "new_context_neighborhood", []
                    )
                    new_tags_neighborhood = response_json.get(
                        "new_tags_neighborhood", []
                    )
                    noteslist = list(self.memories.values())
                    notes_id = list(self.memories.keys())

                    # Update neighbor memories
                    for i in range(min(len(indices), len(new_tags_neighborhood))):
                        tag = new_tags_neighborhood[i]
                        if i < len(new_context_neighborhood):
                            context = new_context_neighborhood[i]
                        else:
                            context = noteslist[indices[i]].context
                        memorytmp_idx = indices[i]
                        notetmp = noteslist[memorytmp_idx]
                        notetmp.tags = tag
                        notetmp.context = context
                        self.memories[notes_id[memorytmp_idx]] = notetmp

        return should_evolve, note

    def find_related_memories(self, query: str, k: int = 5) -> tuple[str, List[int]]:
        """Find related memories and return formatted string with indices.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            Tuple of (formatted_memory_string, indices)
        """
        if not self.memories:
            return "", []

        indices = self.retriever.search(query, k)
        all_memories = list(self.memories.values())
        memory_str = ""

        for i in indices:
            if i < len(all_memories):
                memory = all_memories[i]
                memory_str += (
                    f"memory index: {i}\t"
                    f"talk start time: {memory.timestamp}\t"
                    f"memory content: {memory.content}\t"
                    f"memory context: {memory.context}\t"
                    f"memory keywords: {memory.keywords}\t"
                    f"memory tags: {memory.tags}\n"
                )
        return memory_str, indices

    def get_related_memories(self, query: str, k: int = 5) -> List[MemoryNote]:
        """Find related memories and return MemoryNote objects.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of related MemoryNote objects
        """
        if not self.memories:
            return []

        indices = self.retriever.search(query, k)
        all_memories = list(self.memories.values())
        related_memories = []

        for i in indices:
            if i < len(all_memories):
                related_memories.append(all_memories[i])

        return related_memories
