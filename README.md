# GitHub Code Review Assistant MCP Server

A comprehensive MCP (Model Context Protocol) server that provides intelligent tools for GitHub pull request code reviews. This server enables AI assistants to analyze PRs, suggest improvements, check for patterns, and ensure consistency with team standards.

## Features

- **Comprehensive PR Analysis** - Analyze code patterns, complexity, and potential issues
- **Review Management** - Create comments, submit reviews, and manage feedback
- **Smart Suggestions** - AI-powered review suggestions based on best practices
- **Standards Compliance** - Check PRs against team coding standards
- **File & Diff Analysis** - Detailed examination of changes and their impact
- **Workflow Integration** - Tools designed for complete review workflows

## Installation

### Prerequisites

- Python 3.8 or higher
- GitHub Personal Access Token with `repo` scope
- MCP-compatible client (e.g., Claude Desktop, or any MCP client)

### Setup

1. **Install dependencies:**

```bash
pip install mcp httpx pydantic
```

2. **Set up your GitHub token:**

   - Go to GitHub Settings → Developer Settings → Personal Access Tokens
   - Generate a new token with `repo` scope
   - Save the token securely

3. **Run the server:**

```bash
python github_code_review_mcp.py
```

### Configuration for Claude Desktop

Add to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "github-code-review": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

## Available Tools

### 1. `github_list_pull_requests`

Lists pull requests in a repository with comprehensive filtering options.

**Parameters:**

- `owner`: Repository owner (required)
- `repo`: Repository name (required)
- `github_token`: GitHub access token (required)
- `state`: Filter by state (open/closed/all)
- `sort`: Sort by (created/updated/popularity/long-running)
- `direction`: Sort direction (asc/desc)
- `base`: Filter by base branch
- `head`: Filter by head branch
- `limit`: Maximum results (1-100)
- `page`: Page number for pagination
- `response_format`: Output format (markdown/json)

**Example Usage:**

```
List all open PRs in facebook/react repository
```

### 2. `github_get_pr_details`

Retrieves comprehensive details about a specific pull request.

**Parameters:**

- `owner`: Repository owner (required)
- `repo`: Repository name (required)
- `github_token`: GitHub access token (required)
- `pr_number`: Pull request number (required)
- `include_reviews`: Include review information (default: true)
- `include_checks`: Include status checks (default: true)
- `response_format`: Output format (markdown/json)

**Example Usage:**

```
Get detailed information about PR #123 including reviews and checks
```

### 3. `github_get_pr_files`

Lists all files changed in a pull request with statistics.

**Parameters:**

- `owner`: Repository owner (required)
- `repo`: Repository name (required)
- `github_token`: GitHub access token (required)
- `pr_number`: Pull request number (required)
- `limit`: Maximum results per page
- `page`: Page number
- `response_format`: Output format (markdown/json)

**Example Usage:**

```
Show me all files changed in PR #456
```

### 4. `github_get_pr_diff`

Retrieves the unified diff for a pull request.

**Parameters:**

- `owner`: Repository owner (required)
- `repo`: Repository name (required)
- `github_token`: GitHub access token (required)
- `pr_number`: Pull request number (required)
- `file_path`: Filter for specific file (optional)
- `context_lines`: Number of context lines (0-10)

**Example Usage:**

```
Get the diff for PR #789, focusing on src/main.js
```

### 5. `github_analyze_pr`

Performs comprehensive analysis of a pull request for code quality.

**Parameters:**

- `owner`: Repository owner (required)
- `repo`: Repository name (required)
- `github_token`: GitHub access token (required)
- `pr_number`: Pull request number (required)
- `check_patterns`: Check for code patterns (default: true)
- `check_complexity`: Analyze complexity (default: true)
- `check_security`: Basic security checks (default: true)
- `response_format`: Output format (markdown/json)

**Example Usage:**

```
Analyze PR #234 for code patterns, complexity, and security issues
```

### 6. `github_get_pr_comments`

Retrieves all comments on a pull request.

**Parameters:**

- `owner`: Repository owner (required)
- `repo`: Repository name (required)
- `github_token`: GitHub access token (required)
- `pr_number`: Pull request number (required)
- `comment_type`: Type of comments (all/issue/review)
- `limit`: Maximum results
- `page`: Page number
- `response_format`: Output format (markdown/json)

**Example Usage:**

```
Get all review comments for PR #567
```

### 7. `github_create_review_comment`

Creates a comment on a pull request (general or inline).

**Parameters:**

- `owner`: Repository owner (required)
- `repo`: Repository name (required)
- `github_token`: GitHub access token (required)
- `pr_number`: Pull request number (required)
- `body`: Comment text with markdown support (required)
- `commit_id`: SHA of commit to comment on (optional)
- `path`: File path for inline comment (optional)
- `line`: Line number for inline comment (optional)
- `side`: Side of diff (LEFT/RIGHT)

**Example Usage:**

```
Add a comment to line 42 of src/utils.js suggesting a performance improvement
```

### 8. `github_create_pr_review`

Submits a formal review on a pull request.

**Parameters:**

- `owner`: Repository owner (required)
- `repo`: Repository name (required)
- `github_token`: GitHub access token (required)
- `pr_number`: Pull request number (required)
- `body`: Review summary text (optional)
- `event`: Review action (APPROVE/REQUEST_CHANGES/COMMENT)
- `comments`: Array of inline review comments (optional)

**Example Usage:**

```
Approve PR #890 with a comment about good test coverage
```

### 9. `github_get_review_suggestions`

Generates AI-powered review suggestions for a pull request.

**Parameters:**

- `owner`: Repository owner (required)
- `repo`: Repository name (required)
- `github_token`: GitHub access token (required)
- `pr_number`: Pull request number (required)
- `focus_areas`: Areas to focus on (performance/security/readability/tests/documentation)
- `response_format`: Output format (markdown/json)

