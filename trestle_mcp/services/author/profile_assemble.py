"""Trestle author profile-assemble command service.

This module implements profile JSON assembly from markdown directory.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestleAuthorProfileAssembleInput(BaseModel):
    """Input model for trestle author profile-assemble command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    markdown_dir: str = Field(
        description="Directory containing the profile markdown controls."
    )
    output_profile: str = Field(
        description="Output profile directory name (profiles/<output_profile>/profile.json)"
    )
    name: Optional[str] = Field(
        default=None, description="Profile model name (optional)"
    )
    set_parameters: bool = Field(
        default=False, description="Expand parameters in frontmatter (optional)"
    )
    regenerate: bool = Field(
        default=False, description="Force UUID regeneration (optional)"
    )
    version: Optional[str] = Field(
        default=None, description="Profile version (optional)"
    )
    sections: Optional[str] = Field(
        default=None, description="Sections short:long comma-separated (optional)"
    )
    required_sections: Optional[str] = Field(
        default=None, description="Required section short names, comma-separated"
    )
    allowed_sections: Optional[str] = Field(
        default=None, description="Allowed section short names, comma-separated"
    )
    verbose: bool = Field(default=False, description="Verbose output")
    trestle_root: Optional[str] = Field(
        default=None, description="Path to trestle root dir"
    )


async def trestle_author_profile_assemble(
    params: TrestleAuthorProfileAssembleInput,
) -> str:
    """Assemble markdown controls into a Profile JSON file.

    This tool assembles an OSCAL profile JSON (profile.json) from a directory of markdown controls for a profile.

    Args:
        params (TrestleAuthorProfileAssembleInput):
            - markdown_dir (str): Markdown controls directory (required)
            - output_profile (str): Output profile directory name (required)
            - name (Optional[str]): Profile model name
            - set_parameters (bool): Expand parameters from YAML frontmatter
            - regenerate (bool): Force UUID regeneration
            - version (Optional[str]): Model version
            - sections (Optional[str]): Section info (short:long, comma-separated)
            - required_sections (Optional[str]): Required section short names, comma-separated
            - allowed_sections (Optional[str]): Allowed section short names, comma-separated
            - verbose (bool): Verbose output
            - trestle_root (Optional[str]): Path of trestle root directory

    Returns:
        str: Success message with stdout, or error message with stderr details

    Examples:
        - Use when: Automatically assemble OSCAL profile from markdown directory
        - Use when: CI/CD profile assembling, parameter expansion
        - Don't use when: Input markdown_dir does not exist, or malformed markdown
    """
    args = ["author", "profile-assemble"]

    if params.name:
        args.extend(["--name", params.name])
    if params.markdown_dir:
        args.extend(["--markdown", params.markdown_dir])
    if params.output_profile:
        args.extend(["--output", params.output_profile])
    if params.set_parameters:
        args.append("--set-parameters")
    if params.regenerate:
        args.append("--regenerate")
    if params.version:
        args.extend(["--version", params.version])
    if params.sections:
        args.extend(["--sections", params.sections])
    if params.required_sections:
        args.extend(["--required-sections", params.required_sections])
    if params.allowed_sections:
        args.extend(["--allowed-sections", params.allowed_sections])
    if params.verbose:
        args.append("--verbose")
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])

    result = run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        return f"✅ Profile assembled from markdown successfully\n\nOutput: {params.output_profile}\n\n{output}"
    else:
        error = result["stderr"].strip()
        return f"❌ Failed to assemble profile from markdown\n\nMarkdownDir: {params.markdown_dir}\nError: {error}"
