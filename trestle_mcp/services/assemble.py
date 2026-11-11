"""Trestle assemble command service.

This module implements assembly of a split trestle model back into a single
JSON/YAML file under the workspace `dist` directory.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.oscal_types import FileExtension, OscalModelType
from trestle_mcp.libs.trestle import run_trestle_command


class TrestleAssembleInput(BaseModel):
    """Input model for trestle assemble command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    model_type: OscalModelType = Field(
        ..., description="Type of the model(s) to assemble"
    )
    name: Optional[str] = Field(
        default=None,
        description=(
            "Name of a single model to assemble. Omit it and set all_of_type to "
            "assemble every model of this type."
        ),
    )
    all_of_type: bool = Field(
        default=False,
        description="Assemble all models of the given type instead of a single one",
    )
    extension: Optional[FileExtension] = Field(
        default=None, description="Type of file output: json, yaml or yml"
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_assemble(params: TrestleAssembleInput) -> str:
    """Assemble all subcomponents of a trestle model into a single file under dist.

    This is the counterpart of `trestle_split`: it collects a model that was
    split across directories back into one document and writes it to
    dist/<model-type-plural>/<name>.<ext>. The workspace copy is left alone, so
    `dist` is the publishable artefact and the workspace stays the editable form.

    Note that this is the top-level `trestle assemble`, which is about
    split/merge file layout. It is not the same operation as
    `trestle_author_catalog_assemble` or the other author assemble tools, which
    turn markdown back into OSCAL JSON.

    Args:
        params (TrestleAssembleInput): Input parameters with:
            - model_type (OscalModelType): Model type to assemble (required)
            - name (Optional[str]): Single model name to assemble
            - all_of_type (bool): Assemble every model of this type
            - extension (Optional[FileExtension]): json, yaml or yml
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Produce a single publishable catalog.json under dist"
          model_type="catalog", name="mycat"
        - Use when: "Assemble every profile in the workspace"
          model_type="profile", all_of_type=True
        - Don't use when: You edited markdown and want it back in JSON; use the
          matching `trestle_author_*_assemble` tool.
    """
    # The model type is positional for this command.
    args = ["assemble", params.model_type.value]

    if params.name:
        args.extend(["--name", params.name])
    if params.all_of_type:
        args.append("--type")
    if params.extension:
        args.extend(["--extension", params.extension.value])
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = await run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        target = params.name or f"all {params.model_type.value} models"
        return (
            f"✅ Model assembled into dist successfully\n\nTarget: {target}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return (
            f"❌ Failed to assemble model into dist\n\n"
            f"Type: {params.model_type.value}\nError: {error}"
        )
