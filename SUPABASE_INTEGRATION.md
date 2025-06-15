# AgenticMemory with Supabase Backend - Complete Integration Guide

## Overview

This guide covers the complete integration of AgenticMemory with Supabase as a persistent, scalable backend. The integration provides:

- **Persistent memory storage** in Supabase PostgreSQL
- **Vector similarity search** using pgvector
- **Multi-user support** with user isolation
- **Chat session management** with full history
- **RESTful API** for frontend integration
- **Real-time analytics** and memory statistics

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask API      │    │   Supabase      │
│   (demo.html)   │◄──►│   (chat_api.py)  │◄──►│   PostgreSQL    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ AgenticMemory    │    │ Vector Search   │
                       │ System (Local)   │    │ (pgvector)      │
                       └──────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Prerequisites

- Python 3.8+
- OpenAI API key (for LLM functionality)
- Supabase account and project

### 2. Setup

```bash
# 1. Clone and navigate to the project
cd AgenticMemory

# 2. Run the setup script
python setup_supabase.py

# 3. Or set up manually:
pip install -r requirements.txt
pip install -r src/database/requirements_supabase.txt

# 4. Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"
export OPENAI_API_KEY="your-openai-key"
```

### 3. Database Setup

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run the schema from `src/database/supabase_schema.sql`

### 4. Start the API

```bash
python src/api/chat_api.py
```

### 5. Test the Integration

```bash
python src/api/test_supabase_api.py
```

## API Endpoints

### Health Check

```http
GET /health
```

### Chat

```http
POST /chat
Content-Type: application/json

{
  "message": "Hello, tell me about Python",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id"
}
```

### Memory Management

```http
# Add memory
POST /memory/add
{
  "content": "Python is a programming language",
  "context": "Programming",
  "category": "Technology",
  "user_id": "user123"
}

# Search memories
POST /memory/search
{
  "query": "Python programming",
  "k": 5,
  "user_id": "user123"
}

# Get specific memory
GET /memory/get/{memory_id}
```

### Session Management

```http
# Get session history
GET /session/{session_id}/history

# List all sessions
GET /sessions?user_id=user123

# Get memory statistics
GET /memory/stats?user_id=user123
```

### Demo Interface

```http
GET /demo
```

## Database Schema

### Tables

1. **memories** - Core memory storage with vector embeddings
2. **memory_links** - Connections between memories
3. **chat_sessions** - Chat session metadata
4. **chat_messages** - Individual chat messages and responses
5. **memory_stats** - Analytics and usage statistics

### Key Features

- **Vector Search**: Uses pgvector for semantic similarity
- **Full-Text Search**: PostgreSQL native text search
- **Row Level Security**: User data isolation
- **Indexes**: Optimized for fast queries
- **Functions**: Automated maintenance and cleanup

## Multi-User Support

The system supports multi-user scenarios with:

- **User ID isolation**: Each user's memories are separate
- **Session management**: Separate chat sessions per user
- **Security**: Row-level security (RLS) in Supabase
- **Analytics**: Per-user statistics and insights

## Usage Examples

### Python Integration

```python
from database.supabase_memory_adapter import SupabaseAgenticMemorySystem

# Initialize the system
memory_system = SupabaseAgenticMemorySystem(
    user_id="user123",
    model_name="all-MiniLM-L6-v2",
    llm_backend="openai",
    llm_model="gpt-4o-mini"
)

# Add a memory
memory_id = memory_system.add_note(
    content="Important information about the project",
    context="Project Planning",
    category="Work"
)

# Search for related memories
related = memory_system.get_related_memories("project planning", k=5)

# Get memory statistics
stats = memory_system.get_memory_statistics()
```

### Direct Supabase Client

```python
from database.supabase_client import SupabaseMemoryClient

client = SupabaseMemoryClient()

# Test connection
if client.test_connection():
    print("Connected to Supabase!")

# Create memory with embedding
memory_id = client.create_memory(
    content="Python is great for AI development",
    embedding=[0.1, 0.2, ...],  # Vector embedding
    category="Programming",
    user_id="user123"
)

# Hybrid search (text + semantic)
results = client.hybrid_search_memories(
    query="AI development",
    limit=10,
    user_id="user123"
)
```

