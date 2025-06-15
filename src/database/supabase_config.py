"""
Supabase configuration and connection settings for AgenticMemory.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class SupabaseConfig:
    """Configuration class for Supabase connection."""

    # Supabase connection details
    url: str
    key: str
    service_role_key: Optional[str] = None

    # Database settings
    table_prefix: str = ""
    schema: str = "public"

    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20

    # Security settings
    enable_rls: bool = True
    auto_confirm_users: bool = False


class SupabaseConfigManager:
    """Manager for Supabase configuration settings."""

    # Default configuration values
    DEFAULT_SUPABASE_URL = os.getenv("SUPABASE_URL")
    DEFAULT_SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
    DEFAULT_SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # Table names
    MEMORIES_TABLE = "memories"
    MEMORY_LINKS_TABLE = "memory_links"
    CHAT_SESSIONS_TABLE = "chat_sessions"
    CHAT_MESSAGES_TABLE = "chat_messages"
    MEMORY_STATS_TABLE = "memory_stats"

    # Vector dimensions (must match embedding model)
    EMBEDDING_DIMENSIONS = 384  # for all-MiniLM-L6-v2

    @classmethod
    def get_config(cls) -> SupabaseConfig:
        """Get Supabase configuration from environment variables.

        Returns:
            SupabaseConfig: Configuration object

        Raises:
            ValueError: If required environment variables are not set
        """
        url = cls.DEFAULT_SUPABASE_URL
        key = cls.DEFAULT_SUPABASE_KEY

        if not url:
            raise ValueError(
                "SUPABASE_URL environment variable is required. "
                "Get it from your Supabase project settings."
            )

        if not key:
            raise ValueError(
                "SUPABASE_ANON_KEY environment variable is required. "
                "Get it from your Supabase project settings."
            )

        return SupabaseConfig(
            url=url, key=key, service_role_key=cls.DEFAULT_SUPABASE_SERVICE_KEY
        )

    @classmethod
    def validate_config(cls) -> bool:
        """Validate Supabase configuration.

        Returns:
            bool: True if configuration is valid
        """
        try:
            cls.get_config()
            return True
        except ValueError as e:
            print(f"Supabase configuration error: {e}")
            return False

    @classmethod
    def get_connection_string(cls) -> str:
        """Get PostgreSQL connection string for direct database access.

        Returns:
            str: PostgreSQL connection string
        """
        config = cls.get_config()

        # Extract database URL from Supabase URL
        # Supabase URL format: https://xxx.supabase.co
        # Database URL format: postgresql://[user[:password]@][netloc][:port][/dbname]

        project_id = config.url.split("//")[1].split(".")[0]
        db_host = f"db.{project_id}.supabase.co"

        # Get database password from environment
        db_password = os.getenv("SUPABASE_DB_PASSWORD")
        if not db_password:
            raise ValueError(
                "SUPABASE_DB_PASSWORD environment variable is required for direct database access. "
                "Get it from your Supabase project database settings."
            )

        return f"postgresql://postgres:{db_password}@{db_host}:5432/postgres"


# Environment variable setup instructions
SETUP_INSTRUCTIONS = """
To use Supabase with AgenticMemory, set the following environment variables:

1. SUPABASE_URL - Your Supabase project URL
   Example: https://xxxxxxxxxxxxx.supabase.co

2. SUPABASE_ANON_KEY - Your Supabase anonymous/public key
   Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

3. SUPABASE_SERVICE_ROLE_KEY - Your Supabase service role key (optional, for admin operations)
   Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

4. SUPABASE_DB_PASSWORD - Your Supabase database password (for direct PostgreSQL access)
   Example: your_secure_password

You can find these values in your Supabase project dashboard:
- Go to https://app.supabase.com
- Select your project
- Go to Settings > API
- Copy the URL and keys

For the database password:
- Go to Settings > Database
- Copy or reset the database password

Set them in your environment:
Windows:
set SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
set SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
set SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...
set SUPABASE_DB_PASSWORD=your_password

Linux/Mac:
export SUPABASE_URL="https://xxxxxxxxxxxxx.supabase.co"
export SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIs..."
export SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIs..."
export SUPABASE_DB_PASSWORD="your_password"

Or create a .env file in your project root:
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_DB_PASSWORD=your_password
"""
