# Abstraction - AI Agent Framework

A robust, production-ready agentic framework built with LangGraph, featuring a native Qt GUI, human-in-the-loop approval, caching, and reasoning capabilities.

## Features

- **🤖 LangGraph Orchestration**: Sophisticated agent workflow with state management
- **🖥️ Native Qt GUI**: Beautiful, responsive desktop interface with real-time monitoring
- **✅ Human-in-the-Loop**: Approve or reject agent actions before execution
- **💾 Intelligent Caching**: Persistent memory and conversation history
- **🧠 Reasoning Node**: Self-assessment and confidence scoring for outputs
- **🔧 Rich Tool System**: Pre-built tools for coding, web, accounting, and writing
- **🔌 MCP Integration**: Full Model Context Protocol support for tool sharing
- **🛡️ I/O Firewall**: Advanced input/output validation and sandboxing
- **📦 Single Executable**: Bundle with PyApp for easy distribution
- **🏷️ Apache 2.0 Licensed**: Uses Mistral-7B-Instruct-v0.3 (Apache 2.0)
- **💻 Low Memory**: Runs on 16GB RAM with 4-bit quantization (~3.5GB model size)

## Tool Categories

### Coding Tools
- **Code Formatter**: Format Python code with Black
- **Code Linter**: Run pylint on code
- **Code Executor**: Execute Python code safely
- **File Reader**: Read file contents
- **File Writer**: Write to files

### Web Tools
- **Web Scraper**: Extract content from web pages (respects optional hostname allowlist)
- **HTTP Request**: Make HTTP requests (GET, POST, etc.) with URL safety checks
- **URL Validator**: Validate and parse URLs

### Accounting Tools
- **Calculator**: High-precision financial calculations
- **Spreadsheet Reader**: Read Excel files
- **Invoice Calculator**: Calculate invoice totals with tax

### Writing Tools
- **Word Counter**: Count words, characters, sentences
- **Text Summarizer**: Extract key sentences
- **Grammar Checker**: Basic grammar and style checking
- **Text Formatter**: Clean and format text

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Qt GUI Dashboard                   │
│  (Chat, Tool Approvals, Reasoning, State Viewer)    │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────┐
│              LangGraph Agent Workflow                │
│                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌──────────┐  │
│  │  Agent   │───▶│   Human      │───▶│ Reasoning│  │
│  │  Node    │    │  Approval    │    │   Node   │  │
│  └──────────┘    └──────────────┘    └──────────┘  │
│       ▲                                      │       │
│       └──────────────────────────────────────┘       │
└──────────────────────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
    ┌────▼───┐   ┌───▼────┐  ┌────▼─────┐
    │ Tools  │   │ Memory │  │  Model   │
    │Registry│   │ Cache  │  │ (Mixtral)│
    └────────┘   └────────┘  └──────────┘
```

## Installation

### Prerequisites

**Hardware Requirements:**
- **RAM**: 16GB minimum (model uses ~3.5GB with 4-bit quantization)
- **Disk**: 20GB free space (14GB for model + dependencies)
- **CPU**: Modern multi-core processor (GPU optional but recommended)

**Software:**
```bash
# Python 3.10+
python3 --version

# CUDA (optional, for GPU acceleration - improves speed 5-10x)
nvidia-smi
```

**Note**: For more powerful models like Mixtral-8x7B, you'll need 32GB+ RAM.

### Step 1: Clone and Install Dependencies

```bash
git clone <your-repo>
cd abstraction

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your HuggingFace token
nano .env
```

Required environment variables:
```env
HUGGINGFACE_TOKEN=your_hf_token_here
MODEL_NAME=mixtral-8x7b-instruct
MODEL_CACHE_DIR=./models
```

### Step 3: Download the Model

The model will download automatically on first run. On first launch, expect:
- **Download size**: ~14GB (Mistral-7B)
- **Memory usage**: ~3.5GB with 4-bit quantization
- **Time**: 5-15 minutes depending on internet speed

Alternatively, pre-download:

```bash
python3 -c "from src.agents.model_loader import download_model; download_model()"
```

### Step 4: Run the Application

```bash
python3 src/main.py
```

## Usage

### Basic Workflow

1. **Launch** the application
2. **Enter a task** in the input field (e.g., "Read example.txt and count the words")
3. **Approve tools** when the approval dialog appears
4. **View progress** in the reasoning and state tabs
5. **Get results** in the chat window

### Example Tasks

**Coding:**
```
Format the Python code in script.py and check for errors
```

**Web:**
```
Scrape the main content from https://example.com and summarize it
```

**Accounting:**
```
Calculate an invoice with items: [{"quantity": 2, "unit_price": 49.99}, {"quantity": 1, "unit_price": 99.99}] and 8% tax
```

**Writing:**
```
Check this text for grammar issues: "The quick brown fox jump over the the lazy dog"
```

## MCP Integration (Model Context Protocol)

Abstraction includes full support for Anthropic's Model Context Protocol, allowing you to:
- **Expose tools** via MCP server for other applications to use
- **Connect to external MCP servers** to access their tools
- **Secure tool execution** with I/O firewall protection

### Enabling MCP Server

To expose your tools via MCP, edit your config file:

```yaml
mcp:
  enabled: true
  server:
    host: localhost
    port: 3000
  firewall:
    enabled: true
    max_file_size_mb: 100.0
    filter_sensitive: true
