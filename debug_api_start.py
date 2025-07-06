"""
Debug script to start the AgenticMemory API with detailed logging.

This script helps identify and debug issues in the API startup process.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
current_dir = os.path.dirname(__file__)
src_path = os.path.join(current_dir, "src")
sys.path.insert(0, src_path)
sys.path.insert(0, current_dir)


def setup_debug_logging():
    """Setup detailed logging for debugging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("api_debug.log"),
        ],
    )


def check_environment():
    """Check and display environment configuration."""
    print("🔍 Environment Configuration Check")
    print("=" * 50)

    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "OPENAI_API_KEY"]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if "KEY" in var:
                print(f"✅ {var}: {'*' * 20}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n❌ Missing environment variables: {missing_vars}")
        print("\nExample PowerShell commands to set them:")
        for var in missing_vars:
            print(f'$env:{var}="your_value_here"')
        return False

    print("\n✅ All required environment variables are set!")
    return True


def check_file_structure():
    """Check if required files exist."""
    print("\n📁 File Structure Check")
    print("=" * 50)

    required_files = [
        "src/api/chat_api.py",
        "src/config.py",
        "src/database/supabase_client.py",
        "src/database/supabase_memory_adapter.py",
        "src/database/supabase_config.py",
        "src/llm_controllers.py",
        "src/memory.py",
    ]

    missing_files = []
    for file_path in required_files:
        full_path = Path(current_dir) / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}: NOT FOUND")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        return False

    print("\n✅ All required files exist!")
    return True


def test_imports():
    """Test if all required imports work."""
    print("\n📦 Import Test")
    print("=" * 50)

    try:
        print("Testing basic imports...")
        from flask import Flask

        print("✅ Flask imported successfully")

        from sentence_transformers import SentenceTransformer

        print("✅ SentenceTransformers imported successfully")

        print("\nTesting AgenticMemory imports...")
        from src.config import Config

        print("✅ Config imported successfully")

        from src.database.supabase_client import SupabaseMemoryClient

        print("✅ SupabaseMemoryClient imported successfully")

        from src.database.supabase_memory_adapter import SupabaseAgenticMemorySystem

        print("✅ SupabaseAgenticMemorySystem imported successfully")

        from src.llm_controllers import LLMController

        print("✅ LLMController imported successfully")

        print("\n✅ All imports successful!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False


def test_supabase_connection():
    """Test Supabase connection."""
    print("\n🔗 Supabase Connection Test")
    print("=" * 50)

    try:
        from src.database.supabase_client import SupabaseMemoryClient
        from src.database.supabase_config import SupabaseConfigManager

        config = SupabaseConfigManager.get_config()
        client = SupabaseMemoryClient(config)

        if client.test_connection():
            print("✅ Supabase connection successful!")
            return True
        else:
            print("❌ Supabase connection failed!")
            return False

    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        return False


def start_api_debug():
    """Start the API with debug information."""
    print("\n🚀 Starting AgenticMemory API with Debug Mode")
    print("=" * 50)

    try:
        # Import the API module
        from src.api.chat_api import create_app, initialize_memory_system

        print("Initializing memory system...")
        if initialize_memory_system():
            print("✅ Memory system initialized successfully")

            print("Creating Flask app...")
            app = create_app()

            print("Starting Flask server...")
            print("🌐 API will be available at: http://localhost:5000")
            print("📚 API documentation:")
            print("  - Health check: GET /health")
            print("  - Chat: POST /chat")
            print("  - Add memory: POST /memory/add")
            print("  - Search: POST /memory/search")
            print("  - Statistics: GET /memory/stats")
            print("\nPress Ctrl+C to stop the server")
            print("-" * 50)

            app.run(host="0.0.0.0", port=5000, debug=True)
        else:
            print("❌ Failed to initialize memory system")
            return False

    except Exception as e:
        print(f"❌ Failed to start API: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main function to run all checks and start API."""
    print("🔧 AgenticMemory API Debug Startup")
    print("=" * 60)

    # Setup debug logging
    setup_debug_logging()

    # Run all checks
    checks = [
        ("Environment Variables", check_environment),
        ("File Structure", check_file_structure),
        ("Import Test", test_imports),
        ("Supabase Connection", test_supabase_connection),
    ]

    all_passed = True
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
                print(f"\n❌ {check_name} check failed!")
        except Exception as e:
            print(f"\n❌ {check_name} check failed with exception: {e}")
            all_passed = False

    if all_passed:
        print("\n🎉 All checks passed! Starting API...")
        start_api_debug()
    else:
        print(
            "\n❌ Some checks failed. Please fix the issues above before starting the API."
        )
        print("\nTroubleshooting tips:")
        print("1. Make sure all environment variables are set")
        print("2. Check that all required Python packages are installed")
        print("3. Verify Supabase configuration is correct")
        print("4. Run 'pip install -r requirements.txt' if needed")


if __name__ == "__main__":
    main()
