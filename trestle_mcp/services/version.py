"""Trestle version command service.

This module implements reporting of the trestle and OSCAL versions, and of the
OSCAL version of a model in the workspace.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.oscal_types import OscalModelType
from trestle_mcp.libs.trestle import run_trestle_command


class TrestleVersionInput(BaseModel):
    """Input model for trestle version command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(
        default=None,
        description=(
            "Name of a model in the workspace to report the OSCAL version of. "
            "Omit both name and model_type to report the trestle and OSCAL "
            "versions instead."
        ),
    )
    model_type: Optional[OscalModelType] = Field(
        default=None,
        description="Type of the model being queried (required when name is given)",
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_version(params: TrestleVersionInput) -> str:
    """Report the trestle and OSCAL versions, or the OSCAL version of a model.

    With no arguments this reports the version of the trestle CLI the server is
    driving and the OSCAL version it implements. That is the first thing to check
    when a model another tool produced will not load: OSCAL minor versions change
    the schema, and trestle only reads the version it was built for.

    Give `name` and `model_type` to report the OSCAL version recorded in a
    specific model in the workspace.

    Args:
        params (TrestleVersionInput): Input parameters with:
            - name (Optional[str]): Model name to query
            - model_type (Optional[OscalModelType]): Model type to query
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: The version information, or an error message

    Examples:
        - Use when: "Which trestle and OSCAL version is this server using?"
        - Use when: "What OSCAL version is this catalog?"
          name="mycat", model_type="catalog"
        - Don't use when: You want the version of the MCP server itself — that is
          the package version, not a trestle command.
    """
    args = ["version"]

    if params.name:
        args.extend(["--name", params.name])
    if params.model_type:
        args.extend(["--type", params.model_type.value])
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = await run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        return f"✅ Version information\n\n{output}"
    else:
        error = result["stderr"].strip()
        return f"❌ Failed to get version information\n\nError: {error}"
