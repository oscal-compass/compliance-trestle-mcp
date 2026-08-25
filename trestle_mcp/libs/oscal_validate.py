"""OSCAL schema + semantic validation using the trestle Python library.

Unlike the other tools in this server, this module does **not** shell out to the
trestle CLI. ``trestle validate`` only validates models that live inside a
trestle workspace directory tree, so a standalone OSCAL file (for example a
Plan of Action and Milestones produced by an authoring flow) cannot be checked
that way. Instead we drive trestle's model classes directly:

1. **Schema validation** — ``<Model>.oscal_read()`` parses the JSON/YAML through
   the pydantic OSCAL models, catching missing required fields, wrong types,
   bad enums, malformed UUIDs, and other schema violations.
2. **Semantic validation** — trestle's ``AllValidator`` (duplicate UUIDs, broken
   internal references, links, rule parameters, catalog interface) is run
   against the loaded in-memory model.

The model type is detected from the single top-level JSON/YAML key (the OSCAL
root alias, e.g. ``plan-of-action-and-milestones``), so the same tool validates
any of the seven top-level OSCAL models.
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from trestle.common import const
from trestle.core.validator_factory import validator_factory

# Root JSON/YAML alias -> (module, class name) for the seven top-level OSCAL
# models. The alias is the single wrapper key at the top of an OSCAL document.
ROOT_ALIAS_TO_MODEL: dict[str, tuple[str, str]] = {
    "catalog": ("trestle.oscal.catalog", "Catalog"),
    "profile": ("trestle.oscal.profile", "Profile"),
    "component-definition": ("trestle.oscal.component", "ComponentDefinition"),
    "system-security-plan": ("trestle.oscal.ssp", "SystemSecurityPlan"),
    "assessment-plan": ("trestle.oscal.assessment_plan", "AssessmentPlan"),
    "assessment-results": ("trestle.oscal.assessment_results", "AssessmentResults"),
    "plan-of-action-and-milestones": (
        "trestle.oscal.poam",
        "PlanOfActionAndMilestones",
    ),
}

SUPPORTED_MODEL_TYPES = sorted(ROOT_ALIAS_TO_MODEL)


@dataclass
class ValidationResult:
    """Outcome of validating a single OSCAL file."""

    valid: bool
    model_type: Optional[str]  # detected root alias, or None if undetectable
    messages: list[str] = field(default_factory=list)
    schema_valid: bool = False
    semantic_valid: bool = False


class _WarningCapture(logging.Handler):
    """Collect WARNING+ records emitted on the ``trestle`` logger.

    trestle's validators report *why* a model is invalid via warnings on the
    ``trestle`` logger (e.g. "Duplicate detected of item ..."). Capturing them
    lets us surface the concrete reason instead of a bare pass/fail.
    """

    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())

    def __enter__(self) -> "_WarningCapture":
        self._logger = logging.getLogger("trestle")
        self._prev_level = self._logger.level
        # Ensure WARNINGs propagate to this handler regardless of prior config.
        if self._prev_level > logging.WARNING or self._prev_level == logging.NOTSET:
            self._logger.setLevel(logging.WARNING)
        self._logger.addHandler(self)
        return self

    def __exit__(self, *exc: object) -> None:
        self._logger.removeHandler(self)
        self._logger.setLevel(self._prev_level)


def _load_root_mapping(path: Path) -> dict:
    """Parse the file just enough to read its top-level wrapper key."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        from ruamel.yaml import YAML

        data = YAML(typ="safe").load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("top level of an OSCAL document must be a JSON/YAML object")
    return data


def _detect_root_alias(path: Path) -> str:
    """Return the single OSCAL root alias of the document, or raise ValueError."""
    data = _load_root_mapping(path)
    keys = list(data)
    if len(keys) != 1:
        raise ValueError(
            f"expected exactly one top-level OSCAL wrapper key, found {len(keys)}: "
            f"{keys}"
        )
    return keys[0]


def validate_oscal_file(
    file_path: str,
    expected_model_type: Optional[str] = None,
    semantic: bool = True,
) -> ValidationResult:
    """Validate a standalone OSCAL file against the OSCAL schema (and optionally
    trestle's semantic validators).

    Args:
        file_path: Path to a ``.json``/``.yaml``/``.yml`` OSCAL document.
        expected_model_type: If given, the detected root alias must equal this
            value (e.g. ``plan-of-action-and-milestones``); otherwise the file
            is rejected as the wrong model type.
        semantic: When True, also run trestle's ``AllValidator`` after a
            successful schema load.

    Returns:
        A :class:`ValidationResult`.
    """
    path = Path(file_path)
    if not path.is_file():
        return ValidationResult(False, None, [f"File not found: {file_path}"])

    # --- detect model type from the root wrapper key ---
    try:
        alias = _detect_root_alias(path)
    except Exception as exc:  # noqa: BLE001 - report any parse/shape problem
        return ValidationResult(
            False, None, [f"Could not read OSCAL file or detect model type: {exc}"]
        )

    if alias not in ROOT_ALIAS_TO_MODEL:
        return ValidationResult(
            False,
            alias,
            [
                f"Unsupported OSCAL root '{alias}'. "
                f"Supported model types: {SUPPORTED_MODEL_TYPES}"
            ],
        )

    if expected_model_type and alias != expected_model_type:
        return ValidationResult(
            False,
            alias,
            [
                f"Model type mismatch: expected '{expected_model_type}' "
                f"but file is a '{alias}'"
            ],
        )

    module_name, class_name = ROOT_ALIAS_TO_MODEL[alias]
    model_cls = getattr(importlib.import_module(module_name), class_name)

    result = ValidationResult(valid=True, model_type=alias)

    # --- (1) schema validation via pydantic model load ---
    try:
        with _WarningCapture() as cap:
            model = model_cls.oscal_read(path)
    except Exception as exc:  # noqa: BLE001 - TrestleError et al. carry the detail
        messages = [str(exc)]
        messages.extend(m for m in cap.messages if m not in messages)
        return ValidationResult(False, alias, messages, schema_valid=False)
    result.schema_valid = True

    if not semantic:
        result.semantic_valid = True
        return result

    # --- (2) semantic validation via trestle's AllValidator ---
    args = argparse.Namespace(mode=const.VAL_MODE_ALL, quiet=True)
    validator = validator_factory.get(args)
    with _WarningCapture() as cap, TemporaryDirectory() as tmp_root:
        semantic_ok = validator.model_is_valid(model, True, Path(tmp_root))
    result.semantic_valid = semantic_ok
    if not semantic_ok:
        result.valid = False
        result.messages.extend(cap.messages or ["Semantic validation failed"])

    return result
