#!/usr/bin/env python3
"""
GitHub Code Review Assistant MCP Server

An MCP server that provides comprehensive tools for analyzing pull requests, 
suggesting improvements, checking code patterns, and ensuring consistency with team standards.
"""

import json
import re
import httpx
import asyncio
from typing import Optional, List, Dict, Any, TypedDict
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP

# ==================== Configuration ====================
CHARACTER_LIMIT = 25000  # Maximum response size in characters
API_BASE_URL = "https://api.github.com"
DEFAULT_PAGE_SIZE = 30

# Initialize the MCP server
mcp = FastMCP("github_code_review_mcp")

# ==================== Enums ====================
class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"

class ReviewState(str, Enum):
    """Pull request review states."""
    PENDING = "PENDING"
    COMMENT = "COMMENT"
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    COMMENTED = "COMMENTED"
    APPROVED = "APPROVED"
    DISMISSED = "DISMISSED"

class PRState(str, Enum):
    """Pull request states."""
    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"

class SortDirection(str, Enum):
    """Sort direction."""
    ASC = "asc"
    DESC = "desc"

# ==================== Pydantic Models ====================

class GitHubAuth(BaseModel):
    """GitHub authentication configuration."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    token: str = Field(..., description="GitHub personal access token or GitHub App token", min_length=1)
    
    @field_validator('token')
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Token cannot be empty")
        return v.strip()

# Base models for common parameters
class RepoParams(BaseModel):
    """Common repository parameters."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner (username or organization)", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    github_token: str = Field(..., description="GitHub personal access token with repo access", min_length=1)

class PaginationParams(BaseModel):
    """Common pagination parameters."""
    limit: Optional[int] = Field(default=30, description="Maximum results to return", ge=1, le=100)
    page: Optional[int] = Field(default=1, description="Page number for pagination", ge=1)

# Tool-specific input models
class ListPullRequestsInput(RepoParams, PaginationParams):
    """Input for listing pull requests."""
    state: PRState = Field(default=PRState.OPEN, description="Filter by PR state")
    sort: Optional[str] = Field(default="created", description="Sort by: created, updated, popularity, long-running")
    direction: SortDirection = Field(default=SortDirection.DESC, description="Sort direction")
    base: Optional[str] = Field(default=None, description="Filter by base branch name")
    head: Optional[str] = Field(default=None, description="Filter by head branch name")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetPullRequestDetailsInput(RepoParams):
    """Input for getting pull request details."""
    pr_number: int = Field(..., description="Pull request number", ge=1)
    include_reviews: bool = Field(default=True, description="Include review information")
    include_checks: bool = Field(default=True, description="Include status checks")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetPullRequestFilesInput(RepoParams, PaginationParams):
    """Input for getting PR files."""
    pr_number: int = Field(..., description="Pull request number", ge=1)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetPullRequestDiffInput(RepoParams):
    """Input for getting PR diff."""
    pr_number: int = Field(..., description="Pull request number", ge=1)
    file_path: Optional[str] = Field(default=None, description="Filter diff for specific file path")
    context_lines: Optional[int] = Field(default=3, description="Number of context lines around changes", ge=0, le=10)

class AnalyzePullRequestInput(RepoParams):
    """Input for analyzing a pull request."""
    pr_number: int = Field(..., description="Pull request number", ge=1)
    check_patterns: bool = Field(default=True, description="Check for common code patterns and anti-patterns")
    check_complexity: bool = Field(default=True, description="Analyze code complexity")
    check_security: bool = Field(default=True, description="Basic security checks")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetPullRequestCommentsInput(RepoParams, PaginationParams):
    """Input for getting PR comments."""
    pr_number: int = Field(..., description="Pull request number", ge=1)
    comment_type: str = Field(default="all", description="Type: 'all', 'issue', 'review'")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class CreateReviewCommentInput(RepoParams):
    """Input for creating a review comment."""
    pr_number: int = Field(..., description="Pull request number", ge=1)
    body: str = Field(..., description="Comment text (markdown supported)", min_length=1, max_length=65536)
    commit_id: Optional[str] = Field(default=None, description="SHA of the commit to comment on (defaults to latest)")
    path: Optional[str] = Field(default=None, description="File path to comment on")
    line: Optional[int] = Field(default=None, description="Line number in the file (for line comments)", ge=1)
    side: Optional[str] = Field(default="RIGHT", description="Side of the diff: 'LEFT' or 'RIGHT'")

class CreatePullRequestReviewInput(RepoParams):
    """Input for creating a pull request review."""
    pr_number: int = Field(..., description="Pull request number", ge=1)
    body: Optional[str] = Field(default=None, description="Review summary text (markdown supported)", max_length=65536)
    event: ReviewState = Field(default=ReviewState.COMMENT, description="Review action")
    comments: Optional[List[Dict[str, Any]]] = Field(default=None, description="Inline review comments")

