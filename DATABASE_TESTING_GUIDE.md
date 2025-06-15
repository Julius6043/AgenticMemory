# Database Testing and Examples Guide

This directory contains comprehensive testing and example scripts for the Supabase database integration in AgenticMemory.

## 📁 Scripts Overview

### 🧪 `test_database.py`

**Comprehensive test suite for all database components**

- Tests Supabase client functionality
- Tests memory adapter operations
- Tests utility functions
- Validates database connectivity and operations
- Provides detailed test results and diagnostics

```bash
python test_database.py
```

**Features:**

- ✅ Memory CRUD operations
- ✅ Search functionality (text, semantic, hybrid)
- ✅ Chat session management
- ✅ Statistics and analytics
- ✅ Utility tool validation
- ✅ Error handling and cleanup

### 📚 `examples_database.py`

**Practical examples demonstrating database usage**

- Real-world usage scenarios
- Step-by-step demonstrations
- Best practices and patterns
- Multiple user workflows

```bash
python examples_database.py
```

**Examples Include:**

1. **Basic Memory Operations** - Creating, updating, retrieving memories
2. **Search and Retrieval** - Text search, category filtering, tag-based search
3. **Memory System Usage** - Using AgenticMemorySystem with Supabase
4. **Chat Sessions** - Managing conversations and message history
5. **Utilities and Maintenance** - Database statistics, backup operations
6. **Advanced Search** - Hybrid search, similarity thresholds, multi-tag filtering

### ⚡ `benchmark_database.py`

**Performance benchmarking and optimization**

- Measures operation speed and throughput
- Tests concurrent operations
- Identifies performance bottlenecks
- Provides optimization recommendations

```bash
python benchmark_database.py
```

**Benchmarks:**

- 📝 Memory creation rates
- 🔍 Retrieval performance
- 🔎 Search operation speeds
- 📦 Batch operation efficiency
- 🧠 Memory system performance
- ⚡ Concurrent operation handling

## 🚀 Quick Start

### Prerequisites

1. **Environment Setup:**

   ```bash
   export SUPABASE_URL="https://your-project.supabase.co"
   export SUPABASE_ANON_KEY="your-anon-key"
   export OPENAI_API_KEY="your-openai-key"
   ```

2. **Database Schema:**

   - Apply the SQL schema from `src/database/supabase_schema.sql`
   - Ensure pgvector extension is enabled

3. **Dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r src/database/requirements_supabase.txt
   ```

### Running Tests

```bash
# 1. Test database functionality
python test_database.py

# 2. Run examples to see usage patterns
python examples_database.py

# 3. Benchmark performance (optional)
python benchmark_database.py
```

## 📊 Test Results Interpretation

### ✅ Success Indicators

- All connection tests pass
- CRUD operations work correctly
- Search returns relevant results
- No database errors or timeouts

### ❌ Common Issues

1. **Connection Failed**

   ```
   Solution: Check SUPABASE_URL and SUPABASE_ANON_KEY
   ```

2. **Schema Errors**

   ```
   Solution: Apply the SQL schema from supabase_schema.sql
   ```

3. **Permission Denied**

   ```
   Solution: Check Row Level Security policies in Supabase
   ```

4. **Embedding Errors**
   ```
   Solution: Ensure pgvector extension is enabled
   ```

## 🔧 Customizing Tests

### Adding New Test Cases

```python
def test_custom_functionality(self):
    """Add your custom test case."""
    try:
        # Your test logic here
        result = self.client.custom_operation()

        if result:
            print("   ✅ Custom test passed")
            return True
        else:
            print("   ❌ Custom test failed")
            return False

    except Exception as e:
        print(f"   ❌ Custom test error: {e}")
        return False
```

### Modifying Benchmark Parameters

```python
# In benchmark_database.py
def run_all_benchmarks(self):
    # Customize benchmark parameters
    self.benchmark_memory_creation(100)  # Test 100 memories
    self.benchmark_search_operations(50)  # Test 50 searches
    # Add more benchmarks as needed
```

## 📈 Performance Expectations

### Typical Performance Metrics

| Operation        | Expected Performance  | Notes                       |
| ---------------- | --------------------- | --------------------------- |
| Memory Creation  | 5-15 memories/sec     | Depends on content size     |
| Memory Retrieval | 50-100 retrievals/sec | Single memory lookup        |
| Text Search      | 0.1-0.5s per search   | Simple text queries         |
| Hybrid Search    | 0.5-2s per search     | Includes vector computation |
| Batch Operations | 20-50 items/sec       | Bulk database operations    |

### Performance Factors

- **Network Latency**: Distance to Supabase servers
- **Database Load**: Number of concurrent users
- **Query Complexity**: Search parameters and filters
- **Memory Size**: Content length and metadata volume

## 🛠️ Troubleshooting

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show all database queries and responses
```

### Test Individual Components

```python
# Test only the Supabase client
from src.database.supabase_client import SupabaseMemoryClient
client = SupabaseMemoryClient()
print("Connection:", client.test_connection())

# Test only the memory adapter
from src.database.supabase_memory_adapter import SupabaseAgenticMemorySystem
system = SupabaseAgenticMemorySystem(user_id="test")
print("System ready:", system is not None)
```

### Database Inspection

Check your Supabase dashboard:

1. **Database** → **Tables** → Verify tables exist
2. **Authentication** → **Users** → Check RLS policies
3. **Database** → **Extensions** → Ensure pgvector is enabled
4. **API** → **Logs** → Check for error messages

## 🎯 Best Practices

### Test Environment

- Use a separate Supabase project for testing
- Don't run tests against production data
- Clean up test data after completion

### Performance Testing

- Run benchmarks during off-peak hours
- Test with realistic data volumes
- Monitor Supabase dashboard during tests

### Error Handling

- Always include try/catch blocks
- Log detailed error information
- Implement proper cleanup procedures

## 📚 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [pgvector Guide](https://github.com/pgvector/pgvector)
- [AgenticMemory Documentation](../SUPABASE_INTEGRATION.md)

## 🤝 Contributing

When adding new tests or examples:

1. Follow the existing code structure
2. Include proper error handling
3. Add cleanup procedures
4. Document expected behavior
5. Test with different data scenarios

## 📞 Support

If tests fail or you encounter issues:

1. Check the troubleshooting section above
2. Review Supabase dashboard logs
3. Verify environment configuration
4. Test individual components separately
5. Check network connectivity and permissions

---

**Happy testing! 🎉**

These scripts ensure your Supabase integration is working correctly and performing optimally.
