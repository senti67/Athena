# Contributing to ATHENA

Thank you for your interest in contributing to the ATHENA Quantitative Platform.

## Code Standards
- **Python**: PEP 8 compliant, formatted with `black` and linted with `ruff`.
- **Typing**: All functions and methods must include explicit type hints.
- **Testing**: Every new feature or strategy must include automated unit or integration tests in `tests/`.

## Workflow
1. Fork and clone the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`.
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Run test suite:
   ```bash
   pytest tests/ -v
   ```
5. Format code:
   ```bash
   black .
   ruff check . --fix
   ```
6. Submit a Pull Request.
