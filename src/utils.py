"""
Utility functions for the AgenticMemory system.
"""

from nltk.tokenize import word_tokenize


def simple_tokenize(text: str) -> list:
    """Simple tokenization using NLTK word tokenizer.

    Args:
        text: Input text to tokenize

    Returns:
        List of tokens
    """
    return word_tokenize(text)
