"""Trestle task listing service.

This module implements `trestle task -l` and `trestle task <name> -i`.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import command_output, run_trestle_command


class TrestleTaskListInput(BaseModel):
    """Input model for listing trestle tasks or describing one."""

    model_config = ConfigDict(str_strip_whitespace=True)

    task: Optional[str] = Field(
        default=None,
        # Positional in `trestle task <name> -i`, so a leading "-" would be read
        # as a flag and `trestle task --help -i` exits 0 with its usage text —
        # reported as a described task that does not exist. Same shape as
        # trestle_task_run's `task`.
        pattern=r"^[a-z0-9][a-z0-9-]*$",
        description=(
            "Name of a single task to describe, e.g. 'csv-to-oscal-cd'. "
            "Lowercase letters, digits and hyphens only. Omit it to list every "
            "available task."
        ),
    )
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_task_list(params: TrestleTaskListInput) -> str:
    """List the available trestle tasks, or describe one task's configuration.

    Call it with no arguments to get the names of every task the installed
    trestle provides. Call it with `task` to get that task's help text, which is
    the authoritative list of the configuration keys it accepts and the CSV or
    XLSX columns it requires — exactly what `trestle_task_run` needs in its
    `config` argument.

    The task set belongs to the installed trestle version, not to this server, so
    listing is the only reliable way to know what is available.

    Both forms need a trestle workspace: run them with `trestle_root` set to an
    initialized workspace, or from inside one.

    Args:
        params (TrestleTaskListInput): Input parameters with:
            - task (Optional[str]): Task to describe; omit to list all tasks
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: The task list or the task's configuration help

    Examples:
        - Use when: "What trestle tasks can I run?"
        - Use when: "What config keys does xlsx-to-oscal-profile need?"
          task="xlsx-to-oscal-profile"
        - Don't use when: You already know the task and its config; go straight
          to `trestle_task_run`.
    """
    args = ["task"]

    if params.task:
        args.extend([params.task, "--info"])
    else:
        args.append("--list")
    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = await run_trestle_command(args)

    # `trestle task` writes both the list and the per-task help through its
    # logger, which goes to stderr, so a successful run can have empty stdout.
    body = command_output(result) or "(no output)"

    if result["success"]:
        subject = f"Task info: {params.task}" if params.task else "Available tasks"
        return f"✅ {subject}\n\n{body}"
    else:
        return f"❌ Failed to list trestle tasks\n\nError: {body}"
