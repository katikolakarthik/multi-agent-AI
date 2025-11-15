"""
Multi-agent system for code review
"""
from typing import List
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage
from models import CodeDiff, ReviewComment, ReviewCategory
from config import settings
from watsonx_llm import WatsonxChat
from openrouter_llm import OpenRouterChat
import json
import re


class ReviewAgent:
    """Base class for review agents"""
    
    def __init__(self, category: ReviewCategory, system_prompt: str):
        self.category = category
        self.system_prompt = system_prompt
        self._llm = None  # Lazy initialization
    
    @property
    def llm(self):
        """Lazy-load LLM on first access"""
        if self._llm is None:
            self._llm = self._get_llm()
        return self._llm
    
    def _get_llm(self):
        """Initialize LLM based on configuration"""
        if settings.llm_provider == "openrouter":
            if not settings.openrouter_api_key:
                raise ValueError(
                    "OpenRouter API key is required. "
                    "Please create a .env file with OPENROUTER_API_KEY. "
                    "You can copy .env.example to .env and fill in your credentials."
                )
            return OpenRouterChat(
                api_key=settings.openrouter_api_key,
                model_id=settings.model_name,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )
        elif settings.llm_provider == "watsonx":
            if not settings.watsonx_api_key or not settings.watsonx_project_id:
                raise ValueError(
                    "Watsonx API key and project ID are required. "
                    "Please create a .env file with WATSONX_API_KEY and WATSONX_PROJECT_ID. "
                    "You can copy .env.example to .env and fill in your credentials."
                )
            # Get URL - remove protocol if present, watsonx_llm will add it
            watsonx_url = settings.watsonx_url or "us-south.ml.cloud.ibm.com"
            # Remove protocol prefix if present
            if watsonx_url.startswith("http://") or watsonx_url.startswith("https://"):
                watsonx_url = watsonx_url.replace("http://", "").replace("https://", "")
            
            return WatsonxChat(
                api_key=settings.watsonx_api_key,
                project_id=settings.watsonx_project_id,
                url=watsonx_url,
                model_id=settings.model_name,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )
        elif settings.llm_provider == "anthropic":
            return ChatAnthropic(
                model=settings.model_name if "claude" in settings.model_name else "claude-3-opus-20240229",
                temperature=settings.temperature,
                api_key=settings.anthropic_api_key
            )
        else:
            return ChatOpenAI(
                model=settings.model_name if "gpt" in settings.model_name else "gpt-4-turbo-preview",
                temperature=settings.temperature,
                api_key=settings.openai_api_key
            )
    
    async def review(self, diff: CodeDiff) -> List[ReviewComment]:
        """Review a code diff and return comments"""
        prompt = self._build_prompt(diff)
        try:
            response = await self.llm.ainvoke(prompt)
            
            # Parse the response - handle both string and object responses
            # ChatOpenAI returns AIMessage which has .content attribute
            if hasattr(response, 'content'):
                response_text = response.content
            elif isinstance(response, str):
                response_text = response
            elif hasattr(response, 'text'):  # Some langchain versions use .text
                response_text = response.text
            else:
                response_text = str(response)
        except Exception as e:
            # Log the error and re-raise
            error_msg = f"Error calling LLM for {self.category.value} review: {str(e)}"
            print(f"Warning: {error_msg}")
            raise Exception(error_msg)
        
        comments = self._parse_response(response_text, diff.file_path)
        return comments
    
    def _build_prompt(self, diff: CodeDiff) -> List:
        """Build the prompt for the agent"""
        # Limit diff text size to avoid token limits and speed up processing
        MAX_DIFF_LENGTH = 5000  # Limit to ~5000 chars per file
        diff_text_limited = diff.diff_text[:MAX_DIFF_LENGTH] if len(diff.diff_text) > MAX_DIFF_LENGTH else diff.diff_text
        if len(diff.diff_text) > MAX_DIFF_LENGTH:
            diff_text_limited += "\n... (diff truncated for review)"
        
        # Limit code content size
        new_content_limited = (diff.new_content or "N/A")[:2000] if diff.new_content and len(diff.new_content) > 2000 else (diff.new_content or "N/A")
        old_content_limited = (diff.old_content or "N/A")[:2000] if diff.old_content and len(diff.old_content) > 2000 else (diff.old_content or "N/A")
        
        code_context = f"""
File: {diff.file_path}

Diff:
{diff_text_limited}

New Code:
{new_content_limited}

Old Code:
{old_content_limited}
"""
        
        return [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
Please review the following code changes and identify issues related to {self.category.value}.

{code_context}

Provide your review in the following JSON format:
{{
    "comments": [
        {{
            "line_number": <line number>,
            "severity": "<critical|major|minor|suggestion>",
            "title": "<brief title>",
            "description": "<detailed description>",
            "code_snippet": "<relevant code snippet>",
            "suggestion": "<suggested fix>"
        }}
    ]
}}

Only include issues that are relevant to {self.category.value}. If no issues are found, return an empty comments array.
""")
        ]
    
    def _parse_response(self, response_text: str, file_path: str) -> List[ReviewComment]:
        """Parse LLM response into ReviewComment objects"""
        comments = []
        
        try:
            # Try to find JSON in the response - look for { ... } pattern
            # First try to find JSON object boundaries more accurately
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx + 1]
                try:
                    data = json.loads(json_str)
                    for comment_data in data.get("comments", []):
                        try:
                            comments.append(ReviewComment(
                                file_path=file_path,
                                line_number=int(comment_data.get("line_number", 0)),
                                category=self.category,
                                severity=comment_data.get("severity", "minor"),
                                title=comment_data.get("title", "Review Comment"),
                                description=comment_data.get("description", ""),
                                code_snippet=comment_data.get("code_snippet"),
                                suggestion=comment_data.get("suggestion")
                            ))
                        except Exception as e:
                            # Skip invalid comment data
                            print(f"Warning: Skipping invalid comment data: {e}")
                            continue
                except json.JSONDecodeError:
                    # Try alternative: look for JSON with code blocks
                    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(1))
                            for comment_data in data.get("comments", []):
                                comments.append(ReviewComment(
                                    file_path=file_path,
                                    line_number=int(comment_data.get("line_number", 0)),
                                    category=self.category,
                                    severity=comment_data.get("severity", "minor"),
                                    title=comment_data.get("title", "Review Comment"),
                                    description=comment_data.get("description", ""),
                                    code_snippet=comment_data.get("code_snippet"),
                                    suggestion=comment_data.get("suggestion")
                                ))
                        except:
                            pass
            
            # If no valid JSON found, create a fallback comment
            if not comments:
                # Try to extract any useful information from the response
                description = response_text.strip()
                if len(description) > 1000:
                    description = description[:1000] + "..."
                
                comments.append(ReviewComment(
                    file_path=file_path,
                    line_number=0,
                    category=self.category,
                    severity="minor",
                    title="Review Note",
                    description=description
                ))
        except Exception as e:
            # Ultimate fallback: create a single comment with the raw response
            print(f"Error parsing response: {e}")
            comments.append(ReviewComment(
                file_path=file_path,
                line_number=0,
                category=self.category,
                severity="minor",
                title="Review Note",
                description=response_text[:500] if response_text else "No response received"
            ))
        
        return comments


class LogicReviewAgent(ReviewAgent):
    """Agent specialized in logic and correctness issues"""
    
    def __init__(self):
        system_prompt = """You are an expert code reviewer specializing in logic and correctness.
Your role is to identify:
- Logic errors and bugs
- Edge cases not handled
- Incorrect algorithm implementations
- Missing null/error checks
- Incorrect data transformations
- Race conditions
- Off-by-one errors
- Incorrect conditional logic

Be thorough and specific. Focus on issues that could cause bugs or incorrect behavior."""
        super().__init__(ReviewCategory.LOGIC, system_prompt)


class ReadabilityReviewAgent(ReviewAgent):
    """Agent specialized in code readability and maintainability"""
    
    def __init__(self):
        system_prompt = """You are an expert code reviewer specializing in code readability and maintainability.
Your role is to identify:
- Unclear variable/function names
- Complex code that could be simplified
- Missing or unclear comments
- Code organization issues
- Inconsistent coding style
- Long functions that should be split
- Magic numbers that should be constants
- Duplicated code

Focus on making code easier to understand and maintain."""
        super().__init__(ReviewCategory.READABILITY, system_prompt)


class PerformanceReviewAgent(ReviewAgent):
    """Agent specialized in performance issues"""
    
    def __init__(self):
        system_prompt = """You are an expert code reviewer specializing in performance optimization.
Your role is to identify:
- Inefficient algorithms (O(n²) when O(n) is possible)
- Unnecessary database queries or API calls
- Missing caching opportunities
- Inefficient data structures
- Memory leaks or excessive memory usage
- N+1 query problems
- Unoptimized loops
- Missing indexes on database queries
- Inefficient string concatenation

Focus on performance bottlenecks and optimization opportunities."""
        super().__init__(ReviewCategory.PERFORMANCE, system_prompt)


class SecurityReviewAgent(ReviewAgent):
    """Agent specialized in security vulnerabilities"""
    
    def __init__(self):
        system_prompt = """You are an expert security code reviewer specializing in identifying vulnerabilities.
Your role is to identify:
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting) vulnerabilities
- Authentication/authorization issues
- Sensitive data exposure
- Insecure random number generation
- Missing input validation
- Path traversal vulnerabilities
- Insecure deserialization
- Hardcoded secrets or credentials
- Insecure cryptographic implementations