```

### I/O Firewall Security

The integrated firewall provides multiple security layers:

**Input Validation:**
- Dangerous pattern detection (code injection, shell commands)
- Path traversal prevention
- File extension blocking
- Size limits

**Output Filtering:**
- Sensitive data redaction (passwords, API keys, secrets)
- Output length limits
- Automatic truncation

**Example:**
```python
from src.mcp.firewall import io_firewall

# Validate input
is_valid, error = io_firewall.validate_input(user_input, context="code")

# Filter output
safe_output = io_firewall.filter_output(tool_result)
```

> **Firewall Scope & Expectations:** The firewall is best-effort and focuses on sanitizing tool input/output, enforcing file-system guard rails, and redacting obvious secrets. It does **not** replace network firewalls or DLP tooling; outbound HTTP calls are additionally constrained via the optional `tools.web.allowed_hosts` configuration so you can explicitly declare trusted domains.

### Connecting to External MCP Servers

```python
from src.mcp import MCPClient

# Connect to an external MCP server
client = MCPClient()
await client.connect("python", ["external_server.py"])

# List available tools
tools = client.get_available_tools()

# Call a tool
result = await client.call_tool("external_tool", {"arg": "value"})
```

### MCP Architecture

```
┌────────────────────────────────────────────┐
│      Abstraction Agent (This App)          │
│                                            │
│  ┌──────────────┐      ┌──────────────┐   │
│  │  MCP Server  │      │  MCP Client  │   │
│  │   (Expose)   │      │  (Connect)   │   │
│  └──────┬───────┘      └──────┬───────┘   │
│         │                     │           │
│  ┌──────▼─────────────────────▼───────┐   │
│  │        I/O Firewall Layer          │   │
│  └──────┬─────────────────────┬───────┘   │
│         │                     │           │
│  ┌──────▼─────────────────────▼───────┐   │
│  │         Tool Registry              │   │
│  └────────────────────────────────────┘   │
└────────────────────────────────────────────┘
         │                     ▲
         │ (Expose Tools)      │ (Use External Tools)
         ▼                     │
┌──────────────────┐  ┌────────────────────┐
│   External App   │  │  External MCP      │
│   (via MCP)      │  │  Server            │
└──────────────────┘  └────────────────────┘
```

## Configuration

Edit `config/config.yaml` to customize:

```yaml
agent:
  name: "Abstraction Agent"
  model_name: "mistral-7b-instruct-v0.3"  # or "mixtral-8x7b-instruct" for more power
  temperature: 0.7
  max_tokens: 4096

memory:
  cache_dir: "./data/cache"
  max_cache_size_mb: 1000
  ttl_hours: 24

human_in_loop:
  enabled: true
  auto_approve_read_only: false  # Auto-approve read-only tools
  timeout_seconds: 300

reasoning:
  enabled: true
  min_confidence_threshold: 0.7
  max_iterations: 3

tools:
  web:
    timeout: 30
    allowed_hosts:
      - "example.com"
      - "*.wikipedia.org"

mcp:
  enabled: false  # Set to true to enable MCP server
  server:
    host: localhost
    port: 3000
  firewall:
    enabled: true
    max_file_size_mb: 100.0
    filter_sensitive: true
```

## Building with PyApp

To create a standalone executable:

### Prerequisites

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install PyApp
cargo install pyapp --locked
```

### Build

```bash
# Default PyApp CLI build
./scripts/build.sh

# Fallback/source-driven build (former build_fixed.sh)
./scripts/build.sh --fixed
```

