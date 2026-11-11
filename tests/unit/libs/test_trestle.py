#!/usr/bin/env python3
"""Unit tests for libs/trestle.py."""

from unittest.mock import MagicMock, patch

from trestle_mcp.libs.trestle import (
    DEFAULT_TIMEOUT,
    LONG_TIMEOUT,
    find_trestle_bin,
    run_trestle_command,
)


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

    def test_default_timeout_is_applied(self):
        """Test the default timeout is handed to subprocess.run."""
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
                run_trestle_command(["init", "--local"])

                assert mock_run.call_args[1]["timeout"] == DEFAULT_TIMEOUT

    def test_custom_timeout_is_applied(self):
        """Test an explicit timeout overrides the default."""
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
                run_trestle_command(["import"], timeout=LONG_TIMEOUT)

                assert mock_run.call_args[1]["timeout"] == LONG_TIMEOUT
                assert LONG_TIMEOUT > DEFAULT_TIMEOUT

    def test_timeout_message_reports_the_actual_timeout(self):
        """Test the timeout error names the timeout that was used, not a constant."""
        from subprocess import TimeoutExpired

        with patch(
            "trestle_mcp.libs.trestle.subprocess.run",
            side_effect=TimeoutExpired("cmd", LONG_TIMEOUT),
        ):
            with patch(
                "trestle_mcp.libs.trestle.find_trestle_bin", return_value="trestle"
            ):
                result = run_trestle_command(["import"], timeout=LONG_TIMEOUT)

                assert result["success"] is False
                assert f"timed out after {LONG_TIMEOUT} seconds" in result["stderr"]


class TestTrestleRootIsTheWorkingDirectory:
    """Test the working directory is derived from --trestle-root.

    Without this, a relative path argument is resolved against the directory the
    MCP client started the server in, which is not the workspace, so the command
    fails on a path the caller had every reason to think was right.
    """

    @staticmethod
    def _run(args, **kwargs):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch(
            "trestle_mcp.libs.trestle.subprocess.run", return_value=mock_result
        ) as mock_run:
            with patch(
                "trestle_mcp.libs.trestle.find_trestle_bin", return_value="trestle"
            ):
                run_trestle_command(args, **kwargs)
        return mock_run.call_args

    def test_absolute_root_becomes_the_cwd(self):
        """Test the command runs inside the workspace it was given."""
        call = self._run(
            ["split", "--file", "catalogs/c/catalog.json", "--trestle-root", "/ws"]
        )
        assert call[1]["cwd"] == "/ws"

    def test_relative_root_is_made_absolute_in_both_places(self):
        """Test a relative root is resolved once, for the cwd and the flag.

        The flag has to carry the absolute path too: the command runs *in* that
        directory, so a relative `--trestle-root ws` would resolve to `ws/ws`.
        """
        with patch("trestle_mcp.libs.trestle.os.getcwd", return_value="/start"):
            call = self._run(["describe", "--file", "f.json", "--trestle-root", "ws"])
        args = call[0][0][1:]
        assert args[args.index("--trestle-root") + 1] == "/start/ws"
        assert call[1]["cwd"] == "/start/ws"

    def test_joined_flag_form_is_handled_too(self):
        """Test `--trestle-root=/ws` is resolved like the two-token form."""
        call = self._run(["describe", "--file", "f.json", "--trestle-root=/ws"])
        assert call[1]["cwd"] == "/ws"
        assert "--trestle-root=/ws" in call[0][0]

    def test_an_explicit_cwd_still_wins(self):
        """Test merge can override the root with the model directory."""
        call = self._run(
            ["merge", "--element", "catalog.metadata", "--trestle-root", "/ws"],
            cwd="/ws/catalogs/c",
        )
        assert call[1]["cwd"] == "/ws/catalogs/c"

    def test_no_root_falls_back_to_the_process_directory(self):
        """Test behaviour is unchanged when no root is given."""
        with patch("trestle_mcp.libs.trestle.os.getcwd", return_value="/start"):
            call = self._run(["version"])
        assert call[1]["cwd"] == "/start"
