"""
trestle-mcp: MCP server for compliance-trestle OSCAL framework.

This package provides MCP tools to manage OSCAL models using the trestle CLI.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

try:
    __version__ = _version("compliance-trestle-mcp")
except PackageNotFoundError:
    # Running from a source checkout without an install (e.g. local dev).
    __version__ = "0.0.0+unknown"

# Import main entry point. Deliberately *not* `mcp`: that attribute builds a
# server, so importing it here would make every `import trestle_mcp.anything`
# read the tool selection out of the environment and possibly exit. Reach it as
# `from trestle_mcp.main import mcp` when you want it.
from trestle_mcp.main import main

__all__ = [
    "main",
]
