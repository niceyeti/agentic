# Description: this is a nice KISS single-package langchain project definition
# for multi-agent coordination and routing. The goal here is a basic foundation
# with batteries includes for control plane aspects outside this project:
# tracing, HITL feedback, RBAC, etc.

SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c


# Initializes .venv and installs all deps.
.PHONY: install
install:
	mkdir -p .venv
	uv sync


.PHONY: fmt
fmt:
	black .


.PHONY: dep-scan
dep-scan:
	uv add --upgrade pip-audit
	uv run pip-audit .


# Generates project sbom
.PHONY: sbom
sbom:
	uv add --upgrade cyclonedx-py
	uv run cyclonedx-py environment --pyproject pyproject.toml -o sbom.json


# width and height correspond with 16:9 ratio
.PHONY: shiny-metal-ascii
shiny-metal-ascii:
	aview -driver stdout -width 250 -height 141 -contrast 0.141732 -gamma 1.979932 .img/bender.pnm > .img/bender.txt