#!/usr/bin/env python3
"""Unit tests for services/author/catalog_generate.py."""

from unittest.mock import patch

import pytest

from trestle_mcp.services.author import catalog_generate

MODULE_NAME = "trestle_mcp.services.author.catalog_generate"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"


class TestTrestleCatalogGenerate:
    """Test suite for trestle_catalog_generate tool."""

    @pytest.mark.asyncio
    async def test_catalog_generate_minimal(self):
        """Test required parameters only."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Catalog markdowns generated",
                "stderr": "",
                "returncode": 0,
            }
            params = catalog_generate.TrestleCatalogGenerateInput(
                name="nist", output="md_catalog_nist"
            )
            result = await catalog_generate.trestle_catalog_generate(params)
            assert "✅" in result
            assert "md_catalog_nist" in result
            args = mock_run.call_args[0][0]
            assert "author" in args and "catalog-generate" in args
            assert "--name" in args and "nist" in args
            assert "--output" in args and "md_catalog_nist" in args

    @pytest.mark.asyncio
    async def test_catalog_generate_all_options(self):
        """Test all optional parameters."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "All options successful",
                "stderr": "",
                "returncode": 0,
            }
            params = catalog_generate.TrestleCatalogGenerateInput(
                name="customcat",
                output="md_out",
                force_overwrite=True,
                yaml_header="/tmp/header.yaml",
                overwrite_header_values=True,
                trestle_root="/x/y/z",
                verbose=True,
            )
            result = await catalog_generate.trestle_catalog_generate(params)
            assert "✅" in result and "md_out" in result
            args = mock_run.call_args[0][0]
            assert "--force-overwrite" in args
            assert "--yaml-header" in args
            assert "/tmp/header.yaml" in args
            assert "--overwrite-header-values" in args
            assert "--trestle-root" in args
            assert "/x/y/z" in args
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_catalog_generate_failure(self):
        """Test failure/command error."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "Catalog file not found",
                "returncode": 1,
            }
            params = catalog_generate.TrestleCatalogGenerateInput(
                name="xxx", output="bad"
            )
            result = await catalog_generate.trestle_catalog_generate(params)
            assert "❌" in result
            assert "xxx" in result
            assert "not found" in result
