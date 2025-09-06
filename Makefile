PYTHON := python3
PIP := $(PYTHON) -m pip
NPM := npm

.PHONY: install build test docs docs-serve clean help

install: # Install NumFu from source
	@echo "Installing NumFu from source..."
	./scripts/install.sh

build: # Build NumFu (wheels, stdlib)
	@echo "Building NumFu..."
	./scripts/build.sh

test: # Run all tests
	@echo "Running tests..."
	./scripts/tests.sh

docs: # Build documentation site
	@echo "Building documentation..."
	cd docusaurus && $(NPM) install && $(NPM) run build

serve: # Serve docs locally
	@echo "Serving docs locally..."
	cd docusaurus && $(NPM) run start

clean: # Clean __pycache__
	@echo "Cleaning __pycache__..."
	@find . -name "__pycache__" -type d -exec rm -rf {} +

help: # Show this help
	@grep -E '^[a-zA-Z_-]+:.*?#' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?# "}; {printf "  make %-12s %s\n", $$1, $$2}'
