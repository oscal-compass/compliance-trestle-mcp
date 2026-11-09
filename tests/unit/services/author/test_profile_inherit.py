#!/usr/bin/env python3
"""Unit tests for services/author/profile_inherit.py."""

from unittest.mock import patch

import pytest

from trestle_mcp.services.author import profile_inherit

MODULE_NAME = "trestle_mcp.services.author.profile_inherit"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"


class TestTrestleAuthorProfileInherit:
    """Test suite for trestle_author_profile_inherit tool."""

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
            params = profile_inherit.TrestleAuthorProfileInheritInput(
                ssp="platform_ssp", profile="nist_moderate", output="myprof"
            )
            result = await profile_inherit.trestle_author_profile_inherit(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[:2] == ["author", "profile-inherit"]
            assert args[args.index("--ssp") + 1] == "platform_ssp"
            assert args[args.index("--profile") + 1] == "nist_moderate"
            assert args[args.index("--output") + 1] == "myprof"
            # nothing optional leaked into the command line
            assert len(args) == 8

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
            params = profile_inherit.TrestleAuthorProfileInheritInput(
                ssp="platform_ssp",
                profile="nist_moderate",
                output="myprof",
                version="1.0.1",
                trestle_root="/ws",
                verbose=True,
            )
            result = await profile_inherit.trestle_author_profile_inherit(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[args.index("--version") + 1] == "1.0.1"
            assert args[args.index("--trestle-root") + 1] == "/ws"
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_failure(self):
        """Test the error path reports stderr."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "Leveraged ssp not found",
                "returncode": 1,
            }
            params = profile_inherit.TrestleAuthorProfileInheritInput(
                ssp="platform_ssp", profile="nist_moderate", output="myprof"
            )
            result = await profile_inherit.trestle_author_profile_inherit(params)
            assert "❌" in result
            assert "Leveraged ssp not found" in result
