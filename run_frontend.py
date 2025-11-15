"""
Quick start script for Streamlit frontend
"""
import subprocess
import sys
import os

def main():
    """Run Streamlit app"""
    print("=" * 60)
    print("Lyzr PR Review Agent - Streamlit Frontend")
    print("=" * 60)
    print("\nStarting Streamlit app...")
    print("The app will open in your browser automatically.")
    print("\nMake sure the FastAPI backend is running on http://localhost:8000")
    print("Run 'python run.py' in another terminal to start the backend.\n")
    print("=" * 60)
    
    # Run streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])

if __name__ == "__main__":
    main()

