#!/bin/bash
# Build orchestrator for creating standalone executables with PyApp

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$PROJECT_ROOT"

# Core PyApp metadata defaults (needed even during cargo install)
export PYAPP_PROJECT_NAME="${PYAPP_PROJECT_NAME:-abstraction}"
export PYAPP_IS_GUI="${PYAPP_IS_GUI:-true}"
export PYAPP_PROJECT_VERSION="${PYAPP_PROJECT_VERSION:-1.0.0}"
PYAPP_RELEASE_URL="${PYAPP_RELEASE_URL:-https://github.com/ofek/pyapp/releases/latest/download/source.tar.gz}"
PYAPP_SOURCE_DIR="${PYAPP_SOURCE_DIR:-${PROJECT_ROOT}/pyapp-latest}"

# Activate virtual environment if present
if [ -d "${PROJECT_ROOT}/venv" ]; then
    # shellcheck disable=SC1091
    source "${PROJECT_ROOT}/venv/bin/activate"
fi

# Shell colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults
PYTHON_VERSION="3.11"
EXEC_SPEC="src.main:main"
OUTPUT_NAME="abstraction"
BUILD_MODE="cli"
AUTO_CONFIRM=false

# Resolve python command
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

usage() {
    cat <<EOF
Usage: ./scripts/build.sh [options]

Options:
  --cli            Use the PyApp CLI (default)
  --fixed          Use the source-based flow (former build_fixed.sh)
  --force | -y     Skip interactive confirmations
  --help | -h      Show this message
EOF
}

print_status() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }

ensure_file() {
    if [ ! -f "$1" ]; then
        print_error "Required file '$1' not found."
        exit 1
    fi
}

ensure_command() {
    local cmd="$1"
    local install_hint="$2"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        print_error "'$cmd' command not found.${install_hint:+ $install_hint}"
        exit 1
    fi
}

ensure_rust() {
    if ! command -v cargo >/dev/null 2>&1; then
        print_error "Rust/Cargo not found. Install it via 'curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh'"
        exit 1
    fi
    local rust_version
    rust_version=$(rustc --version | cut -d' ' -f2)
    print_status "Rust detected (version: $rust_version)"
}

ensure_local_pyapp_source() {
    if [ -d "$PYAPP_SOURCE_DIR" ]; then
        print_status "PyApp source present at $PYAPP_SOURCE_DIR"
        return
    fi

    ensure_command curl "Install curl to download PyApp release archives."

    local tarball="$PROJECT_ROOT/pyapp-source.tar.gz"
    local temp_dir
    temp_dir=$(mktemp -d)

    print_info "Downloading PyApp source from $PYAPP_RELEASE_URL ..."
    if ! curl -L "$PYAPP_RELEASE_URL" -o "$tarball"; then
        rm -rf "$temp_dir"
        print_error "Failed to download PyApp source archive."
        exit 1
    fi

    print_info "Extracting PyApp source..."
    if ! tar -xzf "$tarball" -C "$temp_dir"; then
        rm -rf "$temp_dir" "$tarball"
        print_error "Failed to extract PyApp source archive."
        exit 1
    fi

    local extracted_dir
    extracted_dir=$(find "$temp_dir" -maxdepth 1 -type d -name 'pyapp-*' | head -n 1 || true)
    if [ -z "$extracted_dir" ]; then
        rm -rf "$temp_dir" "$tarball"
        print_error "Unable to locate extracted PyApp directory."
        exit 1
    fi

    rm -rf "$PYAPP_SOURCE_DIR"
    mv "$extracted_dir" "$PYAPP_SOURCE_DIR"
    rm -rf "$temp_dir" "$tarball"
    print_status "PyApp source ready at $PYAPP_SOURCE_DIR"
}

install_pyapp_cli_with_project() {
    local wheel_path="$1"

    ensure_rust
    ensure_local_pyapp_source

    print_info "Installing PyApp binary with embedded project wheel..."
    (
        cd "$PYAPP_SOURCE_DIR"
        PYAPP_PROJECT_PATH="$wheel_path" \
        PYAPP_PYTHON_VERSION="$PYTHON_VERSION" \
        PYAPP_EXEC_SPEC="$EXEC_SPEC" \
        PYAPP_IS_GUI="$PYAPP_IS_GUI" \
        cargo install --locked --path . --force >/dev/null
    )
    print_status "PyApp binary installed to cargo bin directory"
}

ensure_python_build_module() {
    if ! "$PYTHON_CMD" -m build --version >/dev/null 2>&1; then
        print_info "Installing python-build tooling..."
        "$PYTHON_CMD" -m pip install --upgrade build
    fi
    print_status "Python build module available"
}

build_python_wheel() {
    print_info "Building wheel artifact (dist/*.whl)..."
    "$PYTHON_CMD" -m build --wheel >/dev/null
    print_status "Wheel built"
}

