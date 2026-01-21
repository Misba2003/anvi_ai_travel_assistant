"""
Test script to verify .env file loading.
Run this from the project root: python test_env.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Same logic as main.py
project_root = Path(__file__).resolve().parent
dotenv_path = project_root / ".env"

print(f"Looking for .env at: {dotenv_path}")
print(f".env exists: {dotenv_path.exists()}\n")

# Load .env
loaded = load_dotenv(dotenv_path=dotenv_path, override=True)

if loaded:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✓ SUCCESS: OPENAI_API_KEY loaded!")
        print(f"  Key length: {len(api_key)} characters")
        print(f"  First 10 chars: {api_key[:10]}...")
        print(f"  Last 4 chars: ...{api_key[-4:]}")
    else:
        print("✗ FAILED: OPENAI_API_KEY is None or empty")
        print("  Make sure your .env file contains: OPENAI_API_KEY=your_key_here")
else:
    print(f"✗ FAILED: Could not load .env file from {dotenv_path}")
    print("  Make sure .env file exists in the project root")