class GetReviewSuggestionsInput(RepoParams):
    """Input for getting AI-powered review suggestions."""
    pr_number: int = Field(..., description="Pull request number", ge=1)
    focus_areas: Optional[List[str]] = Field(
        default=None, 
        description="Areas to focus on: 'performance', 'security', 'readability', 'tests', 'documentation'",
        max_items=5
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class CheckTeamStandardsInput(RepoParams):
    """Input for checking team standards compliance."""
    pr_number: int = Field(..., description="Pull request number", ge=1)
    standards_file: Optional[str] = Field(
        default=".github/CODING_STANDARDS.md",
        description="Path to team standards file in repo"
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

# ==================== Helper Functions ====================

async def make_github_request(
    method: str,
    url: str,
    token: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Make an authenticated request to GitHub API."""
    default_headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    if headers:
        default_headers.update(headers)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=default_headers,
                params=params,
                json=json_data,
                timeout=30.0
            )
            response.raise_for_status()
            
            # Handle different response types
            content_type = response.headers.get("content-type", "")
            if "application/vnd.github.v3.diff" in content_type or "text/plain" in content_type:
                return {"content": response.text, "type": "diff"}
            elif response.text:
                return response.json()
            else:
                return {"status": response.status_code}
                
        except httpx.HTTPStatusError as e:
            error_msg = f"GitHub API error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data.get('message', 'Unknown error')}"
            except:
                error_msg += f" - {e.response.text}"
            raise ValueError(error_msg)
        except httpx.RequestError as e:
            raise ValueError(f"Network error: {str(e)}")

def format_pr_markdown(pr: Dict[str, Any], include_details: bool = False) -> str:
    """Format pull request data as markdown."""
    lines = []
    
    # Basic info
    lines.append(f"## PR #{pr['number']}: {pr['title']}")
    lines.append(f"**Author:** @{pr['user']['login']}")
    lines.append(f"**State:** {pr['state']}")
    lines.append(f"**Created:** {format_datetime(pr['created_at'])}")
    
    if pr.get('updated_at') != pr.get('created_at'):
        lines.append(f"**Updated:** {format_datetime(pr['updated_at'])}")
    
    lines.append(f"**Base:** `{pr['base']['ref']}` ← **Head:** `{pr['head']['ref']}`")
    
    # Labels
    if pr.get('labels'):
        labels = ', '.join([f"`{label['name']}`" for label in pr['labels']])
        lines.append(f"**Labels:** {labels}")
    
    # Stats
    lines.append(f"\n📊 **Stats:**")
    lines.append(f"- Commits: {pr.get('commits', 'N/A')}")
    lines.append(f"- Files changed: {pr.get('changed_files', 'N/A')}")
    lines.append(f"- Additions: +{pr.get('additions', 0)}")
    lines.append(f"- Deletions: -{pr.get('deletions', 0)}")
    
    # Description
    if pr.get('body'):
        lines.append(f"\n### Description")
        lines.append(pr['body'][:500] + ('...' if len(pr['body']) > 500 else ''))
    
    # Review status
    if pr.get('requested_reviewers'):
        reviewers = ', '.join([f"@{r['login']}" for r in pr['requested_reviewers']])
        lines.append(f"\n**Requested Reviewers:** {reviewers}")
    
    # Merge status
    if include_details:
        lines.append(f"\n### Merge Status")
        lines.append(f"- Mergeable: {pr.get('mergeable', 'Unknown')}")
        lines.append(f"- Mergeable State: {pr.get('mergeable_state', 'Unknown')}")
        if pr.get('merge_commit_sha'):
            lines.append(f"- Merge Commit: `{pr['merge_commit_sha'][:8]}`")
    
    lines.append(f"\n[View on GitHub]({pr['html_url']})")
    
    return '\n'.join(lines)

def format_datetime(dt_string: str) -> str:
    """Format ISO datetime string to readable format."""
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return dt_string

def truncate_response(response: str, limit: int = CHARACTER_LIMIT) -> str:
    """Truncate response if it exceeds character limit."""
    if len(response) <= limit:
        return response
    
    truncated = response[:limit - 200]  # Leave room for truncation message
    truncated += f"\n\n⚠️ **Response truncated** (exceeded {limit:,} character limit)\n"
    truncated += "Use pagination parameters or filters to view more results."
    return truncated

def analyze_code_patterns(files_data: List[Dict[str, Any]], diff_content: str) -> Dict[str, Any]:
    """Analyze code for common patterns and anti-patterns."""
    analysis = {
        "patterns_found": [],
        "suggestions": [],
        "complexity_issues": [],
        "security_concerns": []
    }
    
    # File type analysis
    file_types = {}
    for file in files_data:
        ext = file['filename'].split('.')[-1] if '.' in file['filename'] else 'no_ext'
        file_types[ext] = file_types.get(ext, 0) + 1
    
    # Common patterns to check
    patterns_to_check = [
        (r'console\.(log|debug|info)', 'Debug statements found', 'Remove console statements before merging'),
        (r'TODO|FIXME|XXX|HACK', 'TODO/FIXME comments found', 'Address TODO items or create issues for them'),
        (r'api[_\-]?key|secret|password|token', 'Potential sensitive data', 'Ensure no hardcoded secrets'),
        (r'catch\s*\(\s*\)', 'Empty catch blocks', 'Handle errors appropriately in catch blocks'),
        (r'eval\(|exec\(', 'Dynamic code execution', 'Avoid eval/exec for security reasons'),
        (r'SELECT\s+\*\s+FROM', 'SELECT * queries', 'Be specific about selected columns'),
        (r'(if|while|for).*\{[\s\n]*\}', 'Empty control blocks', 'Remove or implement empty blocks'),
    ]
    
    for pattern, issue, suggestion in patterns_to_check:
        if re.search(pattern, diff_content, re.IGNORECASE):
            analysis["patterns_found"].append(issue)
            analysis["suggestions"].append(suggestion)
    
    # Analyze file changes
    large_files = [f for f in files_data if f.get('changes', 0) > 500]
    if large_files:
        analysis["complexity_issues"].append(f"Large file changes ({len(large_files)} files > 500 lines)")
        analysis["suggestions"].append("Consider breaking large changes into smaller PRs")
    
    # Check for test files
    test_files = [f for f in files_data if 'test' in f['filename'].lower() or 'spec' in f['filename'].lower()]
    non_test_files = [f for f in files_data if f not in test_files]
    
    if non_test_files and not test_files:
        analysis["suggestions"].append("Consider adding tests for these changes")
    
    return analysis

# ==================== MCP Tools ====================

@mcp.tool(
    name="github_list_pull_requests",
    annotations={
        "title": "List Pull Requests",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_pull_requests(params: ListPullRequestsInput) -> str:
    """List pull requests in a GitHub repository with filtering options.
    
    This tool retrieves pull requests from a repository with various filtering
    and sorting options. Use it to get an overview of open PRs, find specific
    PRs, or monitor PR activity.
    
    Args:
        params: Input parameters including repo info, filters, and pagination
        
    Returns:
        Formatted list of pull requests (markdown or JSON)
    """
    url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/pulls"
    
    request_params = {
        "state": params.state.value,
        "sort": params.sort,
        "direction": params.direction.value,
        "per_page": params.limit,
        "page": params.page
    }
    
    if params.base:
        request_params["base"] = params.base
    if params.head:
        request_params["head"] = params.head
    
    try:
        response = await make_github_request(
            method="GET",
            url=url,
            token=params.github_token,
            params=request_params
        )
        
        if params.response_format == ResponseFormat.JSON:
            # Return raw JSON response
            result = {
                "total_count": len(response),
                "page": params.page,
                "per_page": params.limit,
                "pull_requests": response
            }
            return truncate_response(json.dumps(result, indent=2))
        
        # Format as markdown
        lines = [f"# Pull Requests - {params.owner}/{params.repo}"]
        lines.append(f"**State:** {params.state.value} | **Page:** {params.page}")
        lines.append(f"**Found:** {len(response)} pull requests\n")
        
        if not response:
            lines.append("*No pull requests found matching criteria*")
        else:
            for pr in response:
                lines.append(format_pr_markdown(pr))
                lines.append("---")
        
        if len(response) == params.limit:
            lines.append(f"\n*More results may be available. Use page={params.page + 1} to see next page.*")
        
        return truncate_response('\n'.join(lines))
        
    except Exception as e:
        return f"Error listing pull requests: {str(e)}"

@mcp.tool(
    name="github_get_pr_details",
    annotations={
        "title": "Get Pull Request Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_pr_details(params: GetPullRequestDetailsInput) -> str:
    """Get comprehensive details about a specific pull request.
    
    Retrieves detailed information including description, commits, reviews,
    checks, and merge status. Use for in-depth PR analysis.
    
    Args:
        params: Input parameters including PR number and detail options
        
    Returns:
        Detailed PR information (markdown or JSON)
    """
    url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}"
    
    try:
        # Get PR details
        pr_data = await make_github_request(
            method="GET",
            url=url,
            token=params.github_token
        )
        
        # Optionally get reviews
        reviews_data = []
        if params.include_reviews:
            reviews_url = f"{url}/reviews"
            reviews_data = await make_github_request(
                method="GET",
                url=reviews_url,
                token=params.github_token
            )
        
        # Optionally get checks
        checks_data = {}
        if params.include_checks:
            commits_url = f"{url}/commits"
            commits = await make_github_request(
                method="GET",
                url=commits_url,
                token=params.github_token
            )
            if commits:
                # Get status checks for latest commit
                latest_sha = commits[-1]['sha']
                checks_url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/commits/{latest_sha}/check-runs"
                checks_response = await make_github_request(
                    method="GET",
                    url=checks_url,
                    token=params.github_token
                )
                checks_data = checks_response.get('check_runs', [])
        
        if params.response_format == ResponseFormat.JSON:
            result = {
                "pull_request": pr_data,
                "reviews": reviews_data,
                "checks": checks_data
            }
            return truncate_response(json.dumps(result, indent=2))
        
        # Format as markdown
        lines = [format_pr_markdown(pr_data, include_details=True)]
        
        # Add review information
        if reviews_data:
            lines.append("\n## Reviews")
            review_summary = {}
            for review in reviews_data:
                state = review['state']
                user = review['user']['login']
                review_summary[state] = review_summary.get(state, [])
                review_summary[state].append(f"@{user}")
            
            for state, users in review_summary.items():
                lines.append(f"- **{state}:** {', '.join(users)}")
        
        # Add checks information
        if checks_data:
            lines.append("\n## Status Checks")
            for check in checks_data[:10]:  # Limit to 10 checks
                status_icon = "✅" if check['conclusion'] == 'success' else "❌" if check['conclusion'] == 'failure' else "⏳"
                lines.append(f"- {status_icon} **{check['name']}:** {check.get('conclusion', check.get('status', 'pending'))}")
        
        return truncate_response('\n'.join(lines))
        
    except Exception as e:
        return f"Error getting PR details: {str(e)}"

@mcp.tool(
    name="github_get_pr_files",
    annotations={
        "title": "Get Pull Request Files",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_pr_files(params: GetPullRequestFilesInput) -> str:
    """Get the list of files changed in a pull request.
    
    Retrieves all files modified in a PR with change statistics.
    Useful for understanding the scope and impact of changes.
    
    Args:
        params: Input parameters including PR number and pagination
        
    Returns:
        List of changed files with statistics (markdown or JSON)
    """
    url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}/files"
    
    try:
        response = await make_github_request(
            method="GET",
            url=url,
            token=params.github_token,
            params={"per_page": params.limit, "page": params.page}
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = {
                "total_files": len(response),
                "page": params.page,
                "files": response
            }
            return truncate_response(json.dumps(result, indent=2))
        
        # Format as markdown
        lines = [f"# Files Changed in PR #{params.pr_number}"]
        lines.append(f"**Total files:** {len(response)}\n")
        
        # Group files by directory
        by_dir = {}
        for file in response:
            dir_name = '/'.join(file['filename'].split('/')[:-1]) or 'root'
            by_dir[dir_name] = by_dir.get(dir_name, [])
            by_dir[dir_name].append(file)
        
        # Statistics
        total_additions = sum(f.get('additions', 0) for f in response)
        total_deletions = sum(f.get('deletions', 0) for f in response)
        lines.append(f"**Total changes:** +{total_additions} / -{total_deletions}\n")
        
        # List files by directory
        for dir_name in sorted(by_dir.keys()):
            lines.append(f"### 📁 {dir_name}/")
            for file in by_dir[dir_name]:
                status_icon = "🆕" if file['status'] == 'added' else "🗑️" if file['status'] == 'removed' else "📝"
                filename = file['filename'].split('/')[-1]
                lines.append(f"- {status_icon} **{filename}** (+{file.get('additions', 0)}/-{file.get('deletions', 0)}) - {file['status']}")
                if file.get('patch'):
                    # Show first few lines of patch
                    patch_lines = file['patch'].split('\n')[:5]
                    for patch_line in patch_lines:
                        lines.append(f"  `{patch_line}`")
        
        if len(response) == params.limit:
            lines.append(f"\n*More files may be available. Use page={params.page + 1} to see next page.*")
        
        return truncate_response('\n'.join(lines))
        
    except Exception as e:
        return f"Error getting PR files: {str(e)}"

@mcp.tool(
    name="github_get_pr_diff",
    annotations={
        "title": "Get Pull Request Diff",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_pr_diff(params: GetPullRequestDiffInput) -> str:
    """Get the unified diff for a pull request.
    
    Retrieves the complete diff showing all changes in the PR.
    Can filter to specific files. Essential for detailed code review.
    
    Args:
        params: Input parameters including PR number and optional file filter
        
    Returns:
        Unified diff of the pull request
    """
    url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}"
    
    try:
        # Get the diff using special Accept header
        response = await make_github_request(
            method="GET",
            url=url,
            token=params.github_token,
            headers={"Accept": "application/vnd.github.v3.diff"}
        )
        
        diff_content = response.get('content', '')
        
        # Filter for specific file if requested
        if params.file_path and diff_content:
            filtered_diff = []
            in_target_file = False
            for line in diff_content.split('\n'):
                if line.startswith('diff --git'):
                    in_target_file = params.file_path in line
                if in_target_file:
                    filtered_diff.append(line)
            diff_content = '\n'.join(filtered_diff) if filtered_diff else f"No changes found for file: {params.file_path}"
        
        # Format output
        lines = [f"# Pull Request #{params.pr_number} - Diff"]
        if params.file_path:
            lines.append(f"**Filtered for:** `{params.file_path}`")
        lines.append("\n```diff")
        lines.append(diff_content[:CHARACTER_LIMIT - 500])  # Leave room for formatting
        if len(diff_content) > CHARACTER_LIMIT - 500:
            lines.append("\n... (diff truncated)")
        lines.append("```")
        
        return '\n'.join(lines)
        
    except Exception as e:
        return f"Error getting PR diff: {str(e)}"

@mcp.tool(
    name="github_analyze_pr",
    annotations={
        "title": "Analyze Pull Request",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_analyze_pr(params: AnalyzePullRequestInput) -> str:
    """Perform comprehensive analysis of a pull request.
    
    Analyzes code patterns, complexity, potential issues, and provides
    improvement suggestions. This is the main tool for automated code review.
    
    Args:
        params: Input parameters including PR number and analysis options
        
    Returns:
        Comprehensive analysis report (markdown or JSON)
    """
    try:
        # Get PR details
        pr_url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}"
        pr_data = await make_github_request(
            method="GET",
            url=pr_url,
            token=params.github_token
        )
        
        # Get files changed
        files_url = f"{pr_url}/files"
        files_data = await make_github_request(
            method="GET",
            url=files_url,
            token=params.github_token
        )
        
        # Get diff
        diff_response = await make_github_request(
            method="GET",
            url=pr_url,
            token=params.github_token,
            headers={"Accept": "application/vnd.github.v3.diff"}
        )
        diff_content = diff_response.get('content', '')
        
        # Perform analysis
        analysis_results = {
            "pr_info": {
                "number": pr_data['number'],
                "title": pr_data['title'],
                "author": pr_data['user']['login'],
                "files_changed": len(files_data),
                "additions": pr_data.get('additions', 0),
                "deletions": pr_data.get('deletions', 0)
            },
            "file_analysis": {},
            "patterns": {},
            "recommendations": []
        }
        
        # Analyze patterns if requested
        if params.check_patterns:
            pattern_analysis = analyze_code_patterns(files_data, diff_content)
            analysis_results["patterns"] = pattern_analysis
        
        # Analyze file types and changes
        file_types = {}
        large_changes = []
        for file in files_data:
            ext = file['filename'].split('.')[-1] if '.' in file['filename'] else 'no_ext'
            file_types[ext] = file_types.get(ext, 0) + 1
            
            if file.get('changes', 0) > 300:
                large_changes.append({
                    "file": file['filename'],
                    "changes": file['changes']
                })
        
        analysis_results["file_analysis"]["file_types"] = file_types
        analysis_results["file_analysis"]["large_changes"] = large_changes
        
        # Generate recommendations
        recommendations = []
        
        # Based on PR size
        total_changes = pr_data.get('additions', 0) + pr_data.get('deletions', 0)
        if total_changes > 1000:
            recommendations.append("⚠️ Large PR (>1000 lines). Consider breaking into smaller PRs for easier review.")
        
        # Based on file count
        if len(files_data) > 20:
            recommendations.append("📁 Many files changed (>20). Ensure changes are cohesive and related.")
        
        # Based on patterns found
        if params.check_patterns and analysis_results["patterns"].get("patterns_found"):
            recommendations.append("🔍 Code patterns detected that may need attention (see patterns section)")
        
        # Check for tests
        has_tests = any('test' in f['filename'].lower() or 'spec' in f['filename'].lower() for f in files_data)
        has_src_changes = any(f['filename'].endswith(('.py', '.js', '.ts', '.java', '.go', '.rb')) for f in files_data)
        if has_src_changes and not has_tests:
            recommendations.append("🧪 Source code changes detected but no test files. Consider adding tests.")
        
        # Documentation check
        has_docs = any('readme' in f['filename'].lower() or 'doc' in f['filename'].lower() for f in files_data)
        if not has_docs and total_changes > 200:
            recommendations.append("📚 Significant changes without documentation updates. Consider updating docs.")
        
        analysis_results["recommendations"] = recommendations
        
        # Format response
        if params.response_format == ResponseFormat.JSON:
            return truncate_response(json.dumps(analysis_results, indent=2))
        
        # Format as markdown
        lines = [f"# Pull Request Analysis - PR #{params.pr_number}"]
        lines.append(f"\n## Overview")
        lines.append(f"- **Title:** {pr_data['title']}")
        lines.append(f"- **Author:** @{pr_data['user']['login']}")
        lines.append(f"- **Files Changed:** {len(files_data)}")
        lines.append(f"- **Lines Changed:** +{pr_data.get('additions', 0)} / -{pr_data.get('deletions', 0)}")
        
        # File type distribution
        lines.append(f"\n## File Types Changed")
        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"- `.{ext}`: {count} file(s)")
        
        # Large changes warning
        if large_changes:
            lines.append(f"\n## ⚠️ Large File Changes")
            for item in large_changes[:5]:
                lines.append(f"- `{item['file']}`: {item['changes']} lines")
        
        # Pattern analysis
        if params.check_patterns and analysis_results["patterns"].get("patterns_found"):
            lines.append(f"\n## 🔍 Code Patterns Detected")
            for pattern in analysis_results["patterns"]["patterns_found"]:
                lines.append(f"- {pattern}")
            lines.append(f"\n### Suggestions")
            for suggestion in analysis_results["patterns"]["suggestions"]:
                lines.append(f"- {suggestion}")
        
        # Security concerns
        if params.check_security and analysis_results["patterns"].get("security_concerns"):
            lines.append(f"\n## 🔒 Security Considerations")
            for concern in analysis_results["patterns"]["security_concerns"]:
                lines.append(f"- {concern}")
        
        # Recommendations
        if recommendations:
            lines.append(f"\n## 💡 Recommendations")
            for rec in recommendations:
                lines.append(f"- {rec}")
        
        # Summary
        lines.append(f"\n## Summary")
        risk_level = "Low"
        if total_changes > 1000 or len(files_data) > 30:
            risk_level = "High"
        elif total_changes > 500 or len(files_data) > 15:
            risk_level = "Medium"
        
        lines.append(f"**Risk Level:** {risk_level}")
        lines.append(f"**Review Priority:** {'High' if risk_level != 'Low' or not has_tests else 'Normal'}")
        
        return truncate_response('\n'.join(lines))
        
    except Exception as e:
        return f"Error analyzing PR: {str(e)}"

@mcp.tool(
    name="github_get_pr_comments",
    annotations={
        "title": "Get Pull Request Comments",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_pr_comments(params: GetPullRequestCommentsInput) -> str:
    """Get comments on a pull request.
    
    Retrieves issue comments and/or review comments on a PR.
    Useful for understanding discussion and feedback history.
    
    Args:
        params: Input parameters including PR number and comment type
        
    Returns:
        List of comments (markdown or JSON)
    """
    try:
        all_comments = []
        
        # Get issue comments (general PR comments)
        if params.comment_type in ['all', 'issue']:
            issue_url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/issues/{params.pr_number}/comments"
            issue_comments = await make_github_request(
                method="GET",
                url=issue_url,
                token=params.github_token,
                params={"per_page": params.limit, "page": params.page}
            )
            for comment in issue_comments:
                comment['comment_type'] = 'issue'
            all_comments.extend(issue_comments)
        
        # Get review comments (inline code comments)
        if params.comment_type in ['all', 'review']:
            review_url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}/comments"
            review_comments = await make_github_request(
                method="GET",
                url=review_url,
                token=params.github_token,
                params={"per_page": params.limit, "page": params.page}
            )
            for comment in review_comments:
                comment['comment_type'] = 'review'
            all_comments.extend(review_comments)
        
        # Sort by created date
        all_comments.sort(key=lambda x: x.get('created_at', ''))
        
        if params.response_format == ResponseFormat.JSON:
            result = {
                "total_comments": len(all_comments),
                "comment_type": params.comment_type,
                "page": params.page,
                "comments": all_comments
            }
            return truncate_response(json.dumps(result, indent=2))
        
        # Format as markdown
        lines = [f"# Pull Request Comments - PR #{params.pr_number}"]
        lines.append(f"**Type:** {params.comment_type} | **Count:** {len(all_comments)}\n")
        
        if not all_comments:
            lines.append("*No comments found*")
        else:
            for comment in all_comments:
                lines.append(f"## 💬 Comment by @{comment['user']['login']}")
                lines.append(f"**Posted:** {format_datetime(comment['created_at'])}")
                
                if comment.get('comment_type') == 'review' and comment.get('path'):
                    lines.append(f"**File:** `{comment['path']}`")
                    if comment.get('line'):
                        lines.append(f"**Line:** {comment['line']}")
                
                lines.append(f"\n{comment['body'][:500]}")
                if len(comment['body']) > 500:
                    lines.append("*(comment truncated)*")
                lines.append("\n---")
        
        if len(all_comments) == params.limit:
            lines.append(f"\n*More comments may be available. Use page={params.page + 1} to see next page.*")
        
        return truncate_response('\n'.join(lines))
        
    except Exception as e:
        return f"Error getting PR comments: {str(e)}"

@mcp.tool(
    name="github_create_review_comment",
    annotations={
        "title": "Create Review Comment",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_create_review_comment(params: CreateReviewCommentInput) -> str:
    """Create a comment on a pull request.
    
    Can create general PR comments or inline code comments on specific lines.
    Use for providing feedback during code review.
    
    Args:
        params: Input parameters including PR number, comment text, and location
        
    Returns:
        Confirmation of comment creation with details
    """
    try:
        if params.path and params.line:
            # Create inline review comment
            url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}/comments"
            
            # Get the latest commit if not provided
            if not params.commit_id:
                pr_url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}"
                pr_data = await make_github_request(
                    method="GET",
                    url=pr_url,
                    token=params.github_token
                )
                params.commit_id = pr_data['head']['sha']
            
            comment_data = {
                "body": params.body,
                "commit_id": params.commit_id,
                "path": params.path,
                "line": params.line,
                "side": params.side
            }
        else:
            # Create general PR comment
            url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/issues/{params.pr_number}/comments"
            comment_data = {"body": params.body}
        
        response = await make_github_request(
            method="POST",
            url=url,
            token=params.github_token,
            json_data=comment_data
        )
        
        # Format response
        lines = ["# ✅ Comment Created Successfully"]
        lines.append(f"\n**PR:** #{params.pr_number}")
        lines.append(f"**Author:** @{response['user']['login']}")
        lines.append(f"**Created:** {format_datetime(response['created_at'])}")
        
        if params.path:
            lines.append(f"**Type:** Inline review comment")
            lines.append(f"**File:** `{params.path}`")
            lines.append(f"**Line:** {params.line}")
        else:
            lines.append(f"**Type:** General PR comment")
        
        lines.append(f"\n**Comment:**")
        lines.append(f"> {params.body[:200]}{'...' if len(params.body) > 200 else ''}")
        
        lines.append(f"\n[View Comment]({response['html_url']})")
        
        return '\n'.join(lines)
        
    except Exception as e:
        return f"Error creating comment: {str(e)}"

@mcp.tool(
    name="github_create_pr_review",
    annotations={
        "title": "Create Pull Request Review",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_create_pr_review(params: CreatePullRequestReviewInput) -> str:
    """Create a formal review on a pull request.
    
    Submit a review with approval, request changes, or comment status.
    Can include multiple inline comments as part of the review.
    
    Args:
        params: Input parameters including PR number, review body, and status
        
    Returns:
        Confirmation of review creation with details
    """
    url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}/reviews"
    
    try:
        review_data = {
            "event": params.event.value
        }
        
        if params.body:
            review_data["body"] = params.body
        
        if params.comments:
            review_data["comments"] = params.comments
        
        response = await make_github_request(
            method="POST",
            url=url,
            token=params.github_token,
            json_data=review_data
        )
        
        # Format response
        lines = ["# ✅ Review Submitted Successfully"]
        lines.append(f"\n**PR:** #{params.pr_number}")
        lines.append(f"**Reviewer:** @{response['user']['login']}")
        lines.append(f"**Status:** {params.event.value}")
        lines.append(f"**Submitted:** {format_datetime(response['submitted_at'])}")
        
        if params.body:
            lines.append(f"\n**Review Summary:**")
            lines.append(f"> {params.body[:300]}{'...' if len(params.body) > 300 else ''}")
        
        if params.comments:
            lines.append(f"\n**Inline Comments:** {len(params.comments)}")
        
        status_emoji = {
            "APPROVE": "✅",
            "REQUEST_CHANGES": "🔄",
            "COMMENT": "💬"
        }
        lines.append(f"\n**Review Decision:** {status_emoji.get(params.event.value, '')} {params.event.value}")
        
        lines.append(f"\n[View Review]({response['html_url']})")
        
        return '\n'.join(lines)
        
    except Exception as e:
        return f"Error creating review: {str(e)}"

@mcp.tool(
    name="github_get_review_suggestions",
    annotations={
        "title": "Get AI-Powered Review Suggestions",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_review_suggestions(params: GetReviewSuggestionsInput) -> str:
    """Generate intelligent review suggestions for a pull request.
    
    Analyzes the PR and provides specific, actionable suggestions based on
    code patterns, best practices, and focus areas. This tool combines
    multiple analysis techniques to provide comprehensive review guidance.
    
    Args:
        params: Input parameters including PR number and focus areas
        
    Returns:
        AI-generated review suggestions (markdown or JSON)
    """
    try:
        # Get PR details and files
        pr_url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}"
        pr_data = await make_github_request(
            method="GET",
            url=pr_url,
            token=params.github_token
        )
        
        files_url = f"{pr_url}/files"
        files_data = await make_github_request(
            method="GET",
            url=files_url,
            token=params.github_token,
            params={"per_page": 100}
        )
        
        # Get diff for pattern analysis
        diff_response = await make_github_request(
            method="GET",
            url=pr_url,
            token=params.github_token,
            headers={"Accept": "application/vnd.github.v3.diff"}
        )
        diff_content = diff_response.get('content', '')
        
        suggestions = {
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
            "positive_feedback": []
        }
        
        # Analyze based on focus areas
        focus_areas = params.focus_areas or ['performance', 'security', 'readability', 'tests']
        
        # Security suggestions
        if 'security' in focus_areas:
            security_patterns = [
                (r'api[_\-]?key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key detected", "high"),
                (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password detected", "high"),
                (r'eval\(|exec\(', "Dynamic code execution can be dangerous", "high"),
                (r'subprocess\.call\(.*shell=True', "Shell injection risk with subprocess", "high"),
                (r'\.innerHTML\s*=', "Potential XSS vulnerability with innerHTML", "medium"),
                (r'SELECT.*FROM.*WHERE.*\+|f["\'].*SELECT', "Potential SQL injection", "high"),
            ]
            
            for pattern, message, priority in security_patterns:
                if re.search(pattern, diff_content, re.IGNORECASE):
                    suggestions[f"{priority}_priority"].append(f"🔒 **Security:** {message}")
        
        # Performance suggestions
        if 'performance' in focus_areas:
            perf_patterns = [
                (r'for.*in.*for.*in', "Nested loops detected - consider optimization", "medium"),
                (r'SELECT.*\*.*FROM', "SELECT * can be inefficient - specify columns", "low"),
                (r'async def.*\n.*time\.sleep', "Use asyncio.sleep in async functions", "medium"),
                (r'\.append\(.*\).*for.*in', "Consider list comprehension for better performance", "low"),
            ]
            
            for pattern, message, priority in perf_patterns:
                if re.search(pattern, diff_content, re.IGNORECASE | re.MULTILINE):
                    suggestions[f"{priority}_priority"].append(f"⚡ **Performance:** {message}")
        
        # Readability suggestions
        if 'readability' in focus_areas:
            # Check for long files
            for file in files_data:
                if file.get('changes', 0) > 300:
                    suggestions["medium_priority"].append(
                        f"📝 **Readability:** File `{file['filename']}` has {file['changes']} changes. Consider splitting into smaller, focused changes."
                    )
            
            # Check for missing docstrings in Python
            if any(f['filename'].endswith('.py') for f in files_data):
                if not re.search(r'""".*"""', diff_content, re.DOTALL):
                    suggestions["low_priority"].append("📚 **Documentation:** Consider adding docstrings to new Python functions")
        
        # Test suggestions
        if 'tests' in focus_areas:
            test_files = [f for f in files_data if 'test' in f['filename'].lower() or 'spec' in f['filename'].lower()]
            src_files = [f for f in files_data if f['filename'].endswith(('.py', '.js', '.ts', '.java', '.go'))]
            
            if src_files and not test_files:
                suggestions["high_priority"].append("🧪 **Tests:** No test files found. Please add tests for new functionality")
            elif test_files:
                suggestions["positive_feedback"].append("✅ **Tests:** Great job including tests!")
        
        # Documentation suggestions
        doc_files = [f for f in files_data if 'readme' in f['filename'].lower() or 'doc' in f['filename'].lower()]
        if pr_data.get('additions', 0) > 100 and not doc_files:
            suggestions["low_priority"].append("📖 **Documentation:** Consider updating documentation for these changes")
        
        # Positive feedback
        if pr_data.get('additions', 0) + pr_data.get('deletions', 0) < 200:
            suggestions["positive_feedback"].append("👍 **Size:** Good job keeping the PR focused and manageable")
        
        if pr_data.get('body') and len(pr_data['body']) > 100:
            suggestions["positive_feedback"].append("📋 **Description:** Excellent PR description!")
        
        # Format response
        if params.response_format == ResponseFormat.JSON:
            return truncate_response(json.dumps(suggestions, indent=2))
        
        # Format as markdown
        lines = [f"# Review Suggestions for PR #{params.pr_number}"]
        lines.append(f"**Title:** {pr_data['title']}")
        lines.append(f"**Focus Areas:** {', '.join(focus_areas)}\n")
        
        if suggestions["high_priority"]:
            lines.append("## 🚨 High Priority")
            for suggestion in suggestions["high_priority"]:
                lines.append(f"- {suggestion}")
        
        if suggestions["medium_priority"]:
            lines.append("\n## ⚠️ Medium Priority")
            for suggestion in suggestions["medium_priority"]:
                lines.append(f"- {suggestion}")
        
        if suggestions["low_priority"]:
            lines.append("\n## 💡 Low Priority / Suggestions")
            for suggestion in suggestions["low_priority"]:
                lines.append(f"- {suggestion}")
        
        if suggestions["positive_feedback"]:
            lines.append("\n## ✨ Positive Feedback")
            for feedback in suggestions["positive_feedback"]:
                lines.append(f"- {feedback}")
        
        # Summary
        total_suggestions = sum(len(suggestions[k]) for k in ['high_priority', 'medium_priority', 'low_priority'])
        lines.append(f"\n## Summary")
        lines.append(f"- **Total Suggestions:** {total_suggestions}")
        lines.append(f"- **Critical Issues:** {len(suggestions['high_priority'])}")
        lines.append(f"- **Review Recommendation:** {'Request Changes' if suggestions['high_priority'] else 'Approve with suggestions' if total_suggestions > 0 else 'Ready to approve'}")
        
        return truncate_response('\n'.join(lines))
        
    except Exception as e:
        return f"Error generating review suggestions: {str(e)}"

@mcp.tool(
    name="github_check_team_standards",
    annotations={
        "title": "Check Team Standards Compliance",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_check_team_standards(params: CheckTeamStandardsInput) -> str:
    """Check if a pull request complies with team coding standards.
    
    Compares PR against team-defined standards (from a standards file in the repo)
    or applies common best practices if no standards file exists.
    
    Args:
        params: Input parameters including PR number and standards file path
        
    Returns:
        Compliance report with violations and recommendations (markdown or JSON)
    """
    try:
        # Try to get team standards file
        standards_content = None
        try:
            standards_url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/contents/{params.standards_file}"
            standards_response = await make_github_request(
                method="GET",
                url=standards_url,
                token=params.github_token
            )
            
            if standards_response.get('content'):
                import base64
                standards_content = base64.b64decode(standards_response['content']).decode('utf-8')
        except:
            # Standards file not found, use defaults
            pass
        
        # Get PR details and files
        pr_url = f"{API_BASE_URL}/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}"
        pr_data = await make_github_request(
            method="GET",
            url=pr_url,
            token=params.github_token
        )
        
        files_url = f"{pr_url}/files"
        files_data = await make_github_request(
            method="GET",
            url=files_url,
            token=params.github_token,
            params={"per_page": 100}
        )
        
        # Get diff
        diff_response = await make_github_request(
            method="GET",
            url=pr_url,
            token=params.github_token,
            headers={"Accept": "application/vnd.github.v3.diff"}
        )
        diff_content = diff_response.get('content', '')
        
        # Check compliance
        compliance_results = {
            "compliant": [],
            "violations": [],
            "warnings": [],
            "not_applicable": []
        }
        
        # Default standards to check
        standards_checks = [
            {
                "name": "PR Size",
                "check": lambda: pr_data.get('additions', 0) + pr_data.get('deletions', 0) < 500,
                "violation": f"PR has {pr_data.get('additions', 0) + pr_data.get('deletions', 0)} changes (recommended < 500)",
                "priority": "warning"
            },
            {
                "name": "PR Description",
                "check": lambda: pr_data.get('body') and len(pr_data['body']) > 50,
                "violation": "PR description is too short or missing",
                "priority": "violation"
            },
            {
                "name": "Branch Naming",
                "check": lambda: re.match(r'^(feature|bugfix|hotfix|release|chore)/', pr_data['head']['ref']),
                "violation": f"Branch name '{pr_data['head']['ref']}' doesn't follow convention (feature/*, bugfix/*, etc.)",
                "priority": "warning"
            },
            {
                "name": "No Console Logs",
                "check": lambda: not re.search(r'console\.(log|debug)', diff_content),
                "violation": "Console statements found in code",
                "priority": "violation"
            },
            {
                "name": "No Commented Code",
                "check": lambda: not re.search(r'^\s*//.*\n\s*//.*\n\s*//', diff_content, re.MULTILINE),
                "violation": "Large blocks of commented code detected",
                "priority": "warning"
            },
            {
                "name": "Tests Included",
                "check": lambda: any('test' in f['filename'].lower() or 'spec' in f['filename'].lower() for f in files_data),
                "violation": "No test files included with code changes",
                "priority": "warning"
            }
        ]
        
        # If we have custom standards, parse and add checks
        if standards_content:
            # Parse standards file for rules (simplified example)
            if "max_file_length:" in standards_content:
                match = re.search(r'max_file_length:\s*(\d+)', standards_content)
                if match:
                    max_length = int(match.group(1))
                    for file in files_data:
                        if file.get('changes', 0) > max_length:
                            compliance_results["violations"].append(
                                f"File `{file['filename']}` exceeds max length ({file['changes']} > {max_length})"
                            )
        
        # Run standard checks
        for check in standards_checks:
            try:
                if check["check"]():
                    compliance_results["compliant"].append(f"✅ {check['name']}")
                else:
                    if check["priority"] == "violation":
                        compliance_results["violations"].append(f"❌ {check['name']}: {check['violation']}")
                    else:
                        compliance_results["warnings"].append(f"⚠️ {check['name']}: {check['violation']}")
            except:
                compliance_results["not_applicable"].append(f"⏭️ {check['name']}: Could not check")
        
        # Calculate compliance score
        total_checks = len(compliance_results["compliant"]) + len(compliance_results["violations"]) + len(compliance_results["warnings"])
        compliance_score = (len(compliance_results["compliant"]) / total_checks * 100) if total_checks > 0 else 0
        
        # Format response
        if params.response_format == ResponseFormat.JSON:
            result = {
                "pr_number": params.pr_number,
                "standards_file": params.standards_file,
                "standards_found": standards_content is not None,
                "compliance_score": compliance_score,
                "results": compliance_results
            }
            return truncate_response(json.dumps(result, indent=2))
        
        # Format as markdown
        lines = [f"# Team Standards Compliance - PR #{params.pr_number}"]
        lines.append(f"**Standards File:** `{params.standards_file}` {'✅ Found' if standards_content else '❌ Not found (using defaults)'}")
        lines.append(f"**Compliance Score:** {compliance_score:.1f}%\n")
        
        if compliance_results["violations"]:
            lines.append("## ❌ Violations (Must Fix)")
            for violation in compliance_results["violations"]:
                lines.append(f"- {violation}")
        
        if compliance_results["warnings"]:
            lines.append("\n## ⚠️ Warnings (Should Address)")
            for warning in compliance_results["warnings"]:
                lines.append(f"- {warning}")
        
        if compliance_results["compliant"]:
            lines.append("\n## ✅ Compliant")
            for item in compliance_results["compliant"]:
                lines.append(f"- {item}")
        
        if compliance_results["not_applicable"]:
            lines.append("\n## ⏭️ Not Applicable / Could Not Check")
            for item in compliance_results["not_applicable"]:
                lines.append(f"- {item}")
        
        # Recommendation
        lines.append("\n## Recommendation")
        if compliance_results["violations"]:
            lines.append("🔴 **Action Required:** Please address violations before merging")
        elif compliance_results["warnings"]:
            lines.append("🟡 **Review Suggested:** Consider addressing warnings")
        else:
            lines.append("🟢 **Good to Go:** PR meets team standards")
        
        return truncate_response('\n'.join(lines))
        
    except Exception as e:
        return f"Error checking team standards: {str(e)}"

# Run the server
if __name__ == "__main__":
    import sys
    if "--help" in sys.argv:
        print("GitHub Code Review Assistant MCP Server")
        print("\nTools available:")
        print("  - github_list_pull_requests: List PRs with filtering")
        print("  - github_get_pr_details: Get comprehensive PR details")
        print("  - github_get_pr_files: List files changed in a PR")
        print("  - github_get_pr_diff: Get unified diff of PR changes")
        print("  - github_analyze_pr: Comprehensive PR analysis")
        print("  - github_get_pr_comments: Get PR comments")
        print("  - github_create_review_comment: Add review comments")
        print("  - github_create_pr_review: Submit formal PR review")
        print("  - github_get_review_suggestions: Get AI-powered suggestions")
        print("  - github_check_team_standards: Check standards compliance")
        print("\nUsage: python github_code_review_mcp.py")
    else:
        mcp.run()