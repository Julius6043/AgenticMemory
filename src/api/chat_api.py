"""
Flask API for AgenticMemory Chat Agent with Supabase Backend.

This module provides a RESTful API for interacting with the AgenticMemory system
through a chat interface using Supabase as the persistent backend.
It allows frontend applications to send messages, receive responses,
and manage memory persistence in the cloud.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from pathlib import Path

# Import our memory system
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from config import Config
from llm_controllers import LLMController

# Import Supabase components
from src.database.supabase_memory_adapter import (
    SupabaseAgenticMemorySystem,
    SupabaseMemoryNote,
)
from src.database.supabase_client import SupabaseMemoryClient
from src.database.supabase_config import SupabaseConfigManager
from src.database.supabase_utils import setup_supabase_environment


# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for memory system and Supabase client
memory_system = None
supabase_client = None


class SupabaseChatAgent:
    """Chat agent that integrates with the Supabase-backed AgenticMemory system."""

    def __init__(
        self,
        memory_system: SupabaseAgenticMemorySystem,
        supabase_client: SupabaseMemoryClient,
    ):
        """Initialize the chat agent with a Supabase memory system.

        Args:
            memory_system: The Supabase AgenticMemory system instance
            supabase_client: The Supabase client for direct database operations
        """
        self.memory_system = memory_system
        self.supabase_client = supabase_client
        self.system_prompt = """
        You are an intelligent assistant with a persistent memory system. 
        You can remember information from previous conversations and use it to provide better responses.
        
        When responding:
        1. Check if the query relates to previously stored memories
        2. Use relevant memories to enhance your response
        3. Store important new information for future reference
        4. Be conversational and helpful
        
        Current query: {query}
        Related memories: {related_memories}
        
        Provide a helpful response based on the query and any related memories.
        """

    def process_message(
        self, message: str, session_id: str, user_id: str = None
    ) -> Dict[str, Any]:
        """Process a chat message and return response with memory updates.

        Args:
            message: User's message
            session_id: Chat session identifier
            user_id: User identifier (optional)

        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Set user_id on memory system for this request
            if user_id:
                self.memory_system.user_id = user_id
                self.memory_system.retriever.user_id = user_id

            # Search for related memories first
            related_memories = self.memory_system.get_related_memories(message, k=5)

            # Format related memories for context
            related_memories_text = ""
            if related_memories:
                related_memories_text = "\n".join(
                    [f"- {mem.content[:100]}..." for mem in related_memories[:3]]
                )

            # Generate response using LLM
            prompt = self.system_prompt.format(
                query=message, related_memories=related_memories_text
            )
            response = self.memory_system.llm_controller.get_completion(prompt)

            # Store user message as memory
            user_memory_id = self.memory_system.add_note(
                content=f"User asked: {message}",
                context="User Query",
                category="Conversation",
                user_id=user_id,
                session_id=session_id,
            )

            # Store assistant response as memory
            assistant_memory_id = self.memory_system.add_note(
                content=f"Assistant responded: {response}",
                context="Assistant Response",
                category="Conversation",
                user_id=user_id,
                session_id=session_id,
            )

            # Ensure chat session exists
            self.supabase_client.create_chat_session(
                session_id=session_id,
                user_id=user_id,
                metadata={"created_via": "chat_api"},
            )

            # Store user message in Supabase
            self.supabase_client.add_chat_message(
                session_id=session_id,
                message_type="user",
                content=message,
                memory_ids=[user_memory_id],
                metadata={
                    "user_message": message,
                    "related_memory_ids": [mem.id for mem in related_memories],
                },
            )

            # Store assistant response in Supabase
            self.supabase_client.add_chat_message(
                session_id=session_id,
                message_type="assistant",
                content=response,
                memory_ids=[assistant_memory_id],
                metadata={
                    "assistant_response": response,
                    "related_memory_ids": [mem.id for mem in related_memories],
                },
            )

            return {
                "response": response,
                "session_id": session_id,
                "memory_ids": [user_memory_id, assistant_memory_id],
                "related_memories_count": len(related_memories),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an error processing your message. Please try again.",
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            }


def initialize_memory_system():
    """Initialize the global Supabase memory system."""
    global memory_system, supabase_client

    try:
        # Setup Supabase environment
        config = SupabaseConfigManager.get_config()

        # Initialize Supabase client
        supabase_client = SupabaseMemoryClient(config)

        # Validate configuration
        if not Config.validate_config():
            logger.warning("Configuration validation failed, but continuing...")

        # Initialize Supabase memory system with config defaults (no default user_id)
        memory_system = SupabaseAgenticMemorySystem(
            supabase_client=supabase_client,
            model_name=Config.DEFAULT_EMBEDDING_MODEL,
            llm_backend=Config.DEFAULT_LLM_BACKEND,
            llm_model=Config.DEFAULT_LLM_MODEL,
            evo_threshold=Config.DEFAULT_EVO_THRESHOLD,
            api_key=Config.get_openai_key(),
            user_id=None,  # Will be set dynamically per request
        )

        logger.info("Supabase memory system initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize Supabase memory system: {str(e)}")
        return False


