"""Shared OSCAL enumerations used by several trestle commands.

Keeping these in one place means the model-type and file-extension choices the
trestle CLI accepts are declared once, rather than once per service module.
"""

from enum import Enum


class OscalModelType(str, Enum):
    """Top-level OSCAL model types trestle can manage in a workspace.

    These are exactly the choices accepted by the `-t/--type` argument of
    `trestle create`, `trestle assemble`, `trestle replicate`, `trestle validate`
    and `trestle version`.
    """

    ASSESSMENT_PLAN = "assessment-plan"
    ASSESSMENT_RESULTS = "assessment-results"
    CATALOG = "catalog"
    COMPONENT_DEFINITION = "component-definition"
    MAPPING_COLLECTION = "mapping-collection"
    PLAN_OF_ACTION_AND_MILESTONES = "plan-of-action-and-milestones"
    PROFILE = "profile"
    SYSTEM_SECURITY_PLAN = "system-security-plan"


class FileExtension(str, Enum):
    """Serialization formats trestle can write for a model."""

    JSON = "json"
    YAML = "yaml"
    YML = "yml"
