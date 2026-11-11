#!/usr/bin/env python3
"""Unit tests for services/remove.py.

`trestle remove` deletes model content in place, so these cover the argument
shape and, just as importantly, that nothing is sent to the CLI that the caller
did not ask for: an extra element path here loses data.
"""

from unittest.mock import patch

import pytest

from trestle_mcp.services import remove

MOCK_RUN = "trestle_mcp.services.remove.run_trestle_command"
SUCCESS = {"success": True, "stdout": "ok", "stderr": "", "returncode": 0}
FAILURE = {"success": False, "stdout": "", "stderr": "boom", "returncode": 1}


class TestTrestleRemove:
    """Test suite for trestle_remove tool."""

    @pytest.mark.asyncio
    async def test_minimal(self):
        """Test the two required arguments and nothing else."""
        with patch(MOCK_RUN) as mock_run:
            mock_run.return_value = SUCCESS
            params = remove.TrestleRemoveInput(
                file="catalogs/mycat/catalog.json", element="catalog.metadata.roles"
            )
            result = await remove.trestle_remove(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[0] == "remove"
            assert args[args.index("--file") + 1] == "catalogs/mycat/catalog.json"
            assert args[args.index("--element") + 1] == "catalog.metadata.roles"
            # Nothing optional leaked into the command line.
            assert len(args) == 5

    @pytest.mark.asyncio
    async def test_all_options(self):
        """Test every optional parameter reaches the command line."""
        with patch(MOCK_RUN) as mock_run:
            mock_run.return_value = SUCCESS
            params = remove.TrestleRemoveInput(
                file="catalogs/mycat/catalog.json",
                element="catalog.groups",
                trestle_root="/ws",
                verbose=True,
            )
            await remove.trestle_remove(params)
            args = mock_run.call_args[0][0]
            assert args[args.index("--trestle-root") + 1] == "/ws"
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_uses_the_default_timeout(self):
        """Test removal is a local edit and is not given the long timeout."""
        with patch(MOCK_RUN) as mock_run:
            mock_run.return_value = SUCCESS
            params = remove.TrestleRemoveInput(file="f.json", element="catalog.groups")
            await remove.trestle_remove(params)
            assert "timeout" not in mock_run.call_args.kwargs

    @pytest.mark.asyncio
    async def test_failure_reports_the_element(self):
        """Test a failed removal names what it was trying to remove.

        The caller needs to know whether the element was the problem, because
        the next step is either a corrected path or a restore from git.
        """
        with patch(MOCK_RUN) as mock_run:
            mock_run.return_value = FAILURE
            params = remove.TrestleRemoveInput(
                file="catalogs/mycat/catalog.json", element="catalog.nope"
            )
            result = await remove.trestle_remove(params)
            assert "❌" in result
            assert "catalog.nope" in result
            assert "boom" in result

    @pytest.mark.asyncio
    async def test_required_arguments(self):
        """Test neither file nor element can be omitted."""
        with pytest.raises(Exception):
            remove.TrestleRemoveInput(file="f.json")
        with pytest.raises(Exception):
            remove.TrestleRemoveInput(element="catalog.groups")
