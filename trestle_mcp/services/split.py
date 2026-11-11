"""Trestle split command service.

This module implements splitting a trestle model into subcomponent files.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import command_output, run_trestle_command


class TrestleSplitInput(BaseModel):
    """Input model for trestle split command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    file: str = Field(..., description="Path of the model file to split")
    element: str = Field(
        ...,
        description=(
            "Path of the element in the OSCAL model to split, e.g. "
            "'catalog.metadata' or 'catalog.groups.*'. Comma-separate several."
        ),
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_split(params: TrestleSplitInput) -> str:
    """Split subcomponents of a trestle model into separate files.

    Splitting moves part of a model into its own file under a directory beside
    the model, so that large models can be edited and reviewed piece by piece and
    so that a diff touches only the part that changed. A wildcard element such
    as `catalog.groups.*` gives one file per group.

    The split form is the workspace form; run `trestle_merge` to fold the pieces
    back in, or `trestle_assemble` to write a single combined document to dist.

    Args:
        params (TrestleSplitInput): Input parameters with:
            - file (str): Model file to split (required)
            - element (str): Element path(s) to split out (required)
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Split the metadata out of this catalog so it can be
          reviewed on its own"
          file="catalogs/mycat/catalog.json", element="catalog.metadata"
        - Use when: "Give me one file per group in the catalog"
          element="catalog.groups.*"
        - Don't use when: The model is already split at that element.
    """
    args = ["split", "--file", params.file, "--element", params.element]

    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = await run_trestle_command(args)

    if result["success"]:
        output = command_output(result)
        return (
            f"✅ Model split successfully\n\n"
            f"File: {params.file}\nElement: {params.element}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return f"❌ Failed to split model\n\nFile: {params.file}\nError: {error}"
