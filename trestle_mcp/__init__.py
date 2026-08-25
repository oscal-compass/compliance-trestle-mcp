"""
trestle-mcp: MCP server for compliance-trestle OSCAL framework.

This package provides MCP tools to manage OSCAL models using the trestle CLI.
"""

from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version("compliance-trestle-mcp")
except PackageNotFoundError:
    # Running from a source checkout without an install (e.g. local dev).
    __version__ = "0.0.0+unknown"

# Import main entry point
from trestle_mcp.main import main, mcp

__all__ = [
    # MCP server
    "mcp",
    "main",
]
