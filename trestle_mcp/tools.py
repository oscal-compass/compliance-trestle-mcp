"""Tool registry and startup tool selection.

Every tool an MCP server registers costs the caller context: the client loads
each tool's name, input schema and description into the model's context window
on every session. This server covers the trestle command surface an agent should
drive -- see ``docs/command-specs-development.md`` for what is deliberately left
out -- but lets the caller choose how much of it to expose, so a session carries
the part it will actually call and the rest is one configuration value away.
``scripts/tool_context_cost.py`` measures what each selection costs.

The selection is a comma-separated list of group names and individual tool
names, read from the ``--tools`` CLI flag or the ``TRESTLE_MCP_TOOLS``
environment variable (the flag wins). The default is ``authoring``.

Groups:

* ``core``, ``author``, ``task`` are structural and mirror the trestle CLI's own
  command structure, so which tool is in which group is predictable from the CLI
  rather than from a taxonomy invented here.
* ``authoring`` is the one curated preset: the authoring lifecycle, and the
  default.
* ``all`` is every tool a group can select.

A tool marked ``opt_in`` is selected by no group, ``all`` included, and is
registered only when the selection names it exactly. That is reserved for tools
whose effect cannot be undone from inside the workspace: ``trestle_remove``
deletes part of a model in place, with no backup, so an agent should not be able
to reach for it merely because the operator asked for a broad group.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable, Mapping, Optional

from pydantic import BaseModel

from trestle_mcp import services

#: Environment variable read at startup when ``--tools`` is not given.
ENV_TOOLS = "TRESTLE_MCP_TOOLS"

#: Command line flag that overrides ENV_TOOLS.
FLAG_TOOLS = "--tools"

#: Selection applied when neither the flag nor the environment variable is set.
DEFAULT_SELECTOR = "authoring"

#: Structural groups, mirroring the trestle CLI command structure.
STRUCTURAL_GROUPS = ("core", "author", "task")

#: Curated cross-cutting presets.
PRESET_GROUPS = ("authoring",)

#: Meta group selecting every tool.
GROUP_ALL = "all"

GROUP_NAMES = (*STRUCTURAL_GROUPS, *PRESET_GROUPS, GROUP_ALL)

GROUP_DESCRIPTIONS = {
    "core": "top-level trestle commands (init, import, create, split, merge, ...)",
    "author": "every trestle author subcommand wrapper",
    "task": "every trestle task wrapper, including the generic task runner",
    "authoring": "the curated authoring lifecycle (default)",
    GROUP_ALL: "every tool this server implements",
}


class ToolSelectionError(ValueError):
    """Raised when a tool selector names something that does not exist."""


@dataclass(frozen=True)
class ToolSpec:
    """One registrable MCP tool.

    Attributes:
        name: The registered MCP tool name.
        title: Human readable title shown by clients.
        group: Structural group, one of STRUCTURAL_GROUPS.
        input_model: The pydantic model the handler takes.
        handler: The async service function; its docstring is the tool
            description.
        annotations: MCP tool annotations (readOnlyHint and friends).
        presets: Additional groups this tool belongs to, e.g. ("authoring",).
        opt_in: When true, no group selects this tool — not even GROUP_ALL — and
            only a selection naming it exactly registers it. `group` and
            `presets` still record where the tool belongs structurally, so it is
            documented with its peers.
    """

    name: str
    title: str
    group: str
    input_model: type[BaseModel]
    handler: Callable[[Any], Awaitable[str]]
    annotations: Mapping[str, bool]
    presets: tuple[str, ...] = ()
    opt_in: bool = False

    @property
    def groups(self) -> frozenset[str]:
        """The groups this tool belongs to structurally, excluding GROUP_ALL.

        Membership here does not imply a group selects the tool: see `opt_in`.
        """
        return frozenset((self.group, *self.presets))


def _annotations(
    *,
    read_only: bool = False,
    destructive: bool = False,
    idempotent: bool = False,
    open_world: bool = False,
) -> dict[str, bool]:
    """Build the MCP annotations dict, keeping the hint names in one place."""
    return {
        "readOnlyHint": read_only,
        "destructiveHint": destructive,
        "idempotentHint": idempotent,
        "openWorldHint": open_world,
    }


_AUTHORING = ("authoring",)

#: The full tool table. Registration order follows this table.
TOOL_SPECS: tuple[ToolSpec, ...] = (
    # ---- core: top-level trestle commands ----------------------------------
    ToolSpec(
        name="trestle_init",
        title="Initialize Trestle Workspace",
        group="core",
        input_model=services.init.TrestleInitInput,
        handler=services.init.trestle_init,
        annotations=_annotations(idempotent=True),
        presets=_AUTHORING,
    ),
    ToolSpec(
        name="trestle_import",
        title="Import OSCAL Model",
        group="core",
        input_model=services.import_.TrestleImportInput,
        handler=services.import_.trestle_import,
        annotations=_annotations(open_world=True),
        presets=_AUTHORING,
    ),
    ToolSpec(
        name="trestle_validate",
        title="Validate OSCAL Document",
        group="core",
        input_model=services.validate.TrestleValidateInput,
        handler=services.validate.trestle_validate,
        annotations=_annotations(read_only=True, idempotent=True),
        presets=_AUTHORING,
    ),
    ToolSpec(
        name="trestle_create",
        title="Create OSCAL Model or Element",
        group="core",
        input_model=services.create.TrestleCreateInput,
        handler=services.create.trestle_create,
        annotations=_annotations(),
    ),
    # Opt-in: the inverse of trestle_create's element mode, but it deletes model
    # content in place with no backup, so no group selects it — see `opt_in`.
    ToolSpec(
        name="trestle_remove",
        title="Remove an Element from an OSCAL Model",
        group="core",
        input_model=services.remove.TrestleRemoveInput,
        handler=services.remove.trestle_remove,
        annotations=_annotations(destructive=True),
        opt_in=True,
    ),
    ToolSpec(
        name="trestle_assemble",
        title="Assemble Model into dist",
        group="core",
        input_model=services.assemble.TrestleAssembleInput,
        handler=services.assemble.trestle_assemble,
        annotations=_annotations(idempotent=True),
    ),
    ToolSpec(
        name="trestle_split",
        title="Split Model into Subcomponents",
        group="core",
        input_model=services.split.TrestleSplitInput,
        handler=services.split.trestle_split,
        annotations=_annotations(),
    ),
    ToolSpec(
        name="trestle_merge",
        title="Merge Subcomponents into Model",
        group="core",
        input_model=services.merge.TrestleMergeInput,
        handler=services.merge.trestle_merge,
        annotations=_annotations(),
    ),
    ToolSpec(
        name="trestle_describe",
        title="Describe OSCAL Model Contents",
        group="core",
        input_model=services.describe.TrestleDescribeInput,
        handler=services.describe.trestle_describe,
        annotations=_annotations(read_only=True, idempotent=True),
    ),
    ToolSpec(
        name="trestle_replicate",
        title="Replicate OSCAL Model",
        group="core",
        input_model=services.replicate.TrestleReplicateInput,
        handler=services.replicate.trestle_replicate,
        annotations=_annotations(),
    ),
    ToolSpec(
        name="trestle_href",
        title="List or Change Profile Import hrefs",
        group="core",
        input_model=services.href.TrestleHrefInput,
        handler=services.href.trestle_href,
        annotations=_annotations(),
    ),
    ToolSpec(
        name="trestle_partial_object_validate",
        title="Validate a Partial OSCAL Object",
        group="core",
        input_model=services.partial_object_validate.TrestlePartialObjectValidateInput,
        handler=services.partial_object_validate.trestle_partial_object_validate,
        annotations=_annotations(read_only=True, idempotent=True),
    ),
    ToolSpec(
        name="trestle_version",
        title="Report Trestle and OSCAL Versions",
        group="core",
        input_model=services.version.TrestleVersionInput,
        handler=services.version.trestle_version,
        annotations=_annotations(read_only=True, idempotent=True),
    ),
    # ---- author: trestle author subcommands ---------------------------------
    ToolSpec(
        name="trestle_author_catalog_generate",
        title="Generate Catalog Markdown Controls",
        group="author",
        input_model=services.author.catalog_generate.TrestleCatalogGenerateInput,
        handler=services.author.catalog_generate.trestle_catalog_generate,
        annotations=_annotations(open_world=True),
        presets=_AUTHORING,
    ),
    ToolSpec(
        name="trestle_author_catalog_assemble",
        title="Assemble Catalog JSON from Markdown",
        group="author",
        input_model=services.author.catalog_assemble.TrestleAuthorCatalogAssembleInput,
        handler=services.author.catalog_assemble.trestle_author_catalog_assemble,
        annotations=_annotations(open_world=True),
        presets=_AUTHORING,
    ),
    ToolSpec(
        name="trestle_author_profile_generate",
        title="Generate Profile Markdown Controls",
        group="author",
        input_model=services.author.profile_generate.TrestleAuthorProfileGenerateInput,
        handler=services.author.profile_generate.trestle_author_profile_generate,
        annotations=_annotations(open_world=True),
        presets=_AUTHORING,
    ),
    ToolSpec(
        name="trestle_author_profile_assemble",
        title="Assemble Profile JSON from Markdown Directory",
        group="author",
        input_model=services.author.profile_assemble.TrestleAuthorProfileAssembleInput,
        handler=services.author.profile_assemble.trestle_author_profile_assemble,
        annotations=_annotations(open_world=True),
        presets=_AUTHORING,
    ),
    ToolSpec(
        name="trestle_author_profile_resolve",
        title="Resolve Profile to Catalog",
        group="author",
        input_model=services.author.profile_resolve.TrestleAuthorProfileResolveInput,
        handler=services.author.profile_resolve.trestle_author_profile_resolve,
        annotations=_annotations(open_world=True),
        presets=_AUTHORING,
    ),
    ToolSpec(
        name="trestle_author_profile_inherit",
        title="Generate Inherited Profile from Leveraged SSP",
        group="author",
        input_model=services.author.profile_inherit.TrestleAuthorProfileInheritInput,
        handler=services.author.profile_inherit.trestle_author_profile_inherit,
        annotations=_annotations(),
    ),
    ToolSpec(
        name="trestle_author_component_generate",
        title="Generate Component Markdown",
        group="author",
        input_model=services.author.component_generate.TrestleAuthorComponentGenerateInput,
        handler=services.author.component_generate.trestle_author_component_generate,
        annotations=_annotations(open_world=True),
        presets=_AUTHORING,
    ),
    ToolSpec(
        name="trestle_author_component_assemble",
        title="Assemble Component Definition from Markdown",
        group="author",
        input_model=services.author.component_assemble.TrestleAuthorComponentAssembleInput,
        handler=services.author.component_assemble.trestle_author_component_assemble,
        annotations=_annotations(open_world=True),
        presets=_AUTHORING,
    ),
    ToolSpec(
        name="trestle_author_ssp_generate",
        title="Generate SSP Markdown from Profile",
        group="author",
        input_model=services.author.ssp_generate.TrestleAuthorSspGenerateInput,
        handler=services.author.ssp_generate.trestle_author_ssp_generate,
        annotations=_annotations(open_world=True),
    ),
    ToolSpec(
        name="trestle_author_ssp_assemble",
        title="Assemble SSP JSON from Markdown",
        group="author",
        input_model=services.author.ssp_assemble.TrestleAuthorSspAssembleInput,
        handler=services.author.ssp_assemble.trestle_author_ssp_assemble,
        annotations=_annotations(open_world=True),
    ),
    ToolSpec(
        name="trestle_author_ssp_filter",
        title="Filter Controls in an SSP",
        group="author",
        input_model=services.author.ssp_filter.TrestleAuthorSspFilterInput,
        handler=services.author.ssp_filter.trestle_author_ssp_filter,
        annotations=_annotations(idempotent=True),
    ),
    # ---- task: trestle task wrappers ---------------------------------------
    ToolSpec(
        name="trestle_task_csv_to_oscal_cd",
        title="Convert CSV to OSCAL Component Definition",
        group="task",
        input_model=services.task.csv_to_oscal_cd.TrestleTaskCsvToOscalCdInput,
        handler=services.task.csv_to_oscal_cd.trestle_task_csv_to_oscal_cd,
        annotations=_annotations(),
        presets=_AUTHORING,
    ),
    ToolSpec(
        name="trestle_task_csv_to_oscal_mc",
        title="Convert CSV to OSCAL Mapping Collection",
        group="task",
        input_model=services.task.csv_to_oscal_mc.TrestleTaskCsvToOscalMcInput,
        handler=services.task.csv_to_oscal_mc.trestle_task_csv_to_oscal_mc,
        annotations=_annotations(),
        presets=_AUTHORING,
    ),
    ToolSpec(
        name="trestle_task_xlsx_to_oscal_poam",
        title="Convert FedRAMP XLSX to OSCAL POA&M",
        group="task",
        input_model=services.task.xlsx_to_oscal_poam.TrestleTaskXlsxToOscalPoamInput,
        handler=services.task.xlsx_to_oscal_poam.trestle_task_xlsx_to_oscal_poam,
        annotations=_annotations(),
        presets=_AUTHORING,
    ),
    ToolSpec(
        name="trestle_task_list",
        title="List or Describe Trestle Tasks",
        group="task",
        input_model=services.task.task_list.TrestleTaskListInput,
        handler=services.task.task_list.trestle_task_list,
        annotations=_annotations(read_only=True, idempotent=True),
    ),
    ToolSpec(
        name="trestle_task_run",
        title="Run Any Trestle Task",
        group="task",
        input_model=services.task.task_run.TrestleTaskRunInput,
        handler=services.task.task_run.trestle_task_run,
        annotations=_annotations(),
    ),
)

TOOL_SPECS_BY_NAME = {spec.name: spec for spec in TOOL_SPECS}


#: Tools no group selects; only a selection naming one exactly registers it.
OPT_IN_TOOL_NAMES = tuple(spec.name for spec in TOOL_SPECS if spec.opt_in)


def group_members(group: str) -> list[str]:
    """Names of the tools a group selects, in registration order.

    Opt-in tools are never included, GROUP_ALL included: a group is a convenience
    and must not quietly hand over a tool that deletes model content.
    """
    selectable = [spec for spec in TOOL_SPECS if not spec.opt_in]
    if group == GROUP_ALL:
        return [spec.name for spec in selectable]
    return [spec.name for spec in selectable if group in spec.groups]


def _valid_names_message() -> str:
    """The help text shown when a selector names something unknown."""
    lines = ["Valid group names:"]
    for group in GROUP_NAMES:
        members = group_members(group)
        lines.append(
            f"  {group:<12} {GROUP_DESCRIPTIONS[group]} ({len(members)} tools)"
        )
    lines.append("Valid tool names:")
    lines.extend(
        f"  {spec.name}" for spec in TOOL_SPECS if spec.name not in OPT_IN_TOOL_NAMES
    )
    if OPT_IN_TOOL_NAMES:
        lines.append("Valid tool names, selectable only by name (no group, not 'all'):")
        lines.extend(f"  {name}" for name in OPT_IN_TOOL_NAMES)
    return "\n".join(lines)


def resolve_tool_specs(selector: Optional[str]) -> list[ToolSpec]:
    """Resolve a selector string to the tool specs it selects.

    Args:
        selector: Comma-separated group and/or tool names. None or empty
            selects DEFAULT_SELECTOR.

    Returns:
        The selected specs, deduplicated, in TOOL_SPECS declaration order.

    Raises:
        ToolSelectionError: If a token is neither a group nor a tool name.
    """
    raw = (selector or "").strip() or DEFAULT_SELECTOR
    tokens = [token.strip() for token in raw.split(",")]
    tokens = [token for token in tokens if token]

    selected: set[str] = set()
    for token in tokens:
        if token == GROUP_ALL or token in GROUP_NAMES:
            selected.update(group_members(token))
        elif token in TOOL_SPECS_BY_NAME:
            selected.add(token)
        else:
            raise ToolSelectionError(
                f"unknown tool selection '{token}' in '{raw}'.\n\n"
                f"{_valid_names_message()}"
            )

    return [spec for spec in TOOL_SPECS if spec.name in selected]


def selector_from_sources(
    argv: Optional[Iterable[str]] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Optional[str]:
    """Read the selector from the command line, falling back to the environment.

    The ``--tools`` flag wins over ``TRESTLE_MCP_TOOLS`` because an ``.mcp.json``
    entry may carry either ``args`` or ``env``, and the more specific one should
    be the one that takes effect.

    Args:
        argv: Argument list without the program name. Defaults to sys.argv[1:].
        env: Environment mapping. Defaults to os.environ.

    Returns:
        The selector string, or None when neither source sets one.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    for index, arg in enumerate(args):
        if arg == FLAG_TOOLS and index + 1 < len(args):
            return args[index + 1]
        if arg.startswith(f"{FLAG_TOOLS}="):
            return arg.split("=", 1)[1]

    environment = os.environ if env is None else env
    return environment.get(ENV_TOOLS)
