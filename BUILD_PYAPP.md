# Building with PyApp

## Prerequisites
1. Install Rust toolchain:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```


> **Tip:** The build script automatically installs PyApp from the vendored source tree whenever it needs to embed a new project wheel, so a manual `cargo install pyapp` step is no longer required.

## Build Instructions

### Recommended (PyApp CLI)

```bash
./scripts/build.sh
```

This mode now builds a fresh wheel, installs PyApp from the vendored source with that wheel embedded (via `cargo install`), and copies the resulting binary to the repository root. Feed answers via stdin (`printf 'y\nn\n' | ./scripts/build.sh`) if you need a non-interactive run.

### Fallback / Source-Based (former build_fixed)

```bash
./scripts/build.sh --fixed
```

This path first builds a wheel into `dist/`, ensures the vendored PyApp source is present, and runs `cargo build --release` directly (no global cargo install). It copies the resulting executable to the repo root as `./abstraction` and uses the same packaging flow as the CLI mode.

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
