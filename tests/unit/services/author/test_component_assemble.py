#!/usr/bin/env python3
"""Unit tests for services/author/component_assemble.py."""

from unittest.mock import patch

import pytest

from trestle_mcp.services.author import component_assemble

MODULE_NAME = "trestle_mcp.services.author.component_assemble"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"


class TestTrestleAuthorComponentAssemble:
    """Test suite for trestle_author_component_assemble tool."""

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
            params = component_assemble.TrestleAuthorComponentAssembleInput(
                markdown="md_comp", output="mycompdef"
            )
            result = await component_assemble.trestle_author_component_assemble(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[:2] == ["author", "component-assemble"]
            assert args[args.index("--markdown") + 1] == "md_comp"
            assert args[args.index("--output") + 1] == "mycompdef"
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
            params = component_assemble.TrestleAuthorComponentAssembleInput(
                markdown="md_comp",
                output="mycompdef",
                name="srccompdef",
                regenerate=True,
                version="2.0.0",
                trestle_root="/ws",
                verbose=True,
            )
            result = await component_assemble.trestle_author_component_assemble(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[args.index("--name") + 1] == "srccompdef"
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
                "stderr": "Markdown directory is empty",
                "returncode": 1,
            }
            params = component_assemble.TrestleAuthorComponentAssembleInput(
                markdown="md_comp", output="mycompdef"
            )
            result = await component_assemble.trestle_author_component_assemble(params)
            assert "❌" in result
            assert "Markdown directory is empty" in result
