"""Trestle CLI wrapper utilities.

This module provides common functions for interacting with the trestle CLI.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional


def find_trestle_bin() -> str:
    """Find the trestle binary in the virtual environment.

    Returns:
        str: Path to trestle binary or "trestle" to use system PATH
    """
    # Try to find trestle in the current venv
    venv_paths = [
        Path.cwd() / ".venv" / "bin" / "trestle",
        Path(__file__).parent.parent.parent / ".venv" / "bin" / "trestle",
    ]

    for path in venv_paths:
        if path.exists():
            return str(path)

    # Fall back to system trestle
    return "trestle"


def run_trestle_command(args: list[str], cwd: Optional[str] = None) -> dict:
    """Run a trestle CLI command and return the result.

    Args:
        args: List of command arguments (without 'trestle' prefix)
        cwd: Working directory for the command

    Returns:
        dict with 'success', 'stdout', 'stderr', 'returncode'
    """
    trestle_bin = find_trestle_bin()
    cmd = [trestle_bin] + args

    try:
        result = subprocess.run(
            cmd, cwd=cwd or os.getcwd(), capture_output=True, text=True, timeout=60
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out after 60 seconds",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Error executing trestle: {str(e)}",
            "returncode": -1,
        }
