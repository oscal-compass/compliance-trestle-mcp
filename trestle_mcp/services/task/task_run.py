"""Generic trestle task runner service.

This module implements `trestle task <name> -c <config>` for any task, by
writing the INI configuration the task expects to a temporary file.
"""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.task_config import write_task_config
from trestle_mcp.libs.trestle import LONG_TIMEOUT, command_output, run_trestle_command


class TrestleTaskRunInput(BaseModel):
    """Input model for running an arbitrary trestle task."""

    model_config = ConfigDict(str_strip_whitespace=True)

    task: str = Field(
        ...,
        # The name lands in a positional slot of `trestle task <name>`, so a
        # value starting with "-" is read as a flag instead: `task="--help"`
        # makes trestle print its usage and exit 0, which this service would
        # report as a successful run of a task that never ran. Every real task
        # name is a lowercase hyphenated word, so pin that shape here and fail
        # before the subprocess starts.
        pattern=r"^[a-z0-9][a-z0-9-]*$",
        description=(
            "Name of the task to run, as reported by trestle_task_list, "
            "e.g. 'xlsx-to-oscal-profile'. Lowercase letters, digits and "
            "hyphens only."
        ),
    )
    config: dict[str, str] = Field(
        ...,
        description=(
            "Configuration keys for the task, exactly as named in its own help "
            "text (hyphenated, not underscored), e.g. "
            '{"title": "...", "version": "1.0", "csv-file": "/path/in.csv", '
            '"output-dir": "/path/out"}. Written to a temporary INI file under '
            "[task.<task>]."
        ),
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_task_run(params: TrestleTaskRunInput) -> str:
    """Run any trestle task from a configuration dictionary.

    Every trestle task is driven by an INI file with one `[task.<name>]` section.
    This tool writes that file for you from `config` and removes it afterwards,
    so any task the installed trestle provides can be run without this server
    having to know about it — including tasks added in a later trestle release.

    Get the task names from `trestle_task_list`, and the exact configuration keys
    from `trestle_task_list` with a `task` argument. Use the hyphenated key names
    the task's own help prints; an unrecognised key is ignored silently, and a
    missing required key fails the run.

    Prefer the typed tools where they exist — `trestle_task_csv_to_oscal_cd`,
    `trestle_task_csv_to_oscal_mc` and `trestle_task_xlsx_to_oscal_poam` validate
    their arguments and document the input format, which this tool cannot do for
    an arbitrary task.

    Args:
        params (TrestleTaskRunInput): Input parameters with:
            - task (str): Task name (required)
            - config (dict[str, str]): INI keys for the task's section (required)
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Run the oscal-catalog-to-csv task on this catalog"
          task="oscal-catalog-to-csv",
          config={"catalog-file": "/ws/catalogs/mycat/catalog.json",
                  "output-dir": "/tmp/out"}
        - Use when: A task has no typed tool here yet.
        - Don't use when: A typed tool covers the task — use it instead.
    """
    config_path = write_task_config(
        f"task.{params.task}", dict(params.config), "trestle_task_"
    )

    try:
        args = ["task", params.task, "--config", config_path]

        if params.trestle_root:
            args.extend(["--trestle-root", params.trestle_root])
        if params.verbose:
            args.append("--verbose")

        # Tasks read spreadsheets and can resolve profiles; none of that fits in
        # the default timeout.
        result = await run_trestle_command(args, timeout=LONG_TIMEOUT)
    finally:
        Path(config_path).unlink(missing_ok=True)

    if result["success"]:
        # `command_output` already falls back to stderr when stdout is empty,
        # which is the case a task that only logs used to need. Keeping an
        # `or result["stderr"]` after it was dead code: the helper returns a
        # non-empty warning string whenever stderr has anything, and when both
        # streams are empty the fallback is empty too.
        output = command_output(result)
        return (
            f"✅ Trestle task completed successfully\n\nTask: {params.task}\n\n{output}"
        )
    else:
        error = result["stderr"].strip()
        return f"❌ Trestle task failed\n\nTask: {params.task}\nError: {error}"
