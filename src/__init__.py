"""
AgenticMemory - An intelligent memory management system with LLM-powered evolution.

This package provides:
- LLM controllers for different backends (OpenAI, Ollama)
- Memory note management with automatic metadata extraction
- Hybrid and semantic retrieval systems
- Self-evolving memory networks
"""

from .memory import MemoryNote, AgenticMemorySystem
from .llm_controllers import LLMController, OpenAIController, OllamaController
from .retrievers import HybridRetriever, SimpleEmbeddingRetriever
from .utils import simple_tokenize

__version__ = "1.0.0"
__all__ = [
    "MemoryNote",
    "AgenticMemorySystem",
    "LLMController",
    "OpenAIController",
    "OllamaController",
    "HybridRetriever",
    "SimpleEmbeddingRetriever",
    "simple_tokenize",
]
