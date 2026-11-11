"""Trestle merge command service.

This module implements merging split subcomponents back into a trestle model.
"""

import os
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestleMergeInput(BaseModel):
    """Input model for trestle merge command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    element: str = Field(
        ...,
        description=(
            "Path of the element in the OSCAL model(s) to merge, e.g. "
            "'catalog.metadata' or 'catalog.*'. The last element is merged into "
            "the second last, so the path must have at least two parts."
        ),
    )
    model_dir: str = Field(
        ...,
        description=(
            "Directory of the model being merged, e.g. 'catalogs/mycat'. "
            "trestle merge resolves the destination model relative to the "
            "working directory, so this must be the directory that holds the "
            "model file. A relative path is taken from `trestle_root`."
        ),
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_merge(params: TrestleMergeInput) -> str:
    """Merge split subcomponents back into a trestle model.

    This undoes `trestle_split`: the pieces in the model's subdirectory are
    folded back into the single model file and the pieces are removed. Use
    `catalog.*` to merge everything that was split out of a catalog in one go.

    Note `model_dir`. Unlike the other commands, `trestle merge` finds the
    destination model relative to its own working directory and uses
    `--trestle-root` only to resolve model types — so passing a trestle root
    alone is not enough, and this tool runs the command inside `model_dir`.

    Args:
        params (TrestleMergeInput): Input parameters with:
            - element (str): Multi-part element path to merge (required)
            - model_dir (str): Directory holding the model file (required)
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Fold the split metadata back into the catalog"
          element="catalog.metadata", model_dir="catalogs/mycat"
        - Use when: "Merge everything back into one catalog file"
          element="catalog.*", model_dir="catalogs/mycat"
        - Don't use when: A single-part element path is all you have — merge
          needs at least two parts, e.g. 'catalog.groups' not 'groups'.
    """
    args = ["merge", "--element", params.element]

    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    # merge is the one command that needs its own working directory: it
    # resolves the destination model from there, not from --trestle-root. So the
    # root cannot do the resolving here the way it does for every other command
    # -- the relative model_dir has to be joined onto it explicitly.
    model_dir = params.model_dir
    if params.trestle_root and not os.path.isabs(model_dir):
        model_dir = os.path.join(params.trestle_root, model_dir)

    result = await run_trestle_command(args, cwd=model_dir)

    if result["success"]:
        output = result["stdout"].strip()
        return (
            f"✅ Model merged successfully\n\n"
            f"Model: {params.model_dir}\nElement: {params.element}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return (
            f"❌ Failed to merge model\n\n"
            f"Model: {params.model_dir}\nElement: {params.element}\nError: {error}"
        )
