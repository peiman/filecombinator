.PHONY: help venv update-pip install test lint format clean

# Python version handling
PYTHON := python3.11
VENV := .venv
VENV_BIN := $(VENV)/bin
VENV_ACTIVATE := source $(VENV_BIN)/activate

# Function to check if the virtual environment is active
define ensure_venv
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "Virtual environment is not activated. Activating now..."; \
		$(VENV_ACTIVATE); \
	fi
endef

help:
	@$(ensure_venv)
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
		echo "Creating virtual environment with $(PYTHON)..."; \
		$(PYTHON) -m venv $(VENV); \
	fi

update-pip:
	@$(ensure_venv)
	@echo "Upgrading pip..."
	$(VENV_BIN)/pip install --upgrade pip

install:
	@$(ensure_venv)
	$(VENV_BIN)/pip install -r requirements.txt
	$(VENV_BIN)/pip install -r requirements-dev.txt
	$(VENV_BIN)/pre-commit install

test:
	@$(ensure_venv)
	$(VENV_BIN)/coverage erase
	PYTHONPATH=${PWD} $(VENV_BIN)/pytest tests/ --cov=filecombinator --cov-report=term-missing --cov-branch
	$(VENV_BIN)/coverage combine || true
	$(VENV_BIN)/coverage report

lint:
	@$(ensure_venv)
	$(VENV_BIN)/pre-commit run --all-files

format:
	@$(ensure_venv)
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
