#!/usr/bin/env python3
"""
MCP Server for compliance-trestle OSCAL framework.

This server provides tools to manage OSCAL models using the trestle CLI.

Which tools are registered is decided at startup from the ``--tools`` flag or
the ``TRESTLE_MCP_TOOLS`` environment variable; see :mod:`trestle_mcp.tools`.
Only the selected tools are registered, because a registered tool's description
is loaded into the client's context on every session.
"""

import argparse
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

from trestle_mcp.tools import (
    DEFAULT_SELECTOR,
    ENV_TOOLS,
    FLAG_TOOLS,
    GROUP_DESCRIPTIONS,
    GROUP_NAMES,
    ToolSelectionError,
    ToolSpec,
    resolve_tool_specs,
    selector_from_sources,
)

SERVER_NAME = "trestle_mcp"


def register_tool(server: FastMCP, spec: ToolSpec) -> None:
    """Register one tool on a FastMCP server.

    The service function is registered directly: FastMCP derives the input
    schema from its ``params`` annotation, and the tool description is its
    docstring.

    Args:
        server: The server to register on.
        spec: The tool to register.

    Raises:
        TypeError: If the spec's input_model disagrees with the handler's
            annotation. That can only be a mistake in the tool table, and it is
            better caught at startup than as a wrong schema at call time.
    """
    annotated = spec.handler.__annotations__.get("params")
    if annotated is not spec.input_model:
        raise TypeError(
            f"tool {spec.name}: input_model {spec.input_model!r} does not match "
            f"the handler's params annotation {annotated!r}"
        )

    server.tool(
        name=spec.name,
        title=spec.title,
        description=spec.handler.__doc__,
        annotations=dict(spec.annotations),
    )(spec.handler)


def build_server(selector: Optional[str] = None) -> FastMCP:
    """Build a server with the selected tools registered.

    Args:
        selector: Comma-separated group and/or tool names. None reads the
            ``--tools`` flag and then ``TRESTLE_MCP_TOOLS``, and falls back to
            DEFAULT_SELECTOR.

    Returns:
        The configured server. Its ``trestle_mcp_selector`` and
        ``trestle_mcp_tool_names`` attributes record what was applied.

    Raises:
        ToolSelectionError: If the selector names something that does not exist.
    """
    applied = selector if selector is not None else selector_from_sources()
    specs = resolve_tool_specs(applied)

    server = FastMCP(SERVER_NAME)
    for spec in specs:
        register_tool(server, spec)

    server.trestle_mcp_selector = applied or DEFAULT_SELECTOR
    server.trestle_mcp_tool_names = tuple(spec.name for spec in specs)
    return server


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI parser, mainly so that --help documents the selector."""
    group_help = "\n".join(
        f"  {name:<12} {GROUP_DESCRIPTIONS[name]}" for name in GROUP_NAMES
    )
    parser = argparse.ArgumentParser(
        prog="trestle-mcp",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"tool groups:\n{group_help}\n",
    )
    parser.add_argument(
        FLAG_TOOLS,
        metavar="SELECTION",
        default=None,
        help=(
            "Comma-separated list of tool groups and/or individual tool names to "
            f"register (default: {DEFAULT_SELECTOR}). Overrides ${ENV_TOOLS}."
        ),
    )
    return parser


def _build_default_server() -> FastMCP:
    """Build the ambient server, reporting a bad selection and exiting.

    A selector naming a tool that does not exist is a configuration mistake, and
    an MCP server that silently drops a requested tool is miserable to debug
    from the client, where all you see is the tool missing. So this exits at
    startup with the list of valid names rather than starting up short-handed.
    """
    try:
        return build_server()
    except ToolSelectionError as error:
        print(f"trestle-mcp: {error}", file=sys.stderr)
        raise SystemExit(2) from error


#: Server built from the ambient configuration, for callers that import `mcp`
#: directly (tests, MCP inspectors, `fastmcp run`).
mcp = _build_default_server()


def main() -> None:
    """Main entry point for the trestle MCP server."""
    # Parsed for validation and for --help; the selection itself was read by
    # build_server, which looks at both the flag and the environment.
    _build_arg_parser().parse_args()

    # stderr, never stdout: the stdio transport owns stdout.
    print(
        f"trestle-mcp: tools={mcp.trestle_mcp_selector} "
        f"({len(mcp.trestle_mcp_tool_names)} registered)",
        file=sys.stderr,
    )
    mcp.run()


if __name__ == "__main__":
    main()
