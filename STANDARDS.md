# Team Coding Standards

This document defines the coding standards and best practices for our team. The GitHub Code Review Assistant MCP server uses this file to automatically check PR compliance.

## General Guidelines

### Pull Request Standards

- **max_file_length:** 500
- **max_pr_size:** 1000
- **max_files_per_pr:** 20
- **require_tests:** true
- **require_documentation:** true
- **min_description_length:** 50

### Branch Naming Convention

**Pattern:** `(feature|bugfix|hotfix|release|chore)/<ticket-number>-<brief-description>`

Examples:

- `feature/PROJ-123-add-user-authentication`
- `bugfix/PROJ-456-fix-memory-leak`
- `hotfix/PROJ-789-critical-security-patch`

### Commit Message Format

**Pattern:** `<type>(<scope>): <subject>`

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

- `feat(auth): add OAuth2 integration`
- `fix(api): resolve timeout issue in user endpoint`
- `docs(readme): update installation instructions`

## Code Quality Standards

### General Rules

1. **No console statements** in production code
2. **No commented-out code** - use version control instead
3. **No hardcoded credentials** or API keys
4. **All functions must have docstrings** (Python) or JSDoc comments (JavaScript)
5. **Maximum line length:** 100 characters
6. **Maximum function length:** 50 lines
7. **Maximum file length:** 500 lines

### Error Handling

- Never use empty catch blocks
- Always log errors with appropriate context
- Use specific exception types, not generic Exception
- Include error recovery strategies where possible

### Testing Requirements

- **Minimum code coverage:** 80%
- **Unit tests required** for all new functions
- **Integration tests required** for API endpoints
- **Test file naming:** `test_*.py` or `*.test.js`

## Language-Specific Standards

### Python

```python
# Required imports organization
# 1. Standard library imports
# 2. Third-party imports
# 3. Local imports

# Type hints required for all functions
def calculate_total(items: List[Item]) -> float:
    """Calculate total price of items.

    Args:
        items: List of Item objects

    Returns:
        Total price as float
    """
    pass

# Use f-strings for formatting
name = "John"
message = f"Hello, {name}!"  # Good
# message = "Hello, " + name  # Bad

# Context managers for resources
with open('file.txt', 'r') as f:
    content = f.read()
```

### JavaScript/TypeScript

```javascript
// Use const/let, never var
const MAX_RETRIES = 3;
let currentAttempt = 0;

// Arrow functions for callbacks
array.map((item) => item.value); // Good
// array.map(function(item) { return item.value; });  // Avoid

// Async/await over promises
async function fetchData() {
  try {
    const response = await api.get("/data");
    return response.data;
  } catch (error) {
    logger.error("Failed to fetch data:", error);
    throw error;
  }
}

// Destructuring for objects
const { name, age } = user; // Good
// const name = user.name; const age = user.age;  // Avoid
```

### SQL Standards

- Use uppercase for SQL keywords
- Table names in snake_case
- Never use `SELECT *` in production code
- Always use parameterized queries
- Include appropriate indexes

```sql
-- Good
SELECT
    u.user_id,
    u.username,
    COUNT(o.order_id) AS order_count
FROM
    users u
    LEFT JOIN orders o ON u.user_id = o.user_id
WHERE
    u.created_at >= ?
GROUP BY
    u.user_id, u.username;

-- Bad
select * from users, orders where users.user_id = orders.user_id
```

## Security Standards

### Required Security Checks

1. **Input validation** on all user inputs
2. **SQL injection prevention** - use parameterized queries
3. **XSS prevention** - sanitize HTML output
4. **Authentication checks** on all protected endpoints
5. **Rate limiting** on public APIs
6. **Secrets management** - use environment variables or secret management systems

### Forbidden Patterns

- `eval()` or `exec()` with user input
- Direct string concatenation in SQL queries
- Storing passwords in plain text
- Hardcoded API keys or secrets
- `innerHTML` with user content
- Shell commands with user input

## Documentation Standards

### Required Documentation

1. **README.md** - Project overview and setup instructions
2. **API documentation** - All endpoints must be documented
3. **Code comments** - Complex logic must be explained
4. **Change log** - Document significant changes
5. **Architecture decisions** - Document key design choices

### Documentation Format

````markdown
## Function/Endpoint Name

**Description:** Brief description of what it does

**Parameters:**

- `param1` (type): Description
- `param2` (type): Optional. Description

**Returns:**

- (type): Description of return value

**Raises/Errors:**

- `ErrorType`: When this error occurs

**Example:**
\```language
code example here
\```
````

## Performance Standards

### Requirements

- **API response time:** < 500ms for 95th percentile
- **Database query time:** < 100ms
- **Frontend load time:** < 3 seconds
- **Memory usage:** Monitor for memory leaks
- **CPU usage:** Optimize hot paths

### Best Practices

1. Use appropriate data structures
2. Implement caching where beneficial
3. Optimize database queries
4. Use pagination for large datasets
5. Implement lazy loading for heavy resources
6. Profile before optimizing

## Code Review Process

### Before Submitting PR

- [ ] Run linter and fix all warnings
- [ ] Run tests and ensure all pass
- [ ] Update documentation if needed
- [ ] Self-review changes
- [ ] Check against these standards

### Review Checklist

- [ ] Code follows team standards
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance impact considered
- [ ] Error handling is appropriate
- [ ] Code is maintainable

## Enforcement

These standards are automatically checked by:

1. **Pre-commit hooks** - Local checks before commit
2. **CI/CD pipeline** - Automated checks on PR
3. **Code review tools** - MCP server analysis
4. **Manual review** - Team member verification

## Exceptions

Exceptions to these standards may be granted for:

- Legacy code maintenance
- Third-party integration requirements
- Performance-critical sections (with documentation)
- Proof-of-concept or prototype code (clearly marked)

All exceptions must be:

1. Documented in code comments
2. Approved by team lead
3. Tracked for future refactoring

## Updates

This document is a living standard and should be updated through team consensus. Proposed changes should be discussed in team meetings and approved before implementation.

**Last Updated:** [Date]
**Version:** 1.0.0
