# Makefile for drama-emcee developer workflow.
#
# Targets:
#   make venv         — create a local virtualenv at .venv/
#   make install      — create .venv/ (if needed) and install dependencies into it
#   make test         — build the Docker image and run pytest inside the container (cross-platform)
#   make test-local   — activate .venv/ and run pytest directly (Mac/Linux fast path)

IMAGE_NAME = drama-emcee-test
VENV_DIR   = .venv
PYTHON     = $(VENV_DIR)/bin/python3
PIP        = $(VENV_DIR)/bin/pip3

.PHONY: venv install test test-local

## venv: create the local virtualenv (skipped if it already exists)
venv:
	python3 -m venv $(VENV_DIR)

## install: create .venv/ if needed, then install all dependencies into it
install: venv
	$(PIP) install -r requirements.txt

## test: build the Docker image and run pytest inside the container (recommended for cross-platform use)
test:
	docker build -t $(IMAGE_NAME) .
	docker run --rm $(IMAGE_NAME)

## test-local: run the full test suite inside the local virtualenv (no Docker required)
test-local: install
	$(PYTHON) -m pytest tests/ -v
