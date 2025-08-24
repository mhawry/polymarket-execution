.PHONY: help install install-dev test test-cov lint format type-check clean build dev-check

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install production dependencies and package"
	@echo "  install-dev  Install development dependencies and package"
	@echo "  test         Run tests with coverage"
	@echo "  test-cov     Run tests with coverage report"
	@echo "  lint         Run all linting tools (flake8, black, isort, mypy)"
	@echo "  format       Format code with black and isort"
	@echo "  type-check   Run mypy type checking"
	@echo "  clean        Clean build artifacts and cache"
	@echo "  build        Build distribution packages"
	@echo "  dev-check    Run all development checks"

# Installation
install:
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

# Testing
test:
	pytest

test-cov:
	pytest --cov=polymarket_execution --cov-report=html --cov-report=term-missing

# Linting and formatting
lint: format type-check
	flake8 src/ tests/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/polymarket_execution/

# Build and package
build: clean
	python -m build

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleaned build artifacts"

# Development workflow
dev-check: format type-check test lint
	@echo "All development checks passed!"
