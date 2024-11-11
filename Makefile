# Makefile
.PHONY: help venv update-pip install test lint format clean

# Python version handling
PYTHON := python3.11
VENV := .venv
VENV_BIN := $(VENV)/bin

help:
	@echo "Available commands:"
	@echo "  venv         - Create virtual environment"
	@echo "  update-pip   - Update pip to latest version"
	@echo "  install      - Install development dependencies"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Run pre-commit checks on all files"
	@echo "  format       - Format code with pre-commit autofixes"
	@echo "  clean        - Remove build artifacts"

venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment with Python 3.11..."; \
		$(PYTHON) -m venv $(VENV); \
	fi

update-pip: venv
	@echo "Upgrading pip..."
	$(VENV_BIN)/pip install --upgrade pip

install: update-pip
	$(VENV_BIN)/pip install -r requirements.txt
	$(VENV_BIN)/pip install -r requirements-dev.txt
	$(VENV_BIN)/pre-commit install

test:
	$(VENV_BIN)/pytest tests/ --cov=filecombinator --cov-report=term-missing

lint:
	$(VENV_BIN)/pre-commit run --all-files

format:
	$(VENV_BIN)/pre-commit run black --all-files
	$(VENV_BIN)/pre-commit run isort --all-files

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.pyc" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

clean-venv: clean
	rm -rf $(VENV)
