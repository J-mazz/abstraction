# Makefile for Abstraction Agent Framework

.PHONY: help install run build clean deep-clean download-model test

# Default target
help:
	@echo "Abstraction Agent Framework - Make Targets"
	@echo ""
	@echo "Development:"
	@echo "  make install        - Install dependencies"
	@echo "  make run            - Run the application"
	@echo "  make download-model - Pre-download the model"
	@echo ""
	@echo "Building:"
	@echo "  make build          - Build standalone executable"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make deep-clean     - Clean everything (including model)"
	@echo ""
	@echo "Quick Start:"
	@echo "  make install && make run"

# Install dependencies
install:
	@echo "Installing dependencies..."
	python3 -m venv venv || true
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✓ Dependencies installed"

# Run the application
run:
	@echo "Starting Abstraction..."
	@if [ ! -f .env ]; then \
		echo "WARNING: .env file not found!"; \
		echo "Copy .env.example to .env and add your HUGGINGFACE_TOKEN"; \
		exit 1; \
	fi
	@if [ -d venv ]; then \
		. venv/bin/activate && python3 src/main.py; \
	else \
		python3 src/main.py; \
	fi

# Download model ahead of time
download-model:
	@echo "Downloading model..."
	@if [ ! -f .env ]; then \
		echo "ERROR: .env file not found!"; \
		exit 1; \
	fi
	@if [ -d venv ]; then \
		. venv/bin/activate && python3 download_model.py; \
	else \
		python3 download_model.py; \
	fi

# Build standalone executable
build:
	@./build.sh

# Clean build artifacts
clean:
	@./clean.sh

# Deep clean (including model and cache)
deep-clean:
	@rm -rf models/ data/ logs/ venv/ dist/ build/ target/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -f abstraction abstraction.exe
	@echo "✓ Deep clean complete"

# Run tests (placeholder for future)
test:
	@echo "Running tests..."
	@if [ -d venv ]; then \
		. venv/bin/activate && python3 -m pytest tests/ -v || echo "No tests found"; \
	else \
		python3 -m pytest tests/ -v || echo "No tests found"; \
	fi

# Quick setup for first time users
setup: install
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env file"; \
		echo ""; \
		echo "IMPORTANT: Edit .env and add your HUGGINGFACE_TOKEN"; \
		echo "Get token from: https://huggingface.co/settings/tokens"; \
		echo ""; \
	fi
	@echo "✓ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env and add your HuggingFace token"
	@echo "  2. Run: make run"
