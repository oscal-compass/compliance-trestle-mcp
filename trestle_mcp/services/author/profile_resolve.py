"""Trestle author profile-resolve command service.

This module implements the trestle author profile-resolve functionality.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestleAuthorProfileResolveInput(BaseModel):
    """Input model for trestle author profile-resolve command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ..., description="Name of the source profile model in the trestle workspace."
    )
    output: str = Field(
        ..., description="Name for the resolved profile catalog output."
    )
    show_values: Optional[bool] = Field(
        False, description="Show values for parameters in prose."
    )
    show_labels: Optional[bool] = Field(
        False, description="Show labels for parameters in prose."
    )
    bracket_format: Optional[str] = Field(
        None, description="Bracket format to wrap value (e.g. [.] or ((.)))."
    )
    value_assigned_prefix: Optional[str] = Field(
        None, description="Prefix for parameter string if value assigned."
    )
    value_not_assigned_prefix: Optional[str] = Field(
        None, description="Prefix for parameter string if value not assigned."
    )
    label_prefix: Optional[str] = Field(None, description="Prefix for parameter label.")
    verbose: Optional[bool] = Field(False, description="Display verbose output.")
    trestle_root: Optional[str] = Field(
        None, description="Path to trestle root directory."
    )


async def trestle_author_profile_resolve(
    params: TrestleAuthorProfileResolveInput,
) -> str:
    """Resolve an OSCAL profile to a resolved profile catalog.

    This tool resolves a specified OSCAL profile (by name from profiles/<name>/profile.json)
    into an operational, parameter-resolved OSCAL catalog, with flexible output and formatting options.

    Args:
        params (TrestleAuthorProfileResolveInput):
            - name (str): Source profile name (required)
            - output (str): Output catalog name (required)
            - show_values (bool): Show parameter values in prose (optional)
            - show_labels (bool): Show parameter labels in prose (optional)
            - bracket_format (str): Bracket format for values (optional)
            - value_assigned_prefix (str): Prefix if value is assigned (optional)
            - value_not_assigned_prefix (str): Prefix if value not assigned (optional)
            - label_prefix (str): Prefix for label output (optional)
            - verbose (bool): Display verbose output (optional)
            - trestle_root (str): Path to trestle root directory (optional)

    Returns:
        str: Result summary string. On success, a checked message with output. On failure, a cross mark and error details.

    Examples:
        - Minimal invocation
            trestle_author_profile_resolve(name="myprofile", output="catalog_resolved")
        - With options
            trestle_author_profile_resolve(name="myprofile", output="catalog_resolved", show_values=True, bracket_format="(.)")
    """
    args = ["author", "profile-resolve", "--name", params.name, "-o", params.output]

    if params.show_values:
        args.append("--show-values")
    if params.show_labels:
        args.append("--show-labels")
    if params.bracket_format:
        args.extend(["--bracket-format", params.bracket_format])
    if params.value_assigned_prefix:
        args.extend(["--value-assigned-prefix", params.value_assigned_prefix])
    if params.value_not_assigned_prefix:
        args.extend(["--value-not-assigned-prefix", params.value_not_assigned_prefix])
    if params.label_prefix:
        args.extend(["--label-prefix", params.label_prefix])
    if params.verbose:
        args.append("--verbose")
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])

    result = run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        return f"✅ Catalog controls generated as markdown successfully\n\nOutput: {params.output}\n\n{output}"
    else:
        error = result["stderr"].strip()
        return f"❌ Failed to generate catalog markdowns\n\nCatalog: {params.name}\nError: {error}"
