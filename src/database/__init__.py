"""
Supabase Database Integration for AgenticMemory.

This module provides comprehensive integration with Supabase for persistent
memory storage, vector search, chat management, and user isolation.

Key Components:
- SupabaseMemoryClient: Direct Supabase database operations
- SupabaseAgenticMemorySystem: Drop-in replacement for local memory system
- Migration and maintenance tools
- Backup and restore functionality

Usage:
    # Basic usage with Supabase backend
    from src.database import get_supabase_memory_system

    memory_system = get_supabase_memory_system("user123")
    memory_id = memory_system.add_note("Remember this important fact")

    # Direct client access for advanced operations
    from src.database import SupabaseMemoryClient

    client = SupabaseMemoryClient()
    results = client.hybrid_search_memories("search query", embedding=embedding)
"""

# Core exports
from src.database.supabase_client import SupabaseMemoryClient
from src.database.supabase_memory_adapter import (
    SupabaseAgenticMemorySystem,
    SupabaseMemoryNote,
)
from src.database.supabase_config import SupabaseConfigManager, SupabaseConfig

# Utility exports
from src.database.supabase_utils import (
    SupabaseMigrationTool,
    SupabaseMaintenanceTool,
    SupabaseBackupTool,
    setup_supabase_environment,
    get_supabase_memory_system,
)

# Version info
__version__ = "1.0.0"
__author__ = "AgenticMemory Team"


# Convenience functions
def create_memory_system(user_id: str = None, **kwargs) -> SupabaseAgenticMemorySystem:
    """Create a Supabase-backed memory system.

    Args:
        user_id: User identifier for memory isolation
        **kwargs: Additional configuration options

    Returns:
        SupabaseAgenticMemorySystem: Configured memory system
    """
    return SupabaseAgenticMemorySystem(user_id=user_id, **kwargs)


def create_client(**kwargs) -> SupabaseMemoryClient:
    """Create a Supabase client.

    Args:
        **kwargs: Configuration options

    Returns:
        SupabaseMemoryClient: Configured client
    """
    return SupabaseMemoryClient(**kwargs)


def validate_setup() -> bool:
    """Validate Supabase setup and configuration.

    Returns:
        bool: True if setup is valid
    """
    return setup_supabase_environment()


# Export all for convenience
__all__ = [
    # Core classes
    "SupabaseMemoryClient",
    "SupabaseAgenticMemorySystem",
    "SupabaseMemoryNote",
    "SupabaseConfigManager",
    "SupabaseConfig",
    # Utility classes
    "SupabaseMigrationTool",
    "SupabaseMaintenanceTool",
    "SupabaseBackupTool",
    # Functions
    "setup_supabase_environment",
    "get_supabase_memory_system",
    "create_memory_system",
    "create_client",
    "validate_setup",
    # Version info
    "__version__",
    "__author__",
]


# Setup instructions for easy access
SETUP_INSTRUCTIONS = """
Supabase Setup Instructions:

1. Install dependencies:
   pip install -r src/database/requirements_supabase.txt

2. Create Supabase project at https://app.supabase.com

3. Run database schema:
   - Copy content from src/database/supabase_schema.sql
   - Execute in Supabase SQL Editor

4. Set environment variables:
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...
   SUPABASE_DB_PASSWORD=your_password

5. Test setup:
   python -c "from src.database import validate_setup; print(validate_setup())"

6. Start using:
   from src.database import get_supabase_memory_system
   system = get_supabase_memory_system("your_user_id")
"""


def print_setup_instructions():
    """Print setup instructions."""
    print(SETUP_INSTRUCTIONS)
