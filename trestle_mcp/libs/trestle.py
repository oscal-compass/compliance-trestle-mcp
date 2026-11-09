"""Trestle CLI wrapper utilities.

This module provides common functions for interacting with the trestle CLI.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

#: Timeout (seconds) applied to a trestle command when the caller does not ask
#: for anything else. Enough for every command that only touches local models.
DEFAULT_TIMEOUT = 60

#: Timeout (seconds) for commands that are routinely slow: `import` of a remote
#: catalog, profile resolution, SSP generation and task runs. Importing the NIST
#: SP 800-53 rev5 catalog alone is ~10 MB over the network and resolving a large
#: profile walks every control, so both exceed DEFAULT_TIMEOUT in practice.
LONG_TIMEOUT = 600


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


def run_trestle_command(
    args: list[str],
    cwd: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Run a trestle CLI command and return the result.

    Args:
        args: List of command arguments (without 'trestle' prefix)
        cwd: Working directory for the command
        timeout: Seconds to wait before giving up. Defaults to DEFAULT_TIMEOUT;
            pass LONG_TIMEOUT for commands that fetch remote content or walk a
            whole catalog.

    Returns:
        dict with 'success', 'stdout', 'stderr', 'returncode'
    """
    trestle_bin = find_trestle_bin()
    cmd = [trestle_bin] + args

    try:
        result = subprocess.run(
            cmd, cwd=cwd or os.getcwd(), capture_output=True, text=True, timeout=timeout
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
            "stderr": f"Command timed out after {timeout} seconds",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Error executing trestle: {str(e)}",
            "returncode": -1,
        }
