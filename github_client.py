"""
GitHub API client for fetching PR information and diffs
"""
import httpx
from typing import List, Optional
from models import CodeDiff
from config import settings
import base64
from urllib.parse import quote


class GitHubClient:
    """Client for interacting with GitHub API"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.github_token
        self.base_url = settings.github_base_url
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Lyzr-PR-Review-Agent"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Fetch the raw diff for a pull request"""
        # URL encode owner and repo to handle special characters
        owner_encoded = quote(owner.strip(), safe='')
        repo_encoded = quote(repo.strip(), safe='')
        
        # Use GitHub API to get diff directly with Accept header for diff format
        url = f"{self.base_url}/repos/{owner_encoded}/{repo_encoded}/pulls/{pr_number}"
        
        # Headers for getting diff format
        diff_headers = self.headers.copy()
        diff_headers["Accept"] = "application/vnd.github.v3.diff"
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            # First verify PR exists
            response = await client.get(url, headers=self.headers)
            
            if response.status_code == 404:
                raise ValueError(
                    f"PR #{pr_number} not found in repository '{owner}/{repo}'. "
                    f"Please check that the repository exists and the PR number is correct."
                )
            elif response.status_code == 403:
                raise ValueError(
                    f"Access denied to repository '{owner}/{repo}'. "
                    f"This might be a private repository. Please provide a GitHub token."
                )
            
            response.raise_for_status()
            
            # Now fetch the diff with diff format header
            diff_response = await client.get(url, headers=diff_headers)
            
            if diff_response.status_code == 404:
                raise ValueError(
                    f"PR #{pr_number} not found in repository '{owner}/{repo}'. "
                    f"Please check that the repository exists and the PR number is correct."
                )
            elif diff_response.status_code == 403:
                raise ValueError(
                    f"Access denied to repository '{owner}/{repo}'. "
                    f"This might be a private repository. Please provide a GitHub token."
                )
            
            diff_response.raise_for_status()
            return diff_response.text
    
    async def get_pr_info(self, owner: str, repo: str, pr_number: int) -> dict:
        """Get PR metadata"""
        # URL encode owner and repo to handle special characters
        owner_encoded = quote(owner.strip(), safe='')
        repo_encoded = quote(repo.strip(), safe='')
        url = f"{self.base_url}/repos/{owner_encoded}/{repo_encoded}/pulls/{pr_number}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code == 404:
                raise ValueError(
                    f"PR #{pr_number} not found in repository '{owner}/{repo}'. "
                    f"Please check that the repository exists and the PR number is correct."
                )
            elif response.status_code == 403:
                raise ValueError(
                    f"Access denied to repository '{owner}/{repo}'. "
                    f"This might be a private repository. Please provide a GitHub token."
                )
            
            response.raise_for_status()
            return response.json()
    
    async def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[dict]:
        """Get list of files changed in PR"""
        # URL encode owner and repo to handle special characters
        owner_encoded = quote(owner.strip(), safe='')
        repo_encoded = quote(repo.strip(), safe='')
        url = f"{self.base_url}/repos/{owner_encoded}/{repo_encoded}/pulls/{pr_number}/files"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> Optional[str]:
        """Get file content from repository"""
        # URL encode owner, repo, and path to handle special characters
        owner_encoded = quote(owner.strip(), safe='')
        repo_encoded = quote(repo.strip(), safe='')
        path_encoded = quote(path, safe='/')
        url = f"{self.base_url}/repos/{owner_encoded}/{repo_encoded}/contents/{path_encoded}"
        params = {"ref": ref}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("encoding") == "base64":
                    content = base64.b64decode(data["content"]).decode("utf-8")
                    return content
                return data.get("content")
            except httpx.HTTPStatusError:
                return None

