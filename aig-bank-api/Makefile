SHELL := /bin/bash
PYTHON ?= python3
VENV := venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
PY := $(BIN)/python
UVICORN := $(BIN)/uvicorn

.PHONY: help setup install dev seed lint fmt type test test-unit test-e2e clean coverage

help:
	@echo "Targets:"
	@echo "  setup          Create venv and install dev deps"
	@echo "  install        Install project (editable) + optional extras"
	@echo "  dev            Start API with reload"
	@echo "  seed           Seed dev data"
	@echo "  lint           Ruff (lint) + Black (check)"
	@echo "  fmt            Black (format) + Ruff (fix)"
	@echo "  type           Type check with mypy"
	@echo "  test           Run all tests"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-e2e	 Run end-to-end tests only"
	@echo "  coverage       Run tests with coverage report"
	@echo "  clean          Remove caches/artifacts"
	@echo "  clean-all      Remove venv and generated files"

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

install:
	$(PIP) install -e "."

dev:
	$(UVICORN) app.main:app --reload --host $${APP_HOST:-0.0.0.0} --port $${APP_PORT:-8000}

fmt:
	$(BIN)/ruff check . --fix
	$(BIN)/black .

lint:
	$(BIN)/ruff check .
	$(BIN)/black --check .

type:
	$(BIN)/mypy app

test:
	$(BIN)/pytest --no-cov -q --dist loadfile -n auto

test-unit:
	$(BIN)/pytest -v -m unit --no-cov

test-e2e:
	$(BIN)/pytest -v -m e2e --no-cov --dist loadfile -n auto

coverage:
	$(BIN)/pytest -v --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-fail-under=80

seed:
	$(PY) scripts/seed_demo.py

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete


clean-all: clean
	find . -type f -name "*.db" -delete
	find . -type f -name "*.db-shm" -delete
	find . -type f -name "*.db-wal" -delete
	find . -type d -name "logs" -exec rm -rf {} +
	find . -type d -name "venv" -exec rm -rf {} +
