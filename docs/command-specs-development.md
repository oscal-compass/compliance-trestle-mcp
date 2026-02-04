# Command-specs Development Guide

## Overview & Audience
You are building code to invoke each trestle CLI command from MCP.

This document is primarily intended for **human open-source developers** who wish to add or extend command support for MCP.

---

## Task Overview (Original Doc Intent)
The `docs/command-specs` directory contains specifications for trestle CLI commands. The hierarchical structure is due to trestle's use of subcommands. For example, the spec for `trestle init` is in `init.md`. The spec for `trestle author catalog-generate` is in `author/catalog-generate.md` because `author` is a subcommand.

The implementation of these specs should be placed under `trestle_mcp/services` in the same directory structure as command-specs.

---

## How to Implement (Step by Step)
To implement a spec, follow these steps:

1. **Understand the command arguments and create an appropriate Pydantic class.** This class serves as the MCP input schema for the command. Name it `InputModel`.
    - You may map command arguments directly to member variables or adjust them for code clarity. As long as you can build CLI arguments from the input, it's acceptable.
2. **Write the MCP interface function using the input model.**
   - The argument type is the InputModel.
   - The docstring should cover Overview, Args, Returns, and Examples (see example below for format).
   - Compose the CLI args from the params, call the runner, and return the result string.
   - On success: include a success message and stdout. On failure: include a failure message and stderr, but do not raise exceptions.
3. **Import the module in each `__init__.py` in the matching services directory.**
    - Import only modules (use the full package path); do not import individual functions/classes.
    - Only import files/directories one level below.
    ```python
    from root.services.foo import repo, service
    ```

## Implementation Example
Below is a reference of a command interface and its implementation, unchanged from the original development guide:

#### Spec
````md
```sh
# trestle init -h
usage: trestle init [-h] [--full] [--local] [-gd] [--verbose] [-tr TRESTLE_ROOT]

Initialize a trestle working directory.

options:
  -h, --help            show this help message and exit
  --full, -fl           Initializes Trestle workspace for local, API and governed documents usage.
  --local, -loc         Initializes Trestle workspace for local management of OSCAL models.
  -gd, --govdocs        Initializes Trestle workspace for governed documents usage only.
  --verbose, -v         Display verbose output
  -tr TRESTLE_ROOT, --trestle-root TRESTLE_ROOT
                        Path of trestle root dir
```

### Examples
```python
trestle_init()
```
**Result:**
```
✅ Trestle workspace initialized successfully

Initialized trestle project successfully in /path/to/workspace
```
```python
trestle_init(mode="full", trestle_root="/path/to/workspace")
```
```python
trestle_init(mode="local", verbose=True)
```
````

#### Implementation
```python
"""Trestle init command service.

This module implements the trestle workspace initialization functionality.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from trestle_mcp.libs.trestle import run_trestle_command

class InitMode(str, Enum):
    """Initialization mode for trestle workspace."""
    LOCAL = "local"
    FULL = "full"
    GOVDOCS = "govdocs"

class TrestleInitInput(BaseModel):
    """Input model for trestle init command."""
    model_config = ConfigDict(str_strip_whitespace=True)
    mode: InitMode = Field(default=InitMode.LOCAL, description="Initialization mode: 'local' (default), 'full', or 'govdocs'")
    trestle_root: Optional[str] = Field(default=None, description="Path to trestle root directory (default: current directory)")
    verbose: bool = Field(default=False, description="Display verbose output")

async def trestle_init(params: TrestleInitInput) -> str:
    """Initialize a trestle working directory.

    This tool initializes the current directory as a Trestle workspace,
    creating the necessary directory structure for OSCAL model management.

    OSCAL Model Types supported:
    - Catalog
    - Profile
    - Component Definition
    - System Security Plan (SSP)
    - Assessment Plan
    - Assessment Result
    - Plan of Action and Milestones (POAM)

    Args:
        params (TrestleInitInput): Validated input parameters containing:
            - mode (InitMode): Initialization mode (local/full/govdocs, default: local)
            - trestle_root (Optional[str]): Path to trestle root directory
            - verbose (bool): Display verbose output (default: false)

    Returns:
        str: Success message or error details

    Examples:
        - Use when: "Initialize trestle workspace"
        - Use when: "Set up trestle in full mode"
        - Don't use when: Workspace is already initialized
    """
    args = ["init"]
    # Add mode flag
    if params.mode == InitMode.FULL:
        args.append("--full")
    elif params.mode == InitMode.GOVDOCS:
        args.append("--govdocs")
    else:  # LOCAL
        args.append("--local")

    # Add optional flags
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = run_trestle_command(args)
    if result["success"]:
        output = result["stdout"].strip()
        return f"✅ Trestle workspace initialized successfully\n\n{output}"
    else:
        error = result["stderr"].strip()
        return f"❌ Failed to initialize trestle workspace\n\nError: {error}"
```

#### Unit Test
Put the test file with the same hierarchy under `tests/unit/services/` using the `test_` prefix (for this example: `tests/unit/services/test_init.py`).
(The example provided remains unchanged from the original tutorial.)

#### Register as MCP Tool
Add the MCP tool registration code in [`trestle_mcp/main.py`](trestle_mcp/main.py:1):
```python
@mcp.tool(
    name="trestle_init",
    title="Initialize Trestle Workspace",
    description=services.trestle_init.__doc__,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def trestle_init(params: services.TrestleInitInput) -> str:
    return await services.trestle_init(params)
```

---

## Additional Guidance for Human Developers
- All code and documentation must be in English for OSS community use.
- Use [PEP8](https://peps.python.org/pep-0008/) style guide for Python code.
- Add helpful error messages for users, not just agents.
- When in doubt about the spec or intended behavior, ask questions in community issues or discussions.
- The above workflow and style ensure that **human contributors** can reliably add new integrations and tests, and maintain the MCP project long-term.

For any unclear instructions, refer to this file first, then contact the maintainers via issues or discussions.
