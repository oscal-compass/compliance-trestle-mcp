#!/usr/bin/env python3
"""Unit tests for services/task/xlsx_to_oscal_poam.py."""

import configparser
from pathlib import Path
from unittest.mock import patch

import pytest

from trestle_mcp.services.task.xlsx_to_oscal_poam import (
    TrestleTaskXlsxToOscalPoamInput,
    trestle_task_xlsx_to_oscal_poam,
)

MODULE_NAME = "trestle_mcp.services.task.xlsx_to_oscal_poam"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"
SECTION = "task.xlsx-to-oscal-poam"


class TestTrestleTaskXlsxToOscalPoam:
    """Test suite for trestle_task_xlsx_to_oscal_poam tool."""

    def _base_params(self, **kwargs):
        defaults = {
            "title": "My POA&M",
            "version": "1.0",
            "xlsx_file": "/data/poam.xlsx",
            "output_dir": "/data/output",
        }
        defaults.update(kwargs)
        return TrestleTaskXlsxToOscalPoamInput(**defaults)

    def _success_result(self, stdout="Created POAM with 2 items"):
        return {"success": True, "stdout": stdout, "stderr": "", "returncode": 0}

    def _failure_result(self, stderr="Error occurred"):
        return {"success": False, "stdout": "", "stderr": stderr, "returncode": 1}

    def _capture_section(self, written):
        def capture(args):
            config_path = args[args.index("--config") + 1]
            cfg = configparser.ConfigParser()
            cfg.read(config_path)
            written.append(dict(cfg[SECTION]))
            return self._success_result()

        return capture

    @pytest.mark.asyncio
    async def test_success_required_params_only(self):
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = self._success_result()
            result = await trestle_task_xlsx_to_oscal_poam(self._base_params())

        assert "✅" in result
        assert "successfully" in result
        assert "/data/output" in result

        args = mock_run.call_args[0][0]
        assert args[:3] == ["task", "xlsx-to-oscal-poam", "--config"]
        assert "--verbose" not in args
        assert "--trestle-root" not in args

    @pytest.mark.asyncio
    async def test_config_required_fields(self):
        written = []
        with patch(MOCK_RUN_MODULE, side_effect=self._capture_section(written)):
            await trestle_task_xlsx_to_oscal_poam(self._base_params())

        section = written[0]
        assert section["title"] == "My POA&M"
        assert section["version"] == "1.0"
        assert section["xlsx-file"] == "/data/poam.xlsx"
        assert section["output-dir"] == "/data/output"
        assert section["output-overwrite"] == "true"
        assert section["validate-required-fields"] == "warn"
        assert section["quiet"] == "false"
        # optional keys omitted unless provided
        assert "work-sheet-name" not in section
        assert "system-id" not in section

    @pytest.mark.asyncio
    async def test_optional_worksheet_and_system_id(self):
        written = []
        with patch(MOCK_RUN_MODULE, side_effect=self._capture_section(written)):
            await trestle_task_xlsx_to_oscal_poam(
                self._base_params(
                    work_sheet_name="Closed POA&M Items", system_id="my-system"
                )
            )

        assert written[0]["work-sheet-name"] == "Closed POA&M Items"
        assert written[0]["system-id"] == "my-system"

    @pytest.mark.asyncio
    async def test_output_overwrite_false(self):
        written = []
        with patch(MOCK_RUN_MODULE, side_effect=self._capture_section(written)):
            await trestle_task_xlsx_to_oscal_poam(
                self._base_params(output_overwrite=False)
            )
        assert written[0]["output-overwrite"] == "false"

    @pytest.mark.asyncio
    async def test_validate_required_fields_and_quiet(self):
        written = []
        with patch(MOCK_RUN_MODULE, side_effect=self._capture_section(written)):
            await trestle_task_xlsx_to_oscal_poam(
                self._base_params(validate_required_fields="on", quiet=True)
            )
        assert written[0]["validate-required-fields"] == "on"
        assert written[0]["quiet"] == "true"

    @pytest.mark.asyncio
    async def test_trestle_root_and_verbose(self):
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = self._success_result()
            await trestle_task_xlsx_to_oscal_poam(
                self._base_params(trestle_root="/workspace", verbose=True)
            )

        args = mock_run.call_args[0][0]
        assert "--trestle-root" in args
        assert "/workspace" in args
        assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_config_file_deleted_after_call(self):
        captured = []

        def capture_and_succeed(args):
            captured.append(args[args.index("--config") + 1])
            return self._success_result()

        with patch(MOCK_RUN_MODULE, side_effect=capture_and_succeed):
            await trestle_task_xlsx_to_oscal_poam(self._base_params())

        assert not Path(captured[0]).exists()

    @pytest.mark.asyncio
    async def test_failure_message(self):
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = self._failure_result("bad worksheet")
            result = await trestle_task_xlsx_to_oscal_poam(self._base_params())

        assert "❌" in result
        assert "/data/poam.xlsx" in result
        assert "bad worksheet" in result
