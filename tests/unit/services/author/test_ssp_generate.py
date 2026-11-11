#!/usr/bin/env python3
"""Unit tests for services/author/ssp_generate.py."""

from unittest.mock import patch

import pytest

from trestle_mcp.services.author import ssp_generate

MODULE_NAME = "trestle_mcp.services.author.ssp_generate"
MOCK_RUN_MODULE = f"{MODULE_NAME}.run_trestle_command"


class TestTrestleAuthorSspGenerate:
    """Test suite for trestle_author_ssp_generate tool."""

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
            params = ssp_generate.TrestleAuthorSspGenerateInput(
                profile="nist_moderate", output="md_ssp"
            )
            result = await ssp_generate.trestle_author_ssp_generate(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[:2] == ["author", "ssp-generate"]
            assert args[args.index("--profile") + 1] == "nist_moderate"
            assert args[args.index("--output") + 1] == "md_ssp"
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
            params = ssp_generate.TrestleAuthorSspGenerateInput(
                profile="nist_moderate",
                output="md_ssp",
                compdefs="ocp4,rhel8",
                leveraged_ssp="platform_ssp",
                yaml_header="/tmp/header.yaml",
                force_overwrite=True,
                overwrite_header_values=True,
                include_all_parts=True,
                trestle_root="/ws",
                verbose=True,
            )
            result = await ssp_generate.trestle_author_ssp_generate(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[args.index("--compdefs") + 1] == "ocp4,rhel8"
            assert args[args.index("--leveraged-ssp") + 1] == "platform_ssp"
            assert args[args.index("--yaml-header") + 1] == "/tmp/header.yaml"
            assert "--force-overwrite" in args
            assert "--overwrite-header-values" in args
            assert "--include-all-parts" in args
            assert args[args.index("--trestle-root") + 1] == "/ws"
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_failure(self):
        """Test the error path reports stderr."""
        with patch(MOCK_RUN_MODULE) as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "Profile not found",
                "returncode": 1,
            }
            params = ssp_generate.TrestleAuthorSspGenerateInput(
                profile="nist_moderate", output="md_ssp"
            )
            result = await ssp_generate.trestle_author_ssp_generate(params)
            assert "❌" in result
            assert "Profile not found" in result
