"""
Main entry point for the Abstraction agent framework.
"""
import sys
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from loguru import logger
from PySide6.QtWidgets import QApplication, QMessageBox
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.model_loader import ModelLoader
from src.memory import CacheManager
from src.tools import register_all_tools, tool_registry
from src.nodes import AgentGraph
from src.gui import MainWindow
from src.mcp import MCPServer, IOFirewall


def setup_logging(log_dir: str = "./logs"):
    """
    Setup logging configuration.

    Args:
        log_dir: Directory for log files
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_path / "agent_{time}.log",
        rotation="100 MB",
        retention="10 days",
        level="INFO"
    )
    logger.info("Logging initialized")


def load_config(config_path: str = "./config/config.yaml") -> dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logger.warning(f"Could not load config from {config_path}: {e}")
        return get_default_config()


def get_default_config() -> dict:
    """
    Get default configuration.

    Returns:
        Default configuration dictionary
    """
    return {
        'agent': {
            'name': 'Abstraction Agent',
            'model_provider': 'transformers',
            'model_name': 'mistral-7b-instruct-v0.3',
            'temperature': 0.7,
            'max_tokens': 4096
        },
        'memory': {
            'type': 'disk',
                'headless': True,
                'timeout': 30,
                'allowed_hosts': []
            'ttl_hours': 24
        },
        'human_in_loop': {
            'enabled': True,
            'auto_approve_read_only': False,
            'timeout_seconds': 300
        },
        'reasoning': {
            'enabled': True,
            'min_confidence_threshold': 0.7,
            'max_iterations': 3
        },
        'mcp': {
            'enabled': False,
            'server': {
                'host': 'localhost',
                'port': 3000
            },
            'firewall': {
                'enabled': True,
                'max_file_size_mb': 100.0,
                'filter_sensitive': True
            }
        },
        'logging': {
            'level': 'INFO',
            'log_dir': './logs'
        }
    }


def initialize_model(config: dict) -> ModelLoader:
    """
    Initialize and load the model.

    Args:
        config: Configuration dictionary

    Returns:
        Initialized ModelLoader
    """
    logger.info("Initializing model...")

    model_name = config['agent']['model_name']
    cache_dir = os.getenv('MODEL_CACHE_DIR', './models')

    model_loader = ModelLoader(
        model_name=model_name,
        cache_dir=cache_dir,
        load_in_4bit=True  # Use 4-bit quantization to save memory
    )

    # Authenticate with HuggingFace
    hf_token = os.getenv('HUGGINGFACE_TOKEN')
    if hf_token:
        model_loader.authenticate(hf_token)
    else:
        logger.warning("No HUGGINGFACE_TOKEN found in environment. Model download may fail.")

    # Load model
    try:
        model_loader.load_model()
        logger.info(f"Model loaded successfully: {model_loader.get_model_info()}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    return model_loader


def initialize_cache(config: dict) -> CacheManager:
    """
    Initialize the cache manager.

    Args:
        config: Configuration dictionary

    Returns:
        Initialized CacheManager
    """
    cache_config = config['memory']

    cache_manager = CacheManager(
        cache_dir=cache_config['cache_dir'],
        max_size_mb=cache_config['max_cache_size_mb'],
        ttl_hours=cache_config['ttl_hours']
    )

    logger.info("Cache manager initialized")
    return cache_manager


def initialize_mcp_server(config: dict) -> Optional[MCPServer]:
    """
    Initialize MCP server if enabled.

    Args:
        config: Configuration dictionary

    Returns:
        MCPServer instance or None if disabled
    """
    mcp_config = config.get('mcp', {})

    if not mcp_config.get('enabled', False):
        logger.info("MCP server disabled in configuration")
        return None

    try:
        server_config = mcp_config.get('server', {})
        mcp_server = MCPServer(
            tool_registry=tool_registry,
            host=server_config.get('host', 'localhost'),
            port=server_config.get('port', 3000)
        )

        logger.info(f"MCP server initialized: {mcp_server.get_info()}")
        return mcp_server

    except Exception as e:
        logger.error(f"Failed to initialize MCP server: {e}")
        return None


def initialize_firewall(config: dict):
    """
    Initialize I/O firewall.

    Args:
        config: Configuration dictionary
    """
    mcp_config = config.get('mcp', {})
    firewall_config = mcp_config.get('firewall', {})

    if not firewall_config.get('enabled', True):
        logger.info("I/O Firewall disabled in configuration")
        return

    try:
        from src.mcp.firewall import io_firewall

        # Update global firewall settings
        io_firewall.enabled = True
        io_firewall.max_file_size_mb = firewall_config.get('max_file_size_mb', 100.0)
        io_firewall.filter_sensitive = firewall_config.get('filter_sensitive', True)

        logger.info(f"I/O Firewall initialized: {io_firewall.get_status()}")

    except Exception as e:
        logger.error(f"Failed to initialize firewall: {e}")


def main():
    """Main entry point."""
    try:
        # Load environment variables
        load_dotenv()

        # Load configuration
        config = load_config()

        # Setup logging
        setup_logging(config['logging']['log_dir'])

        logger.info("=" * 60)
        logger.info("Starting Abstraction Agent Framework")
        logger.info("=" * 60)

        # Register all tools
        logger.info("Registering tools...")
        register_all_tools(config)
        tools = tool_registry.list_tools()
        logger.info(f"Registered {sum(len(v) for v in tools.values())} tools across {len(tools)} categories")

        # Initialize I/O Firewall
        logger.info("Initializing I/O firewall...")
        initialize_firewall(config)

        # Initialize cache
        cache_manager = initialize_cache(config)

        # Initialize MCP server (optional)
        mcp_server = initialize_mcp_server(config)
        if mcp_server:
            logger.info("MCP server will be available for external connections")

        # Initialize model
        logger.info("Loading model (this may take several minutes on first run)...")
        model_loader = initialize_model(config)

        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Abstraction")
        app.setOrganizationName("Abstraction AI")

        # Create agent graph
        logger.info("Building agent graph...")
        agent_graph = AgentGraph(
            model_loader=model_loader,
            auto_approve_read_only=config['human_in_loop']['auto_approve_read_only'],
            min_confidence=config['reasoning']['min_confidence_threshold'],
            max_iterations=config['reasoning']['max_iterations']
        )

        # Create and show main window
        logger.info("Launching GUI...")
        window = MainWindow(agent_graph)

        # Set approval callback
        agent_graph.approval_node.approval_callback = window.approval_callback

        window.show()

        logger.info("Application ready!")
        logger.info("=" * 60)

        # Run application
        sys.exit(app.exec())

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")

        # Show error dialog if Qt is available
        try:
            app = QApplication.instance()
            if app:
                QMessageBox.critical(
                    None,
                    "Fatal Error",
                    f"Application failed to start:\n\n{str(e)}\n\nCheck logs for details."
                )
        except:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
