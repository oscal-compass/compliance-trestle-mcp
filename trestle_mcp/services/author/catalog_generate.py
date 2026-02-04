"""Trestle author catalog-generate command service.

This module implements the generation of catalog controls in markdown form from a catalog in the trestle workspace.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestleCatalogGenerateInput(BaseModel):
    """Input model for trestle author catalog-generate command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ..., description="Name of the catalog model in the trestle workspace"
    )
    output: str = Field(
        ..., description="Name of the output generated catalog markdown folder"
    )
    force_overwrite: bool = Field(
        default=False, description="Overwrite content of markdowns in output folder"
    )
    yaml_header: Optional[str] = Field(
        default=None, description="Path to the optional yaml header file"
    )
    overwrite_header_values: bool = Field(
        default=False,
        description="Flag to overwrite values in markdown control header.",
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_catalog_generate(params: TrestleCatalogGenerateInput) -> str:
    """Generate Catalog controls in markdown form from a catalog in the trestle workspace.

    Args:
        params (TrestleCatalogGenerateInput): Input parameters with:
            - name (str): Catalog model name (required)
            - output (str): Output markdown folder (required)
            - force_overwrite (bool): Force overwrite markdowns (optional)
            - yaml_header (Optional[str]): Path to yaml header file (optional)
            - overwrite_header_values (bool): Overwrite markdown header values (optional)
            - trestle_root (Optional[str]): Trestle workspace root path (optional)
            - verbose (bool): Display verbose output (optional)

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Generate markdown controls from a catalog"
        - Use when: "Split a catalog JSON into control-wise markdowns"
        - Don't use when: "Catalog is missing or output directory already exists and not overwritten"
    """
    args = ["author", "catalog-generate"]

    # Required arguments
    args.extend(["--name", params.name])
    args.extend(["--output", params.output])

    # Optional flags
    if params.force_overwrite:
        args.append("--force-overwrite")
    if params.yaml_header:
        args.extend(["--yaml-header", params.yaml_header])
    if params.overwrite_header_values:
        args.append("--overwrite-header-values")
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        return f"✅ Catalog controls generated as markdown successfully\n\nOutput: {params.output}\n\n{output}"
    else:
        error = result["stderr"].strip()
        return f"❌ Failed to generate catalog markdowns\n\nCatalog: {params.name}\nError: {error}"
