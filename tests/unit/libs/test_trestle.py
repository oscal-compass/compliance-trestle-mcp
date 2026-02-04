#!/usr/bin/env python3
"""Unit tests for libs/trestle.py."""

from unittest.mock import MagicMock, patch

from trestle_mcp.libs.trestle import find_trestle_bin, run_trestle_command


class TestFindTrestleBin:
    """Test suite for find_trestle_bin function."""

    def test_find_trestle_in_cwd_venv(self, tmp_path):
        """Test finding trestle in current working directory .venv."""
        venv_bin = tmp_path / ".venv" / "bin"
        venv_bin.mkdir(parents=True)
        trestle_bin = venv_bin / "trestle"
        trestle_bin.touch()

        with patch("trestle_mcp.libs.trestle.Path.cwd", return_value=tmp_path):
            result = find_trestle_bin()
            assert result == str(trestle_bin)

    def test_find_trestle_fallback_to_system(self):
        """Test fallback to system trestle when not found in venv."""
        with patch("trestle_mcp.libs.trestle.Path.exists", return_value=False):
            result = find_trestle_bin()
            assert result == "trestle"


class TestRunTrestleCommand:
    """Test suite for run_trestle_command function."""

    def test_successful_command(self):
        """Test successful command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success output"
        mock_result.stderr = ""

        with patch("trestle_mcp.libs.trestle.subprocess.run", return_value=mock_result):
            with patch(
                "trestle_mcp.libs.trestle.find_trestle_bin", return_value="trestle"
            ):
                result = run_trestle_command(["init", "--local"])

                assert result["success"] is True
                assert result["stdout"] == "Success output"
                assert result["stderr"] == ""
                assert result["returncode"] == 0

    def test_failed_command(self):
        """Test failed command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error message"

        with patch("trestle_mcp.libs.trestle.subprocess.run", return_value=mock_result):
            with patch(
                "trestle_mcp.libs.trestle.find_trestle_bin", return_value="trestle"
            ):
                result = run_trestle_command(["init", "--local"])

                assert result["success"] is False
                assert result["stdout"] == ""
                assert result["stderr"] == "Error message"
                assert result["returncode"] == 1

    def test_command_timeout(self):
        """Test command timeout handling."""
        from subprocess import TimeoutExpired

        with patch(
            "trestle_mcp.libs.trestle.subprocess.run",
            side_effect=TimeoutExpired("cmd", 60),
        ):
            with patch(
                "trestle_mcp.libs.trestle.find_trestle_bin", return_value="trestle"
            ):
                result = run_trestle_command(["init", "--local"])

                assert result["success"] is False
                assert "timed out" in result["stderr"]
                assert result["returncode"] == -1

    def test_command_exception(self):
        """Test command exception handling."""
        with patch(
            "trestle_mcp.libs.trestle.subprocess.run",
            side_effect=Exception("Test error"),
        ):
            with patch(
                "trestle_mcp.libs.trestle.find_trestle_bin", return_value="trestle"
            ):
                result = run_trestle_command(["init", "--local"])

                assert result["success"] is False
                assert "Test error" in result["stderr"]
                assert result["returncode"] == -1

    def test_command_with_custom_cwd(self):
        """Test command execution with custom working directory."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""

        with patch(
            "trestle_mcp.libs.trestle.subprocess.run", return_value=mock_result
        ) as mock_run:
            with patch(
                "trestle_mcp.libs.trestle.find_trestle_bin", return_value="trestle"
            ):
                result = run_trestle_command(["init", "--local"], cwd="/custom/path")

                assert result["success"] is True
                mock_run.assert_called_once()
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs["cwd"] == "/custom/path"
