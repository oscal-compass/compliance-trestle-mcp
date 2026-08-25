"""Trestle task xlsx-to-oscal-poam command service.

This module implements conversion from a FedRAMP-format XLSX spreadsheet to an
OSCAL Plan of Action and Milestones (POA&M).
"""

import configparser
import tempfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestleTaskXlsxToOscalPoamInput(BaseModel):
    """Input model for trestle task xlsx-to-oscal-poam command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(..., description="The POA&M title (required)")
    version: str = Field(..., description="The POA&M version (required)")
    xlsx_file: str = Field(
        ...,
        description=(
            "Path to the FedRAMP-format .xlsx file. "
            "Row 1: title; rows 2-4: instructions (ignored); row 5: column "
            "headers; row 6+: data. Required columns: 'POAM ID', "
            "'Weakness Name', 'Weakness Description', 'Controls'."
        ),
    )
    output_dir: str = Field(
        ...,
        description=(
            "Path of the output directory for the synthesized OSCAL "
            "plan-of-action-and-milestones.json (required)"
        ),
    )
    work_sheet_name: Optional[str] = Field(
        default=None,
        description="Worksheet to read (default: 'Open POA&M Items')",
    )
    system_id: Optional[str] = Field(
        default=None,
        description="System identifier to record in the POA&M (optional)",
    )
    output_overwrite: bool = Field(
        default=True,
        description="Replace existing output when true (default: true)",
    )
    validate_required_fields: str = Field(
        default="warn",
        description=(
            "Validate that required columns are present/populated: "
            "'on', 'warn', or 'off' (default: warn)"
        ),
    )
    quiet: bool = Field(
        default=False,
        description="Suppress per-item output when true (default: false)",
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_task_xlsx_to_oscal_poam(
    params: TrestleTaskXlsxToOscalPoamInput,
) -> str:
    """Convert a FedRAMP XLSX spreadsheet to an OSCAL POA&M JSON file.

    This tool runs the trestle task xlsx-to-oscal-poam command, which reads a
    FedRAMP-format .xlsx spreadsheet and produces an OSCAL
    plan-of-action-and-milestones .json file. The converter auto-generates the
    observations[] and risks[] and cross-links each poam-item to them with
    deterministic UUIDs.

    This command must run inside a trestle workspace: initialize one first with
    trestle_init and pass its path as trestle_root (or run from within it).

    The spreadsheet must have:
    - Row 1: title
    - Rows 2-4: instructions (ignored)
    - Row 5: column headers
    - Row 6+: data rows

    Required columns:
    - POAM ID, Weakness Name, Weakness Description, Controls

    Args:
        params (TrestleTaskXlsxToOscalPoamInput): Input parameters with:
            - title (str): POA&M title (required)
            - version (str): POA&M version (required)
            - xlsx_file (str): Path to the input .xlsx file (required)
            - output_dir (str): Output directory for the OSCAL JSON (required)
            - work_sheet_name (Optional[str]): Worksheet name (default: 'Open POA&M Items')
            - system_id (Optional[str]): System identifier (optional)
            - output_overwrite (bool): Overwrite existing output (default: true)
            - validate_required_fields (str): Required-field check: on/warn/off (default: warn)
            - quiet (bool): Suppress per-item output (default: false)
            - trestle_root (Optional[str]): Trestle workspace root path (optional)
            - verbose (bool): Display verbose output (optional)

    Returns:
        str: Success or error message with output file location

    Examples:
        - Use when: "Convert this FedRAMP POA&M spreadsheet to OSCAL"
        - Use when: "Generate plan-of-action-and-milestones.json from an xlsx"
        - Don't use when: The input is a CSV, or is missing required columns
    """
    config = configparser.ConfigParser()
    section = "task.xlsx-to-oscal-poam"
    config[section] = {
        "title": params.title,
        "version": params.version,
        "xlsx-file": params.xlsx_file,
        "output-dir": params.output_dir,
        "output-overwrite": str(params.output_overwrite).lower(),
        "validate-required-fields": params.validate_required_fields,
        "quiet": str(params.quiet).lower(),
    }

    if params.work_sheet_name:
        config[section]["work-sheet-name"] = params.work_sheet_name
    if params.system_id:
        config[section]["system-id"] = params.system_id

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ini", delete=False, prefix="trestle_xlsx_to_poam_"
    ) as tmp:
        config.write(tmp)
        config_path = tmp.name

    try:
        args = ["task", "xlsx-to-oscal-poam", "--config", config_path]

        if params.trestle_root:
            args.extend(["--trestle-root", params.trestle_root])
        if params.verbose:
            args.append("--verbose")

        result = run_trestle_command(args)
    finally:
        Path(config_path).unlink(missing_ok=True)

    if result["success"]:
        output = result["stdout"].strip()
        return (
            f"✅ XLSX converted to OSCAL POA&M successfully\n\n"
            f"Output directory: {params.output_dir}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return (
            f"❌ Failed to convert XLSX to OSCAL POA&M\n\n"
            f"XLSX file: {params.xlsx_file}\nError: {error}"
        )
