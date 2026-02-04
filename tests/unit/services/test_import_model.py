#!/usr/bin/env python3
"""Unit tests for services/import_model.py."""

from unittest.mock import patch

import pytest

from trestle_mcp.services.import_ import TrestleImportInput, trestle_import

MODULE_NAME = "trestle_mcp.services.import_.run_trestle_command"


class TestTrestleImport:
    """Test suite for trestle_import tool."""

    @pytest.mark.asyncio
    async def test_trestle_import_from_url(self):
        """Test trestle_import with URL."""
        with patch(MODULE_NAME) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Imported catalog successfully",
                "stderr": "",
                "returncode": 0,
            }

            params = TrestleImportInput(
                file="https://example.com/catalog.json", output="nist_catalog"
            )
            result = await trestle_import(params)

            assert "✅" in result
            assert "successfully" in result
            assert "nist_catalog" in result
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[0] == "import"
            assert "-f" in args
            assert "https://example.com/catalog.json" in args
            assert "-o" in args
            assert "nist_catalog" in args

    @pytest.mark.asyncio
    async def test_trestle_import_from_local_file(self):
        """Test trestle_import with local file path."""
        with patch(MODULE_NAME) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Imported profile successfully",
                "stderr": "",
                "returncode": 0,
            }

            params = TrestleImportInput(
                file="./resources/profiles/my_profile.json", output="my_profile"
            )
            result = await trestle_import(params)

            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "./resources/profiles/my_profile.json" in args

    @pytest.mark.asyncio
    async def test_trestle_import_with_regenerate(self):
        """Test trestle_import with regenerate flag."""
        with patch(MODULE_NAME) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Imported with new UUIDs",
                "stderr": "",
                "returncode": 0,
            }

            params = TrestleImportInput(
                file="https://example.com/catalog.json",
                output="test_catalog",
                regenerate=True,
            )
            result = await trestle_import(params)

            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "--regenerate" in args

    @pytest.mark.asyncio
    async def test_trestle_import_with_custom_root(self):
        """Test trestle_import with custom trestle root."""
        with patch(MODULE_NAME) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Imported successfully",
                "stderr": "",
                "returncode": 0,
            }

            params = TrestleImportInput(
                file="https://example.com/catalog.json",
                output="catalog",
                trestle_root="/path/to/workspace",
            )
            result = await trestle_import(params)

            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "--trestle-root" in args
            assert "/path/to/workspace" in args

    @pytest.mark.asyncio
    async def test_trestle_import_verbose(self):
        """Test trestle_import with verbose flag."""
        with patch(MODULE_NAME) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Detailed import output",
                "stderr": "",
                "returncode": 0,
            }

            params = TrestleImportInput(
                file="https://example.com/catalog.json", output="catalog", verbose=True
            )
            result = await trestle_import(params)

            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_trestle_import_failure_invalid_file(self):
        """Test trestle_import when file is invalid."""
        with patch(MODULE_NAME) as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "Error: File not found or invalid OSCAL format",
                "returncode": 1,
            }

            params = TrestleImportInput(
                file="https://example.com/invalid.json", output="test"
            )
            result = await trestle_import(params)

            assert "❌" in result
            assert "Failed" in result
            assert "invalid.json" in result

    @pytest.mark.asyncio
    async def test_trestle_import_nist_sp800_53_catalog(self):
        """Test importing NIST SP800-53 Rev5 catalog."""
        with patch(MODULE_NAME) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Imported NIST SP800-53 Rev5 catalog",
                "stderr": "",
                "returncode": 0,
            }

            params = TrestleImportInput(
                file="https://raw.githubusercontent.com/usnistgov/oscal-content/refs/heads/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json",
                output="nist_sp800_53_rev5",
            )
            result = await trestle_import(params)

            assert "✅" in result
            assert "nist_sp800_53_rev5" in result

    @pytest.mark.asyncio
    async def test_trestle_import_all_options(self):
        """Test trestle_import with all options."""
        with patch(MODULE_NAME) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Imported successfully",
                "stderr": "",
                "returncode": 0,
            }

            params = TrestleImportInput(
                file="https://example.com/catalog.json",
                output="test_catalog",
                regenerate=True,
                trestle_root="/custom/path",
                verbose=True,
            )
            result = await trestle_import(params)

            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "import" in args
            assert "-f" in args
            assert "https://example.com/catalog.json" in args
            assert "-o" in args
            assert "test_catalog" in args
            assert "--regenerate" in args
            assert "--trestle-root" in args
            assert "/custom/path" in args
            assert "--verbose" in args
