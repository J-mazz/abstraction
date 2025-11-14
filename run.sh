#!/bin/bash
# Quick start script for Abstraction Agent Framework

echo "======================================"
echo "  Abstraction Agent Framework"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python3 -c "import langgraph" 2>/dev/null; then
    echo "Installing dependencies (this may take a few minutes)..."
    pip install -r requirements.txt
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Please create .env from .env.example and add your HUGGINGFACE_TOKEN"
    echo ""
    read -p "Press Enter to continue anyway or Ctrl+C to exit..."
fi

# Run the application
echo ""
echo "Starting Abstraction Agent Framework..."
echo ""
python3 src/main.py
