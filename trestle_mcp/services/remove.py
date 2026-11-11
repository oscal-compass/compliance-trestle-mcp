"""Trestle remove command service.

This module implements removal of a subcomponent from an existing OSCAL model,
the inverse of creating an element with `trestle_create`.

The tool built from this module is opt-in: no group selects it, not even `all`.
See :mod:`trestle_mcp.tools` for why.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestleRemoveInput(BaseModel):
    """Input model for trestle remove command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    file: str = Field(
        ..., description="Path of the model file to remove an element from"
    )
    element: str = Field(
        ...,
        description=(
            "Path of the element in the OSCAL model to remove, e.g. "
            "'catalog.metadata.roles'. The element and everything under it are "
            "deleted from the file."
        ),
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_remove(params: TrestleRemoveInput) -> str:
    """Remove a subcomponent from an existing OSCAL model, in place.

    This deletes `element` and everything nested under it from `file` and writes
    the file back. It is the inverse of creating an element with
    `trestle_create` (`file` + `element`).

    There is no undo. trestle keeps no backup of the previous contents, so the
    only way back is version control or a copy you made first. Confirm the
    element path with `trestle_describe` before calling this, and prefer to have
    the workspace committed to git so the removal shows up as a reviewable diff.

    Removing a required OSCAL field leaves the model invalid rather than
    refusing: run `trestle_validate` afterwards.

    Args:
        params (TrestleRemoveInput): Input parameters with:
            - file (str): Model file to remove an element from (required)
            - element (str): Element path to remove (required)
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Drop the roles list from this catalog's metadata"
          file="catalogs/mycat/catalog.json", element="catalog.metadata.roles"
        - Don't use when: You want the element in its own file rather than gone;
          use `trestle_split`.
        - Don't use when: You have not checked what is at that path; call
          `trestle_describe` first.
    """
    args = ["remove", "--file", params.file, "--element", params.element]

    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        return (
            f"✅ Element removed successfully\n\n"
            f"File: {params.file}\nElement: {params.element}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return (
            f"❌ Failed to remove element\n\n"
            f"File: {params.file}\nElement: {params.element}\nError: {error}"
        )
