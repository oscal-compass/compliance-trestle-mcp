"""Trestle href command service.

This module implements inspection and modification of the import hrefs of a
profile in the trestle workspace.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import command_output, run_trestle_command


class TrestleHrefInput(BaseModel):
    """Input model for trestle href command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ..., description="Name of the trestle profile to inspect or modify"
    )
    href: Optional[str] = Field(
        default=None,
        description=(
            "New href, of the form 'trestle://catalogs/mycat/catalog.json'. "
            "Omit it to list the profile's current imports instead of changing one."
        ),
    )
    item: Optional[int] = Field(
        default=None,
        description=(
            "Index of the import to modify, as shown by a listing run. "
            "Defaults to 0, the first import."
        ),
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_href(params: TrestleHrefInput) -> str:
    """List or change the import hrefs of a profile in the trestle workspace.

    Call it with only `name` to list the profile's imports and their indexes.
    Call it with `href` (and `item` if the profile imports more than one thing)
    to repoint an import.

    This exists because an imported profile usually references its catalog at
    wherever it came from, which is not where the catalog now lives in the
    workspace. Until the href points at the workspace copy,
    `trestle_author_profile_resolve` and `trestle_author_ssp_generate` either
    fail or quietly resolve against the remote original rather than the catalog
    you imported.

    Args:
        params (TrestleHrefInput): Input parameters with:
            - name (str): Profile name (required)
            - href (Optional[str]): New href; omit to list current imports
            - item (Optional[int]): Index of the import to modify
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: The import list, or the result of the change

    Examples:
        - Use when: "What does this profile import?"
          name="myprofile"
        - Use when: "Point this profile at the catalog in my workspace"
          name="myprofile", href="trestle://catalogs/mycat/catalog.json"
        - Don't use when: The model is not a profile — only profiles have
          imports to repoint.
    """
    args = ["href", "--name", params.name]

    if params.href:
        args.extend(["--href", params.href])
    if params.item is not None:
        args.extend(["--item", str(params.item)])
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = await run_trestle_command(args)

    if result["success"]:
        output = command_output(result)
        action = "Profile href updated" if params.href else "Profile imports listed"
        return f"✅ {action}\n\nProfile: {params.name}\n\n{output}"
    else:
        error = result["stderr"].strip()
        return f"❌ Failed to read or change profile href\n\nProfile: {params.name}\nError: {error}"
