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
from database.supabase_memory_adapter import (
    SupabaseAgenticMemorySystem,
    SupabaseMemoryNote,
)
from database.supabase_client import SupabaseMemoryClient
from database.supabase_config import SupabaseConfigManager
from database.supabase_utils import setup_supabase_environment


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
            # Find related memories
            related_memories = self.memory_system.get_related_memories(message, k=3)

            # Format related memories for context
            memory_context = ""
            if related_memories:
                memory_context = "\n".join(
                    [
                        f"- {mem.content} (Context: {mem.context}, Keywords: {', '.join(mem.keywords)})"
                        for mem in related_memories
                    ]
                )

            # Generate response using LLM
            prompt = self.system_prompt.format(
                query=message,
                related_memories=memory_context or "No related memories found.",
            )

            response = self.memory_system.llm_controller.llm.get_completion(
                prompt, response_format={"type": "text"}, temperature=0.7
            )

            # Store the user message and response as memories
            user_memory_id = self.memory_system.add_note(
                content=f"User asked: {message}",
                context="User Query",
                category="Conversation",
                user_id=user_id,
            )

            assistant_memory_id = self.memory_system.add_note(
                content=f"Assistant responded: {response}",
                context="Assistant Response",
                category="Conversation",
                user_id=user_id,
            )  # Store chat message in Supabase
            self.supabase_client.add_chat_message(
                session_id=session_id,
                message_type="conversation",
                content=f"User: {message}\nAssistant: {response}",
                memory_ids=[user_memory_id, assistant_memory_id],
                metadata={
                    "user_message": message,
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

        # Initialize Supabase memory system with config defaults
        memory_system = SupabaseAgenticMemorySystem(
            supabase_client=supabase_client,
            model_name=Config.DEFAULT_EMBEDDING_MODEL,
            llm_backend=Config.DEFAULT_LLM_BACKEND,
            llm_model=Config.DEFAULT_LLM_MODEL,
            evo_threshold=Config.DEFAULT_EVO_THRESHOLD,
            api_key=Config.get_openai_key(),
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

        if not data or "message" not in data:
            return jsonify({"error": "Message is required"}), 400

        message = data["message"]
        session_id = data.get("session_id", str(uuid.uuid4()))
        user_id = data.get("user_id")  # Optional user identifier

        if not memory_system or not supabase_client:
            return jsonify({"error": "Memory system not initialized"}), 500

        # Initialize Supabase chat agent
        agent = SupabaseChatAgent(memory_system, supabase_client)

        # Process message
        result = agent.process_message(message, session_id, user_id)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/memory/add", methods=["POST"])
def add_memory():
    """Add a memory note directly to the system."""
    try:
        data = request.get_json()

        if not data or "content" not in data:
            return jsonify({"error": "Content is required"}), 400

        if not memory_system:
            return jsonify({"error": "Memory system not initialized"}), 500

        # Add memory note
        memory_id = memory_system.add_note(
            content=data["content"],
            context=data.get("context", "User Added"),
            category=data.get("category", "Manual"),
            user_id=data.get("user_id"),
            **{
                k: v
                for k, v in data.items()
                if k not in ["content", "context", "category", "user_id"]
            },
        )

        return jsonify(
            {
                "memory_id": memory_id,
                "message": "Memory added successfully",
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Add memory error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/memory/search", methods=["POST"])
def search_memories():
    """Search for related memories."""
    try:
        data = request.get_json()

        if not data or "query" not in data:
            return jsonify({"error": "Query is required"}), 400

        if not memory_system:
            return jsonify({"error": "Memory system not initialized"}), 500

        query = data["query"]
        k = data.get("k", 5)
        user_id = data.get(
            "user_id"
        )  # Optional user filter        # Search memories (user_id filtering handled by Supabase adapter)
        related_memories = memory_system.get_related_memories(query, k=k)

        # Format results
        results = []
        for mem in related_memories:
            results.append(
                {
                    "id": mem.id,
                    "content": mem.content,
                    "context": mem.context,
                    "keywords": mem.keywords,
                    "tags": mem.tags,
                    "category": mem.category,
                    "importance_score": mem.importance_score,
                    "timestamp": mem.timestamp,
                    "last_accessed": mem.last_accessed,
                    "user_id": getattr(mem, "user_id", None),
                }
            )

        return jsonify(
            {
                "results": results,
                "query": query,
                "count": len(results),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Search memories error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/memory/get/<memory_id>", methods=["GET"])
def get_memory(memory_id):
    """Get a specific memory by ID."""
    try:
        if not memory_system or not supabase_client:
            return jsonify({"error": "Memory system not initialized"}), 500

        # Get memory from Supabase
        memory_data = supabase_client.get_memory(memory_id)

        if not memory_data:
            return jsonify({"error": "Memory not found"}), 404

        return jsonify(memory_data)

    except Exception as e:
        logger.error(f"Get memory error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/session/<session_id>/history", methods=["GET"])
def get_session_history(session_id):
    """Get chat history for a specific session."""
    try:
        if not supabase_client:
            return (
                jsonify({"error": "Supabase client not initialized"}),
                500,
            )  # Get session history from Supabase
        history = supabase_client.get_chat_history(session_id)

        return jsonify(
            {
                "session_id": session_id,
                "history": history,
                "message_count": len(history),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Get session history error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/sessions", methods=["GET"])
def list_sessions():
    """List all active chat sessions."""
    try:
        if not supabase_client:
            return (
                jsonify({"error": "Supabase client not initialized"}),
                500,
            )  # Get session list from Supabase
        user_id = request.args.get("user_id")  # Optional user filter
        sessions_info = supabase_client.get_chat_sessions(user_id=user_id)

        return jsonify(
            {
                "sessions": sessions_info,
                "total_sessions": len(sessions_info),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"List sessions error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/memory/stats", methods=["GET"])
def memory_stats():
    """Get memory system statistics."""
    try:
        if not memory_system or not supabase_client:
            return (
                jsonify({"error": "Memory system not initialized"}),
                500,
            )  # Get stats from Supabase
        user_id = request.args.get("user_id")  # Optional user filter
        stats = supabase_client.get_memory_statistics()

        return jsonify(
            {
                **stats,
                "evolution_threshold": memory_system.evo_threshold,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Memory stats error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/demo", methods=["GET"])
def demo():
    """Serve the demo frontend."""
    try:
        demo_file = os.path.join(os.path.dirname(__file__), "demo.html")
        with open(demo_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({"error": "Demo file not found"}), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


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
        logger.error("Cannot start server: Memory system initialization failed")
