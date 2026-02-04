#!/usr/bin/env python3
"""Unit tests for services/author/profile_assemble.py."""

from unittest.mock import patch

import pytest

from trestle_mcp.services.author.profile_assemble import (
    TrestleAuthorProfileAssembleInput,
    trestle_author_profile_assemble,
)

MODULE_NAME = "trestle_mcp.services.author.profile_assemble"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"


class TestTrestleAuthorProfileAssemble:
    """Test suite for trestle_author_profile_assemble tool."""

    @pytest.mark.asyncio
    async def test_basic_assemble(self):
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Profile assembled successfully",
                "stderr": "",
                "returncode": 0,
            }
            params = TrestleAuthorProfileAssembleInput(
                markdown_dir="controls_md_dir", output_profile="profile1"
            )
            result = await trestle_author_profile_assemble(params)
            assert "✅" in result
            assert "profile1" in result
            assert "successfully" in result
            args = mock_run.call_args[0][0]
            assert "--markdown" in args
            assert "controls_md_dir" in args
            assert "--output" in args
            assert "profile1" in args

    @pytest.mark.asyncio
    async def test_with_name_and_version(self):
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Profile assembled (named, versioned)",
                "stderr": "",
                "returncode": 0,
            }
            params = TrestleAuthorProfileAssembleInput(
                markdown_dir="mddir",
                output_profile="prof2",
                name="NiceProfile",
                version="2.1.0",
            )
            result = await trestle_author_profile_assemble(params)
            assert "NiceProfile" not in result  # only output dir shown
            args = mock_run.call_args[0][0]
            assert "--name" in args
            assert "NiceProfile" in args
            assert "--version" in args
            assert "2.1.0" in args
            assert "--output" in args
            assert "prof2" in args

    @pytest.mark.asyncio
    async def test_with_flags(self):
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "All flags used.",
                "stderr": "",
                "returncode": 0,
            }
            params = TrestleAuthorProfileAssembleInput(
                markdown_dir="md",
                output_profile="out_p",
                set_parameters=True,
                regenerate=True,
                verbose=True,
            )
            result = await trestle_author_profile_assemble(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "--set-parameters" in args
            assert "--regenerate" in args
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_sections_required_allowed(self):
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Sections args handled",
                "stderr": "",
                "returncode": 0,
            }
            params = TrestleAuthorProfileAssembleInput(
                markdown_dir="md",
                output_profile="p",
                sections="A:Alpha,B:Beta",
                required_sections="A,B",
                allowed_sections="A,B,C",
            )
            result = await trestle_author_profile_assemble(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "--sections" in args
            assert "A:Alpha,B:Beta" in args
            assert "--required-sections" in args
            assert "A,B" in args
            assert "--allowed-sections" in args
            assert "A,B,C" in args

    @pytest.mark.asyncio
    async def test_trestle_root(self):
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Located root",
                "stderr": "",
                "returncode": 0,
            }
            params = TrestleAuthorProfileAssembleInput(
                markdown_dir="md", output_profile="prof", trestle_root="/tmp/proj"
            )
            result = await trestle_author_profile_assemble(params)
            args = mock_run.call_args[0][0]
            assert "--trestle-root" in args
            assert "/tmp/proj" in args

    @pytest.mark.asyncio
    async def test_failure(self):
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "Error happened",
                "returncode": 1,
            }
            params = TrestleAuthorProfileAssembleInput(
                markdown_dir="missingmd", output_profile="outprof"
            )
            result = await trestle_author_profile_assemble(params)
            assert "❌" in result
            assert "missingmd" in result
            assert "Error happened" in result
