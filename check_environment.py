#!/usr/bin/env python3
"""
Environment Variable Checker for AgenticMemory System

This script helps verify that all required environment variables are properly set
for the Supabase AgenticMemory system.
"""

import os
import sys
from datetime import datetime


def check_environment_variables():
    """Check all required environment variables for the system."""

    print("🔍 AgenticMemory Environment Variable Checker")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print()

    # Define required environment variables
    required_vars = {
        "SUPABASE_URL": {
            "description": "Supabase project URL",
            "example": "https://your-project-id.supabase.co",
            "required": True,
        },
        "SUPABASE_ANON_KEY": {
            "description": "Supabase anonymous/public key",
            "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "required": True,
        },
        "SUPABASE_SERVICE_ROLE_KEY": {
            "description": "Supabase service role key (for admin operations)",
            "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "required": False,
        },
        "OPENAI_API_KEY": {
            "description": "OpenAI API key for LLM operations",
            "example": "sk-proj-...",
            "required": True,
        },
    }

    all_good = True
    missing_required = []

    print("📋 Environment Variable Status:")
    print("-" * 40)

    for var_name, config in required_vars.items():
        value = os.getenv(var_name)

        if value:
            # Show partial value for security
            if "KEY" in var_name.upper():
                if len(value) > 8:
                    display_value = f"{value[:4]}...{value[-4:]}"
                else:
                    display_value = "*" * len(value)
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value

            status = "✅"
            print(f"{status} {var_name}")
            print(f"   Value: {display_value}")
            print(f"   Description: {config['description']}")
        else:
            if config["required"]:
                status = "❌"
                all_good = False
                missing_required.append(var_name)
            else:
                status = "⚠️ "

            print(f"{status} {var_name}")
            print(
                f"   Status: {'MISSING (Required)' if config['required'] else 'MISSING (Optional)'}"
            )
            print(f"   Description: {config['description']}")
            print(f"   Example: {config['example']}")

        print()

    # Summary
    print("=" * 50)
    if all_good:
        print("🎉 SUCCESS: All required environment variables are set!")
        print("You should be able to run the AgenticMemory system tests.")
    else:
        print(
            f"❌ FAILED: Missing {len(missing_required)} required environment variable(s):"
        )
        for var in missing_required:
            print(f"   - {var}")

        print("\n📋 Setup Instructions:")
        print("-" * 25)
        print("For PowerShell (Windows):")
        for var in missing_required:
            print(f'$env:{var}="your_value_here"')

        print("\nFor Bash (Linux/Mac):")
        for var in missing_required:
            print(f'export {var}="your_value_here"')

        print("\n💡 Tips:")
        print(
            "- Get Supabase credentials from your project settings at https://supabase.com/dashboard"
        )
        print("- Get OpenAI API key from https://platform.openai.com/api-keys")
        print(
            "- Make sure to use the correct key names (SUPABASE_ANON_KEY, not SUPABASE_KEY)"
        )

    return all_good


def test_basic_imports():
    """Test if the basic imports work."""
    print("\n🔬 Testing Basic Imports:")
    print("-" * 30)

    try:
        import supabase

        print("✅ supabase package available")
    except ImportError:
        print("❌ supabase package not installed. Run: pip install supabase")
        return False

    try:
        import openai

        print("✅ openai package available")
    except ImportError:
        print("❌ openai package not installed. Run: pip install openai")
        return False

    try:
        import numpy

        print("✅ numpy package available")
    except ImportError:
        print("❌ numpy package not installed. Run: pip install numpy")
        return False

    return True


if __name__ == "__main__":
    env_ok = check_environment_variables()
    imports_ok = test_basic_imports()

    print("\n" + "=" * 50)
    if env_ok and imports_ok:
        print("🚀 READY: Environment is properly configured!")
        print("You can now run: python test_enhanced_memory_system.py")
    else:
        print("🔧 SETUP NEEDED: Please fix the issues above before proceeding.")
        sys.exit(1)
