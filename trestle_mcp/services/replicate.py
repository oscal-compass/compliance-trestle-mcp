"""Trestle replicate command service.

This module implements replication of a top level model in the trestle workspace.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.oscal_types import OscalModelType
from trestle_mcp.libs.trestle import run_trestle_command


class TrestleReplicateInput(BaseModel):
    """Input model for trestle replicate command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    model_type: OscalModelType = Field(
        ..., description="Type of the model to replicate"
    )
    name: str = Field(..., description="Name of the model to replicate")
    output: str = Field(..., description="Name of the replicated model")
    regenerate: bool = Field(
        default=False, description="Force generation of new uuids in the model"
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_replicate(params: TrestleReplicateInput) -> str:
    """Replicate a top level model within the trestle workspace.

    This copies an existing model to a new name in the same workspace. It is the
    safe way to start a variant: derive a tailored profile from an imported one,
    or keep a baseline copy before an edit that may not work out.

    Set `regenerate` to give the copy fresh uuids. Without it the copy carries
    the same uuids as the original, which is correct when the copy *is* the same
    document under another name, and wrong as soon as both are published — two
    OSCAL documents with the same uuid are indistinguishable to a consumer.

    Args:
        params (TrestleReplicateInput): Input parameters with:
            - model_type (OscalModelType): Model type to replicate (required)
            - name (str): Source model name (required)
            - output (str): Replicated model name (required)
            - regenerate (bool): Force generation of new uuids (default: false)
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Make a copy of the imported profile I can tailor"
          model_type="profile", name="nist_moderate", output="my_moderate",
          regenerate=True
        - Don't use when: You want the copy to track the original — a profile
          that imports the original is a reference, a replica is a fork.
    """
    # The model type is positional for this command.
    args = ["replicate", params.model_type.value]
    args.extend(["--name", params.name])
    args.extend(["--output", params.output])

    if params.regenerate:
        args.append("--regenerate")
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = run_trestle_command(args)

    if result["success"]:
        output = result["stdout"].strip()
        return (
            f"✅ Model replicated successfully\n\n"
            f"Output: {params.output}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return f"❌ Failed to replicate model\n\nModel: {params.name}\nError: {error}"