**Example Usage:**

```
Generate review suggestions for PR #345 focusing on security and performance
```

### 10. `github_check_team_standards`

Checks if a PR complies with team coding standards.

**Parameters:**

- `owner`: Repository owner (required)
- `repo`: Repository name (required)
- `github_token`: GitHub access token (required)
- `pr_number`: Pull request number (required)
- `standards_file`: Path to standards file in repo (default: .github/CODING_STANDARDS.md)
- `response_format`: Output format (markdown/json)

**Example Usage:**

```
Check if PR #678 meets our team's coding standards
```

## Usage Examples

### Example 1: Complete PR Review Workflow

```python
# 1. List open PRs to find ones needing review
github_list_pull_requests(
    owner="myorg",
    repo="myrepo",
    github_token="ghp_xxx",
    state="open",
    sort="created"
)

# 2. Get details about a specific PR
github_get_pr_details(
    owner="myorg",
    repo="myrepo",
    github_token="ghp_xxx",
    pr_number=123
)

# 3. Analyze the PR for issues
github_analyze_pr(
    owner="myorg",
    repo="myrepo",
    github_token="ghp_xxx",
    pr_number=123
)

# 4. Get AI suggestions
github_get_review_suggestions(
    owner="myorg",
    repo="myrepo",
    github_token="ghp_xxx",
    pr_number=123,
    focus_areas=["security", "performance"]
)

# 5. Check team standards
github_check_team_standards(
    owner="myorg",
    repo="myrepo",
    github_token="ghp_xxx",
    pr_number=123
)

# 6. Submit review with comments
github_create_pr_review(
    owner="myorg",
    repo="myrepo",
    github_token="ghp_xxx",
    pr_number=123,
    body="Great work! A few suggestions for improvement...",
    event="APPROVE"
)
```

### Example 2: Focused Code Pattern Analysis

```python
# Get files changed
files = github_get_pr_files(
    owner="myorg",
    repo="myrepo",
    github_token="ghp_xxx",
    pr_number=456
)

# Get diff for specific analysis
diff = github_get_pr_diff(
    owner="myorg",
    repo="myrepo",
    github_token="ghp_xxx",
    pr_number=456,
    file_path="src/api/handler.js"
)

# Analyze for patterns
analysis = github_analyze_pr(
    owner="myorg",
    repo="myrepo",
    github_token="ghp_xxx",
    pr_number=456,
    check_patterns=True,
    check_security=True
)
```

## Best Practices

### For Reviewers

1. **Start with Overview**: Use `github_get_pr_details` to understand the PR context
2. **Analyze First**: Run `github_analyze_pr` before manual review
3. **Check Standards**: Use `github_check_team_standards` for consistency
4. **Get Suggestions**: Use `github_get_review_suggestions` for comprehensive feedback
5. **Be Constructive**: When creating comments, be specific and suggest improvements

### For PR Authors

1. **Self-Review**: Use the analysis tools on your own PRs before requesting review
2. **Address Standards**: Check standards compliance before submitting
3. **Keep PRs Focused**: Analysis tools work better on smaller, focused changes
4. **Include Tests**: The tools check for test coverage
5. **Write Good Descriptions**: Tools analyze PR descriptions for context

## Security Considerations

1. **Token Security**: Never hardcode GitHub tokens. Use environment variables or secure credential storage
2. **Permissions**: Ensure tokens have appropriate scopes (usually `repo` is sufficient)
3. **Rate Limiting**: GitHub API has rate limits. The tools handle this gracefully but be aware of limits
4. **Private Repos**: Ensure tokens have access to private repositories if needed

## Pattern Detection

The analysis tools detect various code patterns including:

- **Security Issues**: Hardcoded secrets, SQL injection risks, XSS vulnerabilities
- **Performance Issues**: Nested loops, SELECT \*, synchronous operations in async code
- **Code Quality**: Console logs, commented code, empty catch blocks
- **Best Practices**: Missing tests, large files, missing documentation

## Team Standards Integration

Create a `.github/CODING_STANDARDS.md` file in your repository with your team's standards. The tool will automatically use this for compliance checking. Example format:

```markdown
# Coding Standards

## General Rules

- max_file_length: 500
- max_pr_size: 1000
- require_tests: true
- require_documentation: true

## Branch Naming

- Pattern: (feature|bugfix|hotfix|release)/description

## Commit Messages

- Format: type(scope): description
- Types: feat, fix, docs, style, refactor, test, chore
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**

   - Verify your GitHub token is valid
   - Check token has required scopes
   - Ensure token hasn't expired

2. **Rate Limiting**

   - GitHub limits API calls to 5000/hour for authenticated requests
   - Tools will report rate limit errors
   - Consider implementing caching for frequently accessed data

3. **Large PRs**

   - Very large PRs may hit response size limits
   - Use pagination parameters
   - Filter to specific files when possible

4. **Network Errors**
   - Check internet connectivity
   - Verify GitHub API is accessible
   - Check for proxy/firewall issues

## Contributing

Contributions are welcome! Areas for improvement:

- Additional pattern detection rules
- Support for GitLab/Bitbucket
- Enhanced security scanning
- Integration with more CI/CD systems
- Custom rule definitions
- Caching layer for improved performance

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built using:

- [MCP (Model Context Protocol)](https://modelcontextprotocol.io)
- [GitHub REST API](https://docs.github.com/en/rest)
- [FastMCP](https://github.com/modelcontextprotocol/python-sdk)

## Support

For issues, questions, or suggestions:

- Open an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

---

**Note**: This tool is designed to assist with code reviews but should not replace human judgment. Always apply context and domain knowledge when reviewing code.
