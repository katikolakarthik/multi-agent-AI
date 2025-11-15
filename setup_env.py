"""
Helper script to set up .env file from .env.example
"""
import os
import shutil

def setup_env():
    """Copy .env.example to .env if it doesn't exist"""
    env_example = ".env.example"
    env_file = ".env"
    
    if os.path.exists(env_file):
        print(f"✓ {env_file} already exists")
        return
    
    if not os.path.exists(env_example):
        print(f"✗ {env_example} not found")
        return
    
    try:
        shutil.copy(env_example, env_file)
        print(f"✓ Created {env_file} from {env_example}")
        print(f"\n⚠️  Please edit {env_file} and add your API keys:")
        print("   - WATSONX_API_KEY")
        print("   - WATSONX_PROJECT_ID")
        print("   - GITHUB_TOKEN (optional)")
    except Exception as e:
        print(f"✗ Error creating {env_file}: {e}")

if __name__ == "__main__":
    setup_env()

