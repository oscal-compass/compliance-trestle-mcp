"""Trestle author ssp-assemble command service.

This module implements assembly of a system-security-plan JSON file from a
directory of SSP markdown files.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import LONG_TIMEOUT, command_output, run_trestle_command


class TrestleAuthorSspAssembleInput(BaseModel):
    """Input model for trestle author ssp-assemble command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    markdown: str = Field(..., description="Name of the input markdown file directory")
    output: str = Field(..., description="Name of the output generated json SSP")
    name: Optional[str] = Field(
        default=None,
        description=(
            "Optional name of the ssp model in the trestle workspace that is "
            "being modified. If not provided the output name is used."
        ),
    )
    compdefs: Optional[str] = Field(
        default=None,
        description=(
            "Comma-separated list of component-definition names for the ssp. "
            "Must match the list given to ssp-generate."
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


async def trestle_author_ssp_assemble(params: TrestleAuthorSspAssembleInput) -> str:
    """Assemble markdown files of controls into a system-security-plan json file.

    This is the return leg of the SSP authoring round trip: generate markdown
    with `trestle_author_ssp_generate`, write the implementation statements, then
    assemble into system-security-plans/<output>/system-security-plan.json.

    Pass the same `compdefs` list that was given to ssp-generate. The assembled
    SSP carries the components those definitions describe, and omitting the list
    here drops them from the output even though the markdown still mentions them.

    Args:
        params (TrestleAuthorSspAssembleInput): Input parameters with:
            - markdown (str): Input markdown directory (required)
            - output (str): Output json SSP name (required)
            - name (Optional[str]): Source ssp model name (defaults to output)
            - compdefs (Optional[str]): Comma-separated component-definition names
            - regenerate (bool): Force generation of new uuids (default: false)
            - version (Optional[str]): New version for the assembled model
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Turn the SSP markdown I just finished into OSCAL json"
        - Use when: "Assemble the SSP and release it as version 2.0.0"
        - Don't use when: You want to narrow an existing SSP to fewer controls or
          components; use `trestle_author_ssp_filter`.
    """
    args = ["author", "ssp-assemble"]

    # Required
    args.extend(["--markdown", params.markdown])
    args.extend(["--output", params.output])
    # Optional
    if params.name:
        args.extend(["--name", params.name])
    if params.compdefs:
        args.extend(["--compdefs", params.compdefs])
    if params.regenerate:
        args.append("--regenerate")
    if params.version:
        args.extend(["--version", params.version])
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    # Assembling an SSP loads the generated markdown for every control in the
    # baseline the SSP was generated from, so it scales with that baseline the
    # way ssp-generate does.
    result = await run_trestle_command(args, timeout=LONG_TIMEOUT)

    if result["success"]:
        output = command_output(result)
        return (
            f"✅ SSP assembled from markdown successfully\n\n"
            f"Output: {params.output}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return (
            f"❌ Failed to assemble SSP from markdown\n\n"
            f"MarkdownDir: {params.markdown}\nError: {error}"
        )
