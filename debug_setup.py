"""
Debug script to check environment variables and basic imports.
"""

import os
import sys


def check_environment():
    """Check if all required environment variables are set."""
    print("🔍 Environment Variables Check")
    print("=" * 40)

    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "OPENAI_API_KEY"]

    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(
                f"✅ {var}: {value[:30]}..."
                if len(value) > 30
                else f"✅ {var}: {value}"
            )
        else:
            print(f"❌ {var}: Not set")

    print()
    return all(os.getenv(var) for var in required_vars)


def check_imports():
    """Check if we can import the required modules."""
    print("🔍 Import Check")
    print("=" * 40)

    # Add src to path
    current_dir = os.path.dirname(__file__)
    src_path = os.path.join(current_dir, "src")
    sys.path.insert(0, src_path)
    sys.path.insert(0, current_dir)

    print(f"Current directory: {current_dir}")
    print(f"Source path: {src_path}")
    print(f"Python path (first 3): {sys.path[:3]}")

    imports_success = True

    try:
        from src.database.supabase_memory_adapter_v2 import SupabaseAgenticMemorySystem

        print("✅ SupabaseAgenticMemorySystem imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import SupabaseAgenticMemorySystem: {e}")
        imports_success = False

    try:
        from src.database.supabase_client import SupabaseMemoryClient

        print("✅ SupabaseMemoryClient imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import SupabaseMemoryClient: {e}")
        imports_success = False

    try:
        from src.database.supabase_config import SupabaseConfigManager

        print("✅ SupabaseConfigManager imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import SupabaseConfigManager: {e}")
        imports_success = False

    return imports_success


def check_file_structure():
    """Check if the required files exist."""
    print("\n🔍 File Structure Check")
    print("=" * 40)

    current_dir = os.path.dirname(__file__)

    required_files = [
        "src/database/supabase_memory_adapter_v2.py",
        "src/database/supabase_client.py",
        "src/database/supabase_config.py",
        "src/memory.py",
        "src/llm_controllers.py",
        "src/retrievers.py",
    ]

    all_files_exist = True

    for file_path in required_files:
        full_path = os.path.join(current_dir, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - File not found")
            all_files_exist = False

    return all_files_exist


def test_basic_connection():
    """Test basic connection to Supabase."""
    print("\n🔍 Basic Connection Test")
    print("=" * 40)

    try:
        # Add src to path
        current_dir = os.path.dirname(__file__)
        src_path = os.path.join(current_dir, "src")
        sys.path.insert(0, src_path)
        sys.path.insert(0, current_dir)

        from src.database.supabase_client import SupabaseMemoryClient

        print("Creating Supabase client...")
        client = SupabaseMemoryClient()

        print("Testing connection...")
        if client.test_connection():
            print("✅ Supabase connection successful")
            return True
        else:
            print("❌ Supabase connection failed")
            return False

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all checks."""
    print("🚀 AgenticMemory Debug Script")
    print("=" * 50)

    # Check environment variables
    env_ok = check_environment()

    # Check file structure
    files_ok = check_file_structure()

    # Check imports
    imports_ok = check_imports()

    # Test connection only if previous checks pass
    connection_ok = False
    if env_ok and files_ok and imports_ok:
        connection_ok = test_basic_connection()

    # Summary
    print("\n📊 Summary")
    print("=" * 40)
    print(f"Environment Variables: {'✅' if env_ok else '❌'}")
    print(f"File Structure: {'✅' if files_ok else '❌'}")
    print(f"Imports: {'✅' if imports_ok else '❌'}")
    print(f"Supabase Connection: {'✅' if connection_ok else '❌'}")

    if all([env_ok, files_ok, imports_ok, connection_ok]):
        print("\n🎉 All checks passed! You can run the main test script.")
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")

        if not env_ok:
            print("\n💡 To set environment variables:")
            print("Windows (PowerShell):")
            print('$env:SUPABASE_URL="https://your-project.supabase.co"')
            print('$env:SUPABASE_KEY="your-anon-key"')
            print('$env:OPENAI_API_KEY="your-openai-key"')
            print("\nWindows (Command Prompt):")
            print("set SUPABASE_URL=https://your-project.supabase.co")
            print("set SUPABASE_KEY=your-anon-key")
            print("set OPENAI_API_KEY=your-openai-key")
            print("\nLinux/Mac:")
            print('export SUPABASE_URL="https://your-project.supabase.co"')
            print('export SUPABASE_KEY="your-anon-key"')
            print('export OPENAI_API_KEY="your-openai-key"')


if __name__ == "__main__":
    main()
