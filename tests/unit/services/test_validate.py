#!/usr/bin/env python3
"""Unit tests for services/validate.py and libs/oscal_validate.py.

These exercise the real trestle model classes (no mocking): the validate tool
is intentionally implemented against the trestle Python library rather than the
CLI, so the tests drive genuine schema + semantic validation.
"""

import json
from pathlib import Path

import pytest

# A minimal, schema-valid POA&M. oscal_version must match the trestle build.
from trestle.oscal import OSCAL_VERSION  # noqa: E402

from trestle_mcp.libs.oscal_validate import (
    SUPPORTED_MODEL_TYPES,
    validate_oscal_file,
)
from trestle_mcp.services.validate import TrestleValidateInput, trestle_validate

VALID_POAM = {
    "plan-of-action-and-milestones": {
        "uuid": "11111111-1111-4111-8111-111111111111",
        "metadata": {
            "title": "Test POA&M",
            "last-modified": "2026-08-25T00:00:00+00:00",
            "version": "1.0",
            "oscal-version": OSCAL_VERSION,
        },
        "poam-items": [
            {
                "uuid": "22222222-2222-4222-8222-222222222222",
                "title": "Item A",
                "description": "desc a",
            }
        ],
    }
}


def _write(tmp_path: Path, name: str, obj: dict) -> str:
    p = tmp_path / name
    p.write_text(json.dumps(obj), encoding="utf-8")
    return str(p)


class TestValidateOscalFileLib:
    """Direct tests of the library core."""

    def test_valid_poam_passes_schema_and_semantic(self, tmp_path):
        path = _write(tmp_path, "poam.json", VALID_POAM)
        res = validate_oscal_file(path)
        assert res.valid
        assert res.schema_valid and res.semantic_valid
        assert res.model_type == "plan-of-action-and-milestones"

    def test_missing_required_field_fails_schema(self, tmp_path):
        bad = json.loads(json.dumps(VALID_POAM))
        del bad["plan-of-action-and-milestones"]["metadata"]["title"]
        path = _write(tmp_path, "poam.json", bad)
        res = validate_oscal_file(path)
        assert not res.valid
        assert not res.schema_valid
        # The trestle error text should name the offending field.
        assert any("title" in m for m in res.messages)

    def test_duplicate_uuid_fails_semantic_not_schema(self, tmp_path):
        dup = json.loads(json.dumps(VALID_POAM))
        items = dup["plan-of-action-and-milestones"]["poam-items"]
        items.append(dict(items[0]))  # same uuid twice
        path = _write(tmp_path, "poam.json", dup)
        res = validate_oscal_file(path)
        assert not res.valid
        assert res.schema_valid  # schema is fine
        assert not res.semantic_valid
        assert any("Duplicate" in m for m in res.messages)

    def test_semantic_can_be_disabled(self, tmp_path):
        dup = json.loads(json.dumps(VALID_POAM))
        items = dup["plan-of-action-and-milestones"]["poam-items"]
        items.append(dict(items[0]))
        path = _write(tmp_path, "poam.json", dup)
        res = validate_oscal_file(path, semantic=False)
        assert res.valid  # only schema checked
        assert res.schema_valid

    def test_expected_model_type_match(self, tmp_path):
        path = _write(tmp_path, "poam.json", VALID_POAM)
        res = validate_oscal_file(
            path, expected_model_type="plan-of-action-and-milestones"
        )
        assert res.valid

    def test_expected_model_type_mismatch(self, tmp_path):
        path = _write(tmp_path, "poam.json", VALID_POAM)
        res = validate_oscal_file(path, expected_model_type="catalog")
        assert not res.valid
        assert res.model_type == "plan-of-action-and-milestones"
        assert any("mismatch" in m.lower() for m in res.messages)

    def test_file_not_found(self):
        res = validate_oscal_file("/no/such/file.json")
        assert not res.valid
        assert any("not found" in m.lower() for m in res.messages)

    def test_unknown_root_key(self, tmp_path):
        path = _write(tmp_path, "weird.json", {"not-an-oscal-model": {}})
        res = validate_oscal_file(path)
        assert not res.valid
        assert res.model_type == "not-an-oscal-model"
        assert any("Unsupported" in m for m in res.messages)

    def test_multiple_root_keys_rejected(self, tmp_path):
        path = _write(tmp_path, "two.json", {"catalog": {}, "profile": {}})
        res = validate_oscal_file(path)
        assert not res.valid
        assert any("exactly one" in m for m in res.messages)

    def test_malformed_json(self, tmp_path):
        p = tmp_path / "broken.json"
        p.write_text("{not json", encoding="utf-8")
        res = validate_oscal_file(str(p))
        assert not res.valid
        assert res.model_type is None

    def test_all_supported_types_listed(self):
        assert "plan-of-action-and-milestones" in SUPPORTED_MODEL_TYPES
        assert len(SUPPORTED_MODEL_TYPES) == 7


class TestTrestleValidateTool:
    """Tests of the MCP-facing service wrapper."""

    @pytest.mark.asyncio
    async def test_success_message(self, tmp_path):
        path = _write(tmp_path, "poam.json", VALID_POAM)
        out = await trestle_validate(TrestleValidateInput(file=path))
        assert "✅" in out
        assert "plan-of-action-and-milestones" in out
        assert "schema + semantic" in out

    @pytest.mark.asyncio
    async def test_success_schema_only_message(self, tmp_path):
        path = _write(tmp_path, "poam.json", VALID_POAM)
        out = await trestle_validate(TrestleValidateInput(file=path, semantic=False))
        assert "✅" in out
        assert "semantic" not in out

    @pytest.mark.asyncio
    async def test_failure_message_reports_reason(self, tmp_path):
        bad = json.loads(json.dumps(VALID_POAM))
        del bad["plan-of-action-and-milestones"]["metadata"]["version"]
        path = _write(tmp_path, "poam.json", bad)
        out = await trestle_validate(TrestleValidateInput(file=path))
        assert "❌" in out
        assert "schema" in out
        assert "version" in out

    @pytest.mark.asyncio
    async def test_expected_type_mismatch_message(self, tmp_path):
        path = _write(tmp_path, "poam.json", VALID_POAM)
        out = await trestle_validate(
            TrestleValidateInput(file=path, expected_model_type="catalog")
        )
        assert "❌" in out
        assert "mismatch" in out.lower()
