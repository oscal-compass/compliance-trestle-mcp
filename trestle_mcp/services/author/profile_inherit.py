"""Trestle author profile-inherit command service.

This module implements generation of a profile from a parent profile and a
leveraged SSP.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import LONG_TIMEOUT, run_trestle_command


class TrestleAuthorProfileInheritInput(BaseModel):
    """Input model for trestle author profile-inherit command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    ssp: str = Field(
        ..., description="Name of the leveraged ssp model in the trestle workspace"
    )
    profile: str = Field(
        ..., description="Name of the parent profile model in the trestle workspace"
    )
    output: str = Field(..., description="Name of the output generated json Profile")
    version: Optional[str] = Field(
        default=None, description="New version for the generated model"
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_author_profile_inherit(
    params: TrestleAuthorProfileInheritInput,
) -> str:
    """Generate and populate a profile from a parent profile and a leveraged SSP.

    This is the provider/consumer split for a system built on top of another
    system. Given the parent profile (what the consuming system must satisfy) and
    the leveraged SSP (what the underlying system already provides), it writes a
    profile in which the controls the provider satisfies are marked as inherited,
    leaving the consumer's own responsibilities behind.

    The leveraged SSP must already be in the workspace and must carry the
    inheritance information — an SSP assembled without components or exported
    provided/responsibility statements has nothing to inherit from.

    Args:
        params (TrestleAuthorProfileInheritInput): Input parameters with:
            - ssp (str): Leveraged ssp model name (required)
            - profile (str): Parent profile model name (required)
            - output (str): Output json profile name (required)
            - version (Optional[str]): New version for the generated model
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Which of the moderate baseline controls does the platform
          SSP already cover for me?"
          ssp="platform_ssp", profile="nist_moderate", output="my_profile"
        - Don't use when: There is no leveraged system — a plain profile is what
          you want, created with `trestle_create` or imported.
    """
    args = ["author", "profile-inherit"]

    # Required
    args.extend(["--ssp", params.ssp])
    args.extend(["--profile", params.profile])
    args.extend(["--output", params.output])
    # Optional
    if params.version:
        args.extend(["--version", params.version])
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    # Deriving a profile resolves both the parent profile and the leveraged
    # SSP's own profile, so this is profile resolution twice over.
    result = await run_trestle_command(args, timeout=LONG_TIMEOUT)

    if result["success"]:
        output = result["stdout"].strip()
        return (
            f"✅ Inherited profile generated successfully\n\n"
            f"Output: {params.output}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return (
            f"❌ Failed to generate inherited profile\n\n"
            f"Profile: {params.profile}\nLeveraged SSP: {params.ssp}\nError: {error}"
        )
