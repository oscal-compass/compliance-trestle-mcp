#!/usr/bin/env python3
"""Unit tests for services/author/component_generate.py."""

from unittest.mock import patch

import pytest

from trestle_mcp.services.author import component_generate

MODULE_NAME = "trestle_mcp.services.author.component_generate"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"


class TestTrestleAuthorComponentGenerate:
    """Test suite for trestle_author_component_generate tool."""

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
            params = component_generate.TrestleAuthorComponentGenerateInput(
                name="mycompdef", output="md_comp"
            )
            result = await component_generate.trestle_author_component_generate(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[:2] == ["author", "component-generate"]
            assert args[args.index("--name") + 1] == "mycompdef"
            assert args[args.index("--output") + 1] == "md_comp"
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
            params = component_generate.TrestleAuthorComponentGenerateInput(
                name="mycompdef",
                output="md_comp",
                force_overwrite=True,
                trestle_root="/ws",
                verbose=True,
            )
            result = await component_generate.trestle_author_component_generate(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "--force-overwrite" in args
            assert args[args.index("--trestle-root") + 1] == "/ws"
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_failure(self):
        """Test the error path reports stderr."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "component-definition not found",
                "returncode": 1,
            }
            params = component_generate.TrestleAuthorComponentGenerateInput(
                name="mycompdef", output="md_comp"
            )
            result = await component_generate.trestle_author_component_generate(params)
            assert "❌" in result
            assert "component-definition not found" in result
