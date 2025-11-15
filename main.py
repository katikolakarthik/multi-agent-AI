"""
FastAPI application for PR Review Agent
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import asyncio
import httpx

from models import (
    PRReviewRequest, 
    ManualDiffRequest, 
    PRReviewResponse, 
    ReviewComment,
    ReviewCategory,
    CodeDiff
)
from github_client import GitHubClient
from diff_parser import DiffParser
from agents import MultiAgentReviewer
from config import settings

app = FastAPI(
    title="Lyzr PR Review Agent",
    description="Automated GitHub Pull Request Review Agent with Multi-Agent Architecture",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
github_client = GitHubClient()
diff_parser = DiffParser()
reviewer = MultiAgentReviewer()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Lyzr PR Review Agent API",
        "version": "1.0.0",
        "endpoints": {
            "review_pr": "/api/review/pr",
            "review_diff": "/api/review/diff",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "llm_provider": settings.llm_provider,
        "model": settings.model_name,
        "watsonx_configured": bool(settings.watsonx_api_key and settings.watsonx_project_id) if settings.llm_provider == "watsonx" else None,
        "openrouter_configured": bool(settings.openrouter_api_key) if settings.llm_provider == "openrouter" else None
    }


@app.post("/api/review/pr", response_model=PRReviewResponse)
async def review_pr(request: PRReviewRequest):
    """
    Review a GitHub Pull Request
    
    Fetches the PR diff from GitHub and runs multi-agent review
    """
    try:
        # Use provided token or default
        client = GitHubClient(token=request.github_token) if request.github_token else github_client
        
        # Fetch PR diff
        diff_text = await client.get_pr_diff(
            request.repo_owner,
            request.repo_name,
            request.pr_number
        )
        
        # Get PR info for metadata
        pr_info = await client.get_pr_info(
            request.repo_owner,
            request.repo_name,
            request.pr_number
        )
        
        # Parse diff
        diffs = diff_parser.parse_diff(diff_text)
        
        if not diffs:
            return PRReviewResponse(
                pr_number=request.pr_number,
                repo=f"{request.repo_owner}/{request.repo_name}",
                total_files_changed=0,
                total_comments=0,
                comments=[],
                summary="No code changes found in PR",
                review_metadata={"pr_title": pr_info.get("title", "")}
            )
        
        # Limit number of files to review for faster response
        # Check if quick review mode is requested
        quick_mode = getattr(request, 'quick_review', False)
        
        # For large PRs, review only the most important files
        MAX_FILES_TO_REVIEW = 3 if quick_mode else 5  # Even fewer files in quick mode
        if len(diffs) > MAX_FILES_TO_REVIEW:
            # Review most important files first (prioritize source code files)
            source_files = [d for d in diffs if any(d.file_path.endswith(ext) for ext in ['.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.go', '.rs', '.tsx'])]
            config_files = [d for d in diffs if any(d.file_path.endswith(ext) for ext in ['.json', '.yaml', '.yml', '.toml', '.ini'])]
            other_files = [d for d in diffs if d not in source_files and d not in config_files]
            # Prioritize: source code > config > others
            diffs_to_review = (source_files + config_files + other_files)[:MAX_FILES_TO_REVIEW]
        else:
            diffs_to_review = diffs
        
        # Run multi-agent review on limited files
        all_comments = await reviewer.review_diffs(diffs_to_review, quick_mode=quick_mode)
        
        # Add note if files were limited
        if len(diffs) > MAX_FILES_TO_REVIEW:
            all_comments.append(ReviewComment(
                file_path="",
                line_number=0,
                category=ReviewCategory.READABILITY,
                severity="suggestion",
                title="Review Limited",
                description=f"Note: This PR has {len(diffs)} files. Only the first {MAX_FILES_TO_REVIEW} files were reviewed for faster response. Consider reviewing remaining files separately."
            ))
        
        # Generate summary
        summary = _generate_summary(all_comments, pr_info)
        
        return PRReviewResponse(
            pr_number=request.pr_number,
            repo=f"{request.repo_owner}/{request.repo_name}",
            total_files_changed=len(diffs),
            total_comments=len(all_comments),
            comments=all_comments,
            summary=summary,
            review_metadata={
                "pr_title": pr_info.get("title", ""),
                "pr_author": pr_info.get("user", {}).get("login", ""),
                "pr_state": pr_info.get("state", ""),
                "files_changed": [d.file_path for d in diffs]
            }
        )
    
    except ValueError as e:
        # Handle user-friendly error messages from GitHub client
        raise HTTPException(status_code=404, detail=str(e))
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"PR #{request.pr_number} not found in repository '{request.repo_owner}/{request.repo_name}'. "
                       f"Please check that the repository exists and the PR number is correct."
            )
        elif e.response.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to repository '{request.repo_owner}/{request.repo_name}'. "
                       f"This might be a private repository. Please provide a GitHub token."
            )
        else:
            raise HTTPException(status_code=e.response.status_code, detail=f"GitHub API error: {str(e)}")
    except Exception as e:
        import traceback
        error_detail = str(e)
        error_traceback = traceback.format_exc()
        print(f"Error reviewing PR: {error_detail}")
        print(f"Traceback: {error_traceback}")
        raise HTTPException(status_code=500, detail=f"Error reviewing PR: {error_detail}")


@app.post("/api/review/diff", response_model=PRReviewResponse)
async def review_diff(request: ManualDiffRequest):
    """
    Review a manual diff text
    
    Accepts raw diff text and runs multi-agent review
    """
    try:
        # Parse diff
        diffs = diff_parser.parse_diff(request.diff_text)
        
        if not diffs:
            return PRReviewResponse(
                total_files_changed=0,
                total_comments=0,
                comments=[],
                summary="No code changes found in diff",
                review_metadata={}
            )
        
        # Run multi-agent review
        all_comments = await reviewer.review_diffs(diffs)
        
        # Generate summary
        summary = _generate_summary(all_comments, {})
        
        return PRReviewResponse(
            total_files_changed=len(diffs),
            total_comments=len(all_comments),
            comments=all_comments,
            summary=summary,
            review_metadata={
                "files_changed": [d.file_path for d in diffs],
                "source": "manual_diff"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reviewing diff: {str(e)}")


@app.get("/api/review/stats")
async def get_review_stats():
    """Get review statistics"""
    return {
        "agents": {
            "logic": "Identifies logic errors and bugs",
            "readability": "Checks code clarity and maintainability",
            "performance": "Identifies performance bottlenecks",
            "security": "Detects security vulnerabilities"
        },
        "supported_categories": [
            "logic",
            "readability",
            "performance",
            "security",
            "best_practices",
            "testing"
        ],
        "severity_levels": ["critical", "major", "minor", "suggestion"]
    }


def _generate_summary(comments: List[ReviewComment], pr_info: dict) -> str:
    """Generate a summary of the review"""
    if not comments:
        return "✅ No issues found. Code looks good!"
    
    # Count by category
    by_category = {}
    by_severity = {"critical": 0, "major": 0, "minor": 0, "suggestion": 0}
    
    for comment in comments:
        cat = comment.category.value
        by_category[cat] = by_category.get(cat, 0) + 1
        by_severity[comment.severity] = by_severity.get(comment.severity, 0) + 1
    
    summary_parts = [
        f"Found {len(comments)} review comment(s) across {len(set(c.file_path for c in comments))} file(s)."
    ]
    
    if by_severity["critical"] > 0:
        summary_parts.append(f"⚠️ {by_severity['critical']} critical issue(s) found.")
    if by_severity["major"] > 0:
        summary_parts.append(f"🔴 {by_severity['major']} major issue(s) found.")
    
    if by_category:
        summary_parts.append("\nIssues by category:")
        for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            summary_parts.append(f"  - {cat}: {count}")
    
    return "\n".join(summary_parts)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

