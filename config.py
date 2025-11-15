"""
Configuration settings for the PR Review Agent
"""
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    watsonx_api_key: Optional[str] = None
    watsonx_project_id: Optional[str] = None
    watsonx_url: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    github_token: Optional[str] = None
    
    # LLM Configuration
    llm_provider: str = "openrouter"  # "openai", "anthropic", "watsonx", or "openrouter"
    model_name: str = "deepseek/deepseek-chat-v3.1:free"  # OpenRouter model
    temperature: float = 0.5
    max_tokens: int = 500  # Reduced for faster responses (can be increased if needed)
    
    # GitHub Configuration
    github_base_url: str = "https://api.github.com"
    
    # Agent Configuration
    max_agents: int = 4  # Logic, Readability, Performance, Security
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "protected_namespaces": ("settings_",)
    }


settings = Settings()

