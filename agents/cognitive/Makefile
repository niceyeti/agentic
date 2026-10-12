# Description: this is a nice KISS single-package langchain project definition
# for multi-agent coordination and routing. The goal here is a basic foundation
# with batteries includes for control plane aspects outside this project:
# tracing, HITL feedback, RBAC, etc.

SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c


.PHONY: clean
clean:
	rm -rf .venv


.PHONY: install-node-dependencies
install-node-dependencies:
	npm init -y
	npm install @modelcontextprotocol/server-memory@2026.8.31
	npm install @brave/brave-search-mcp-server@2.1.4
	npm audit


# Initializes .venv and installs all deps.
.PHONY: install
install:
	mkdir -p .venv
	uv sync


.PHONY: unit-tests
unit-tests:
	uv run pytest -s


.PHONY: fmt
fmt:
	black .


.PHONY: dep-scan
dep-scan:
	uv add --upgrade pip-audit
	uv run pip-audit .


.PHONY: build
build:
	docker build -f Dockerfile .


# Automagically activates the .venv (default) and runs the app. To show the venv
# location: 'uv python find'. The sqlite string is for dev, and ensures the
# sqlite file is written to memory/temp.
.PHONY: run
run: install
	echo "todo"
	exit 1


# Generates project sbom
.PHONY: sbom
sbom:
	uv add --upgrade cyclonedx-py
	uv run cyclonedx-py environment --pyproject pyproject.toml -o sbom.json
