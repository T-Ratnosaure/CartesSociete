# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment pipeline for CartesSociete.

## Overview

The CI/CD pipeline is implemented using GitHub Actions and runs on every push and pull request to the `master` or `main` branches.

## Workflow File

Location: `.github/workflows/ci.yml`

## Jobs

### 1. Lint & Format Check

**Purpose**: Ensure code quality and consistent formatting across the codebase.

**Steps**:
1. Checkout repository
2. Set up Python 3.12
3. Install uv package manager (with caching enabled)
4. Install dev dependencies
5. Check import sorting with isort
6. Check code formatting with ruff format
7. Lint code with ruff check

**Failure Conditions**:
- Imports not sorted correctly
- Code not formatted according to ruff standards
- Linting errors detected

### 2. Test

**Purpose**: Run the test suite and collect coverage metrics.

**Dependencies**: Requires `lint` job to pass first.

**Steps**:
1. Checkout repository
2. Set up Python 3.12
3. Install uv with caching
4. Install dev dependencies
5. Run pytest with coverage
6. Upload coverage report to Codecov (optional)

**Coverage Configuration**:
- Source directory: `src/`
- Reports: Terminal output and XML for CI integration

### 3. Security Scan

**Purpose**: Check for known vulnerabilities in project dependencies.

**Steps**:
1. Checkout repository
2. Set up Python 3.12
3. Install uv with caching
4. Install dev dependencies
5. Run pip-audit for vulnerability scanning

**Note**: Currently set to `continue-on-error: true` to prevent blocking on vulnerability findings during initial development. Consider making this strict once dependencies are finalized.

## Caching

The pipeline uses uv's built-in caching mechanism:

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v4
  with:
    enable-cache: true
    cache-dependency-glob: "uv.lock"
```

This significantly speeds up subsequent runs by caching the virtual environment and dependencies.

## Security

### Permissions

The workflow uses minimal permissions:

```yaml
permissions:
  contents: read
  pull-requests: read
```

This follows the principle of least privilege.

### Concurrency

Redundant workflow runs are cancelled automatically:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

This saves CI minutes and prevents queue buildup.

## Dependabot

Location: `.github/dependabot.yml`

Automatically creates PRs for:
- **GitHub Actions**: Weekly updates with `ci` prefix
- **Python dependencies**: Weekly updates with `deps` prefix

Limited to 5 open PRs for Python dependencies to prevent PR overload.

## Local Development

To replicate CI checks locally:

```bash
# Install dev dependencies
uv sync --dev

# Run the same checks as CI
uv run isort --check-only --diff .
uv run ruff format --check --diff .
uv run ruff check .
uv run pytest -v --cov=src --cov-report=term-missing
uv run pip-audit

# Or use pre-commit to run all checks
uv run pre-commit run --all-files
```

## Troubleshooting

### Common Issues

1. **isort fails**: Run `uv run isort .` locally to fix imports

2. **ruff format fails**: Run `uv run ruff format .` locally to fix formatting

3. **ruff check fails**: Run `uv run ruff check --fix .` to auto-fix some issues

4. **Tests fail**: Check test output, ensure you haven't broken existing functionality

5. **pip-audit fails**: Review the vulnerability report and update affected packages

## Future Enhancements

Planned improvements to the CI/CD pipeline:

- [ ] Add type checking with pyrefly when configured
- [ ] Set up code coverage thresholds
- [ ] Add automated release workflow
- [ ] Integrate with code review tools
- [ ] Add performance benchmarking
