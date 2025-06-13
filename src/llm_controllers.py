"""
LLM Controllers for different backends.

This module provides abstract base classes and concrete implementations
for interacting with various Language Model backends.
"""

from typing import Optional, Literal, Any, Dict
import json
import os
from abc import ABC, abstractmethod
from litellm import completion


class BaseLLMController(ABC):
    """Abstract base class for LLM controllers."""

    @abstractmethod
    def get_completion(
        self, prompt: str, response_format: dict, temperature: float = 0.7
    ) -> str:
        """Get completion from LLM with structured response format."""
        pass


class OpenAIController(BaseLLMController):
    """OpenAI API controller for GPT models."""

    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        """Initialize OpenAI controller.

        Args:
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
        """
        try:
            from openai import OpenAI

            self.model = model
            if api_key is None:
                api_key = os.getenv("OPENAI_API_KEY")
            if api_key is None:
                raise ValueError(
                    "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
                )
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError(
                "OpenAI package not found. Install it with: pip install openai"
            )

    def get_completion(
        self, prompt: str, response_format: dict, temperature: float = 0.7
    ) -> str:
        """Get completion from OpenAI API with structured JSON response."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You must respond with a JSON object."},
                {"role": "user", "content": prompt},
            ],
            response_format=response_format,
            temperature=temperature,
            max_tokens=1000,
        )
        return response.choices[0].message.content


class OllamaController(BaseLLMController):
    """Ollama local model controller."""

    def __init__(self, model: str = "llama2"):
        """Initialize Ollama controller.

        Args:
            model: Local model name (e.g., "llama2", "mistral")
        """
        self.model = model

    def _generate_empty_value(self, schema_type: str, schema_items: dict = None) -> Any:
        """Generate empty value based on JSON schema type."""
        if schema_type == "array":
            return []
        elif schema_type == "string":
            return ""
        elif schema_type == "object":
            return {}
        elif schema_type == "number":
            return 0
        elif schema_type == "boolean":
            return False
        return None

    def _generate_empty_response(self, response_format: dict) -> dict:
        """Generate empty response structure based on schema."""
        if "json_schema" not in response_format:
            return {}

        schema = response_format["json_schema"]["schema"]
        result = {}

        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                result[prop_name] = self._generate_empty_value(
                    prop_schema["type"], prop_schema.get("items")
                )

        return result

    def get_completion(
        self, prompt: str, response_format: dict, temperature: float = 0.7
    ) -> str:
        """Get completion from Ollama with fallback to empty response."""
        try:
            response = completion(
                model=f"ollama_chat/{self.model}",
                messages=[
                    {
                        "role": "system",
                        "content": "You must respond with a JSON object.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format=response_format,
            )
            return response.choices[0].message.content
        except Exception as e:
            # Fallback to empty response if model fails
            empty_response = self._generate_empty_response(response_format)
            return json.dumps(empty_response)


class LLMController:
    """Factory class for LLM backend selection."""

    def __init__(
        self,
        backend: Literal["openai", "ollama"] = "openai",
        model: str = "gpt-4",
        api_key: Optional[str] = None,
    ):
        """Initialize LLM controller with specified backend.

        Args:
            backend: Backend type ("openai" or "ollama")
            model: Model name
            api_key: API key for OpenAI (if applicable)
        """
        if backend == "openai":
            self.llm = OpenAIController(model, api_key)
        elif backend == "ollama":
            self.llm = OllamaController(model)
        else:
            raise ValueError("Backend must be either 'openai' or 'ollama'")
