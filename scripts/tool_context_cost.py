#!/usr/bin/env python3
"""Measure what each tool selection costs the caller in context.

An MCP client loads the `tools/list` result into the model's context window on
every session, so the size of that result is what a selection actually costs.
This script builds a server for each selection and measures the JSON the server
would return, rather than estimating from source — so the numbers stay true as
descriptions and schemas are edited.

The measured quantity is characters of JSON. A token count depends on the
client's tokenizer, so the token column is a rough division and is labelled as
such; use the character column when you need a number to stand behind.

    python scripts/tool_context_cost.py                 # one row per selection
    python scripts/tool_context_cost.py --per-tool      # also break down by tool
    python scripts/tool_context_cost.py --format json   # machine-readable
    python scripts/tool_context_cost.py --select core,trestle_remove
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from trestle_mcp.main import build_server  # noqa: E402
from trestle_mcp.tools import (  # noqa: E402
    DEFAULT_SELECTOR,
    GROUP_NAMES,
    OPT_IN_TOOL_NAMES,
)

#: Characters per token, for the clearly-approximate token column only. Real
#: tokenizers vary; JSON with many short keys runs denser than prose.
CHARS_PER_TOKEN = 4


def tool_payloads(selector: str) -> list[dict]:
    """The tools/list entries a server built from `selector` would return."""
    server = build_server(selector)
    tools = asyncio.run(server.list_tools())
    return [tool.model_dump(exclude_none=True) for tool in tools]


def measure(selector: str) -> dict:
    """Measure one selection: tool count, JSON size, and per-tool sizes."""
    payloads = tool_payloads(selector)
    per_tool = {
        payload["name"]: len(json.dumps(payload, separators=(",", ":")))
        for payload in payloads
    }
    return {
        "selector": selector,
        "tools": len(payloads),
        "chars": len(json.dumps(payloads, separators=(",", ":"))),
        "per_tool": per_tool,
    }


def selections(explicit: str | None) -> list[str]:
    """The selections to measure: the explicit one, or every documented one."""
    if explicit:
        return [explicit]
    # Every group, then each opt-in tool added to `all`, so the cost of the
    # tools no group selects is visible too.
    return [*GROUP_NAMES, *(f"all,{name}" for name in OPT_IN_TOOL_NAMES)]


def render_table(results: list[dict], per_tool: bool) -> str:
    """Render the measurements as a markdown table, ready to paste into docs."""
    lines = [
        "| Selection | Tools | Characters | ~Tokens |",
        "|---|---:|---:|---:|",
    ]
    for result in results:
        label = result["selector"]
        if label == DEFAULT_SELECTOR:
            label = f"`{label}` (default)"
        else:
            label = f"`{label}`"
        lines.append(
            f"| {label} | {result['tools']} | {result['chars']:,} "
            f"| ~{result['chars'] // CHARS_PER_TOKEN:,} |"
        )

    if per_tool:
        lines.append("")
        lines.append("| Tool | Characters |")
        lines.append("|---|---:|")
        # Union of every tool seen, largest first: the ones worth trimming.
        sizes: dict[str, int] = {}
        for result in results:
            sizes.update(result["per_tool"])
        for name, size in sorted(sizes.items(), key=lambda kv: -kv[1]):
            lines.append(f"| `{name}` | {size:,} |")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--select",
        metavar="SELECTION",
        default=None,
        help="measure one selection instead of every documented one",
    )
    parser.add_argument(
        "--per-tool",
        action="store_true",
        help="also list each tool's own size, largest first",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="output format (default: table)",
    )
    args = parser.parse_args()

    results = [measure(selector) for selector in selections(args.select)]

    if args.format == "json":
        if not args.per_tool:
            for result in results:
                del result["per_tool"]
        print(json.dumps(results, indent=2))
    else:
        print(render_table(results, args.per_tool))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
