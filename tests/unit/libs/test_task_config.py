#!/usr/bin/env python3
"""Unit tests for libs/task_config.py.

These pin the round trip: this module writes the file, and trestle reads it with
`ExtendedInterpolation`. A value that survives the write but not the read is
still a bug, so the reader is part of every test here.
"""

import configparser
from pathlib import Path

import pytest

from trestle_mcp.libs.task_config import escape_for_trestle, write_task_config


def read_as_trestle_does(path: str) -> dict:
    """Read a config file the way `trestle task` reads it."""
    parser = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation()
    )
    parser.read(path, encoding="utf8")
    return {section: dict(parser[section]) for section in parser.sections()}


class TestEscapeForTrestle:
    """Test suite for escape_for_trestle."""

    def test_dollar_is_doubled(self):
        """Test `$` is doubled, which is what ExtendedInterpolation accepts."""
        assert escape_for_trestle("Cost $5") == "Cost $$5"

    def test_percent_is_left_alone(self):
        """Test `%` is untouched: only BasicInterpolation cares about it."""
        assert escape_for_trestle("100% coverage") == "100% coverage"

    def test_plain_values_are_unchanged(self):
        """Test the common case adds nothing."""
        assert escape_for_trestle("/ws/catalogs/c/catalog.json") == (
            "/ws/catalogs/c/catalog.json"
        )


class TestWriteTaskConfig:
    """Test suite for write_task_config."""

    @pytest.fixture
    def written(self, request):
        """Write a config and clean it up afterwards."""
        paths = []

        def write(values, section="task.x", prefix="trestle_test_"):
            path = write_task_config(section, values, prefix)
            paths.append(path)
            return path

        yield write
        for path in paths:
            Path(path).unlink(missing_ok=True)

    def test_a_percent_value_survives_the_round_trip(self, written):
        """Test `%` no longer raises on write.

        The default BasicInterpolation validates on assignment, which happens
        before any try block, so a percent-encoded path escaped the service as a
        ValueError rather than an error message the caller could read.
        """
        path = written({"input-file": "x%20y.json", "title": "100% coverage"})
        assert read_as_trestle_does(path)["task.x"] == {
            "input-file": "x%20y.json",
            "title": "100% coverage",
        }

    def test_a_dollar_value_survives_the_round_trip(self, written):
        """Test `$` is escaped on write and read back as a single `$`."""
        path = written({"title": "Cost $5"})
        assert read_as_trestle_does(path)["task.x"]["title"] == "Cost $5"

    def test_the_file_is_utf8_whatever_the_locale(self, written):
        """Test non-ASCII values are written as UTF-8, which trestle reads."""
        path = written({"title": "統制カタログ — 第 2 版"})
        assert Path(path).read_bytes().decode("utf-8")
        assert read_as_trestle_does(path)["task.x"]["title"] == "統制カタログ — 第 2 版"

    def test_the_section_name_is_used_as_given(self, written):
        """Test the caller's section name reaches the file."""
        path = written({"a": "b"}, section="task.csv-to-oscal-cd")
        assert list(read_as_trestle_does(path)) == ["task.csv-to-oscal-cd"]

    def test_the_prefix_names_the_file(self, written):
        """Test the prefix is applied, so a leaked file names its service."""
        path = written({"a": "b"}, prefix="trestle_csv_to_cd_")
        assert Path(path).name.startswith("trestle_csv_to_cd_")
        assert Path(path).suffix == ".ini"
