"""
Data models for PR Review Agent
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum


class ReviewCategory(str, Enum):
    """Categories of code review issues"""
    LOGIC = "logic"
    READABILITY = "readability"
    PERFORMANCE = "performance"
    SECURITY = "security"
    BEST_PRACTICES = "best_practices"
    TESTING = "testing"


class ReviewComment(BaseModel):
    """Individual review comment"""
    file_path: str = Field(..., description="Path to the file being reviewed")
    line_number: int = Field(..., description="Line number where the issue occurs")
    category: ReviewCategory = Field(..., description="Category of the issue")
    severity: Literal["critical", "major", "minor", "suggestion"] = Field(
        ..., description="Severity of the issue"
    )
    title: str = Field(..., description="Brief title of the issue")
    description: str = Field(..., description="Detailed description of the issue")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    suggestion: Optional[str] = Field(None, description="Suggested fix or improvement")


class CodeDiff(BaseModel):
    """Represents a code diff"""
    file_path: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    added_lines: List[int] = Field(default_factory=list)
    removed_lines: List[int] = Field(default_factory=list)
    diff_text: str


class PRReviewRequest(BaseModel):
    """Request model for PR review"""
    repo_owner: str = Field(..., description="GitHub repository owner")
    repo_name: str = Field(..., description="GitHub repository name")
    pr_number: int = Field(..., description="Pull request number")
    github_token: Optional[str] = Field(None, description="GitHub personal access token")
    quick_review: bool = Field(False, description="Quick review mode - reviews fewer files and uses fewer agents")


class ManualDiffRequest(BaseModel):
    """Request model for manual diff review"""
    diff_text: str = Field(..., description="Raw diff text")
    file_path: Optional[str] = Field(None, description="Optional file path for context")


class PRReviewResponse(BaseModel):
    """Response model for PR review"""
    pr_number: Optional[int] = None
    repo: Optional[str] = None
    total_files_changed: int
    total_comments: int
    comments: List[ReviewComment]
    summary: str = Field(..., description="Overall summary of the review")
    review_metadata: dict = Field(default_factory=dict)

