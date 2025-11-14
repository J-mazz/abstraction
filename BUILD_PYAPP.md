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

### Recommended (PyApp CLI)

```bash
./scripts/build.sh
```

This mode mirrors the previous `build.sh` workflow: it checks for Rust, installs the PyApp CLI if needed, exports the right env vars, and runs `pyapp build`. Use `./scripts/build.sh --force` to bypass prompts in CI.

### Fallback / Source-Based (former build_fixed)

```bash
./scripts/build.sh --fixed
```

This path first builds a wheel into `dist/`, clones/updates `pyapp-build/`, and runs `cargo build --release` so you're not reliant on a globally-installed PyApp binary. It copies the resulting executable to the repo root as `./abstraction` and uses the same packaging flow as the CLI mode.

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
