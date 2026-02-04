"""Trestle import command service

This module implements the OSCAL model import functionality.
Note: Named 'import_model' because 'import' is a Python reserved keyword.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestleImportInput(BaseModel):
    """Input model for trestle import command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    file: str = Field(..., description="OSCAL file to import - either file path or URL")
    output: str = Field(..., description="Name of output element")
    regenerate: bool = Field(
        default=False, description="Flag to force generation of new UUIDs in the model"
    )
    trestle_root: Optional[str] = Field(
        default=None, description="Path to trestle root directory"
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_import(params: TrestleImportInput) -> str:
    """Import an existing OSCAL model into the trestle workspace.

    This tool imports OSCAL models from URLs or local file paths.
    The imported file will be saved in the appropriate directory based on
    its OSCAL type (e.g., catalogs/, profiles/, component-definitions/).

    Import Behavior:
    - Catalog → catalogs/{output}/catalog.json
    - Profile → profiles/{output}/profile.json
    - Component Definition → component-definitions/{output}/component-definition.json
    - SSP → system-security-plans/{output}/system-security-plan.json

    Args:
        params (TrestleImportInput): Validated input parameters containing:
            - file (str): OSCAL file to import (URL or file path)
            - output (str): Name of output element
            - regenerate (bool): Force generation of new UUIDs (default: false)
            - trestle_root (Optional[str]): Path to trestle root directory
            - verbose (bool): Display verbose output (default: false)

    Returns:
        str: Success message with import details or error

    Examples:
        - Import NIST SP800-53 Rev5 Catalog:
          file="https://raw.githubusercontent.com/usnistgov/oscal-content/refs/heads/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json"
          output="nist_sp800_53_rev5"

        - Import from local file:
          file="./resources/catalogs/your_catalog.json"
          output="mycatalog"
    """
    args = ["import", "-f", params.file, "-o", params.output]

    if params.regenerate:
        args.append("--regenerate")

    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])

    if params.verbose:
        args.append("--verbose")

    result = run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        return f"✅ OSCAL model imported successfully\n\nOutput: {params.output}\n\n{output}"
    else:
        error = result["stderr"].strip()
        return f"❌ Failed to import OSCAL model\n\nFile: {params.file}\nError: {error}"
