"""
Unit tests for the AgenticMemory system.
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import Mock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import (
    MemoryNote,
    AgenticMemorySystem,
    LLMController,
    SimpleEmbeddingRetriever,
    HybridRetriever,
)


class TestMemoryNote(unittest.TestCase):
    """Test cases for MemoryNote class."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_content = "This is a test memory about machine learning."

    def test_memory_note_creation_basic(self):
        """Test basic memory note creation without LLM."""
        note = MemoryNote(self.sample_content)

        self.assertEqual(note.content, self.sample_content)
        self.assertIsNotNone(note.id)
        self.assertIsNotNone(note.timestamp)
        self.assertEqual(note.category, "Uncategorized")
        self.assertEqual(note.context, "General")
        self.assertEqual(note.importance_score, 1.0)

    def test_memory_note_with_custom_params(self):
        """Test memory note creation with custom parameters."""
        note = MemoryNote(
            self.sample_content,
            id="test-123",
            keywords=["machine", "learning"],
            tags=["AI", "tech"],
            importance_score=2.5,
        )

        self.assertEqual(note.id, "test-123")
        self.assertEqual(note.keywords, ["machine", "learning"])
        self.assertEqual(note.tags, ["AI", "tech"])
        self.assertEqual(note.importance_score, 2.5)

    @patch("src.memory.MemoryNote.analyze_content")
    def test_memory_note_with_llm_controller(self, mock_analyze):
        """Test memory note creation with LLM analysis."""
        # Mock LLM response
        mock_analyze.return_value = {
            "keywords": ["machine", "learning", "test"],
            "context": "Technical discussion about ML",
            "tags": ["AI", "technology", "education"],
        }

        mock_llm = Mock()
        note = MemoryNote(self.sample_content, llm_controller=mock_llm)

        mock_analyze.assert_called_once()
        self.assertEqual(note.keywords, ["machine", "learning", "test"])
        self.assertEqual(note.context, "Technical discussion about ML")
        self.assertEqual(note.tags, ["AI", "technology", "education"])


class TestSimpleEmbeddingRetriever(unittest.TestCase):
    """Test cases for SimpleEmbeddingRetriever class."""

    def setUp(self):
        """Set up test fixtures."""
        self.retriever = SimpleEmbeddingRetriever("all-MiniLM-L6-v2")
        self.test_docs = [
            "Machine learning is a subset of artificial intelligence.",
            "Neural networks are inspired by biological neural networks.",
            "Data preprocessing is important for model performance.",
        ]

    def test_add_documents(self):
        """Test adding documents to retriever."""
        self.retriever.add_documents(self.test_docs)

        self.assertEqual(len(self.retriever.corpus), 3)
        self.assertEqual(len(self.retriever.document_ids), 3)
        self.assertIsNotNone(self.retriever.embeddings)

    def test_search_functionality(self):
        """Test search functionality."""
        self.retriever.add_documents(self.test_docs)

        # Search for related content
        results = self.retriever.search("artificial intelligence", k=2)

        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 2)
        self.assertLessEqual(len(results), len(self.test_docs))

    def test_empty_corpus_search(self):
        """Test search with empty corpus."""
        results = self.retriever.search("test query", k=5)
        self.assertEqual(results, [])


class TestAgenticMemorySystem(unittest.TestCase):
    """Test cases for AgenticMemorySystem class."""

    def setUp(self):
        """Set up test fixtures."""
        # Use mock LLM to avoid API calls in tests
        with patch("src.memory.LLMController") as mock_llm_controller:
            self.memory_system = AgenticMemorySystem(
                llm_backend="openai", evo_threshold=5
            )

    def test_system_initialization(self):
        """Test system initialization."""
        self.assertIsNotNone(self.memory_system.memories)
        self.assertIsNotNone(self.memory_system.retriever)
        self.assertEqual(self.memory_system.evo_threshold, 5)
        self.assertEqual(self.memory_system.evo_cnt, 0)

    @patch("src.memory.AgenticMemorySystem.process_memory")
    def test_add_note(self, mock_process):
        """Test adding a note to the system."""
        # Mock the process_memory method
        mock_note = MemoryNote("Test content")
        mock_process.return_value = (False, mock_note)

        with patch("src.memory.MemoryNote") as mock_memory_note:
            mock_memory_note.return_value = mock_note

            note_id = self.memory_system.add_note("Test content")

            self.assertIsNotNone(note_id)
            self.assertIn(note_id, self.memory_system.memories)

    def test_get_related_memories_empty(self):
        """Test getting related memories from empty system."""
        results = self.memory_system.get_related_memories("test query")
        self.assertEqual(results, [])


class TestLLMController(unittest.TestCase):
    """Test cases for LLM Controller classes."""

    def test_llm_controller_factory_openai(self):
        """Test LLM controller factory for OpenAI."""
        with patch("src.llm_controllers.OpenAIController") as mock_openai:
            controller = LLMController(backend="openai", model="gpt-4")
            mock_openai.assert_called_once_with("gpt-4", None)

    def test_llm_controller_factory_ollama(self):
        """Test LLM controller factory for Ollama."""
        with patch("src.llm_controllers.OllamaController") as mock_ollama:
            controller = LLMController(backend="ollama", model="llama2")
            mock_ollama.assert_called_once_with("llama2")

    def test_llm_controller_invalid_backend(self):
        """Test LLM controller with invalid backend."""
        with self.assertRaises(ValueError):
            LLMController(backend="invalid")


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""

    @patch("src.llm_controllers.OpenAIController")
    def test_basic_workflow(self, mock_openai_controller):
        """Test basic workflow without API calls."""
        # Mock LLM responses
        mock_llm = Mock()
        mock_llm.get_completion.return_value = (
            '{"keywords": ["test"], "context": "Test context", "tags": ["test"]}'
        )
        mock_openai_controller.return_value = mock_llm

        # Create system
        memory_system = AgenticMemorySystem(llm_backend="openai", evo_threshold=10)

        # Add some memories
        contents = [
            "Machine learning algorithms learn from data.",
            "Neural networks have multiple layers.",
            "Data preprocessing improves model accuracy.",
        ]

        memory_ids = []
        for content in contents:
            with patch("src.memory.AgenticMemorySystem.process_memory") as mock_process:
                note = MemoryNote(content)
                mock_process.return_value = (False, note)
                memory_id = memory_system.add_note(content)
                memory_ids.append(memory_id)

        # Verify memories were added
        self.assertEqual(len(memory_system.memories), 3)

        # Test retrieval
        related = memory_system.get_related_memories("machine learning", k=2)
        self.assertIsInstance(related, list)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
