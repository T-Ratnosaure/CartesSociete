# Contributing to CartesSociete

Thank you for your interest in contributing to CartesSociete! This document provides guidelines for contributing.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/T-Ratnosaure/CartesSociete.git
   cd CartesSociete
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Install pre-commit hooks:
   ```bash
   uv run pre-commit install
   ```

## Development Workflow

### Creating a Feature Branch

Always create a feature branch for your changes:

```bash
git checkout -b feat/your-feature-name
# or for bug fixes:
git checkout -b fix/bug-description
```

### Code Quality

Before committing, ensure your code passes all checks:

```bash
# Run all checks
uv run isort .              # Sort imports
uv run ruff format .        # Format code
uv run ruff check .         # Lint code
uv run pytest               # Run tests
```

Or use pre-commit to run checks automatically:

```bash
uv run pre-commit run --all-files
```

### Commit Messages

Use conventional commit format:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `ci:` - CI/CD changes
- `chore:` - Maintenance tasks

Example:
```
feat(cards): add new card type for special abilities

- Implement SpecialCard class with ability system
- Add tests for ability activation
- Update game engine to handle special cards
```

### Pull Requests

1. Push your branch:
   ```bash
   git push -u origin your-branch-name
   ```

2. Create a Pull Request on GitHub

3. Fill out the PR template completely

4. Ensure all CI checks pass

5. Request review from maintainers

## Code Standards

### Type Hints

All functions must have type hints:

```python
def calculate_damage(attacker: Card, defender: Card) -> int:
    """Calculate damage dealt by attacker to defender."""
    ...
```

### Docstrings

Public functions and classes require docstrings:

```python
def play_card(card: Card, target: Target) -> GameState:
    """Play a card targeting a specific entity.

    Args:
        card: The card to play.
        target: The target of the card effect.

    Returns:
        Updated game state after the card is played.

    Raises:
        InvalidPlayError: If the card cannot be played.
    """
    ...
```

### Testing

- All new features must include tests
- Maintain or improve code coverage
- Test edge cases and error conditions

## Project Structure

```
CartesSociete/
├── src/
│   ├── cards/        # Card definitions
│   ├── game/         # Game engine
│   ├── players/      # Player AI/strategies
│   ├── simulation/   # Simulation tools
│   └── analysis/     # Balance analysis
├── tests/            # Test suite
├── data/             # Game data
├── configs/          # Configuration files
├── notebooks/        # Analysis notebooks
└── scripts/          # CLI scripts
```

## Questions?

Open an issue on GitHub for questions or discussions about contributing.

Thank you for contributing!
