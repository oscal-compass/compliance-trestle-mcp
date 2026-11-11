"""Trestle author catalog-assemble command service.

This module implements assembly of a Catalog JSON file from a directory of
control markdown files.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestleAuthorCatalogAssembleInput(BaseModel):
    """Input model for trestle author catalog-assemble command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    markdown: str = Field(
        ..., description="Name of the input markdown control directory"
    )
    output: str = Field(..., description="Name of the output generated json Catalog")
    name: Optional[str] = Field(
        default=None,
        description=(
            "Optional name of the catalog model in the trestle workspace that is "
            "being modified. If not provided the output name is used."
        ),
    )
    set_parameters: bool = Field(
        default=False,
        description=(
            "Set parameters and properties based on the yaml header in control markdown"
        ),
    )
    regenerate: bool = Field(
        default=False, description="Force generation of new uuids in the model"
    )
    version: Optional[str] = Field(
        default=None, description="New version for the assembled model"
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_author_catalog_assemble(
    params: TrestleAuthorCatalogAssembleInput,
) -> str:
    """Assemble markdown files of controls into a Catalog json file.

    This is the return leg of the catalog authoring round trip: run
    `trestle_author_catalog_generate` to get markdown, edit the control prose or
    the yaml header, then run this tool to write the edits back into
    catalogs/<output>/catalog.json.

    Set `set_parameters` when the edits include parameter values or properties in
    the markdown yaml header — without it only the control prose is read back,
    and header edits are silently discarded.

    Args:
        params (TrestleAuthorCatalogAssembleInput): Input parameters with:
            - markdown (str): Input markdown control directory (required)
            - output (str): Output json catalog name (required)
            - name (Optional[str]): Source catalog model name (defaults to output)
            - set_parameters (bool): Read parameters and properties from the
              markdown yaml header (default: false)
            - regenerate (bool): Force generation of new uuids (default: false)
            - version (Optional[str]): New version for the assembled model
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Write my markdown control edits back into the catalog json"
        - Use when: "Assemble a catalog from markdown and stamp it version 1.1.0"
        - Don't use when: The markdown directory was never generated from a
          catalog — assemble cannot invent the catalog metadata it needs.
        - Don't use when: You want a profile json out of profile markdown; use
          `trestle_author_profile_assemble`.
    """
    args = ["author", "catalog-assemble"]

    # Required
    args.extend(["--markdown", params.markdown])
    args.extend(["--output", params.output])
    # Optional
    if params.name:
        args.extend(["--name", params.name])
    if params.set_parameters:
        args.append("--set-parameters")
    if params.regenerate:
        args.append("--regenerate")
    if params.version:
        args.extend(["--version", params.version])
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = await run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        return (
            f"✅ Catalog assembled from markdown successfully\n\n"
            f"Output: {params.output}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return (
            f"❌ Failed to assemble catalog from markdown\n\n"
            f"MarkdownDir: {params.markdown}\nError: {error}"
        )
