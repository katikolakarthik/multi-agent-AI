"""
OpenRouter LLM integration for LangChain
Supports DeepSeek and other models via OpenRouter API
"""
from typing import List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from pydantic import Field


class OpenRouterChat:
    """Chat interface for OpenRouter that mimics LangChain's ChatOpenAI interface"""
    
    def __init__(self, api_key: str, model_id: str, temperature: float = 0.5, max_tokens: int = 500):
        """
        Initialize OpenRouter chat client
        
        Args:
            api_key: OpenRouter API key
            model_id: Model identifier (e.g., 'deepseek/deepseek-chat-v3.1:free')
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        # OpenRouter uses OpenAI-compatible API
        # Format model name correctly (remove :free suffix if present)
        clean_model_id = model_id.replace(":free", "") if ":free" in model_id else model_id
        
        # OpenRouter uses OpenAI-compatible API with custom base URL
        # The api_key parameter will be used for Authorization header automatically
        self.llm = ChatOpenAI(
            model=clean_model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1"
        )
        
        # Store API key for reference
        self.api_key = api_key
    
    async def ainvoke(self, messages: List[BaseMessage]) -> Any:
        """Invoke the LLM with messages and return a response object"""
        try:
            # ChatOpenAI already handles messages directly
            response = await self.llm.ainvoke(messages)
            
            # Return response (ChatOpenAI returns AIMessage with content attribute)
            # Ensure we return an object with .content attribute for compatibility
            if hasattr(response, 'content'):
                return response
            else:
                # Wrap in a simple object if needed
                class Response:
                    def __init__(self, content):
                        self.content = content
                return Response(str(response))
        except Exception as e:
            # Re-raise with more context
            raise Exception(f"OpenRouter API error: {str(e)}")

