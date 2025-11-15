"""
Quick start script for the PR Review Agent
"""
import uvicorn
import os
from config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("Lyzr PR Review Agent")
    print("=" * 60)
    print(f"LLM Provider: {settings.llm_provider}")
    print(f"Model: {settings.model_name}")
    print(f"Server: http://localhost:8000")
    print(f"Docs: http://localhost:8000/docs")
    print("=" * 60)
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("\n⚠️  WARNING: .env file not found!")
        print("   Run 'python setup_env.py' to create it from .env.example")
        print("   Or manually create .env with your API keys\n")
    elif settings.llm_provider == "watsonx" and (not settings.watsonx_api_key or not settings.watsonx_project_id):
        print("\n⚠️  WARNING: Watsonx credentials not found in .env file!")
        print("   Please add WATSONX_API_KEY and WATSONX_PROJECT_ID to .env\n")
    else:
        print("\n✓ Configuration looks good!\n")
    
    print("Starting server...\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

