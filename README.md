# CartesSociete

[![CI](https://github.com/T-Ratnosaure/CartesSociete/actions/workflows/ci.yml/badge.svg)](https://github.com/T-Ratnosaure/CartesSociete/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

Solutions and tools for a cardboard/card game design. This project provides a framework for designing, simulating, and balancing card games.

## Features

- **Game Engine**: Core game mechanics and rules system
- **Card System**: Flexible card definitions and types
- **Player AI**: Strategies and AI implementations
- **Simulation**: Monte Carlo simulations for balance testing
- **Analysis**: Statistical analysis and balance metrics

## Requirements

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/T-Ratnosaure/CartesSociete.git
cd CartesSociete

# Install dependencies
uv sync

# Install dev dependencies
uv sync --dev
```

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
# Sort imports (run first - authoritative)
uv run isort .

# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Run all checks at once with pre-commit
uv run pre-commit run --all-files
```

## Development

### Setting Up Pre-commit Hooks

Pre-commit hooks automatically run code quality checks before each commit:

```bash
uv run pre-commit install
```

### Git Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. Make your changes and ensure all checks pass

3. Commit with conventional commit messages:
   ```bash
   git commit -m "feat(cards): add new card type"
   ```

4. Push and create a Pull Request:
   ```bash
   git push -u origin feat/your-feature-name
   ```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## Project Structure

```
CartesSociete/
├── src/                   # Main source code
│   ├── cards/            # Card definitions and types
│   ├── game/             # Game engine and rules
│   ├── players/          # Player strategies and AI
│   ├── simulation/       # Game simulation tools
│   └── analysis/         # Balance and statistics analysis
├── tests/                # Test suite
├── data/                 # Card data, game logs
├── notebooks/            # Analysis notebooks
├── configs/              # Game configuration files
└── scripts/              # CLI scripts
```

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration:

- **Lint & Format Check**: Validates isort, ruff format, and ruff lint
- **Test**: Runs pytest with coverage reporting
- **Security Scan**: Checks for dependency vulnerabilities with pip-audit

All checks must pass before merging pull requests.

## Security

For security-related information, see [SECURITY.md](SECURITY.md).

To report a vulnerability, please follow the responsible disclosure process outlined in our security policy.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a Pull Request.
