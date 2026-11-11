#!/usr/bin/env python3
"""Unit tests for services/task/task_run.py."""

import configparser
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from trestle_mcp.libs.trestle import LONG_TIMEOUT
from trestle_mcp.services.task import task_run

MOCK_RUN_MODULE = "trestle_mcp.services.task.task_run.run_trestle_command"


class TestTrestleTaskRun:
    """Test suite for trestle_task_run tool."""

    @pytest.mark.asyncio
    async def test_config_is_written_under_the_task_section(self):
        """Test the config dict becomes a [task.<name>] INI section."""
        captured = {}
        sections = []

        def capture(args, **kwargs):
            config_path = args[args.index("--config") + 1]
            parser = configparser.ConfigParser()
            parser.read(config_path)
            sections.extend(parser.sections())
            captured.update(dict(parser["task.oscal-catalog-to-csv"]))
            return {"success": True, "stdout": "done", "stderr": "", "returncode": 0}

        with patch(MOCK_RUN_MODULE, side_effect=capture) as mock_run:
            params = task_run.TrestleTaskRunInput(
                task="oscal-catalog-to-csv",
                config={
                    "catalog-file": "/ws/catalogs/mycat/catalog.json",
                    "output-dir": "/tmp/out",
                },
            )
            result = await task_run.trestle_task_run(params)
            assert "✅" in result and "oscal-catalog-to-csv" in result
            args = mock_run.call_args[0][0]
            assert args[:2] == ["task", "oscal-catalog-to-csv"]
            assert mock_run.call_args[1]["timeout"] == LONG_TIMEOUT

        assert sections == ["task.oscal-catalog-to-csv"]
        assert captured["catalog-file"] == "/ws/catalogs/mycat/catalog.json"
        assert captured["output-dir"] == "/tmp/out"

    @pytest.mark.asyncio
    async def test_trestle_root_and_verbose(self):
        """Test the CLI-level options are passed through."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "done",
                "stderr": "",
                "returncode": 0,
            }
            params = task_run.TrestleTaskRunInput(
                task="base", config={"k": "v"}, trestle_root="/ws", verbose=True
            )
            await task_run.trestle_task_run(params)
            args = mock_run.call_args[0][0]
            assert args[args.index("--trestle-root") + 1] == "/ws"
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_config_file_cleaned_up_on_failure(self):
        """Test the temporary INI file is removed even when the task fails."""
        paths = []

        def capture(args, **kwargs):
            paths.append(args[args.index("--config") + 1])
            return {
                "success": False,
                "stdout": "",
                "stderr": 'config missing "title"',
                "returncode": 1,
            }

        with patch(MOCK_RUN_MODULE, side_effect=capture):
            params = task_run.TrestleTaskRunInput(task="csv-to-oscal-cd", config={})
            result = await task_run.trestle_task_run(params)
            assert "❌" in result and 'config missing "title"' in result

        assert len(paths) == 1
        assert not Path(paths[0]).exists()


class TestTaskNameValidation:
    """Test suite for the shape required of a task name.

    The name lands in a positional slot of `trestle task <name>`, so a value
    starting with "-" is read as a flag instead. `trestle task --help` prints
    usage and exits 0, which the success check would report as a task that ran
    when nothing did. The name is validated before the subprocess starts.
    """

    @pytest.mark.parametrize(
        "name",
        [
            "csv-to-oscal-cd",
            "csv-to-oscal-mc",
            "xlsx-to-oscal-poam",
            "xlsx-to-oscal-profile",
            "oscal-catalog-to-csv",
            "aws-config-result-to-oscal-ar",
            "ocp4-cis-profile-to-oscal-catalog",
            "base",
            "pass-fail",
        ],
    )
    def test_real_task_names_are_accepted(self, name):
        """Test every task the installed trestle ships still validates."""
        assert task_run.TrestleTaskRunInput(task=name, config={}).task == name

    @pytest.mark.parametrize(
        "name",
        [
            "--help",
            "-h",
            "--list",
            "-l",
            "--config",
            "../../etc/passwd",
            "csv to oscal cd",
            "csv_to_oscal_cd",
            "CSV-TO-OSCAL-CD",
            "",
        ],
    )
    def test_names_that_are_not_task_names_are_rejected(self, name):
        """Test a flag, a path or a wrong-cased name fails validation."""
        with pytest.raises(ValidationError):
            task_run.TrestleTaskRunInput(task=name, config={})

    @pytest.mark.asyncio
    async def test_a_flag_like_name_never_reaches_the_cli(self):
        """Test validation happens before anything is run.

        Without this, `task="--help"` returned "✅ completed successfully" with
        trestle's usage text as the output.
        """
        with patch(MOCK_RUN_MODULE) as mock_run:
            with pytest.raises(ValidationError):
                task_run.TrestleTaskRunInput(task="--help", config={})
            mock_run.assert_not_called()
