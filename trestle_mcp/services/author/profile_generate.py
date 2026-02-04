"""Trestle author profile-generate command service.

This module implements the profile-generate functionality under trestle author.
"""

from typing import Optional

from pydantic import BaseModel, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestleAuthorProfileGenerateInput(BaseModel):
    """Input model for trestle author profile-generate command."""

    name: str = Field(
        ..., description="Profile name to transform (profiles/<name>/profile.json)"
    )
    output: str = Field(..., description="Output directory for generated markdown")
    yaml_header: Optional[str] = Field(
        default=None, description="YAML to insert as markdown header (optional)"
    )
    force_overwrite: bool = Field(
        default=False, description="Overwrite all markdown files in output directory"
    )
    overwrite_header_values: bool = Field(
        default=False,
        description="Overwrite only YAML header values in markdown controls",
    )
    sections: Optional[str] = Field(
        default=None,
        description="Sections to split in each control markdown file (comma-separated)",
    )
    required_sections: Optional[str] = Field(
        default=None,
        description="Comma-separated section short names required in the output",
    )
    trestle_root: Optional[str] = Field(
        default=None, description="Path to trestle workspace root"
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_author_profile_generate(
    params: TrestleAuthorProfileGenerateInput,
) -> str:
    """Generate markdown documentation set for controls defined in specified profile.

    This tool extracts controls defined in the specified profile (profiles/<name>/profile.json)
    and generates a set of markdown documents for them. This set can be used for custom documentation,
    reviews, and organization-specific profile documentation.

    Args:
        params (TrestleAuthorProfileGenerateInput):
            - name (str): profile name (required)
            - output (str): output directory for markdown docs (required)
            - yaml_header (Optional[str]): yaml header file path
            - force_overwrite (bool): overwrite all in output dir
            - overwrite_header_values (bool): overwrite header values only
            - sections (Optional[str]): targeted sections in markdown
            - required_sections (Optional[str]): required section short names, comma-separated
            - trestle_root (Optional[str]): workspace root path
            - verbose (bool): verbose output

    Returns:
        str: Success message or error details

    Examples:
        - Use when: "Generate markdown controls for a given profile"
        - Use when: "Customize output with required sections or header overwrite"
        - Don't use when: Profile file does not exist
    """
    args = ["author", "profile-generate"]

    # Required
    args.extend(["-n", params.name])
    args.extend(["--output", params.output])
    # Optional
    if params.yaml_header:
        args.extend(["--yaml-header", params.yaml_header])
    if params.force_overwrite:
        args.append("--force-overwrite")
    if params.overwrite_header_values:
        args.append("--overwrite-header-values")
    if params.sections:
        args.extend(["--sections", params.sections])
    if params.required_sections:
        args.extend(["--required-sections", params.required_sections])
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        return f"✅ Profile-based markdown controls generated successfully\n\nOutput: {params.output}\n\n{output}"
    else:
        error = result["stderr"].strip()
        return f"❌ Failed to generate profile-based markdowns\n\nProfile: {params.name}\nError: {error}"
