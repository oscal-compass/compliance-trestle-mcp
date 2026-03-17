#!/usr/bin/env python3
"""Unit tests for services/task/csv_to_oscal_cd.py."""

import configparser
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from trestle_mcp.services.task.csv_to_oscal_cd import (
    TrestleTaskCsvToOscalCdInput,
    trestle_task_csv_to_oscal_cd,
)

MODULE_NAME = "trestle_mcp.services.task.csv_to_oscal_cd"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"


def _parse_config_from_call(mock_run) -> configparser.ConfigParser:
    """Helper: read the temp config file that was passed to run_trestle_command."""
    args = mock_run.call_args[0][0]
    config_path = args[args.index("--config") + 1]
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


class TestTrestleTaskCsvToOscalCd:
    """Test suite for trestle_task_csv_to_oscal_cd tool."""

    def _base_params(self, **kwargs):
        defaults = {
            "title": "My Component",
            "version": "1.0",
            "csv_file": "/data/input.csv",
            "output_dir": "/data/output",
        }
        defaults.update(kwargs)
        return TrestleTaskCsvToOscalCdInput(**defaults)

    def _success_result(self, stdout="Done"):
        return {"success": True, "stdout": stdout, "stderr": "", "returncode": 0}

    def _failure_result(self, stderr="Error occurred"):
        return {"success": False, "stdout": "", "stderr": stderr, "returncode": 1}

    @pytest.mark.asyncio
    async def test_success_required_params_only(self):
        """Test with only required parameters."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = self._success_result("component-definition.json written")
            result = await trestle_task_csv_to_oscal_cd(self._base_params())

        assert "✅" in result
        assert "successfully" in result
        assert "/data/output" in result

        args = mock_run.call_args[0][0]
        assert args[:3] == ["task", "csv-to-oscal-cd", "--config"]
        assert "--verbose" not in args
        assert "--trestle-root" not in args

    @pytest.mark.asyncio
    async def test_config_file_contents(self):
        """Test that the generated config file has correct contents."""
        captured_config_path = []

        def capture_and_succeed(args):
            captured_config_path.append(args[args.index("--config") + 1])
            return self._success_result()

        with patch(MOCK_RUN_MODULE, side_effect=capture_and_succeed):
            await trestle_task_csv_to_oscal_cd(self._base_params())

        # Config file should be deleted after the call
        assert not Path(captured_config_path[0]).exists()

    @pytest.mark.asyncio
    async def test_config_file_required_fields(self):
        """Test that required config fields are written correctly."""
        written_configs = []

        def capture(args):
            config_path = args[args.index("--config") + 1]
            cfg = configparser.ConfigParser()
            cfg.read(config_path)
            written_configs.append(dict(cfg["task.csv-to-oscal-cd"]))
            return self._success_result()

        with patch(MOCK_RUN_MODULE, side_effect=capture):
            await trestle_task_csv_to_oscal_cd(self._base_params())

        section = written_configs[0]
        assert section["title"] == "My Component"
        assert section["version"] == "1.0"
        assert section["csv-file"] == "/data/input.csv"
        assert section["output-dir"] == "/data/output"
        assert section["output-overwrite"] == "true"
        assert section["validate-controls"] == "off"

    @pytest.mark.asyncio
    async def test_optional_component_definition(self):
        """Test with optional component_definition path."""
        written_configs = []

        def capture(args):
            config_path = args[args.index("--config") + 1]
            cfg = configparser.ConfigParser()
            cfg.read(config_path)
            written_configs.append(dict(cfg["task.csv-to-oscal-cd"]))
            return self._success_result()

        with patch(MOCK_RUN_MODULE, side_effect=capture):
            await trestle_task_csv_to_oscal_cd(
                self._base_params(component_definition="/existing/cd.json")
            )

        assert written_configs[0]["component-definition"] == "/existing/cd.json"

    @pytest.mark.asyncio
    async def test_output_overwrite_false(self):
        """Test with output_overwrite=False."""
        written_configs = []

        def capture(args):
            config_path = args[args.index("--config") + 1]
            cfg = configparser.ConfigParser()
            cfg.read(config_path)
            written_configs.append(dict(cfg["task.csv-to-oscal-cd"]))
            return self._success_result()

        with patch(MOCK_RUN_MODULE, side_effect=capture):
            await trestle_task_csv_to_oscal_cd(self._base_params(output_overwrite=False))

        assert written_configs[0]["output-overwrite"] == "false"

    @pytest.mark.asyncio
    async def test_validate_controls_on(self):
        """Test with validate_controls='on'."""
        written_configs = []

        def capture(args):
            config_path = args[args.index("--config") + 1]
            cfg = configparser.ConfigParser()
            cfg.read(config_path)
            written_configs.append(dict(cfg["task.csv-to-oscal-cd"]))
            return self._success_result()

        with patch(MOCK_RUN_MODULE, side_effect=capture):
            await trestle_task_csv_to_oscal_cd(
                self._base_params(validate_controls="on")
            )

        assert written_configs[0]["validate-controls"] == "on"

    @pytest.mark.asyncio
    async def test_class_column_mappings(self):
        """Test with class_column_mappings."""
        written_configs = []

        def capture(args):
            config_path = args[args.index("--config") + 1]
            cfg = configparser.ConfigParser()
            cfg.read(config_path)
            written_configs.append(dict(cfg["task.csv-to-oscal-cd"]))
            return self._success_result()

        with patch(MOCK_RUN_MODULE, side_effect=capture):
            await trestle_task_csv_to_oscal_cd(
                self._base_params(class_column_mappings={"Rule_Id": "scc_class"})
            )

        assert written_configs[0]["class.rule_id"] == "scc_class"

    @pytest.mark.asyncio
    async def test_trestle_root_and_verbose(self):
        """Test with trestle_root and verbose flags."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = self._success_result()
            await trestle_task_csv_to_oscal_cd(
                self._base_params(trestle_root="/workspace", verbose=True)
            )

        args = mock_run.call_args[0][0]
        assert "--trestle-root" in args
        assert "/workspace" in args
        assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_failure_returns_error_message(self):
        """Test that command failure returns an error message."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = self._failure_result("Missing required column $$Rule_Id")
            result = await trestle_task_csv_to_oscal_cd(self._base_params())

        assert "❌" in result
        assert "Failed" in result
        assert "Missing required column" in result
        assert "/data/input.csv" in result

    @pytest.mark.asyncio
    async def test_config_file_cleaned_up_on_success(self):
        """Test that the temp config file is deleted after a successful run."""
        captured_path = []

        def capture(args):
            captured_path.append(args[args.index("--config") + 1])
            return self._success_result()

        with patch(MOCK_RUN_MODULE, side_effect=capture):
            await trestle_task_csv_to_oscal_cd(self._base_params())

        assert not Path(captured_path[0]).exists()

    @pytest.mark.asyncio
    async def test_config_file_cleaned_up_on_failure(self):
        """Test that the temp config file is deleted even when the command fails."""
        captured_path = []

        def capture(args):
            captured_path.append(args[args.index("--config") + 1])
            return self._failure_result()

        with patch(MOCK_RUN_MODULE, side_effect=capture):
            await trestle_task_csv_to_oscal_cd(self._base_params())

        assert not Path(captured_path[0]).exists()
