"""Trestle CLI wrapper utilities.

This module provides common functions for interacting with the trestle CLI.
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping, Optional

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


#: The flag every service passes to point trestle at the workspace. Named here
#: because the working directory is derived from it, not just handed to trestle.
FLAG_TRESTLE_ROOT = "--trestle-root"


def absolute_trestle_root(args: list[str]) -> tuple[list[str], Optional[str]]:
    """Make a `--trestle-root` argument absolute and report the path.

    trestle resolves `--trestle-root` itself, but every *other* path argument --
    `--file`, `--output-dir`, a task's `input-file` -- is resolved by the OS
    against the process's working directory. For an MCP server that directory is
    wherever the client happened to launch it, which is almost never the
    workspace, so a relative path from the caller pointed at nothing. Returning
    the root lets the command run inside the workspace, which is what makes a
    relative argument mean what the caller meant.

    The path has to be made absolute because the command then runs *in* it: a
    relative `--trestle-root ws` left alone would resolve to `ws/ws`.

    Args:
        args: Command arguments, without the 'trestle' prefix.

    Returns:
        The arguments with any `--trestle-root` value made absolute, and that
        absolute path, or None when the arguments do not set a root.
    """
    joined = f"{FLAG_TRESTLE_ROOT}="
    for index, arg in enumerate(args):
        if arg == FLAG_TRESTLE_ROOT and index + 1 < len(args):
            root = os.path.abspath(args[index + 1])
            return args[: index + 1] + [root] + args[index + 2 :], root
        if arg.startswith(joined):
            root = os.path.abspath(arg[len(joined) :])
            return args[:index] + [joined + root] + args[index + 1 :], root
    return list(args), None


def command_output(result: Mapping[str, Any]) -> str:
    """Return a successful command's output, keeping any warning it wrote.

    trestle reports problems it recovered from on stderr and still exits 0: a
    percentage outside 0-100 that it drops, a control id in a list that it
    cannot resolve and discards. Returning stdout alone told the caller the run
    succeeded and threw away the news that part of the input did not make it
    into the output -- the caller has no other way to find out, short of reading
    the generated file and noticing something missing.

    Costs nothing when there is nothing to say: a successful trestle command
    writes to stderr only when it has a warning.

    Args:
        result: A result dict from `run_trestle_command`.

    Returns:
        stdout, with any stderr appended under a warning heading.
    """
    stdout = result["stdout"].strip()
    stderr = result["stderr"].strip()
    if not stderr:
        return stdout
    warning = f"⚠️ trestle also reported:\n{stderr}"
    return f"{stdout}\n\n{warning}" if stdout else warning


async def run_trestle_command(
    args: list[str],
    cwd: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Run a trestle CLI command and return the result.

    Awaitable, and the subprocess is waited for on a worker thread. Run
    directly, the wait blocked the event loop for up to LONG_TIMEOUT -- ten
    minutes during which the whole server answered nothing: no other tool call,
    no ping, no cancellation. A client with a shorter request timeout gave up
    while the server stayed stuck.

    The command runs in `cwd` if the caller names one and it exists, otherwise
    in the `--trestle-root` the arguments carry if that exists, otherwise in
    this process's working directory -- see `_working_directory` for why a
    directory that is not there is skipped rather than passed on. Deriving it
    from the root is what keeps a relative path argument relative to the
    workspace rather than to wherever the client started the server -- see
    `absolute_trestle_root`. Only `trestle merge` needs an explicit `cwd`,
    because it resolves its destination model from the working directory.

    Args:
        args: List of command arguments (without 'trestle' prefix)
        cwd: Working directory for the command. Overrides the trestle root.
        timeout: Seconds to wait before giving up. Defaults to DEFAULT_TIMEOUT;
            pass LONG_TIMEOUT for commands that fetch remote content or walk a
            whole catalog.

    Returns:
        dict with 'success', 'stdout', 'stderr', 'returncode'
    """
    args, trestle_root = absolute_trestle_root(args)
    trestle_bin = find_trestle_bin()
    cmd = [trestle_bin] + args
    workdir = _working_directory(cwd, trestle_root)

    return await asyncio.to_thread(_run_blocking, cmd, workdir, timeout)


def _working_directory(cwd: Optional[str], trestle_root: Optional[str]) -> str:
    """Choose the directory to run in, never one that does not exist.

    A directory that is not there would make `subprocess.run` raise
    `FileNotFoundError` before trestle starts, and the generic handler reports
    that as "Error executing trestle: [Errno 2] No such file or directory",
    which reads like the trestle binary is missing rather than like the
    workspace path was wrong. A typo in `trestle_root` is the most ordinary
    mistake there is, so the message matters.

    Skipping a missing directory hands the problem to trestle, which says what
    is actually wrong: "Given directory /x/ws is not in a valid trestle root
    directory", or for init, "Given directory /x/ws does not exist or is not a
    directory". The path still reaches it, because `--trestle-root` is passed
    as an argument either way.

    Args:
        cwd: Directory the caller asked for, if any. Only `merge` sets this.
        trestle_root: The absolute `--trestle-root` from the arguments, if any.

    Returns:
        The first of those that is an existing directory, else this process's
        working directory.
    """
    for candidate in (cwd, trestle_root):
        if candidate and os.path.isdir(candidate):
            return candidate
    return os.getcwd()


def _run_blocking(cmd: list[str], workdir: str, timeout: int) -> dict:
    """Run the command and wait for it. Called on a worker thread.

    Every failure comes back as a result dict rather than an exception, so the
    service layer has one shape to report from.
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=timeout,
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
