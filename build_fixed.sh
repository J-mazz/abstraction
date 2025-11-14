#!/bin/bash
# Fixed build script for PyApp with proper configuration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  Abstraction PyApp Build (Fixed)${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Configuration
PROJECT_DIR=$(pwd)
WHEEL_NAME="abstraction_agent-0.1.0-py3-none-any.whl"
WHEEL_PATH="${PROJECT_DIR}/dist/${WHEEL_NAME}"

# Step 1: Build the wheel if it doesn't exist
if [ ! -f "$WHEEL_PATH" ]; then
    echo -e "${BLUE}Building Python wheel...${NC}"
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    python -m build --wheel
    echo -e "${GREEN}✓ Wheel built${NC}"
else
    echo -e "${GREEN}✓ Wheel already exists${NC}"
fi

# Step 2: Clone PyApp if not already cloned
if [ ! -d "pyapp-build" ]; then
    echo -e "${BLUE}Cloning PyApp...${NC}"
    git clone --depth 1 https://github.com/ofek/pyapp.git pyapp-build
    echo -e "${GREEN}✓ PyApp cloned${NC}"
else
    echo -e "${GREEN}✓ PyApp already cloned${NC}"
fi

# Step 3: Build with PyApp
echo -e "${BLUE}Building executable with PyApp...${NC}"
echo ""

cd pyapp-build

# Set environment variables for this build
export PYAPP_PROJECT_PATH="$WHEEL_PATH"
export PYAPP_PYTHON_VERSION="3.11"
export PYAPP_EXEC_SPEC="src.main:main"

echo "Configuration:"
echo "  Wheel: $WHEEL_PATH"
echo "  Python: $PYAPP_PYTHON_VERSION"
echo "  Entry point: $PYAPP_EXEC_SPEC"
echo ""

# Build
echo -e "${BLUE}Running cargo build (this takes 5-10 minutes)...${NC}"
cargo build --release

cd ..

# Step 4: Copy executable
if [ -f "pyapp-build/target/release/pyapp" ]; then
    cp pyapp-build/target/release/pyapp ./abstraction-agent
    chmod +x ./abstraction-agent

    SIZE=$(du -h ./abstraction-agent | cut -f1)

    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}  Build Successful!${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""
    echo "Executable: ./abstraction-agent"
    echo "Size: $SIZE"
    echo ""
    echo "To run: ./abstraction-agent"
else
    echo -e "${RED}✗ Build failed - executable not found${NC}"
    exit 1
fi
