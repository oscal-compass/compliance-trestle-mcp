"""Trestle task csv-to-oscal-mc command service.

This module implements conversion from CSV to an OSCAL mapping-collection.
"""

import configparser
import tempfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import LONG_TIMEOUT, run_trestle_command


class TrestleTaskCsvToOscalMcInput(BaseModel):
    """Input model for trestle task csv-to-oscal-mc command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(..., description="The mapping collection title (required)")
    version: str = Field(..., description="The mapping collection version (required)")
    csv_file: str = Field(
        ...,
        description=(
            "Path to the CSV file. "
            "1st row: column headings; 2nd row: column descriptions; 3rd row+: data. "
            "Required columns: $$Source_Resource, $$Target_Resource, "
            "$$Map_Source_Id_Ref_List, $$Map_Target_Id_Ref_List, $$Map_Relationship. "
            "Optional columns: $$Map_Confidence_Score, $$Map_Coverage. "
            "Any further column becomes a property on each map entry."
        ),
    )
    output_dir: str = Field(
        ...,
        description=(
            "Path of the output directory for the synthesized "
            "mapping-collection.json (required)"
        ),
    )
    output_overwrite: bool = Field(
        default=True,
        description="Replace existing output when true (default: true)",
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_task_csv_to_oscal_mc(params: TrestleTaskCsvToOscalMcInput) -> str:
    """Convert a CSV file to an OSCAL mapping-collection JSON file.

    This tool runs the trestle task csv-to-oscal-mc command, which reads a
    specially formatted CSV of control-to-control correspondences and produces
    mapping-collection.json — the OSCAL model for "control X over here means the
    same thing as controls Y and Z over there".

    The CSV must have:
    - Row 1: column headings
    - Row 2: column descriptions
    - Row 3+: data rows

    Required CSV columns:
    - $$Source_Resource, $$Target_Resource: for each side, a path to a catalog
      JSON file or an href to a profile. Both sides are loaded and every id in
      the ref lists is looked up in them, so a typo in a control id fails the
      run rather than producing a dangling mapping.
    - $$Map_Source_Id_Ref_List, $$Map_Target_Id_Ref_List: whitespace-separated
      control ids, or statement ids such as `ac-1_smt.a`. Several ids on one
      side are what makes a mapping many-to-many.
    - $$Map_Relationship: the relationship type, as an NCName token. The
      conventional values are the NIST IR 8477 section 4.3 set-theory
      relationships — `equivalent`, `subset-of`, `superset-of`,
      `intersects-with`, `no-relationship` — but trestle does not restrict the
      vocabulary. Leave the cell empty to declare a control unmapped: it is then
      recorded in the gap summary instead of producing a map entry.

    Optional CSV columns:
    - $$Map_Confidence_Score, $$Map_Coverage: percentages expressed in the range
      0 to 1, not 0 to 100. A value of 80 is silently dropped with a
      "Percentage value out of range" warning and the map entry is written
      without it; write 0.8.

    Resource paths in the CSV are resolved relative to the trestle process's
    working directory, which is `trestle_root` when you pass one and wherever
    the server was started when you do not. Pass `trestle_root`, or use absolute
    paths, so the CSV does not depend on how the server was launched.

    Args:
        params (TrestleTaskCsvToOscalMcInput): Input parameters with:
            - title (str): Mapping collection title (required)
            - version (str): Mapping collection version (required)
            - csv_file (str): Path to the input CSV file (required)
            - output_dir (str): Output directory for mapping-collection.json (required)
            - output_overwrite (bool): Overwrite existing output (default: true)
            - trestle_root (Optional[str]): Trestle workspace root path (optional)
            - verbose (bool): Display verbose output (optional)

    Returns:
        str: Success or error message with the output file location

    Examples:
        - Use when: "Map our internal control set onto NIST SP 800-53"
        - Use when: "Produce an OSCAL mapping collection from this crosswalk
          spreadsheet"
        - Don't use when: You want a component definition out of a CSV; use
          `trestle_task_csv_to_oscal_cd`.
        - Don't use when: The CSV is missing a required column, or names control
          ids that are not in the source or target resource.
    """
    config = configparser.ConfigParser()
    section = "task.csv-to-oscal-mc"
    config[section] = {
        "title": params.title,
        "version": params.version,
        "csv-file": params.csv_file,
        "output-dir": params.output_dir,
        "output-overwrite": str(params.output_overwrite).lower(),
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ini", delete=False, prefix="trestle_csv_to_mc_"
    ) as tmp:
        config.write(tmp)
        config_path = tmp.name

    try:
        args = ["task", "csv-to-oscal-mc", "--config", config_path]

        if params.trestle_root:
            args.extend(["--trestle-root", params.trestle_root])
        if params.verbose:
            args.append("--verbose")

        # Both sides of every mapping are loaded, and a profile href on either
        # side is fully resolved, so this is as slow as profile resolution.
        result = run_trestle_command(args, timeout=LONG_TIMEOUT)
    finally:
        Path(config_path).unlink(missing_ok=True)

    if result["success"]:
        output = result["stdout"].strip()
        return (
            f"✅ CSV converted to OSCAL mapping collection successfully\n\n"
            f"Output directory: {params.output_dir}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return (
            f"❌ Failed to convert CSV to OSCAL mapping collection\n\n"
            f"CSV file: {params.csv_file}\nError: {error}"
        )
