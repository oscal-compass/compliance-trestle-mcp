"""Trestle describe command service.

This module implements describing the contents of an OSCAL model file.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestleDescribeInput(BaseModel):
    """Input model for trestle describe command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    file: str = Field(..., description="OSCAL file to describe")
    element: Optional[str] = Field(
        default=None,
        description=(
            "Optional name of an element in the file to describe, e.g. "
            "'catalog.metadata'"
        ),
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_describe(params: TrestleDescribeInput) -> str:
    """Describe the contents of an OSCAL model file, optionally at an element path.

    This prints the model type and the shape of its fields — which are present,
    which are None, and how many items each list holds. It reads the file and
    changes nothing, so it is the cheap way to find out what is actually in a
    model before deciding what to split, filter or generate from it.

    Args:
        params (TrestleDescribeInput): Input parameters with:
            - file (str): OSCAL file to describe (required)
            - element (Optional[str]): Element path within the file
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: The description, or an error message

    Examples:
        - Use when: "What is in this catalog? How many groups does it have?"
          file="catalogs/mycat/catalog.json"
        - Use when: "Show me just the metadata of this profile"
          element="profile.metadata"
        - Don't use when: You want to know whether the file is valid OSCAL; use
          `trestle_validate`.
    """
    args = ["describe", "--file", params.file]

    if params.element:
        args.extend(["--element", params.element])
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = await run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        return f"✅ Model described\n\nFile: {params.file}\n\n{output}"
    else:
        error = result["stderr"].strip()
        return f"❌ Failed to describe model\n\nFile: {params.file}\nError: {error}"
