# CartesSociete

Solutions and tools for a cardboard/card game design.

## Setup

```bash
# Install dependencies
uv sync

# Install dev dependencies
uv sync --group dev
```

## Development

```bash
# Run tests
uv run pytest

# Format code
uv run ruff format .

# Lint code
uv run ruff check .
```

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
