SHELL := /bin/bash
.SHELLFLAGS = -e -o pipefail -c
.DEFAULT_GOAL := setup

VENV = .venv
TEST_VENV = .venv-test
PYTHON := $(shell command -v python3 || command -v python)
DOCKER_PROJECT = user-manager

PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
TEST_PIP := $(TEST_VENV)/bin/pip
TEST_PY := $(TEST_VENV)/bin/python

ifeq ($(OS),Windows_NT)
	PIP := $(VENV)/Scripts/pip.exe
	PY := $(VENV)/Scripts/python.exe
	TEST_PIP := $(TEST_VENV)/Scripts/pip.exe
	TEST_PY := $(TEST_VENV)/Scripts/python.exe
endif

setup: venv install test lint docker
	@echo "Application is running in Docker."

venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
	else \
		echo "Virtual environment already exists."; \
	fi

install:
	@echo "Installing dependencies..."
	@$(PIP) install --require-hashes -r requirements.txt

test-env:
	@if [ ! -d "$(TEST_VENV)" ]; then \
		echo "Creating test virtual environment..."; \
		$(PYTHON) -m venv $(TEST_VENV); \
	else \
		echo "Test virtual environment already exists."; \
	fi
	@echo "Installing test dependencies..."
	@$(TEST_PIP) install --require-hashes -r requirements-test.txt

test: test-env
	@echo "Running tests..."
	@$(TEST_PY) -m pytest --cov=./ --cov-report=term-missing --cov-report html -q || echo "Some tests failed"

docker:
	@echo "Starting Docker container..."
	@docker compose -p $(DOCKER_PROJECT) up --build -d

lint: test-env
	@echo "Running Pylint..."
	@$(TEST_PY) -m pylint app tests || echo "Linting warnings/errors found"

reset:
	@echo "Cleaning everything..."
	@echo "Stopping and removing Docker containers and images..."
	@docker compose -p $(DOCKER_PROJECT) down --rmi all -v --remove-orphans || true
	@echo "Removing development virtual environment..."
	@rm -rf $(VENV)
	@echo "Removing test virtual environment..."
	@rm -rf $(TEST_VENV)
	@echo "Removing test coverage reports..."
	@rm -rf htmlcov .coverage .pytest_cache
	@echo "Removing Python cache..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + || true
	@echo "Project fully cleaned!"
