#!/usr/bin/env python3
"""
Start script for AgenticMemory with Supabase backend.

This script provides an easy way to start the AgenticMemory system
with Supabase integration.
"""

import os
import sys
import subprocess
from pathlib import Path


def print_banner():
    """Print the startup banner."""
    print("=" * 60)
    print("  AgenticMemory with Supabase Backend")
    print("=" * 60)


def check_environment():
    """Check if environment is properly configured."""
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "OPENAI_API_KEY"]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables or run setup_supabase.py first.")
        return False

    print("✅ Environment variables configured")
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import supabase
        import flask
        import sentence_transformers

        print("✅ Dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False


def start_api_server():
    """Start the Flask API server."""
    print("\n🚀 Starting AgenticMemory API server...")
    print("   API will be available at: http://localhost:5000")
    print("   Demo interface at: http://localhost:5000/demo")
    print("   Press Ctrl+C to stop\n")

    # Start the Flask app
    api_path = Path(__file__).parent / "src" / "api" / "chat_api.py"

    try:
        subprocess.run([sys.executable, str(api_path)], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        return False

    return True


def main():
    """Main function to start the system."""
    print_banner()

    # Check prerequisites
    if not check_environment():
        print("\n💡 Tip: Run 'python setup_supabase.py' to configure your environment")
        return False

    if not check_dependencies():
        return False

    # Start the server
    return start_api_server()


if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
