"""Model Context Protocol (MCP) integration for Abstraction framework."""
from .mcp_server import MCPServer
from .mcp_client import MCPClient
from .firewall import IOFirewall

__all__ = ['MCPServer', 'MCPClient', 'IOFirewall']
