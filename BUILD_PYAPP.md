# Building with PyApp

## Prerequisites
1. Install Rust toolchain:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

2. Install PyApp:
```bash
cargo install pyapp --locked
```

## Build Instructions

### Linux
```bash
# Set environment variables
export PYAPP_PROJECT_PATH=.
export PYAPP_PYTHON_VERSION=3.11
export PYAPP_EXEC_SPEC=src.main:main
export PYAPP_GUI_ENABLED=true

# Build
pyapp build
```

### Windows
```cmd
set PYAPP_PROJECT_PATH=.
set PYAPP_PYTHON_VERSION=3.11
set PYAPP_EXEC_SPEC=src.main:main
set PYAPP_GUI_ENABLED=true

pyapp build
```

### macOS
```bash
export PYAPP_PROJECT_PATH=.
export PYAPP_PYTHON_VERSION=3.11
export PYAPP_EXEC_SPEC=src.main:main
export PYAPP_GUI_ENABLED=true

pyapp build
```

## Output
The executable will be created in the current directory:
- Linux: `abstraction`
- Windows: `abstraction.exe`
- macOS: `abstraction`

## Distribution
Simply distribute the single executable file. On first run, it will:
1. Extract the bundled Python environment
2. Install dependencies
3. Launch the application

Subsequent runs will be much faster as the environment is cached.
