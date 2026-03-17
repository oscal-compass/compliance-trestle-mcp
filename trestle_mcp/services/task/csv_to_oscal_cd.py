"""Trestle task csv-to-oscal-cd command service.

This module implements conversion from CSV to OSCAL component definition format.
"""

import configparser
import tempfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class ValidateControlsMode(str):
    """Validate controls mode options."""

    ON = "on"
    WARN = "warn"
    OFF = "off"


class TrestleTaskCsvToOscalCdInput(BaseModel):
    """Input model for trestle task csv-to-oscal-cd command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(..., description="The component definition title (required)")
    version: str = Field(..., description="The component definition version (required)")
    csv_file: str = Field(
        ...,
        description=(
            "Path to the CSV file. "
            "1st row: column headings; 2nd row: column descriptions; 3rd row+: data. "
            "Required columns: $$Component_Title, $$Component_Description, $$Component_Type, "
            "$$Rule_Id, $$Rule_Description, $$Profile_Source, $$Profile_Description, "
            "$$Control_Id_List, $$Namespace"
        ),
    )
    output_dir: str = Field(
        ...,
        description="Path of the output directory for synthesized OSCAL .json files (required)",
    )
    component_definition: Optional[str] = Field(
        default=None,
        description="Path to an existing component-definition OSCAL .json file to update (optional)",
    )
    output_overwrite: bool = Field(
        default=True,
        description="Replace existing output when true (default: true)",
    )
    validate_controls: str = Field(
        default="off",
        description="Validate controls exist in resolved profile: 'on', 'warn', or 'off' (default: off)",
    )
    class_column_mappings: Optional[dict] = Field(
        default=None,
        description=(
            "Optional mapping of column names to CSS classes, "
            "e.g. {\"Rule_Id\": \"scc_class\"}. "
            "Each entry becomes class.<column-name> = <value> in the config."
        ),
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_task_csv_to_oscal_cd(params: TrestleTaskCsvToOscalCdInput) -> str:
    """Convert a CSV file to an OSCAL component definition JSON file.

    This tool runs the trestle task csv-to-oscal-cd command, which reads a specially
    formatted CSV file and produces an OSCAL component_definition .json file.

    The CSV must have:
    - Row 1: column headings
    - Row 2: column descriptions
    - Row 3+: data rows

    Required CSV columns:
    - $$Component_Title, $$Component_Description, $$Component_Type
    - $$Rule_Id, $$Rule_Description, $$Profile_Source, $$Profile_Description
    - $$Control_Id_List, $$Namespace

    Args:
        params (TrestleTaskCsvToOscalCdInput): Input parameters with:
            - title (str): Component definition title (required)
            - version (str): Component definition version (required)
            - csv_file (str): Path to the input CSV file (required)
            - output_dir (str): Output directory for OSCAL JSON files (required)
            - component_definition (Optional[str]): Existing component-definition to update (optional)
            - output_overwrite (bool): Overwrite existing output (default: true)
            - validate_controls (str): Control validation mode: on/warn/off (default: off)
            - class_column_mappings (Optional[dict]): Column-to-class mappings (optional)
            - trestle_root (Optional[str]): Trestle workspace root path (optional)
            - verbose (bool): Display verbose output (optional)

    Returns:
        str: Success or error message with output file location

    Examples:
        - Use when: "Convert CSV to OSCAL component definition"
        - Use when: "Generate component_definition.json from a CSV mapping file"
        - Don't use when: Input CSV is missing required columns
    """
    config = configparser.ConfigParser()
    section = "task.csv-to-oscal-cd"
    config[section] = {
        "title": params.title,
        "version": params.version,
        "csv-file": params.csv_file,
        "output-dir": params.output_dir,
        "output-overwrite": str(params.output_overwrite).lower(),
        "validate-controls": params.validate_controls,
    }

    if params.component_definition:
        config[section]["component-definition"] = params.component_definition

    if params.class_column_mappings:
        for col_name, class_value in params.class_column_mappings.items():
            config[section][f"class.{col_name}"] = class_value

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ini", delete=False, prefix="trestle_csv_to_cd_"
    ) as tmp:
        config.write(tmp)
        config_path = tmp.name

    try:
        args = ["task", "csv-to-oscal-cd", "--config", config_path]

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
            f"✅ CSV converted to OSCAL component definition successfully\n\n"
            f"Output directory: {params.output_dir}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return (
            f"❌ Failed to convert CSV to OSCAL component definition\n\n"
            f"CSV file: {params.csv_file}\nError: {error}"
        )
