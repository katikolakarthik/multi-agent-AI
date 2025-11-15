"""
IBM Watsonx LLM integration for LangChain
"""
from typing import List, Optional, Any
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import BaseLLM
from langchain.schema import Generation, LLMResult
from pydantic import Field
import httpx
import json
from config import settings


# Class-level cache for IAM tokens (shared across instances)
_iam_token_cache: dict = {}
_iam_token_expiry: dict = {}

class WatsonxLLM(BaseLLM):
    """IBM Watsonx LLM wrapper for LangChain"""
    
    watsonx_api_key: str = Field(alias="watsonx_api_key")
    watsonx_project_id: str = Field(alias="watsonx_project_id")
    watsonx_url: str = Field(alias="watsonx_url")
    model_id: str = Field(alias="model_id")
    temperature: float = Field(default=0.5)
    max_tokens: int = Field(default=300)
    
    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True  # Allow both alias and field name
    
    @property
    def _llm_type(self) -> str:
        return "watsonx"
    
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Generate text from prompts - required by BaseLLM"""
        import asyncio
        generations = []
        
        for prompt in prompts:
            text = asyncio.run(self._acall(prompt, stop, run_manager, **kwargs))
            generations.append([Generation(text=text)])
        
        return LLMResult(generations=generations)
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Synchronous call to Watsonx API"""
        import asyncio
        return asyncio.run(self._acall(prompt, stop, run_manager, **kwargs))
    
    async def _get_iam_token(self, api_key: str) -> str:
        """Get IAM access token from IBM using API key (with caching)"""
        import time
        
        # Use class-level cache with API key as key
        cache_key = api_key[:20]  # Use first 20 chars as cache key
        
        # Check cache - IAM tokens typically expire in 1 hour, cache for 50 minutes
        current_time = time.time()
        if (cache_key in _iam_token_cache and 
            cache_key in _iam_token_expiry and 
            current_time < _iam_token_expiry[cache_key]):
            return _iam_token_cache[cache_key]
        
        # Get new token
        iam_url = "https://iam.cloud.ibm.com/identity/token"
        iam_payload = {
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    iam_url,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data=iam_payload
                )
                response.raise_for_status()
                token_data = response.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    raise ValueError("No access token received from IAM service")
                
                # Cache the token (expires in ~1 hour, cache for 50 minutes)
                _iam_token_cache[cache_key] = access_token
                _iam_token_expiry[cache_key] = current_time + (50 * 60)  # 50 minutes
                
                return access_token
        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to get IAM token: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Error getting IAM token: {str(e)}")
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Asynchronous call to Watsonx API"""
        # Get values from Pydantic model - access by field name directly
        try:
            # Direct attribute access - Pydantic should populate these
            url_value = getattr(self, 'watsonx_url', '') or getattr(self, 'url', '')
            api_key_val = getattr(self, 'watsonx_api_key', '') or getattr(self, 'api_key', '')
            project_id_val = getattr(self, 'watsonx_project_id', '') or getattr(self, 'project_id', '')
            model_id_val = getattr(self, 'model_id', '')
            
            # If direct access didn't work, try model_dump
            if not url_value or not isinstance(url_value, str):
                if hasattr(self, 'model_dump'):
                    model_data = self.model_dump(by_alias=False)  # Get by field name
                    url_value = model_data.get('watsonx_url', '')
                    api_key_val = model_data.get('watsonx_api_key', '')
                    project_id_val = model_data.get('watsonx_project_id', '')
                    model_id_val = model_data.get('model_id', '')
        except Exception as e:
            # Ultimate fallback
            print(f"Warning: Error getting model values: {e}")
            url_value = ''
            api_key_val = ''
            project_id_val = ''
            model_id_val = ''
        
        # Ensure we have string values
        url_value = str(url_value).strip() if url_value else ''
        api_key_val = str(api_key_val).strip() if api_key_val else ''
        project_id_val = str(project_id_val).strip() if project_id_val else ''
        model_id_val = str(model_id_val).strip() if model_id_val else ''
        
        # Validate required fields
        if not url_value:
            raise ValueError("Watsonx URL is not configured. Please set WATSONX_URL in your .env file.")
        if not api_key_val:
            raise ValueError("Watsonx API key is not configured. Please set WATSONX_API_KEY in your .env file.")
        if not project_id_val:
            raise ValueError("Watsonx Project ID is not configured. Please set WATSONX_PROJECT_ID in your .env file.")
        if not model_id_val:
            raise ValueError("Watsonx Model ID is not configured. Please set MODEL_NAME in your .env file.")
        
        # Prepare the API endpoint - ensure proper URL format
        base_url = url_value.rstrip('/')
        # Remove http:// or https:// if present, we'll add https://
        base_url = base_url.replace('http://', '').replace('https://', '')
        
        # Construct full URL
        if not base_url:
            raise ValueError("Watsonx URL is empty. Please set WATSONX_URL in your .env file (e.g., us-south.ml.cloud.ibm.com)")
        
        # Ensure we have a valid hostname
        if '.' not in base_url:
            raise ValueError(f"Invalid Watsonx URL format: {base_url}. Expected format: us-south.ml.cloud.ibm.com")
        
        full_base_url = f"https://{base_url}"
        endpoint = f"{full_base_url}/ml/v1/text/generation?version=2023-05-29"
        
        # Watsonx requires IAM access token, not API key directly
        # Get IAM token first
        iam_token = await self._get_iam_token(api_key_val)
        
        # Prepare headers with IAM token
        headers = {
            "Authorization": f"Bearer {iam_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Debug: Check if API key looks valid (should not be empty and should have some length)
        if not api_key_val or len(api_key_val.strip()) < 10:
            raise ValueError(f"Invalid API key format. API key appears to be empty or too short.")
        
        # Prepare request body for Watsonx API
        payload = {
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": 0.9,
                "repetition_penalty": 1.1,
                "stop_sequences": []
            },
            "model_id": model_id_val,
            "project_id": project_id_val
        }
        
        # Make API call
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                # Extract generated text
                if "results" in result and len(result["results"]) > 0:
                    generated_text = result["results"][0].get("generated_text", "")
                    return generated_text
                else:
                    return "No response generated"
                    
            except httpx.ConnectError as e:
                error_msg = f"Failed to connect to Watsonx API at {endpoint}. "
                error_msg += f"Error: {str(e)}. "
                error_msg += "Please check:\n"
                error_msg += "1. Your internet connection\n"
                error_msg += f"2. The WATSONX_URL in .env file (current: {url_value})\n"
                error_msg += "3. The URL format (should be: us-south.ml.cloud.ibm.com or similar)"
                raise Exception(error_msg)
            except httpx.HTTPStatusError as e:
                error_msg = f"Watsonx API error: {e.response.status_code}"
                if e.response.text:
                    try:
                        error_data = e.response.json()
                        error_msg += f" - {error_data}"
                    except:
                        error_msg += f" - {e.response.text}"
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Error calling Watsonx API: {str(e)}"
                if "getaddrinfo" in str(e).lower() or "11001" in str(e):
                    error_msg += f"\n\nDNS resolution failed. Check:\n"
                    error_msg += f"1. WATSONX_URL in .env: {url_value}\n"
                    error_msg += f"2. Network connectivity\n"
                    error_msg += f"3. URL format (should be hostname without http://, e.g., us-south.ml.cloud.ibm.com)"
                raise Exception(error_msg)


class WatsonxChat:
    """Chat interface for Watsonx that mimics LangChain's ChatOpenAI interface"""
    
    def __init__(self, api_key: str, project_id: str, url: str, model_id: str, temperature: float = 0.5, max_tokens: int = 300):
        self.llm = WatsonxLLM(
            watsonx_api_key=api_key,
            watsonx_project_id=project_id,
            watsonx_url=url,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens
        )
        # Cache is now class-level, no need to initialize instance attributes
    
    async def ainvoke(self, messages: List[BaseMessage]) -> Any:
        """Invoke the LLM with messages and return a response object"""
        # Convert messages to prompt
        prompt_parts = []
        for message in messages:
            if isinstance(message, SystemMessage):
                prompt_parts.append(f"System: {message.content}")
            elif isinstance(message, HumanMessage):
                prompt_parts.append(f"Human: {message.content}")
            else:
                prompt_parts.append(str(message.content))
        
        prompt = "\n\n".join(prompt_parts)
        
        # Call the LLM
        response_text = await self.llm._acall(prompt)
        
        # Return a response object that mimics LangChain's response
        class Response:
            def __init__(self, content: str):
                self.content = content
        
        return Response(response_text)