latest_wheel_path() {
    local wheel
    wheel=$(ls -t dist/*.whl 2>/dev/null | head -n 1 || true)
    if [ -z "$wheel" ]; then
        print_error "No wheel artifacts found under dist/."
        exit 1
    fi
    wheel=$("$PYTHON_CMD" -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$wheel")
    echo "$wheel"
}

confirm_or_exit() {
    if [ "$AUTO_CONFIRM" = true ]; then
        print_info "Auto-confirm enabled; continuing without prompt."
        return
    fi
    read -p "Proceed with build? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Build cancelled by user"
        exit 0
    fi
}

post_build_success() {
    local exec_path="$1"
    chmod +x "$exec_path"
    local exec_size
    exec_size=$(du -h "$exec_path" | cut -f1)

    echo ""
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}  Build Successful! 🎉${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    echo "Executable: $exec_path"
    echo "Size: $exec_size"
    echo ""
    echo "To run the application:"
    echo "  $exec_path"
    echo ""
    print_warning "Reminder: the first launch downloads ~14GB of model data."

    maybe_create_distribution "$exec_path" "$exec_size"
}

maybe_create_distribution() {
    local exec_path="$1"
    local exec_size="$2"
    if [ "$AUTO_CONFIRM" = true ]; then
        print_info "Skipping distribution packaging prompt (--force)."
        return
    fi
    read -p "Create distribution tarball? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi

    print_info "Creating distribution package..."
    local dist_name="abstraction-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)"
    local dist_dir="./dist/$dist_name"

    mkdir -p "$dist_dir"
    cp "$exec_path" "$dist_dir/"
    cp README.md "$dist_dir/" 2>/dev/null || true
    cp QUICKSTART.md "$dist_dir/" 2>/dev/null || true
    cp .env.example "$dist_dir/" 2>/dev/null || true
    cp LICENSE "$dist_dir/" 2>/dev/null || true

    cat > "$dist_dir/INSTALL.txt" <<'EOF'
Abstraction - AI Agent Framework
================================

Quick Start:
1. Create .env from .env.example
2. Add your HuggingFace token
3. Run the bundled executable
4. Wait for the initial model download (~14GB)

Requirements:
- 16GB RAM minimum
- 20GB free disk space
- Linux/macOS/Windows

For details, see QUICKSTART.md
EOF

    (cd ./dist && tar -czf "${dist_name}.tar.gz" "$dist_name")
    local pkg_size
    pkg_size=$(du -h "./dist/${dist_name}.tar.gz" | cut -f1)
    print_status "Distribution package ready at ./dist/${dist_name}.tar.gz (${pkg_size})"
}

run_cli_build() {
    print_info "Selected mode: PyApp CLI"
    ensure_file "requirements.txt"
    ensure_file "pyproject.toml"
    ensure_python_build_module

    echo ""
    print_info "Build Configuration:"
    echo "  Project Path: $PROJECT_ROOT"
    echo "  Python Version: $PYTHON_VERSION"
    echo "  Entry Point: $EXEC_SPEC"
    echo "  Output Name: $OUTPUT_NAME"
    echo "  Cargo Bin Install: ${CARGO_HOME:-$HOME/.cargo}/bin/pyapp"
    echo ""

    confirm_or_exit

    build_python_wheel
    local wheel_path
    wheel_path=$(latest_wheel_path)
    print_status "Using wheel: $wheel_path"

    install_pyapp_cli_with_project "$wheel_path"

    local cargo_bin_dir="${CARGO_HOME:-$HOME/.cargo}/bin"
    local installed_binary="$cargo_bin_dir/pyapp"
    if [ ! -f "$installed_binary" ]; then
        print_error "PyApp binary not found at $installed_binary after installation"
        exit 1
    fi

    cp "$installed_binary" "./$OUTPUT_NAME"
    local exec_path="./$OUTPUT_NAME"
    post_build_success "$exec_path"
}

run_fixed_build() {
    print_info "Selected mode: source-based build (--fixed)"
    ensure_rust
    ensure_file "requirements.txt"
    ensure_file "pyproject.toml"
    ensure_python_build_module
    ensure_local_pyapp_source

    echo ""
    print_info "Build Configuration:"
    echo "  Project Path: $PROJECT_ROOT"
    echo "  Python Version: $PYTHON_VERSION"
    echo "  Entry Point: $EXEC_SPEC"
    echo "  Output Name: $OUTPUT_NAME"
    echo "  Wheel Cache: dist/"
    echo "  PyApp Source: $PYAPP_SOURCE_DIR"
    echo ""

    confirm_or_exit

    build_python_wheel
    local wheel_path
    wheel_path=$(latest_wheel_path)
    print_status "Using wheel: $wheel_path"

    export PYAPP_PROJECT_PATH="$wheel_path"
    export PYAPP_PYTHON_VERSION="$PYTHON_VERSION"
    export PYAPP_EXEC_SPEC="$EXEC_SPEC"
    export PYAPP_IS_GUI="true"

    print_info "Building PyApp from source via cargo (may take 5-10 minutes)..."
    (cd "$PYAPP_SOURCE_DIR" && cargo build --release)

    local built_binary="$PYAPP_SOURCE_DIR/target/release/pyapp"
    if [ ! -f "$built_binary" ]; then
        print_error "Expected binary '$built_binary' not found."
        exit 1
    fi

    cp "$built_binary" "./$OUTPUT_NAME"
    local exec_path="./$OUTPUT_NAME"
    post_build_success "$exec_path"
}

# --- argument parsing ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --cli)
            BUILD_MODE="cli"
            ;;
        --fixed)
            BUILD_MODE="fixed"
            ;;
        --force|-y)
            AUTO_CONFIRM=true
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown argument: $1"
            usage
            exit 1
            ;;
    esac
    shift
done

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  Abstraction Build Orchestrator${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

if [ "$BUILD_MODE" = "fixed" ]; then
    run_fixed_build
else
    run_cli_build
fi

print_status "All done!"
