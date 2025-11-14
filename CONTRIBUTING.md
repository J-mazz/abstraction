# Contributing to Abstraction

Thank you for your interest in contributing to Abstraction! 🎉 We welcome contributions from everyone. This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Documentation](#documentation)

## 🤝 Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other contributors
- Help create a positive community

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **Git** for version control
- **Rust toolchain** (for PyApp builds)
- **16GB RAM minimum** (for running the application)
- **HuggingFace account** (for model access)

### Quick Setup

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/abstraction.git
   cd abstraction
   ```
3. **Set up upstream remote**:
   ```bash
   git remote add upstream https://github.com/J-mazz/abstraction.git
   ```

## 🛠️ Development Setup

### Environment Setup

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install development dependencies**:
   ```bash
   pip install pytest pytest-asyncio pytest-cov black pylint mypy
   ```

### Configuration

1. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Add your HuggingFace token** to `.env`:
   ```
   HUGGINGFACE_TOKEN=your_token_here
   ```

### Verify Setup

Run the tests to ensure everything works:
```bash
python -m pytest tests/ -v
```

## 🔄 Development Workflow

### 1. Choose an Issue

- Check [open issues](https://github.com/J-mazz/abstraction/issues) for tasks
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to indicate you're working on it

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Changes

- Write clear, focused commits
- Test your changes thoroughly
- Follow the coding standards below

### 4. Test Your Changes

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_memory.py -v

# Run with coverage
python -m pytest --cov=src --cov-report=html
```

### 5. Update Documentation

- Update relevant documentation for your changes
- Add docstrings to new functions/classes
- Update README if needed

## 💻 Coding Standards

### Python Style

We follow PEP 8 with some specific guidelines:

- **Line length**: 100 characters maximum
- **Imports**: Use absolute imports, group them properly
- **Docstrings**: Use Google-style docstrings
- **Type hints**: Add type annotations where possible

### Code Formatting

We use Black for automatic code formatting:

```bash
# Format code
black src/ tests/

# Check formatting without changing files
black --check src/ tests/
```

### Linting

Use pylint for code quality checks:

```bash
# Run pylint
pylint src/ tests/

# With specific configuration
pylint --rcfile=.pylintrc src/
```

### Type Checking

Use mypy for static type checking:

```bash
# Type check
mypy src/

# With strict mode
mypy --strict src/
```

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

Examples:
```
feat(ui): add dark mode toggle
fix(cache): resolve message serialization bug
docs(readme): update installation instructions
```

## 🧪 Testing

### Running Tests

```bash
# All tests
python -m pytest

# Specific test file
python -m pytest tests/test_memory.py

# With verbose output
python -m pytest -v

# With coverage
python -m pytest --cov=src --cov-report=html
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files as `test_*.py`
- Use descriptive test function names: `test_should_do_something`
- Include docstrings explaining what each test verifies
- Use fixtures for common setup/teardown

Example:
```python
def test_cache_set_get_delete(cache_manager):
    """Test basic cache operations."""
    cache_manager.set("key", "value")
    assert cache_manager.get("key") == "value"
    assert cache_manager.delete("key") is True
    assert cache_manager.get("key") is None
```

### Test Coverage

Maintain high test coverage (>85%). Check coverage with:
```bash
pytest --cov=src --cov-report=term-missing
```

## 📝 Submitting Changes

### Pull Request Process

1. **Ensure your branch is up to date**:
   ```bash
   git fetch upstream
   git rebase upstream/master
   ```

2. **Run final checks**:
   ```bash
   # Format code
   black src/ tests/
   
   # Run tests
   python -m pytest --cov=src
   
   # Type check
   mypy src/
   
   # Lint
   pylint src/
   ```

3. **Push your branch**:
   ```bash
   git push origin your-branch-name
   ```

4. **Create Pull Request**:
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Fill out the PR template
   - Reference any related issues

### PR Requirements

Your PR should:
- ✅ Pass all tests
- ✅ Pass linting and type checking
- ✅ Include appropriate tests for new features
- ✅ Update documentation if needed
- ✅ Follow coding standards
- ✅ Have a clear description of changes

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Clear title** describing the issue
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, etc.)
- **Error messages** and stack traces
- **Screenshots** if applicable

### Feature Requests

For feature requests, please:

- **Check existing issues** first
- **Describe the problem** you're trying to solve
- **Explain your proposed solution**
- **Consider alternative approaches**
- **Discuss potential impacts**

## 📚 Documentation

### Building Documentation

```bash
# Install docs dependencies
pip install mkdocs mkdocs-material

# Serve docs locally
mkdocs serve

# Build docs
mkdocs build
```

### Writing Documentation

- Use clear, concise language
- Include code examples where helpful
- Keep screenshots up to date
- Test instructions on a clean environment

## 🎯 Areas for Contribution

### High Priority
- **Performance optimizations**
- **Additional tool integrations**
- **UI/UX improvements**
- **Cross-platform testing**

### Medium Priority
- **Documentation improvements**
- **Additional test coverage**
- **Code refactoring**
- **Feature enhancements**

### Good for Beginners
- **Bug fixes**
- **Documentation updates**
- **Test improvements**
- **Code formatting**

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check the docs first

## 🙏 Recognition

Contributors will be recognized in:
- Release notes
- Contributors file
- GitHub's contributor insights

Thank you for contributing to Abstraction! 🚀
