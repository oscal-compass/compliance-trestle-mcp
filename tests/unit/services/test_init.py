#!/usr/bin/env python3
"""Unit tests for services/init.py."""

from unittest.mock import patch

import pytest

from trestle_mcp.services.init import InitMode, TrestleInitInput, trestle_init

MODULE_NAME = "trestle_mcp.services.init"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"


class TestTrestleInit:
    """Test suite for trestle_init tool."""

    @pytest.mark.asyncio
    async def test_trestle_init_default(self):
        """Test trestle_init with default parameters."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Initialized trestle workspace",
                "stderr": "",
                "returncode": 0,
            }

            params = TrestleInitInput()
            result = await trestle_init(params)

            assert "✅" in result
            assert "successfully" in result
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[0] == "init"
            assert "--local" in args

    @pytest.mark.asyncio
    async def test_trestle_init_full_mode(self):
        """Test trestle_init with full mode."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Initialized trestle workspace in full mode",
                "stderr": "",
                "returncode": 0,
            }

            params = TrestleInitInput(mode=InitMode.FULL)
            result = await trestle_init(params)

            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "--full" in args
            assert "--local" not in args

    @pytest.mark.asyncio
    async def test_trestle_init_govdocs_mode(self):
        """Test trestle_init with govdocs mode."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Initialized trestle workspace for govdocs",
                "stderr": "",
                "returncode": 0,
            }

            params = TrestleInitInput(mode=InitMode.GOVDOCS)
            result = await trestle_init(params)

            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "--govdocs" in args

    @pytest.mark.asyncio
    async def test_trestle_init_with_custom_root(self):
        """Test trestle_init with custom trestle root."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Initialized trestle workspace",
                "stderr": "",
                "returncode": 0,
            }

            params = TrestleInitInput(trestle_root="/path/to/workspace")
            result = await trestle_init(params)

            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "--trestle-root" in args
            assert "/path/to/workspace" in args

    @pytest.mark.asyncio
    async def test_trestle_init_verbose(self):
        """Test trestle_init with verbose flag."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Detailed initialization output",
                "stderr": "",
                "returncode": 0,
            }

            params = TrestleInitInput(verbose=True)
            result = await trestle_init(params)

            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_trestle_init_failure(self):
        """Test trestle_init when command fails."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "Error: Directory already initialized",
                "returncode": 1,
            }

            params = TrestleInitInput()
            result = await trestle_init(params)

            assert "❌" in result
            assert "Failed" in result
            assert "already initialized" in result

    @pytest.mark.asyncio
    async def test_trestle_init_all_options(self):
        """Test trestle_init with all options."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Initialized successfully",
                "stderr": "",
                "returncode": 0,
            }

            params = TrestleInitInput(
                mode=InitMode.FULL, trestle_root="/custom/path", verbose=True
            )
            result = await trestle_init(params)

            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "init" in args
            assert "--full" in args
            assert "--trestle-root" in args
            assert "/custom/path" in args
            assert "--verbose" in args
