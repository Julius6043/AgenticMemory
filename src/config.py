"""
Configuration settings for the AgenticMemory system.
"""

import os
from typing import Optional


class Config:
    """Configuration class for AgenticMemory system."""

    # Default model settings
    DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    DEFAULT_LLM_BACKEND = "openai"
    DEFAULT_LLM_MODEL = "gpt-4o-mini"

    # Evolution settings
    DEFAULT_EVO_THRESHOLD = 100

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # File paths
    DEFAULT_CACHE_DIR = "cache"
    DEFAULT_DATA_DIR = "data"

    # Retrieval settings
    DEFAULT_RETRIEVAL_K = 5
    DEFAULT_HYBRID_ALPHA = 0.5  # Balance between BM25 and semantic search

    @classmethod
    def get_openai_key(cls) -> Optional[str]:
        """Get OpenAI API key from environment or config."""
        return cls.OPENAI_API_KEY

    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings."""
        if cls.DEFAULT_LLM_BACKEND == "openai" and not cls.OPENAI_API_KEY:
            print(
                "Warning: OpenAI API key not found. Set OPENAI_API_KEY environment variable."
            )
            return False
        return True
