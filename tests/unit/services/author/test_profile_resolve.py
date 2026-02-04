#!/usr/bin/env python3
"""Unit tests for services/author/profile_resolve.py."""

from unittest.mock import patch

import pytest

from trestle_mcp.services.author.profile_resolve import (
    TrestleAuthorProfileResolveInput,
    trestle_author_profile_resolve,
)

MODULE_NAME = "trestle_mcp.services.author.profile_resolve"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"


class TestTrestleAuthorProfileResolve:
    @pytest.mark.asyncio
    async def test_minimal(self):
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Catalog generated successfully.",
                "stderr": "",
                "returncode": 0,
            }
            params = TrestleAuthorProfileResolveInput(
                name="myprofile", output="catalog_resolved"
            )
            result = await trestle_author_profile_resolve(params)
            assert "✅" in result
            assert "Output: catalog_resolved" in result
            args = mock_run.call_args[0][0]
            assert "author" in args
            assert "profile-resolve" in args
            assert "--name" in args
            assert "-o" in args

    @pytest.mark.asyncio
    async def test_with_all_options(self):
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Options applied.",
                "stderr": "",
                "returncode": 0,
            }
            params = TrestleAuthorProfileResolveInput(
                name="myprofile",
                output="catalog_resolved",
                show_values=True,
                show_labels=True,
                bracket_format="(.)",
                value_assigned_prefix="[ASSIGNED]",
                value_not_assigned_prefix="[NOT]",
                label_prefix="LBL:",
                verbose=True,
                trestle_root="/path/to/ws",
            )
            result = await trestle_author_profile_resolve(params)
            assert "✅" in result
            # Ensure all options trigger corresponding CLI flags
            args = mock_run.call_args[0][0]
            assert "--show-values" in args
            assert "--show-labels" in args
            assert "--bracket-format" in args
            assert "(.)" in args
            assert "--value-assigned-prefix" in args
            assert "[ASSIGNED]" in args
            assert "--value-not-assigned-prefix" in args
            assert "[NOT]" in args
            assert "--label-prefix" in args
            assert "LBL:" in args
            assert "--verbose" in args
            assert "--trestle-root" in args
            assert "/path/to/ws" in args

    @pytest.mark.asyncio
    async def test_failure(self):
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "Bad parameter",
                "returncode": 1,
            }
            params = TrestleAuthorProfileResolveInput(name="bad_profile", output="out")
            result = await trestle_author_profile_resolve(params)
            assert "❌" in result
            assert "Failed to generate" in result
            assert "bad_profile" in result
            assert "Bad parameter" in result
