#!/usr/bin/env python3
"""Unit tests for services/author/profile_generate.py."""

from unittest.mock import patch

import pytest

from trestle_mcp.services.author import profile_generate

MODULE_NAME = "trestle_mcp.services.author.profile_generate"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"


class TestTrestleAuthorProfileGenerate:
    """Test suite for trestle_author_profile_generate tool."""

    @pytest.mark.asyncio
    async def test_profile_generate_minimal(self):
        """Test minimal required parameters only."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Profile markdowns generated",
                "stderr": "",
                "returncode": 0,
            }
            params = profile_generate.TrestleAuthorProfileGenerateInput(
                name="custom-profile", output="md_profile"
            )
            result = await profile_generate.trestle_author_profile_generate(params)
            assert "✅" in result
            assert "md_profile" in result
            args = mock_run.call_args[0][0]
            assert "author" in args and "profile-generate" in args
            assert "-n" in args
            assert "custom-profile" in args
            assert "--output" in args
            assert "md_profile" in args

    @pytest.mark.asyncio
    async def test_profile_generate_all_options(self):
        """Test all optional parameters."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "All options successful",
                "stderr": "",
                "returncode": 0,
            }
            params = profile_generate.TrestleAuthorProfileGenerateInput(
                name="testprof",
                output="md_out",
                yaml_header="/some/header.yaml",
                force_overwrite=True,
                overwrite_header_values=True,
                sections="implementation,statement",
                required_sections="statement,assessment",
                trestle_root="/workspace",
                verbose=True,
            )
            result = await profile_generate.trestle_author_profile_generate(params)
            assert "✅" in result and "md_out" in result
            args = mock_run.call_args[0][0]
            assert "--yaml-header" in args
            assert "/some/header.yaml" in args
            assert "--force-overwrite" in args
            assert "--overwrite-header-values" in args
            assert "--sections" in args
            assert "implementation,statement" in args
            assert "--required-sections" in args
            assert "statement,assessment" in args
            assert "--trestle-root" in args
            assert "/workspace" in args
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_profile_generate_failure(self):
        """Test error handling/failure of command."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "No profile file found",
                "returncode": 1,
            }
            params = profile_generate.TrestleAuthorProfileGenerateInput(
                name="badprofile", output="faildir"
            )
            result = await profile_generate.trestle_author_profile_generate(params)
            assert "❌" in result
            assert "badprofile" in result
            assert "No profile file found" in result

    @pytest.mark.asyncio
    async def test_profile_generate_partial_options(self):
        """Test some optional parameters specified."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Partial options done",
                "stderr": "",
                "returncode": 0,
            }
            params = profile_generate.TrestleAuthorProfileGenerateInput(
                name="prof2",
                output="out2",
                sections="implementation",
                verbose=True,
            )
            result = await profile_generate.trestle_author_profile_generate(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "--sections" in args
            assert "implementation" in args
            assert "--verbose" in args
