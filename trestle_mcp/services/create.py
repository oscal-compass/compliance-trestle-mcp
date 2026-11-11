"""Trestle create command service.

This module implements creation of a sample OSCAL model in the trestle
workspace, or of new elements within an existing model file.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.oscal_types import FileExtension, OscalModelType
from trestle_mcp.libs.trestle import run_trestle_command


class TrestleCreateInput(BaseModel):
    """Input model for trestle create command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    model_type: Optional[OscalModelType] = Field(
        default=None,
        description=(
            "Type of model to create anew. Required when creating a new model; "
            "omit it when creating an element inside an existing file."
        ),
    )
    output: Optional[str] = Field(
        default=None,
        description="Name of the created model (required when model_type is given)",
    )
    include_optional_fields: bool = Field(
        default=False,
        description=(
            "Include fields that are optional in the OSCAL model when generating "
            "the new object"
        ),
    )
    extension: Optional[FileExtension] = Field(
        default=None, description="Type of file output: json, yaml or yml"
    )
    file: Optional[str] = Field(
        default=None,
        description=(
            "Existing OSCAL file that will have elements created within it "
            "(used with element)"
        ),
    )
    element: Optional[str] = Field(
        default=None,
        description=(
            "Path of the element to create within the file given in file, "
            "e.g. 'catalog.groups'"
        ),
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_create(params: TrestleCreateInput) -> str:
    """Create a sample OSCAL model in the trestle workspace, or new elements within a model.

    This command has two modes and they do not mix:

    1. Give `model_type` and `output` to scaffold an empty model of that type,
       e.g. profiles/<output>/profile.json. The result is a valid skeleton with
       placeholder metadata, which is what you want as a starting point for
       authoring something that has no upstream to import.
    2. Give `file` and `element` to add an element inside a model file that
       already exists, e.g. appending to `catalog.groups`. This fails if the
       element already exists and is not a list or a dictionary.

    Use `include_optional_fields` when you want the skeleton to show every field
    OSCAL permits rather than only the required ones — useful for seeing the
    shape of a model, noisy as a starting document.

    Args:
        params (TrestleCreateInput): Input parameters with:
            - model_type (Optional[OscalModelType]): Model type to create anew
            - output (Optional[str]): Name of the created model
            - include_optional_fields (bool): Include optional OSCAL fields
            - extension (Optional[FileExtension]): json, yaml or yml
            - file (Optional[str]): Existing OSCAL file to add an element to
            - element (Optional[str]): Element path to create within file
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Create an empty component definition called mycomp"
          model_type="component-definition", output="mycomp"
        - Use when: "Add a groups element to this catalog"
          file="catalogs/mycat/catalog.json", element="catalog.groups"
        - Don't use when: The model exists upstream — `trestle_import` keeps the
          real uuids and metadata, create gives you placeholders.
    """
    args = ["create"]

    if params.model_type:
        args.extend(["--type", params.model_type.value])
    if params.output:
        args.extend(["--output", params.output])
    if params.include_optional_fields:
        args.append("--include-optional-fields")
    if params.extension:
        args.extend(["--extension", params.extension.value])
    if params.file:
        args.extend(["--file", params.file])
    if params.element:
        args.extend(["--element", params.element])
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = await run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        target = params.output or params.file or "(unnamed)"
        return f"✅ OSCAL model created successfully\n\nTarget: {target}\n\n{output}"
    else:
        error = result["stderr"].strip()
        return f"❌ Failed to create OSCAL model\n\nError: {error}"
