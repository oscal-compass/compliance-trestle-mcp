#!/usr/bin/env python3
"""Unit tests for services/author/ssp_filter.py."""

from unittest.mock import patch

import pytest

from trestle_mcp.services.author import ssp_filter

MODULE_NAME = "trestle_mcp.services.author.ssp_filter"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"


class TestTrestleAuthorSspFilter:
    """Test suite for trestle_author_ssp_filter tool."""

    @pytest.mark.asyncio
    async def test_minimal(self):
        """Test minimal required parameters only."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "done",
                "stderr": "",
                "returncode": 0,
            }
            params = ssp_filter.TrestleAuthorSspFilterInput(
                name="myssp", output="myssp_low"
            )
            result = await ssp_filter.trestle_author_ssp_filter(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[:2] == ["author", "ssp-filter"]
            assert args[args.index("--name") + 1] == "myssp"
            assert args[args.index("--output") + 1] == "myssp_low"
            # nothing optional leaked into the command line
            assert len(args) == 6

    @pytest.mark.asyncio
    async def test_all_options(self):
        """Test every optional parameter reaches the command line."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "done",
                "stderr": "",
                "returncode": 0,
            }
            params = ssp_filter.TrestleAuthorSspFilterInput(
                name="myssp",
                output="myssp_low",
                profile="nist_low",
                components="ocp4:rhel8",
                implementation_status="implemented,partial",
                control_origination="system-specific",
                regenerate=True,
                version="1.2.0",
                trestle_root="/ws",
                verbose=True,
            )
            result = await ssp_filter.trestle_author_ssp_filter(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[args.index("--profile") + 1] == "nist_low"
            assert args[args.index("--components") + 1] == "ocp4:rhel8"
            assert (
                args[args.index("--implementation-status") + 1] == "implemented,partial"
            )
            assert args[args.index("--control-origination") + 1] == "system-specific"
            assert "--regenerate" in args
            assert args[args.index("--version") + 1] == "1.2.0"
            assert args[args.index("--trestle-root") + 1] == "/ws"
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_failure(self):
        """Test the error path reports stderr."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "SSP not found",
                "returncode": 1,
            }
            params = ssp_filter.TrestleAuthorSspFilterInput(
                name="myssp", output="myssp_low"
            )
            result = await ssp_filter.trestle_author_ssp_filter(params)
            assert "❌" in result
            assert "SSP not found" in result
