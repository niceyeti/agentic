# Description: this is a nice KISS single-package langchain project definition
# for multi-agent coordination and routing. The goal here is a basic foundation
# with batteries includes for control plane aspects outside this project:
# tracing, HITL feedback, RBAC, etc.

SHELL := /bin/bash



# Initializes .venv and installs all deps.
.PHONY: install
install:
	mkdir -p .venv
	uv sync


# There's no reason for this, use 'uv add [pkg]' manually. I often forget uv style.
.PHONY: install-langchain
install-langchain:
	uv add langchain langgraph


.PHONY: unit-tests
unit-tests:
	uv run pytest


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


# Generates project sbom
.PHONY: sbom
sbom:
	uv add --upgrade cyclonedx-py
	uv run cyclonedx-py environment --pyproject pyproject.toml -o sbom.json


# width and height correspond with 16:9 ratio
.PHONY: shiny-metal-ascii
shiny-metal-ascii:
	echo "Alllright..."
	aview -driver stdout -width 250 -height 141 -contrast 0.141732 -gamma 1.979932 .img/bender.pnm > .img/bender.txt