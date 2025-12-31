"""Pytest configuration and fixtures for CartesSociete tests."""

import os

import pytest


def is_ci() -> bool:
    """Check if running in CI environment."""
    return os.environ.get("CI", "").lower() in ("true", "1", "yes")


@pytest.fixture
def ci_aware_game_count() -> int:
    """Return reduced game count for CI, normal count otherwise."""
    return 2 if is_ci() else 5


@pytest.fixture
def ci_aware_mcts_simulations() -> int:
    """Return reduced MCTS simulation count for CI."""
    return 3 if is_ci() else 10


# Configure pytest-timeout default
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with CI-aware settings."""
    # Register custom markers
    config.addinivalue_line("markers", "slow: marks tests as slow (may skip in CI)")

    # Set default timeout if not specified
    if config.option.timeout is None:
        config.option.timeout = 120 if is_ci() else 300
