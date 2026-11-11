"""Trestle author ssp-generate command service.

This module implements generation of SSP markdown from a profile and an optional
set of component-definitions.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import LONG_TIMEOUT, command_output, run_trestle_command


class TrestleAuthorSspGenerateInput(BaseModel):
    """Input model for trestle author ssp-generate command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    profile: str = Field(
        ...,
        description=(
            "Main profile href, or name of the profile model in the trestle workspace"
        ),
    )
    output: str = Field(
        ..., description="Name of the output generated ssp markdown folder"
    )
    compdefs: Optional[str] = Field(
        default=None,
        description=(
            "Comma-separated list of component-definition names to include in the ssp"
        ),
    )
    leveraged_ssp: Optional[str] = Field(
        default=None,
        description=(
            "Leveraged ssp with inheritable controls: href, or name in the "
            "trestle workspace"
        ),
    )
    yaml_header: Optional[str] = Field(
        default=None, description="Path to the optional yaml header file"
    )
    force_overwrite: bool = Field(
        default=False,
        description="Overwrite the content of all markdowns in the output folder",
    )
    overwrite_header_values: bool = Field(
        default=False,
        description=(
            "Overwrite values in a markdown control header that are also present "
            "in the yaml header passed with yaml_header"
        ),
    )
    include_all_parts: bool = Field(
        default=False,
        description=(
            "Include all control parts. By default only controls and parts with "
            "an attached rule are written out."
        ),
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_author_ssp_generate(params: TrestleAuthorSspGenerateInput) -> str:
    """Generate SSP in markdown form from a Profile.

    The profile selects which controls the SSP must answer; the
    component-definitions passed in `compdefs` supply the rules, parameter values
    and implementation prose that pre-populate each control. Without `compdefs`
    you get an empty questionnaire — correct, but every control has to be written
    by hand.

    By default only controls and parts that have a rule attached from a
    component-definition are written out. Pass `include_all_parts` to get the
    full control text, which is what you want for a human-authored SSP and is
    much larger.

    This command resolves the profile, so it runs for minutes on a large catalog
    and is given a long timeout.

    Args:
        params (TrestleAuthorSspGenerateInput): Input parameters with:
            - profile (str): Profile name in the workspace, or an href (required)
            - output (str): Output ssp markdown folder (required)
            - compdefs (Optional[str]): Comma-separated component-definition names
            - leveraged_ssp (Optional[str]): Leveraged ssp providing inherited controls
            - yaml_header (Optional[str]): Path to a yaml header file
            - force_overwrite (bool): Overwrite existing markdown (default: false)
            - overwrite_header_values (bool): Overwrite common header values
            - include_all_parts (bool): Write all control parts (default: false)
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Start an SSP for the moderate baseline using these
          component definitions"
          profile="nist_moderate", output="md_ssp", compdefs="ocp4,rhel8"
        - Use when: "Generate SSP markdown including the full control text"
          include_all_parts=True
        - Don't use when: You want the controls of the profile as a catalog
          rather than an SSP; use `trestle_author_profile_resolve`.
        - Don't use when: The profile is not in the workspace and you have no
          href for it — import it first.
    """
    args = ["author", "ssp-generate"]

    # Required
    args.extend(["--profile", params.profile])
    args.extend(["--output", params.output])
    # Optional
    if params.compdefs:
        args.extend(["--compdefs", params.compdefs])
    if params.leveraged_ssp:
        args.extend(["--leveraged-ssp", params.leveraged_ssp])
    if params.yaml_header:
        args.extend(["--yaml-header", params.yaml_header])
    if params.force_overwrite:
        args.append("--force-overwrite")
    if params.overwrite_header_values:
        args.append("--overwrite-header-values")
    if params.include_all_parts:
        args.append("--include-all-parts")
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    # ssp-generate resolves the profile, which walks every control in the
    # imported catalog; the default timeout is not enough for a real baseline.
    result = await run_trestle_command(args, timeout=LONG_TIMEOUT)

    if result["success"]:
        output = command_output(result)
        return (
            f"✅ SSP markdown generated successfully\n\n"
            f"Output: {params.output}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return (
            f"❌ Failed to generate SSP markdown\n\n"
            f"Profile: {params.profile}\nError: {error}"
        )
