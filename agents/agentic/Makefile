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


# Note: the langchain project seems to be immature and potentially unstable,
# breaking out packages. This provides for an explicit install for now, but
# these seem fragile. Note the dash in 'text-splitters'.
#
# There's no reason for this, use 'uv add [pkg]' manually. I often forget uv
# style.
.PHONY: install-langchain
install-langchain:
	uv add \
		langchain \
		langgraph \
		langchain_community \
		langchain_openai \
		langchain-text-splitters \
		beautifulsoup4


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


# Automagically activates the .venv (default) and runs the app. To show the venv
# location: 'uv python find'. The sqlite string is for dev, and ensures the
# sqlite file is written to memory/temp.
.PHONY: run
run: install
	mkdir -p /tmp/hotel_db
	rm -rf /tmp/hotel_db/cornwall_hotels.db
	touch /tmp/hotel_db/cornwall_hotels.db
	chmod ugo+rw /tmp/hotel_db/cornwall_hotels.db
#	SQLITE_URI="sqlite:///tmp/hotel_db/cornwall_hotels.db?mode=memory&cache=shared"
	SQLITE_URI="sqlite:///:memory:" \
		uv run src/agentic/main.py


# Generates project sbom
.PHONY: sbom
sbom:
	uv add --upgrade cyclonedx-py
	uv run cyclonedx-py environment --pyproject pyproject.toml -o sbom.json


# width and height correspond with 16:9 ratio
.PHONY: shiny-metal-ascii
shiny-metal-ascii:
	echo "Alllright... since you asked politely."
	aview -driver stdout -width 250 -height 141 -contrast 0.141732 -gamma 1.979932 .img/bender.pnm > .img/bender.txt