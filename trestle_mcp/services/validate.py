"""Trestle OSCAL validation service.

Validates a standalone OSCAL document (any of the seven top-level models) using
the trestle Python library directly — see :mod:`trestle_mcp.libs.oscal_validate`
for why this does not use the trestle CLI.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.oscal_validate import (
    SUPPORTED_MODEL_TYPES,
    validate_oscal_file,
)


class TrestleValidateInput(BaseModel):
    """Input model for the OSCAL validate tool."""

    model_config = ConfigDict(str_strip_whitespace=True)

    file: str = Field(
        ...,
        description=(
            "Path to a standalone OSCAL document (.json, .yaml, or .yml) to "
            "validate. The model type is detected from the file's top-level key."
        ),
    )
    expected_model_type: Optional[str] = Field(
        default=None,
        description=(
            "If set, the file must be this OSCAL model type or validation fails. "
            f"One of: {SUPPORTED_MODEL_TYPES}. "
            "For a POA&M, pass 'plan-of-action-and-milestones'."
        ),
    )
    semantic: bool = Field(
        default=True,
        description=(
            "Also run trestle's semantic validators (duplicate UUIDs, broken "
            "internal references, links, rule parameters) after schema "
            "validation (default: true)."
        ),
    )


async def trestle_validate(params: TrestleValidateInput) -> str:
    """Validate a standalone OSCAL file against the OSCAL schema.

    This tool loads the OSCAL document through the trestle model classes, which
    enforces the OSCAL schema (required fields, field types, enums, UUID
    formats, and nesting). Optionally it also runs trestle's semantic validators
    (duplicate UUIDs, broken internal references, links, and rule parameters).

    It detects the model type from the file's single top-level wrapper key, so
    it validates any top-level OSCAL model: catalog, profile,
    component-definition, system-security-plan, assessment-plan,
    assessment-results, or plan-of-action-and-milestones.

    Unlike ``trestle validate`` on the CLI, this works on a standalone file that
    is not part of a trestle workspace — for example a POA&M JSON produced by an
    authoring flow.

    Args:
        params (TrestleValidateInput): Input parameters with:
            - file (str): Path to the OSCAL .json/.yaml/.yml file (required)
            - expected_model_type (Optional[str]): Enforce the file is this
              model type (e.g. 'plan-of-action-and-milestones')
            - semantic (bool): Run semantic validators too (default: true)

    Returns:
        str: A pass/fail message; on failure, the concrete reasons.

    Examples:
        - Use when: "Validate this POA&M JSON is valid OSCAL"
          file="./poam.json", expected_model_type="plan-of-action-and-milestones"
        - Use when: "Check that catalog.json conforms to the OSCAL schema"
        - Don't use when: The file is inside a trestle workspace and you want
          the full `trestle validate` workspace checks.
    """
    result = validate_oscal_file(
        params.file,
        expected_model_type=params.expected_model_type,
        semantic=params.semantic,
    )

    model_desc = result.model_type or "unknown"

    if result.valid:
        checks = "schema" + (" + semantic" if params.semantic else "")
        return f"✅ Valid OSCAL {model_desc} ({checks})\n\n" f"File: {params.file}"

    detail = "\n".join(f"  - {m}" for m in result.messages) or "  - (no detail)"
    stage = "schema" if not result.schema_valid else "semantic"
    return (
        f"❌ Invalid OSCAL {model_desc} — failed {stage} validation\n\n"
        f"File: {params.file}\n\nIssues:\n{detail}"
    )
