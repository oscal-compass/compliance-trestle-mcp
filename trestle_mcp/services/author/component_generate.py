"""Trestle author component-generate command service.

This module implements generation of component markdown from a
component-definition in the trestle workspace.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import LONG_TIMEOUT, run_trestle_command


class TrestleAuthorComponentGenerateInput(BaseModel):
    """Input model for trestle author component-generate command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        description="Name of the source component-definition model in the trestle workspace",
    )
    output: str = Field(
        ..., description="Name of the output generated component markdown folder"
    )
    force_overwrite: bool = Field(
        default=False,
        description="Overwrite the content of all markdowns in the output folder",
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_author_component_generate(
    params: TrestleAuthorComponentGenerateInput,
) -> str:
    """Generate component in markdown form from a component-definition in the trestle workspace.

    This writes one markdown file per control implementation, per component, under
    <output>/<component-name>/<source>/. The markdown is where an author writes
    the implementation prose and the rule/parameter yaml header that
    `trestle_author_component_assemble` reads back.

    Note that generate only writes what the component-definition already
    declares: it will not create implemented requirements for controls the
    component-definition does not claim.

    Args:
        params (TrestleAuthorComponentGenerateInput): Input parameters with:
            - name (str): Source component-definition model name (required)
            - output (str): Output markdown folder (required)
            - force_overwrite (bool): Overwrite existing markdown content,
              discarding edits (default: false)
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Generate editable markdown for this component definition"
        - Use when: "Let me write implementation prose for each control a
          component claims"
        - Don't use when: There is no component-definition in the workspace yet;
          import one, or create one with `trestle_task_csv_to_oscal_cd`.
        - Don't use when: You only want to regenerate without losing edits —
          force_overwrite discards author prose.
    """
    args = ["author", "component-generate"]

    # Required
    args.extend(["--name", params.name])
    args.extend(["--output", params.output])
    # Optional
    if params.force_overwrite:
        args.append("--force-overwrite")
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    # The component definition names a profile in each rule's Profile_Source,
    # and generating the markdown resolves it. That is the same walk as
    # profile-resolve, over a profile this server did not choose -- a
    # Profile_Source pointing at NIST SP 800-53 rev5 is ~10 MB fetched and
    # every control resolved.
    result = await run_trestle_command(args, timeout=LONG_TIMEOUT)

    if result["success"]:
        output = result["stdout"].strip()
        return (
            f"✅ Component markdown generated successfully\n\n"
            f"Output: {params.output}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return (
            f"❌ Failed to generate component markdown\n\n"
            f"Component: {params.name}\nError: {error}"
        )
