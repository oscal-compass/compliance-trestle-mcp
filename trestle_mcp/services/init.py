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

    mode: InitMode = Field(
        default=InitMode.LOCAL,
        description="Initialization mode: 'local' (default), 'full', or 'govdocs'",
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
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
