"""Trestle partial-object-validate command service.

This module implements direct validation of an OSCAL object held in a file,
including list objects.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestlePartialObjectValidateInput(BaseModel):
    """Input model for trestle partial-object-validate command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    file: str = Field(..., description="Path of the file to validate")
    element: str = Field(
        ...,
        description=(
            "Path of the element in the OSCAL model the file holds, e.g. "
            "'catalog.metadata'. The file's top-level key must be the last part "
            "of this path."
        ),
    )
    no_validators: bool = Field(
        default=False,
        description="Only perform the most basic validation of the file",
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_partial_object_validate(
    params: TrestlePartialObjectValidateInput,
) -> str:
    """Validate a single OSCAL object held in a file, including list objects.

    This validates a fragment rather than a whole model: the file must contain
    the object itself at its top level, which is the shape `trestle_split`
    produces. Pointing it at a complete model and naming an inner element fails,
    because the file's top-level key is then the model, not the element.

    Use it after hand-editing a split piece, to find the problem in that piece
    before merging it back and validating the whole model.

    Args:
        params (TrestlePartialObjectValidateInput): Input parameters with:
            - file (str): File holding the object (required)
            - element (str): Element path the file holds (required)
            - no_validators (bool): Basic validation only (default: false)
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Check the metadata file I just split out is still valid"
          file="catalogs/mycat/catalog/metadata.json", element="catalog.metadata"
        - Don't use when: You have a whole OSCAL document; use `trestle_validate`.
    """
    args = [
        "partial-object-validate",
        "--file",
        params.file,
        "--element",
        params.element,
    ]

    if params.no_validators:
        args.append("--no-validators")
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        return (
            f"✅ Partial object is valid\n\n"
            f"File: {params.file}\nElement: {params.element}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return (
            f"❌ Partial object validation failed\n\n"
            f"File: {params.file}\nElement: {params.element}\nError: {error}"
        )
