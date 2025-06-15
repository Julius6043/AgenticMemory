#!/usr/bin/env python3
"""
Startup script for the AgenticMemory Chat API.
This script handles dependency installation and server startup.
"""

import subprocess
import sys
import os
from pathlib import Path


def install_requirements():
    """Install required packages."""
    print("🔧 Installing API requirements...")

    # Install API-specific requirements
    api_requirements = Path(__file__).parent / "requirements_api.txt"
    if api_requirements.exists():
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(api_requirements)]
        )

    # Install main project requirements
    main_requirements = Path(__file__).parent.parent.parent / "requirements.txt"
    if main_requirements.exists():
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(main_requirements)]
        )

    print("✅ Requirements installed successfully!")


def check_environment():
    """Check if required environment variables are set."""
    print("🔍 Checking environment...")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set!")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        print("   Or on Windows: set OPENAI_API_KEY=your-key-here")
        return False

    print("✅ Environment check passed!")
    return True


def start_server():
    """Start the Flask development server."""
    print("🚀 Starting AgenticMemory Chat API server...")
    print("📱 API will be available at: http://localhost:5000")
    print("🌐 Demo frontend will be available at: http://localhost:5000/demo")
    print("💡 Press Ctrl+C to stop the server")
    print("-" * 50)

    # Import and run the Flask app
    from chat_api import app

    app.run(host="0.0.0.0", port=5000, debug=True)


def main():
    """Main startup function."""
    print("🧠 AgenticMemory Chat API Startup")
    print("=" * 40)

    try:
        # Install requirements
        install_requirements()

        # Check environment
        env_ok = check_environment()
        if not env_ok:
            print(
                "\n❌ Environment check failed. Please set OPENAI_API_KEY and try again."
            )
            return 1

        # Start server
        start_server()

    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
