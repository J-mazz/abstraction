#!/bin/bash
# Build orchestrator for creating standalone executable with PyApp

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_PATH=$(pwd)
PYTHON_VERSION="3.11"
EXEC_SPEC="src.main:main"
OUTPUT_NAME="abstraction"

echo -e "${BLUE}"
echo "=========================================="
echo "  Abstraction Build Orchestrator"
echo "=========================================="
echo -e "${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if Rust is installed
echo ""
print_info "Checking prerequisites..."
if ! command -v cargo &> /dev/null; then
    print_error "Rust/Cargo not found!"
    echo ""
    echo "Please install Rust toolchain:"
    echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    echo ""
    echo "After installation, run:"
    echo "  source \$HOME/.cargo/env"
    echo "  ./build.sh"
    exit 1
else
    RUST_VERSION=$(rustc --version | cut -d' ' -f2)
    print_status "Rust installed (version: $RUST_VERSION)"
fi

# Check if PyApp is installed
if ! command -v pyapp &> /dev/null; then
    print_warning "PyApp not found. Installing..."
    echo ""
    cargo install pyapp --locked
    print_status "PyApp installed"
else
    print_status "PyApp already installed"
fi

# Check if dependencies are up to date
echo ""
print_info "Checking Python dependencies..."
if [ -f "requirements.txt" ]; then
    print_status "requirements.txt found"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Check if pyproject.toml exists
if [ -f "pyproject.toml" ]; then
    print_status "pyproject.toml found"
else
    print_error "pyproject.toml not found!"
    exit 1
fi

# Display build configuration
echo ""
print_info "Build Configuration:"
echo "  Project Path: $PROJECT_PATH"
echo "  Python Version: $PYTHON_VERSION"
echo "  Entry Point: $EXEC_SPEC"
echo "  Output Name: $OUTPUT_NAME"
echo ""

# Ask for confirmation
read -p "Proceed with build? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Build cancelled by user"
    exit 0
fi

# Set environment variables for PyApp
echo ""
print_info "Setting PyApp environment variables..."
export PYAPP_PROJECT_PATH="$PROJECT_PATH"
export PYAPP_PYTHON_VERSION="$PYTHON_VERSION"
export PYAPP_EXEC_SPEC="$EXEC_SPEC"
export PYAPP_IS_GUI="true"

print_status "Environment configured"

# Build the executable
echo ""
print_info "Building executable (this may take 5-10 minutes)..."
echo ""

if pyapp build; then
    print_status "Build completed successfully!"
else
    print_error "Build failed!"
    exit 1
fi

# Find the generated executable
echo ""
print_info "Locating executable..."

# PyApp typically creates the executable in the current directory
if [ -f "$OUTPUT_NAME" ]; then
    EXEC_PATH="./$OUTPUT_NAME"
elif [ -f "./target/release/$OUTPUT_NAME" ]; then
    EXEC_PATH="./target/release/$OUTPUT_NAME"
    mv "$EXEC_PATH" "./$OUTPUT_NAME"
    EXEC_PATH="./$OUTPUT_NAME"
else
    print_error "Could not find generated executable!"
    exit 1
fi

# Make it executable
chmod +x "$EXEC_PATH"
print_status "Executable located: $EXEC_PATH"

# Get file size
EXEC_SIZE=$(du -h "$EXEC_PATH" | cut -f1)
echo ""
print_info "Executable Details:"
echo "  Location: $EXEC_PATH"
echo "  Size: $EXEC_SIZE"
echo ""

# Test the executable
echo ""
print_info "Testing executable..."
if [ -f "$EXEC_PATH" ] && [ -x "$EXEC_PATH" ]; then
    print_status "Executable is valid"
else
    print_error "Executable test failed!"
    exit 1
fi

# Success message
echo ""
echo -e "${GREEN}"
echo "=========================================="
echo "  Build Successful! 🎉"
echo "=========================================="
echo -e "${NC}"
echo ""
echo "To run the application:"
echo "  $EXEC_PATH"
echo ""
echo "To distribute:"
echo "  1. Copy '$OUTPUT_NAME' to target system"
echo "  2. Run it (first run will download model)"
echo ""
print_warning "Note: The executable is ~${EXEC_SIZE}. The model (~14GB) downloads on first run."
echo ""

# Optional: Create distribution package
read -p "Create distribution package (tar.gz)? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Creating distribution package..."

    DIST_NAME="abstraction-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)"
    DIST_DIR="./dist/$DIST_NAME"

    mkdir -p "$DIST_DIR"

    # Copy executable
    cp "$EXEC_PATH" "$DIST_DIR/"

    # Copy essential files
    cp README.md "$DIST_DIR/" 2>/dev/null || true
    cp QUICKSTART.md "$DIST_DIR/" 2>/dev/null || true
    cp .env.example "$DIST_DIR/" 2>/dev/null || true
    cp LICENSE "$DIST_DIR/" 2>/dev/null || true

    # Create simple README for distribution
    cat > "$DIST_DIR/INSTALL.txt" << 'EOF'
Abstraction - AI Agent Framework
================================

Quick Start:
1. Create .env file from .env.example
2. Add your HuggingFace token to .env
3. Run: ./abstraction
4. Wait for model download (first run only, ~14GB)

Requirements:
- 16GB RAM minimum
- 20GB free disk space
- Linux/macOS/Windows

For detailed instructions, see QUICKSTART.md

Support: https://github.com/your-repo
EOF

    # Create tarball
    cd ./dist
    tar -czf "${DIST_NAME}.tar.gz" "$DIST_NAME"
    cd ..

    DIST_SIZE=$(du -h "./dist/${DIST_NAME}.tar.gz" | cut -f1)

    print_status "Distribution package created!"
    echo ""
    echo "  Package: ./dist/${DIST_NAME}.tar.gz"
    echo "  Size: $DIST_SIZE"
    echo ""
fi

print_status "All done!"