The script checks prerequisites, guides you through the PyApp build, and offers to produce a distributable `.tar.gz`. Use `--force` to skip prompts. The `--fixed` flag bundles the wheel first and compiles PyApp from source (handy when the CLI route hits environment issues).

This still produces a single executable that contains the Python runtime, dependencies, and your code. The first run will download the ~14GB model (not bundled).

## Project Structure

```
abstraction/
├── src/
│   ├── agents/          # Model loader and agent logic
│   ├── gui/             # Qt GUI components
│   ├── memory/          # Caching and conversation history
│   ├── nodes/           # LangGraph nodes (agent, approval, reasoning)
│   ├── tools/           # Tool implementations
│   └── main.py          # Entry point
├── config/              # Configuration files
├── models/              # Model cache directory
├── data/                # Data and cache
├── logs/                # Application logs
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project metadata and PyApp config
└── README.md           # This file
```

## Development

### Adding New Tools

1. Create a new tool class in `src/tools/`:

```python
from src.tools.base import BaseTool, ToolCategory, ToolOutput

class MyCustomTool(BaseTool):
    """Description of what this tool does."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CODING

    @property
    def requires_approval(self) -> bool:
        return True  # Requires human approval

    def execute(self, param1: str, param2: int) -> ToolOutput:
        # Your tool logic here
        result = do_something(param1, param2)
        return ToolOutput(success=True, result=result)
```

2. Register the tool in `src/tools/__init__.py`:

```python
from .my_tools import MyCustomTool

def register_all_tools():
    # ... existing registrations
    tool_registry.register(MyCustomTool())
```

  ### Running Tests

  Install the testing extras once (they're also listed in `requirements.txt`):

  ```bash
  pip install -r requirements.txt
  ```

  Run the full pytest suite, including the MCP integration test:

  ```bash
  pytest
  ```

  The HTTP and filesystem tools use temporary directories during tests, so they are safe to run on your development machine.

### Customizing the GUI

The GUI is built with PySide6 (Qt6). Main window is in `src/gui/main_window.py`.

To customize:
- Modify layouts in `init_ui()`
- Add new tabs to the right panel
- Customize colors and styles with Qt stylesheets

## Troubleshooting

### Model Download Fails

**Issue**: HuggingFace authentication error

**Solution**:
1. Get a HuggingFace token from https://huggingface.co/settings/tokens
2. Add to `.env`: `HUGGINGFACE_TOKEN=your_token_here`

### Out of Memory

**Issue**: Out of memory error

**Solution**:
1. Ensure 4-bit quantization is enabled (default)
2. Close other applications
3. Use Mistral-7B instead of Mixtral-8x7B (set in .env)
4. For GPU: Close other GPU applications
5. For integrated graphics: CPU inference is automatic

### GUI Not Showing

**Issue**: Qt/PySide6 not working

**Solution**:
```bash
# Linux: Install Qt dependencies
sudo apt install libxcb-xinerama0 libxcb-cursor0

# Verify PySide6 installation
python3 -c "from PySide6.QtWidgets import QApplication"
```

## Performance

**Mistral-7B-Instruct-v0.3** (default):
- **Model Loading**: 1-2 minutes (first time)
- **Inference Speed**:
  - GPU: ~30-60 tokens/second
  - CPU: ~5-10 tokens/second
  - Integrated Graphics: ~3-8 tokens/second
- **Memory Usage**: ~3.5GB model + ~2GB overhead = **~6GB total**

**Mixtral-8x7B-Instruct** (requires 32GB+ RAM):
- **Model Loading**: 3-5 minutes
- **Inference Speed**: GPU: ~20-50 tokens/second, CPU: ~2-5 tokens/second
- **Memory Usage**: ~26GB model + ~4GB overhead = **~30GB total**

## License

This project uses Mixtral-8x7B-Instruct-v0.1, which is licensed under **Apache 2.0**.

Your code is also released under Apache 2.0 (or your chosen license).

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions:
- Open an issue on GitHub
- Check logs in `./logs/` directory
- Enable debug logging in `config/config.yaml`

## Roadmap

- [ ] Additional tool categories (databases, APIs, etc.)
- [ ] Multi-model support (Llama, GPT-4, etc.)
- [ ] Plugin system for custom tools
- [ ] Web interface option (in addition to Qt)
- [ ] Docker container distribution
- [ ] Cloud deployment guides

---

**Built with ❤️ using LangGraph, Transformers, and Qt**
