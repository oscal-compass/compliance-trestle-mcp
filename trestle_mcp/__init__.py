"""
trestle-mcp: MCP server for compliance-trestle OSCAL framework.

This package provides MCP tools to manage OSCAL models using the trestle CLI.
"""

__version__ = "0.1.0"

# Import main entry point
from trestle_mcp.main import main, mcp

__all__ = [
    # MCP server
    "mcp",
    "main",
]