Be thorough and prioritize critical security issues."""
        super().__init__(ReviewCategory.SECURITY, system_prompt)


class MultiAgentReviewer:
    """Orchestrates multiple review agents"""
    
    def __init__(self):
        self.all_agents = {
            "logic": LogicReviewAgent(),
            "readability": ReadabilityReviewAgent(),
            "performance": PerformanceReviewAgent(),
            "security": SecurityReviewAgent()
        }
        self.agents = list(self.all_agents.values())
    
    def get_agents_for_review(self, quick_mode: bool = False):
        """Get agents to use based on review mode"""
        if quick_mode:
            # Quick mode: only Logic and Security (most critical)
            return [self.all_agents["logic"], self.all_agents["security"]]
        return self.agents
    
    async def review_diff(self, diff: CodeDiff, quick_mode: bool = False) -> List[ReviewComment]:
        """Run all agents on a diff and collect comments"""
        all_comments = []
        
        # Get agents to use based on mode
        agents_to_use = self.get_agents_for_review(quick_mode)
        
        # Run agents sequentially with minimal delay to avoid rate limits
        # Watsonx has rate limit of 2 requests per second
        import asyncio
        for i, agent in enumerate(agents_to_use):
            max_retries = 2  # Reduced retries for faster failure
            retry_delay = 0.8  # Reduced initial delay
            
            for attempt in range(max_retries):
                try:
                    # Add delay between requests to respect rate limits
                    # 0.55s delay = ~1.8 req/s, safely under 2 req/s limit
                    if i > 0 or attempt > 0:
                        await asyncio.sleep(0.55)  # Reduced from 0.6s
                    
                    comments = await agent.review(diff)
                    all_comments.extend(comments)
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    error_str = str(e)
                    # Check if it's a rate limit error
                    if "429" in error_str or "rate_limit" in error_str.lower():
                        if attempt < max_retries - 1:
                            # Exponential backoff for rate limits
                            wait_time = retry_delay * (2 ** attempt)
                            print(f"Rate limit hit for {agent.category.value} agent. Waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # Max retries reached - skip this agent
                            print(f"Warning: {agent.category.value} agent skipped due to rate limiting")
                    else:
                        # Non-rate-limit error - skip this agent
                        print(f"Warning: {agent.category.value} agent failed: {str(e)[:100]}")
                    
                    # Don't add fallback comment for rate limits to keep response clean
                    if "429" not in error_str and "rate_limit" not in error_str.lower():
                        all_comments.append(ReviewComment(
                            file_path=diff.file_path,
                            line_number=0,
                            category=agent.category,
                            severity="minor",
                            title=f"{agent.category.value.title()} Review Error",
                            description=f"Could not complete {agent.category.value} review: {str(e)[:200]}"
                        ))
                    break  # Exit retry loop
        
        # Sort by line number and severity
        all_comments.sort(key=lambda x: (x.line_number, x.severity == "critical", x.severity == "major"))
        
        return all_comments
    
    async def review_diffs(self, diffs: List[CodeDiff], quick_mode: bool = False) -> List[ReviewComment]:
        """Review multiple diffs"""
        all_comments = []
        
        for diff in diffs:
            comments = await self.review_diff(diff, quick_mode)
            all_comments.extend(comments)
        
        return all_comments

