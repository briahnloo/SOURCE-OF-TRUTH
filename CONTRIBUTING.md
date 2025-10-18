# Contributing to Truth Layer

Thank you for your interest in contributing to the Truth Layer project! This document provides guidelines for contributing.

## Getting Started

1. **Fork the repository** and clone locally
2. **Install dependencies:**
   ```bash
   cd backend && pip install -e ".[dev]"
   cd ../frontend && npm install
   ```
3. **Read the documentation** in `/docs/` to understand the architecture

## Development Workflow

### Backend (Python)

1. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write code following PEP 8:**
   ```bash
   # Format with Black
   black backend/app

   # Lint with Ruff
   ruff check backend/app
   ```

3. **Add tests:**
   - Place tests in `backend/tests/`
   - Follow naming convention: `test_*.py`
   - Run tests: `pytest backend/tests/`

4. **Type hints required:**
   ```python
   def my_function(param: str) -> int:
       return len(param)
   ```

### Frontend (TypeScript)

1. **Follow TypeScript/React best practices**

2. **Lint and format:**
   ```bash
   npm run lint
   ```

3. **Test components:**
   ```bash
   npm test
   ```

## Pull Request Process

1. **Update documentation** if you're changing functionality
2. **Add tests** for new features
3. **Run full test suite:** `make test`
4. **Write a clear PR description:**
   - What does this change?
   - Why is it needed?
   - How was it tested?
5. **Ensure CI passes** (linting, tests, build)

## Code Review Guidelines

Reviewers will check:
- Code quality and readability
- Test coverage
- Performance implications
- Security considerations
- Documentation updates

## Adding New Data Sources

To add a new news source or API:

1. **Create fetcher module:** `backend/app/services/fetch/my_source.py`
2. **Implement fetch function:**
   ```python
   def fetch_my_source_articles() -> List[Dict[str, Any]]:
       # Returns list of article dicts with keys: title, url, source, timestamp, summary
       pass
   ```
3. **Add to pipeline:** Import in `scheduler.py` and call in `run_ingestion_pipeline()`
4. **Document in `/docs/sources.md`:** Include URL, license, rate limits
5. **Add tests:** Test error handling and rate limits

## Modifying Scoring Algorithm

If you propose changes to the truth confidence scoring:

1. **Document the change** in `/docs/scoring.md`
2. **Provide justification** with examples or research
3. **Add test cases** in `tests/test_score.py`
4. **Consider backwards compatibility:** Will this change existing scores?

## Bug Reports

Use GitHub Issues with:
- Clear title
- Steps to reproduce
- Expected vs actual behavior
- Logs/screenshots if applicable
- Environment details (OS, Docker version, etc.)

## Feature Requests

Open a GitHub Issue with:
- Use case description
- Proposed solution
- Alternatives considered
- Impact on existing features

## Style Guides

### Python
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Type hints required
- Docstrings for all public functions

### TypeScript/React
- Follow [Airbnb React Style Guide](https://github.com/airbnb/javascript/tree/master/react)
- Use functional components with hooks
- Props should be typed with interfaces

### Git Commits
- Use present tense ("Add feature" not "Added feature")
- Reference issues: "Fix #123: Description"
- Keep commits atomic (one logical change per commit)

## Testing Philosophy

- **Unit tests:** Test individual functions in isolation
- **Integration tests:** Test components working together
- **No mocks for database:** Use test database or SQLite in-memory
- **Test edge cases:** Empty inputs, invalid data, API failures

## Performance Considerations

- **Database queries:** Use indexes, avoid N+1 queries
- **API calls:** Implement caching and rate limiting
- **Embeddings:** Batch processing, cache results
- **Frontend:** Code splitting, lazy loading

## Security Guidelines

- **Never commit secrets:** Use environment variables
- **Validate all inputs:** Use Pydantic schemas
- **Sanitize user data:** Prevent injection attacks
- **Review dependencies:** Check for known vulnerabilities

## Documentation

Update documentation when changing:
- API endpoints → `/docs/api.md`
- Architecture → `/docs/architecture.md`
- Data sources → `/docs/sources.md`
- Scoring logic → `/docs/scoring.md`
- Operations → `/docs/runbook.md`

## Community Guidelines

- Be respectful and inclusive
- Assume positive intent
- Provide constructive feedback
- Help newcomers
- Focus on code, not people

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Open a GitHub Discussion or reach out to maintainers.

Thank you for contributing to making news verification more accessible! 🎉
