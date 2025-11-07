# Contributing to IDCardOCR

Thank you for considering contributing to IDCardOCR! This document provides guidelines for contributing to the project.

## Code of Conduct

This project adheres to a code of conduct that all participants are expected to uphold. Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear description** of the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, etc.)
- **Relevant logs** or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **Clear description** of the enhancement
- **Use case** - why this would be useful
- **Proposed implementation** (if you have ideas)

### Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main` for your feature/fix
3. **Make your changes** with clear, descriptive commits
4. **Test your changes** thoroughly
5. **Update documentation** if needed
6. **Submit a pull request** with a clear description

#### Pull Request Guidelines

- Follow the existing code style
- Add tests for new features
- Update documentation for changes
- Keep commits focused and atomic
- Write clear commit messages

#### Commit Message Format

```
type(scope): brief description

Detailed explanation if needed

Fixes #issue_number
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Development Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Tencent Cloud API credentials (for testing)

### Setup Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/IDCardOCR.git
cd IDCardOCR
```

2. Install dependencies:
```bash
uv sync
# or
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
# Add your test credentials
```

4. Run tests:
```bash
python -m pytest
```

## Project Structure

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed information about the project organization.

## Code Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Add comments for complex logic

### Example

```python
def extract_id_number(response: dict) -> str:
    """
    Extract ID number from API response.
    
    Args:
        response: API response dictionary
        
    Returns:
        str: Extracted ID number with apostrophe prefix
        
    Raises:
        ValueError: If response format is invalid
    """
    if 'Response' not in response:
        raise ValueError("Invalid API response format")
    
    id_num = response['Response'].get('IdNum', '')
    return f"'{id_num}" if id_num else ''
```

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Include both unit and integration tests where appropriate
- Test with real API calls using test credentials

## Documentation

- Update README.md for user-facing changes
- Update technical docs in `docs/` for implementation details
- Add inline comments for complex logic
- Update PROJECT_STRUCTURE.md if adding new files/directories

## Areas for Contribution

### High Priority

- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Support for other OCR providers
- [ ] Web interface
- [ ] Docker container
- [ ] CI/CD pipeline

### Medium Priority

- [ ] Batch processing optimization
- [ ] Progress bar for processing
- [ ] Email notifications
- [ ] Cloud storage integration
- [ ] Multi-language support

### Low Priority

- [ ] GUI application
- [ ] Mobile app
- [ ] Real-time processing
- [ ] Analytics dashboard

## Questions?

Feel free to open an issue for:
- Questions about the codebase
- Clarification on contribution process
- Discussion of potential features

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to IDCardOCR! 🎉

