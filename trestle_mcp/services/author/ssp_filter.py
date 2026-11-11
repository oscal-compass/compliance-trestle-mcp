"""Trestle author ssp-filter command service.

This module implements filtering of an SSP by profile, components,
implementation status and/or control origination.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestleAuthorSspFilterInput(BaseModel):
    """Input model for trestle author ssp-filter command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., description="Name of the input ssp")
    output: str = Field(..., description="Name of the output generated SSP")
    profile: Optional[str] = Field(
        default=None,
        description=(
            "Name of an optional input profile that defines the set of controls "
            "to keep in the filtered ssp"
        ),
    )
    components: Optional[str] = Field(
        default=None,
        description=(
            "Colon-delimited list of component names to include in the filtered ssp"
        ),
    )
    implementation_status: Optional[str] = Field(
        default=None,
        description=(
            "Comma-delimited list of control implementation statuses to include, "
            "e.g. 'implemented,partial'"
        ),
    )
    control_origination: Optional[str] = Field(
        default=None,
        description=(
            "Comma-delimited list of control origination values to include, "
            "e.g. 'system-specific,inherited'"
        ),
    )
    regenerate: bool = Field(
        default=False, description="Force generation of new uuids in the model"
    )
    version: Optional[str] = Field(
        default=None, description="New version for the filtered model"
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_author_ssp_filter(params: TrestleAuthorSspFilterInput) -> str:
    """Filter the controls in an SSP by profile, components, implementation status or control origination.

    This produces a new SSP that is a subset of an existing one. The typical use
    is handing an assessor or a customer the part of the SSP that concerns them:
    the controls of one baseline, or the statements of one component, without
    re-authoring anything.

    The filters intersect: giving a profile and a component list keeps only the
    statements that are in that profile and attributed to those components.

    Watch the delimiters, they differ: `components` is colon-delimited, while
    `implementation_status` and `control_origination` are comma-delimited.

    Args:
        params (TrestleAuthorSspFilterInput): Input parameters with:
            - name (str): Input ssp name (required)
            - output (str): Output ssp name (required)
            - profile (Optional[str]): Profile defining the controls to keep
            - components (Optional[str]): Colon-delimited component names
            - implementation_status (Optional[str]): Comma-delimited statuses
            - control_origination (Optional[str]): Comma-delimited originations
            - regenerate (bool): Force generation of new uuids (default: false)
            - version (Optional[str]): New version for the filtered model
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Give me just the low-baseline controls out of this SSP"
          name="my_ssp", output="my_ssp_low", profile="nist_low"
        - Use when: "Extract only what component ocp4 is responsible for"
          components="ocp4"
        - Don't use when: You need to add controls — filter only removes. Change
          the profile and re-run `trestle_author_ssp_generate` instead.
    """
    args = ["author", "ssp-filter"]

    # Required
    args.extend(["--name", params.name])
    args.extend(["--output", params.output])
    # Optional
    if params.profile:
        args.extend(["--profile", params.profile])
    if params.components:
        args.extend(["--components", params.components])
    if params.implementation_status:
        args.extend(["--implementation-status", params.implementation_status])
    if params.control_origination:
        args.extend(["--control-origination", params.control_origination])
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
        return f"✅ SSP filtered successfully\n\nOutput: {params.output}\n\n{output}"
    else:
        error = result["stderr"].strip()
        return f"❌ Failed to filter SSP\n\nSSP: {params.name}\nError: {error}"