# API Routes


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "memory_system_active": memory_system is not None,
            "supabase_client_active": supabase_client is not None,
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint for sending messages to the agent."""
    try:
        data = request.get_json()
        message = data.get("message", "").strip()
        session_id = data.get(
            "session_id", f"session-{int(datetime.now().timestamp() * 1000)}"
        )
        user_id = data.get("user_id", "anonymous")

        if not message:
            return jsonify({"error": "Message is required"}), 400

        # Create chat agent
        chat_agent = SupabaseChatAgent(memory_system, supabase_client)

        # Process message
        result = chat_agent.process_message(message, session_id, user_id)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route("/memory/add", methods=["POST"])
def add_memory():
    """Add a memory note directly to the system."""
    try:
        data = request.get_json()
        content = data.get("content", "").strip()
        user_id = data.get("user_id", "anonymous")

        if not content:
            return jsonify({"error": "Content is required"}), 400

        # Set user_id on memory system
        memory_system.user_id = user_id
        memory_system.retriever.user_id = user_id

        # Add memory with additional parameters
        memory_id = memory_system.add_note(
            content=content,
            context=data.get("context", "General"),
            category=data.get("category", "Manual"),
            keywords=data.get("keywords", []),
            tags=data.get("tags", []),
            user_id=user_id,
        )

        return jsonify(
            {
                "memory_id": memory_id,
                "content": content,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Add memory error: {str(e)}")
        return jsonify({"error": "Failed to add memory", "details": str(e)}), 500


@app.route("/memory/search", methods=["POST"])
def search_memories():
    """Search for related memories."""
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        user_id = data.get("user_id", "anonymous")
        limit = data.get("limit", 5)

        if not query:
            return jsonify({"error": "Query is required"}), 400

        # Set user_id on memory system
        memory_system.user_id = user_id
        memory_system.retriever.user_id = user_id

        # Search memories
        results = memory_system.get_related_memories(query, k=limit)

        # Format results
        formatted_results = []
        for memory in results:
            formatted_results.append(
                {
                    "id": memory.id,
                    "content": (
                        memory.content[:200] + "..."
                        if len(memory.content) > 200
                        else memory.content
                    ),
                    "context": memory.context,
                    "category": memory.category,
                    "importance_score": memory.importance_score,
                    "retrieval_count": memory.retrieval_count,
                    "timestamp": memory.timestamp,
                }
            )

        return jsonify(
            {
                "query": query,
                "user_id": user_id,
                "results": formatted_results,
                "count": len(formatted_results),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Search memories error: {str(e)}")
        return jsonify({"error": "Failed to search memories", "details": str(e)}), 500


@app.route("/memory/get/<memory_id>", methods=["GET"])
def get_memory(memory_id):
    """Get a specific memory by ID."""
    try:
        user_id = request.args.get("user_id", "anonymous")

        # Set user_id on memory system
        memory_system.user_id = user_id
        memory_system.retriever.user_id = user_id

        memory = memory_system.get_memory(memory_id)
        if not memory:
            return jsonify({"error": "Memory not found"}), 404

        return jsonify(
            {
                "id": memory.id,
                "content": memory.content,
                "context": memory.context,
                "category": memory.category,
                "keywords": memory.keywords,
                "tags": memory.tags,
                "importance_score": memory.importance_score,
                "retrieval_count": memory.retrieval_count,
                "timestamp": memory.timestamp,
                "last_accessed": memory.last_accessed,
                "user_id": getattr(memory, "user_id", None),
            }
        )

    except Exception as e:
        logger.error(f"Get memory error: {str(e)}")
        return jsonify({"error": "Failed to get memory", "details": str(e)}), 500


@app.route("/session/<session_id>/history", methods=["GET"])
def get_session_history(session_id):
    """Get chat history for a specific session."""
    try:
        limit = request.args.get("limit", 50, type=int)

        messages = supabase_client.get_chat_history(session_id, limit)

        return jsonify(
            {
                "session_id": session_id,
                "messages": messages,
                "count": len(messages),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Get session history error: {str(e)}")
        return (
            jsonify({"error": "Failed to get session history", "details": str(e)}),
            500,
        )


@app.route("/sessions", methods=["GET"])
def list_sessions():
    """List all active chat sessions."""
    try:
        user_id = request.args.get("user_id")
        limit = request.args.get("limit", 20, type=int)

        sessions = supabase_client.get_chat_sessions(user_id, limit)

        return jsonify(
            {
                "sessions": sessions,
                "count": len(sessions),
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"List sessions error: {str(e)}")
        return jsonify({"error": "Failed to list sessions", "details": str(e)}), 500


@app.route("/memory/stats", methods=["GET"])
def memory_stats():
    """Get memory system statistics."""
    try:
        user_id = request.args.get("user_id")

        # Set user_id on memory system if provided
        if user_id:
            memory_system.user_id = user_id
            memory_system.retriever.user_id = user_id

        stats = memory_system.get_memory_statistics()

        response_data = {
            "total_memories": stats.get("total_memories", 0),
            "categories": stats.get("categories", {}),
            "users": stats.get("users", {}),
            "evolution_threshold": memory_system.evo_threshold,
            "timestamp": datetime.now().isoformat(),
        }

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Memory stats error: {str(e)}")
        logger.error(f"Memory stats traceback: {e}", exc_info=True)
        return jsonify({"error": "Failed to get memory stats", "details": str(e)}), 500


@app.route("/demo", methods=["GET"])
def demo():
    """Serve the demo frontend."""
    try:
        demo_file = Path(__file__).parent / "demo.html"
        if demo_file.exists():
            return demo_file.read_text()
        else:
            return (
                "<h1>Demo HTML not found</h1><p>Please create demo.html file</p>",
                404,
            )
    except FileNotFoundError:
        return "<h1>Demo not available</h1><p>Demo HTML file not found</p>", 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request", "message": str(error)}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found", "message": str(error)}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "message": str(error)}), 500


def create_app(config=None):
    """Application factory function."""
    if config:
        app.config.update(config)

    # Initialize memory system
    if not initialize_memory_system():
        logger.error("Failed to initialize memory system")

    return app


if __name__ == "__main__":
    # Initialize memory system
    if initialize_memory_system():
        logger.info("Starting Flask API server...")
        app.run(host="0.0.0.0", port=5000, debug=True)
    else:
        logger.error("Failed to initialize memory system. Exiting.")
