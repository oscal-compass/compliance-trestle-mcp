#!/usr/bin/env python3
"""Unit tests for services/author/ssp_assemble.py."""

from unittest.mock import patch

import pytest

from trestle_mcp.services.author import ssp_assemble

MODULE_NAME = "trestle_mcp.services.author.ssp_assemble"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"


class TestTrestleAuthorSspAssemble:
    """Test suite for trestle_author_ssp_assemble tool."""

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
            params = ssp_assemble.TrestleAuthorSspAssembleInput(
                markdown="md_ssp", output="myssp"
            )
            result = await ssp_assemble.trestle_author_ssp_assemble(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[:2] == ["author", "ssp-assemble"]
            assert args[args.index("--markdown") + 1] == "md_ssp"
            assert args[args.index("--output") + 1] == "myssp"
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
            params = ssp_assemble.TrestleAuthorSspAssembleInput(
                markdown="md_ssp",
                output="myssp",
                name="srcssp",
                compdefs="ocp4,rhel8",
                regenerate=True,
                version="2.0.0",
                trestle_root="/ws",
                verbose=True,
            )
            result = await ssp_assemble.trestle_author_ssp_assemble(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[args.index("--name") + 1] == "srcssp"
            assert args[args.index("--compdefs") + 1] == "ocp4,rhel8"
            assert "--regenerate" in args
            assert args[args.index("--version") + 1] == "2.0.0"
            assert args[args.index("--trestle-root") + 1] == "/ws"
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_failure(self):
        """Test the error path reports stderr."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "Markdown directory not found",
                "returncode": 1,
            }
            params = ssp_assemble.TrestleAuthorSspAssembleInput(
                markdown="md_ssp", output="myssp"
            )
            result = await ssp_assemble.trestle_author_ssp_assemble(params)
            assert "❌" in result
            assert "Markdown directory not found" in result
