#!/usr/bin/env python3
"""Unit tests for services/task/csv_to_oscal_mc.py."""

import configparser
from pathlib import Path
from unittest.mock import patch

import pytest

from trestle_mcp.services.task import csv_to_oscal_mc

MOCK_RUN_MODULE = "trestle_mcp.services.task.csv_to_oscal_mc.run_trestle_command"
SECTION = "task.csv-to-oscal-mc"


def _parse_config_from_call(mock_run) -> configparser.ConfigParser:
    """Read back the INI file the service wrote for the task."""
    args = mock_run.call_args[0][0]
    config_path = args[args.index("--config") + 1]
    parser = configparser.ConfigParser()
    parser.read(config_path)
    return parser


class TestTrestleTaskCsvToOscalMc:
    """Test suite for trestle_task_csv_to_oscal_mc tool."""

    def _base_params(self, **kwargs):
        defaults = {
            "title": "My Crosswalk",
            "version": "1.0.0",
            "csv_file": "/tmp/mapping.csv",
            "output_dir": "/tmp/out",
        }
        defaults.update(kwargs)
        return csv_to_oscal_mc.TrestleTaskCsvToOscalMcInput(**defaults)

    @pytest.mark.asyncio
    async def test_required_config_keys(self):
        """Test the required keys land in the task's INI section."""
        captured = {}

        def capture(args, **kwargs):
            config_path = args[args.index("--config") + 1]
            parser = configparser.ConfigParser()
            parser.read(config_path)
            captured.update(dict(parser[SECTION]))
            return {"success": True, "stdout": "ok", "stderr": "", "returncode": 0}

        with patch(MOCK_RUN_MODULE, side_effect=capture) as mock_run:
            result = await csv_to_oscal_mc.trestle_task_csv_to_oscal_mc(
                self._base_params()
            )
            assert "✅" in result and "/tmp/out" in result
            args = mock_run.call_args[0][0]
            assert args[:2] == ["task", "csv-to-oscal-mc"]

        assert captured["title"] == "My Crosswalk"
        assert captured["version"] == "1.0.0"
        assert captured["csv-file"] == "/tmp/mapping.csv"
        assert captured["output-dir"] == "/tmp/out"
        assert captured["output-overwrite"] == "true"

    @pytest.mark.asyncio
    async def test_output_overwrite_false(self):
        """Test output_overwrite=False is written as the string 'false'."""
        captured = {}

        def capture(args, **kwargs):
            config_path = args[args.index("--config") + 1]
            parser = configparser.ConfigParser()
            parser.read(config_path)
            captured.update(dict(parser[SECTION]))
            return {"success": True, "stdout": "ok", "stderr": "", "returncode": 0}

        with patch(MOCK_RUN_MODULE, side_effect=capture):
            await csv_to_oscal_mc.trestle_task_csv_to_oscal_mc(
                self._base_params(output_overwrite=False)
            )

        assert captured["output-overwrite"] == "false"

    @pytest.mark.asyncio
    async def test_trestle_root_and_verbose(self):
        """Test the CLI-level options are passed through."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "ok",
                "stderr": "",
                "returncode": 0,
            }
            await csv_to_oscal_mc.trestle_task_csv_to_oscal_mc(
                self._base_params(trestle_root="/ws", verbose=True)
            )
            args = mock_run.call_args[0][0]
            assert args[args.index("--trestle-root") + 1] == "/ws"
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_long_timeout_is_used(self):
        """Test the task is given the long timeout, not the default one."""
        from trestle_mcp.libs.trestle import LONG_TIMEOUT

        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "ok",
                "stderr": "",
                "returncode": 0,
            }
            await csv_to_oscal_mc.trestle_task_csv_to_oscal_mc(self._base_params())
            assert mock_run.call_args[1]["timeout"] == LONG_TIMEOUT

    @pytest.mark.asyncio
    async def test_config_file_cleaned_up(self):
        """Test the temporary INI file is removed after the run."""
        paths = []

        def capture(args, **kwargs):
            paths.append(args[args.index("--config") + 1])
            return {"success": False, "stdout": "", "stderr": "nope", "returncode": 1}

        with patch(MOCK_RUN_MODULE, side_effect=capture):
            result = await csv_to_oscal_mc.trestle_task_csv_to_oscal_mc(
                self._base_params()
            )
            assert "❌" in result and "nope" in result

        assert len(paths) == 1
        assert not Path(paths[0]).exists()
