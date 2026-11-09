"""Trestle author component-assemble command service.

This module implements assembly of a component-definition JSON file from a
directory of component markdown files.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestleAuthorComponentAssembleInput(BaseModel):
    """Input model for trestle author component-assemble command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    markdown: str = Field(..., description="Name of the source markdown directory")
    output: str = Field(
        ...,
        description=(
            "Name of the output generated json component-definition "
            "(ok to overwrite the original)"
        ),
    )
    name: Optional[str] = Field(
        default=None,
        description=(
            "Optional name of the component-definition model in the trestle "
            "workspace that is being modified. If not provided the output name is used."
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


async def trestle_author_component_assemble(
    params: TrestleAuthorComponentAssembleInput,
) -> str:
    """Assemble markdown files of controls into a component-definition json file.

    This is the return leg of the component authoring round trip: generate
    markdown with `trestle_author_component_generate`, edit the implementation
    prose and the rule/parameter yaml headers, then assemble back into
    component-definitions/<output>/component-definition.json.

    Unlike catalog-assemble and profile-assemble there is no set-parameters
    flag — component markdown headers (rules, parameter values, implementation
    status) are always read back.

    Pass `name` whenever `output` is a name that does not already exist. The
    source model defaults to the output name, so assembling into a new
    component-definition without `name` fails with "Unable to load model
    <output> without specifying json or yaml". (catalog-assemble does not have
    this constraint — it takes the source from the markdown header.)

    Args:
        params (TrestleAuthorComponentAssembleInput): Input parameters with:
            - markdown (str): Source markdown directory (required)
            - output (str): Output json component-definition name (required)
            - name (Optional[str]): Source component-definition model name
              (defaults to output)
            - regenerate (bool): Force generation of new uuids (default: false)
            - version (Optional[str]): New version for the assembled model
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Write the implementation prose I edited back into the
          component definition"
        - Use when: "Assemble the component definition and bump its version"
        - Don't use when: The markdown directory was not produced by
          component-generate.
    """
    args = ["author", "component-assemble"]

    # Required
    args.extend(["--markdown", params.markdown])
    args.extend(["--output", params.output])
    # Optional
    if params.name:
        args.extend(["--name", params.name])
    if params.regenerate:
        args.append("--regenerate")
    if params.version:
        args.extend(["--version", params.version])
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        return (
            f"✅ Component definition assembled from markdown successfully\n\n"
            f"Output: {params.output}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return (
            f"❌ Failed to assemble component definition from markdown\n\n"
            f"MarkdownDir: {params.markdown}\nError: {error}"
        )
