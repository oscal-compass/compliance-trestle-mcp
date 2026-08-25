#!/usr/bin/env python3
"""Verify the project version is consistent across all files that pin it.

pyproject.toml is the source of truth. server.json (used for the MCP registry)
duplicates the version in two places and must match. Run with no arguments to
check internal consistency (used on every PR); pass --expect <version> to also
require they match a release tag (used by the release workflow).

Exits non-zero and prints the mismatches if anything disagrees.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def collect_versions() -> dict[str, str]:
    """Map a human-readable location -> the version string found there."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    server = json.loads((ROOT / "server.json").read_text())
    return {
        "pyproject.toml [project.version]": pyproject["project"]["version"],
        "server.json version": server["version"],
        "server.json packages[0].version": server["packages"][0]["version"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expect",
        metavar="VERSION",
        help="also require every version to equal this (e.g. a release tag without the leading 'v')",
    )
    args = parser.parse_args()

    versions = collect_versions()
    if args.expect:
        versions[f"--expect ({args.expect})"] = args.expect

    unique = set(versions.values())
    if len(unique) == 1:
        print(f"✓ version consistent: {unique.pop()}")
        return 0

    print("✗ version mismatch:", file=sys.stderr)
    for location, value in versions.items():
        print(f"    {value:<20} {location}", file=sys.stderr)
    print(
        "\nUpdate pyproject.toml and server.json so all versions match.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