### Frontend Integration

```javascript
// Chat with the assistant
const response = await fetch("/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message: "Tell me about machine learning",
    session_id: "session-123",
    user_id: "user-456",
  }),
});

const data = await response.json();
console.log(data.response); // Assistant's response
```

## Migration from Local System

```python
from database.supabase_utils import SupabaseMigrationTool
from memory import AgenticMemorySystem

# Load existing local system
local_system = AgenticMemorySystem()

# Initialize migration tool
migration_tool = SupabaseMigrationTool(supabase_client)

# Migrate all memories
results = migration_tool.migrate_local_memories_to_supabase(
    local_memory_system=local_system,
    user_id="migrated_user"
)

print(f"Migrated {results['migrated_memories']} memories")
```

## Maintenance and Utilities

### Backup and Restore

```python
from database.supabase_utils import SupabaseBackupTool

backup_tool = SupabaseBackupTool(supabase_client)

# Create backup
backup_tool.create_backup("backup.json", user_id="user123")

# Restore backup
backup_tool.restore_backup("backup.json", user_id="user123")
```

### Database Maintenance

```python
from database.supabase_utils import SupabaseMaintenanceTool

maintenance = SupabaseMaintenanceTool(supabase_client)

# Clean up old memories
cleanup_results = maintenance.cleanup_old_memories(
    days_old=365,
    min_retrieval_count=1,
    dry_run=False
)

# Get database statistics
stats = maintenance.get_database_statistics()
```

## Configuration

### Environment Variables

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
OPENAI_API_KEY=your-openai-key

# Optional
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_DB_PASSWORD=your-db-password
```

### Custom Configuration

```python
from database.supabase_config import SupabaseConfig, SupabaseConfigManager

# Custom configuration
config = SupabaseConfig(
    url="https://your-project.supabase.co",
    key="your-key",
    table_prefix="custom_",
    enable_rls=True
)

# Use with client
client = SupabaseMemoryClient(config)
```

## Performance Optimization

### Indexing

The schema includes optimized indexes for:

- Vector similarity search (HNSW index)
- Full-text search (GIN index)
- User-based queries (B-tree indexes)
- Timestamp-based queries

### Caching

- LLM responses are cached in memory
- Vector embeddings are stored once and reused
- Database connections are pooled

### Scaling

- Horizontal scaling via Supabase
- Connection pooling for high concurrency
- Background processing for heavy operations

## Security

### Row Level Security (RLS)

All tables have RLS policies that ensure:

- Users can only access their own data
- Anonymous access is properly controlled
- Service role has admin access when needed

### API Security

- CORS enabled for frontend integration
- Input validation on all endpoints
- Error handling without information leakage

## Troubleshooting

### Common Issues

1. **Connection Failed**

   - Check SUPABASE_URL and keys
   - Verify network connectivity
   - Ensure Supabase project is active

2. **Schema Errors**

   - Run the SQL schema from `supabase_schema.sql`
   - Check table permissions
   - Verify pgvector extension is enabled

3. **Import Errors**
   - Install all requirements: `pip install -r requirements.txt`
   - Check Python path configuration
   - Verify Supabase client installation

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show all Supabase API calls and responses
```

### Testing

```bash
# Run all tests
python src/api/test_supabase_api.py

# Test specific components
python -c "from database.supabase_client import SupabaseMemoryClient; print(SupabaseMemoryClient().test_connection())"
```

## Contributing

When contributing to the Supabase integration:

1. Follow the existing code structure
2. Add appropriate error handling
3. Include docstrings for new methods
4. Update tests for new functionality
5. Document any schema changes

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the database logs in Supabase dashboard
3. Enable debug logging for detailed information
4. Check the demo frontend at `/demo` for working examples

## License

This integration follows the same license as the main AgenticMemory project.
