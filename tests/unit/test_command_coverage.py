#!/usr/bin/env python3
"""Tests that the trestle command surface is either covered or documented.

The README and the development guide both claim a complete picture: the tools cover the
commands an agent should drive, and the guide's "Commands deliberately not
covered" section explains the rest. Nothing enforced that, so a command could be
neither — `trestle remove` was, for a while.

These tests close the gap from both ends. Coverage is derived from the command
line each tool actually builds, not from a list maintained by hand, so adding a
tool updates the test's idea of what is covered automatically. The commands the
installed trestle offers come from its own CLI classes, so a trestle release
that adds a command fails this test until someone decides which side it belongs
on.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import re
from pathlib import Path
from unittest.mock import patch

import pytest
import trestle.cli
from trestle.core.commands.author.command import AuthorCmd

from trestle_mcp import tools

REPO_ROOT = Path(__file__).resolve().parents[2]
GUIDE = REPO_ROOT / "docs" / "development" / "README.md"

#: Repo-relative path, for failure messages: GUIDE.name alone is "README.md",
#: which reads as the root README rather than the development guide.
GUIDE_PATH = GUIDE.relative_to(REPO_ROOT).as_posix()

#: The one section that accounts for a command having no tool of its own.
#: "Commands behind an explicit opt-in" deliberately does NOT appear here: the
#: commands it describes do have tools, so letting it exempt them would mean a
#: deleted tool still looked accounted for.
EXEMPTING_HEADINGS = ("Commands deliberately not covered",)

#: The section that has to describe each opt-in tool.
OPT_IN_HEADING = "Commands behind an explicit opt-in"

#: Guide sections these tests read, all of which must exist and name something.
REQUIRED_HEADINGS = (*EXEMPTING_HEADINGS, OPT_IN_HEADING)

#: `trestle task <name>` wrappers are covered generically by trestle_task_run,
#: and the individual task set belongs to the installed trestle, not to us.
GENERIC_TASK_RUNNER = "trestle_task_run"


def _argv_of(spec: tools.ToolSpec) -> list[str] | None:
    """The command line a tool builds, or None if it never shells out.

    Every field is populated so that optional arguments appear too. Only the
    leading command path is read, so the values mostly do not matter -- the
    exception is a path a service checks before shelling out, which has to
    exist or the handler returns an error instead of building a command line.
    """
    module = __import__(spec.handler.__module__, fromlist=["run_trestle_command"])
    if not hasattr(module, "run_trestle_command"):
        return None

    # `trestle_merge` returns early when `model_dir` is not a directory, so the
    # dummy has to be a real one. Anything else that grows a pre-flight check
    # on a path will show up here as a None argv and a coverage failure naming
    # the command, which is the right way to find out.
    workspace = tempfile.mkdtemp()
    model_dir = os.path.join(workspace, "models", "sample")
    os.makedirs(model_dir, exist_ok=True)

    def value(annotation: object) -> object:
        text = str(annotation)
        if "bool" in text:
            return True
        if "int" in text:
            return 1
        if "dict" in text:
            return {"title": "t"}
        if "OscalModelType" in text:
            return "catalog"
        if "FileExtension" in text:
            return "json"
        if "Mode" in text:
            return "local"
        # Task names are validated against a real-task-name shape.
        return "csv-to-oscal-cd"

    fields = spec.input_model.model_fields
    supplied = {name: value(field.annotation) for name, field in fields.items()}
    if "model_dir" in supplied:
        supplied["model_dir"] = model_dir
    if "trestle_root" in supplied:
        supplied["trestle_root"] = workspace
    params = spec.input_model(**supplied)
    with patch(f"{module.__name__}.run_trestle_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "",
            "stderr": "",
            "returncode": 0,
        }
        asyncio.run(spec.handler(params))
        return list(mock_run.call_args[0][0])


def covered_commands() -> set[str]:
    """Command paths the tools invoke, e.g. {"split", "author ssp-generate"}."""
    covered: set[str] = set()
    for spec in tools.TOOL_SPECS:
        argv = _argv_of(spec)
        if argv is None:
            continue
        # "author ssp-generate" and "task csv-to-oscal-cd" are two words; every
        # other command is the first token on its own.
        if argv[0] in ("author", "task") and len(argv) > 1:
            covered.add(f"{argv[0]} {argv[1]}")
        else:
            covered.add(argv[0])
    return covered


def exempted_names() -> set[str]:
    """Every backticked name under a heading that accounts for an absent tool."""
    text = GUIDE.read_text()
    exempted: set[str] = set()
    for heading in EXEMPTING_HEADINGS:
        match = re.search(
            rf"^#+\s*{re.escape(heading)}\s*$(.*?)(?=^#+\s|\Z)",
            text,
            re.M | re.S,
        )
        assert match, f"{GUIDE_PATH} has no '{heading}' section"
        for quoted in re.findall(r"`([^`]+)`", match.group(1)):
            # Strip a leading "trestle " so `trestle validate` matches "validate".
            exempted.add(re.sub(r"^trestle\s+", "", quoted).strip())
    return exempted


def installed_commands() -> set[str]:
    """Every command the installed trestle offers, as a command path."""
    commands = set()
    for command in trestle.cli.Trestle.subcommands:
        if command.name == "author":
            commands.update(f"author {sub.name}" for sub in AuthorCmd.subcommands)
        else:
            commands.add(command.name)
    return commands


class TestCommandCoverage:
    """Test suite for the tool table against the installed trestle CLI."""

    def test_every_installed_command_is_covered_or_documented(self):
        """Test no command is silently absent from both the tools and the guide.

        A command that is neither wrapped nor explained is the failure this
        catches: the README claims the picture is complete, so a gap makes the
        README wrong rather than merely incomplete.
        """
        covered = covered_commands()
        exempted = exempted_names()
        unaccounted = set()

        for command in installed_commands():
            if command in covered:
                continue
            # A `task <name>` wrapper is accounted for by the generic runner.
            if command.startswith("task "):
                continue
            if command in exempted:
                continue
            # `author docs` is exempted as `author docs`; also accept the bare
            # subcommand name, which is how some entries are written.
            if command.split()[-1] in exempted:
                continue
            unaccounted.add(command)

        assert not unaccounted, (
            "these trestle commands have no tool and are not listed under "
            f"{EXEMPTING_HEADINGS} in {GUIDE_PATH}: {sorted(unaccounted)}"
        )

    def test_every_tool_maps_to_an_installed_command(self):
        """Test no tool builds a command the installed trestle does not have.

        The mirror of the test above: a renamed or dropped trestle command would
        otherwise only fail at call time, in the client.
        """
        installed = installed_commands()
        unknown = set()
        for command in covered_commands():
            if command in installed:
                continue
            # `task <name>` is a task, not a trestle subcommand.
            if command.startswith("task "):
                continue
            unknown.add(command)
        assert not unknown, f"tools invoke commands trestle does not have: {unknown}"

    def test_remove_is_covered_rather_than_exempted(self):
        """Test the command that prompted this file stays covered.

        `trestle remove` is reachable as an opt-in tool. If it ever goes back to
        having no tool, it has to be written into the guide instead.
        """
        assert "remove" in covered_commands()

    def test_every_opt_in_tool_is_documented(self):
        """Test a tool no group selects is explained where operators will look.

        An opt-in tool is invisible in every group listing, so the guide is the
        only place its existence and its reason are recorded.
        """
        text = GUIDE.read_text()
        match = re.search(
            rf"^#+\s*{re.escape(OPT_IN_HEADING)}\s*$(.*?)(?=^#+\s|\Z)",
            text,
            re.M | re.S,
        )
        assert match, f"missing section: {OPT_IN_HEADING}"
        section = match.group(1)
        for name in tools.OPT_IN_TOOL_NAMES:
            assert name in section, f"{name} is not described under {OPT_IN_HEADING}"

    def test_the_generic_task_runner_exists(self):
        """Test the exemption for individual task wrappers still has a basis."""
        assert GENERIC_TASK_RUNNER in tools.TOOL_SPECS_BY_NAME


class TestGuideSections:
    """Test suite for the guide sections the tests above depend on."""

    @pytest.mark.parametrize("heading", REQUIRED_HEADINGS)
    def test_section_is_present_and_not_empty(self, heading):
        """Test a renamed heading fails loudly instead of exempting nothing."""
        text = GUIDE.read_text()
        match = re.search(
            rf"^#+\s*{re.escape(heading)}\s*$(.*?)(?=^#+\s|\Z)", text, re.M | re.S
        )
        assert match, f"missing section: {heading}"
        assert re.search(r"`[^`]+`", match.group(1)), f"no names under: {heading}"
