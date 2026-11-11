#!/usr/bin/env python3
"""Unit tests for services/task/task_list.py."""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from trestle_mcp.services.task import task_list

MOCK_RUN_MODULE = "trestle_mcp.services.task.task_list.run_trestle_command"


class TestTrestleTaskList:
    """Test suite for trestle_task_list tool."""

    @pytest.mark.asyncio
    async def test_listing_all_tasks(self):
        """Test the listing form passes --list and no task name."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "",
                "stderr": "Available tasks:\n    csv-to-oscal-cd",
                "returncode": 0,
            }
            result = await task_list.trestle_task_list(task_list.TrestleTaskListInput())
            # trestle logs the list to stderr, so a successful run can have
            # empty stdout and the body must still be reported
            assert "✅" in result and "csv-to-oscal-cd" in result
            assert mock_run.call_args[0][0] == ["task", "--list"]

    @pytest.mark.asyncio
    async def test_describing_one_task(self):
        """Test the info form passes the task name positionally plus --info."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Help information",
                "stderr": "",
                "returncode": 0,
            }
            params = task_list.TrestleTaskListInput(
                task="csv-to-oscal-mc", trestle_root="/ws", verbose=True
            )
            result = await task_list.trestle_task_list(params)
            assert "✅" in result and "csv-to-oscal-mc" in result
            args = mock_run.call_args[0][0]
            assert args[:3] == ["task", "csv-to-oscal-mc", "--info"]
            assert "--list" not in args
            assert args[args.index("--trestle-root") + 1] == "/ws"
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_failure(self):
        """Test the error path, e.g. running outside a trestle workspace."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "Given directory /tmp is not in a valid trestle root directory",
                "returncode": 1,
            }
            result = await task_list.trestle_task_list(task_list.TrestleTaskListInput())
            assert "❌" in result
            assert "not in a valid trestle root directory" in result


class TestTaskNameValidation:
    """Test suite for the shape required of the optional task name.

    Same reasoning as trestle_task_run: the name is positional in
    `trestle task <name> -i`, so `trestle task --help -i` would exit 0 with its
    usage text and be reported as a described task.
    """

    @pytest.mark.parametrize(
        "name", ["csv-to-oscal-cd", "xlsx-to-oscal-poam", "base", "pass-fail"]
    )
    def test_real_task_names_are_accepted(self, name):
        """Test a real task name validates."""
        assert task_list.TrestleTaskListInput(task=name).task == name

    def test_omitting_the_task_is_still_allowed(self):
        """Test the listing form, which has no task name, is unaffected."""
        assert task_list.TrestleTaskListInput().task is None

    @pytest.mark.parametrize(
        "name", ["--help", "-h", "--list", "-l", "../../etc/passwd", "Foo", ""]
    )
    def test_names_that_are_not_task_names_are_rejected(self, name):
        """Test a flag, a path or a wrong-cased name fails validation."""
        with pytest.raises(ValidationError):
            task_list.TrestleTaskListInput(task=name)
