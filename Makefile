PYTHON := python3
PIP := $(PYTHON) -m pip
NPM := npm

.PHONY: install build test docs docs-serve clean help

install: # Install NumFu from source
	@echo "Installing NumFu from source..."
	./scripts/install.sh

dev: # Install NumFu and its development dependencies
	@echo "Installing NumFu and its development dependencies..."
	./scripts/install.sh && pip install ruff pyright

build: # Build NumFu (wheels, stdlib)
	@echo "Building NumFu..."
	./scripts/build.sh

test: # Run all tests
	@echo "Running tests..."
	./scripts/tests.sh

docs: # Build documentation site
	@echo "Building documentation..."
	python3 scripts/make_ico.py docusaurus/static/img/logo.png -o docusaurus/static/img/favicon.ico
	cd docusaurus && $(NPM) install && $(NPM) run build
	@echo "Documentation built successfully."

serve: # Serve docs locally
	@echo "Serving docs locally..."
	cd docusaurus && $(NPM) run start

clean: # Clean __pycache__ and .egg-info
	@echo "Cleaning __pycache__ and .egg-info..."
	@find . -name "__pycache__" -type d -exec rm -rf {} +
	@find . -name "*.egg-info" -type d -exec rm -rf {} +

help: # Show this help
	@grep -E '^[a-zA-Z_-]+:.*?#' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?# "}; {printf "  make %-12s %s\n", $$1, $$2}'
