#!/usr/bin/env python3
"""Unit tests for services/author/catalog_assemble.py."""

from unittest.mock import patch

import pytest

from trestle_mcp.services.author import catalog_assemble

MODULE_NAME = "trestle_mcp.services.author.catalog_assemble"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"


class TestTrestleAuthorCatalogAssemble:
    """Test suite for trestle_author_catalog_assemble tool."""

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
            params = catalog_assemble.TrestleAuthorCatalogAssembleInput(
                markdown="md_catalog", output="mycat"
            )
            result = await catalog_assemble.trestle_author_catalog_assemble(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[:2] == ["author", "catalog-assemble"]
            assert args[args.index("--markdown") + 1] == "md_catalog"
            assert args[args.index("--output") + 1] == "mycat"
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
            params = catalog_assemble.TrestleAuthorCatalogAssembleInput(
                markdown="md_catalog",
                output="mycat",
                name="srccat",
                set_parameters=True,
                regenerate=True,
                version="1.1.0",
                trestle_root="/ws",
                verbose=True,
            )
            result = await catalog_assemble.trestle_author_catalog_assemble(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[args.index("--name") + 1] == "srccat"
            assert "--set-parameters" in args
            assert "--regenerate" in args
            assert args[args.index("--version") + 1] == "1.1.0"
            assert args[args.index("--trestle-root") + 1] == "/ws"
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_failure(self):
        """Test the error path reports stderr."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "No markdown directory found",
                "returncode": 1,
            }
            params = catalog_assemble.TrestleAuthorCatalogAssembleInput(
                markdown="md_catalog", output="mycat"
            )
            result = await catalog_assemble.trestle_author_catalog_assemble(params)
            assert "❌" in result
            assert "No markdown directory found" in result
