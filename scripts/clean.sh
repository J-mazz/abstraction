#!/bin/bash
# Clean up build artifacts and cache

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}"
echo "=========================================="
echo "  Abstraction Cleanup Script"
echo "=========================================="
echo -e "${NC}"
echo ""

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "This will remove:"
echo "  - Build artifacts (executable, dist/)"
echo "  - Python cache (__pycache__, *.pyc)"
echo "  - Logs (./logs/)"
echo ""
echo "This will NOT remove:"
echo "  - Downloaded model (./models/)"
echo "  - Agent cache (./data/)"
echo "  - Virtual environment (./venv/)"
echo ""

read -p "Continue? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Cleanup cancelled"
    exit 0
fi

echo ""
print_status "Cleaning up..."

# Remove executable
if [ -f "abstraction" ]; then
    rm -f abstraction
    print_status "Removed executable"
fi

# Remove distribution packages
if [ -d "dist" ]; then
    rm -rf dist
    print_status "Removed dist/"
fi

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
print_status "Removed Python cache"

# Remove logs
if [ -d "logs" ]; then
    rm -rf logs
    print_status "Removed logs/"
fi

# Remove build directories
if [ -d "build" ]; then
    rm -rf build
    print_status "Removed build/"
fi

if [ -d "target" ]; then
    rm -rf target
    print_status "Removed target/"
fi

echo ""
print_status "Cleanup complete!"
echo ""

# Optional deep clean
read -p "Also remove model and cache? (DEEP CLEAN) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Performing deep clean..."

    if [ -d "models" ]; then
        rm -rf models
        print_status "Removed models/ (~14GB freed)"
    fi

    if [ -d "data" ]; then
        rm -rf data
        print_status "Removed data/"
    fi

    if [ -d "venv" ]; then
        rm -rf venv
        print_status "Removed venv/"
    fi

    echo ""
    print_status "Deep clean complete!"
fi

echo ""
