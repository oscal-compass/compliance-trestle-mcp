#!/usr/bin/env python3
"""Unit tests for the tool registry and the startup tool selection."""

import asyncio

import pytest

from trestle_mcp import tools
from trestle_mcp.main import build_server, register_tool


def _names(selector):
    return [spec.name for spec in tools.resolve_tool_specs(selector)]


class TestToolTable:
    """Test suite for the tool table itself."""

    def test_names_are_unique(self):
        """Test no tool name is registered twice."""
        names = [spec.name for spec in tools.TOOL_SPECS]
        assert len(names) == len(set(names))

    def test_every_tool_has_a_structural_group(self):
        """Test each tool is in exactly one of core/author/task."""
        for spec in tools.TOOL_SPECS:
            assert spec.group in tools.STRUCTURAL_GROUPS

    def test_structural_groups_partition_the_table(self):
        """Test core, author and task together cover every tool, once each."""
        total = sum(
            len(tools.group_members(group)) for group in tools.STRUCTURAL_GROUPS
        )
        assert total == len(tools.TOOL_SPECS)

    def test_every_tool_has_a_description(self):
        """Test the docstring that becomes the tool description is present."""
        for spec in tools.TOOL_SPECS:
            assert spec.handler.__doc__, f"{spec.name} has no docstring"

    def test_input_model_matches_the_handler_annotation(self):
        """Test the table's input_model agrees with the service signature."""
        for spec in tools.TOOL_SPECS:
            assert spec.handler.__annotations__["params"] is spec.input_model


class TestResolveToolSpecs:
    """Test suite for resolve_tool_specs."""

    def test_default_is_authoring(self):
        """Test an unset selector gives the curated authoring lifecycle."""
        assert tools.DEFAULT_SELECTOR == "authoring"
        assert _names(None) == _names("authoring")
        assert _names("") == _names("authoring")
        assert _names("   ") == _names("authoring")

    def test_authoring_preset_contents(self):
        """Test the authoring preset is the documented 13 tools."""
        assert _names("authoring") == [
            "trestle_init",
            "trestle_import",
            "trestle_validate",
            "trestle_author_catalog_generate",
            "trestle_author_catalog_assemble",
            "trestle_author_profile_generate",
            "trestle_author_profile_assemble",
            "trestle_author_profile_resolve",
            "trestle_author_component_generate",
            "trestle_author_component_assemble",
            "trestle_task_csv_to_oscal_cd",
            "trestle_task_csv_to_oscal_mc",
            "trestle_task_xlsx_to_oscal_poam",
        ]

    @pytest.mark.parametrize("group", tools.STRUCTURAL_GROUPS)
    def test_structural_group_selects_its_own_members(self, group):
        """Test each structural group selects exactly the tools in it."""
        selected = tools.resolve_tool_specs(group)
        assert selected
        assert all(spec.group == group for spec in selected)
        assert len(selected) == len(tools.group_members(group))

    def test_author_group_is_every_author_subcommand(self):
        """Test the author group mirrors the trestle author subcommands."""
        assert _names("author") == [
            "trestle_author_catalog_generate",
            "trestle_author_catalog_assemble",
            "trestle_author_profile_generate",
            "trestle_author_profile_assemble",
            "trestle_author_profile_resolve",
            "trestle_author_profile_inherit",
            "trestle_author_component_generate",
            "trestle_author_component_assemble",
            "trestle_author_ssp_generate",
            "trestle_author_ssp_assemble",
            "trestle_author_ssp_filter",
        ]

    def test_all_selects_everything(self):
        """Test 'all' selects the whole table."""
        assert _names("all") == [spec.name for spec in tools.TOOL_SPECS]

    def test_individual_tool_name(self):
        """Test a single tool can be selected by its registered name."""
        assert _names("trestle_author_ssp_generate") == ["trestle_author_ssp_generate"]

    def test_mixed_groups_and_tool_names(self):
        """Test a group and an extra tool combine, in table order."""
        selected = _names("authoring,trestle_author_ssp_generate")
        assert selected == sorted(
            selected, key=[s.name for s in tools.TOOL_SPECS].index
        )
        assert set(selected) == set(_names("authoring")) | {
            "trestle_author_ssp_generate"
        }
        assert len(selected) == len(_names("authoring")) + 1

    def test_mixed_groups(self):
        """Test two structural groups combine without duplication."""
        selected = _names("task,core")
        assert set(selected) == set(_names("task")) | set(_names("core"))
        assert len(selected) == len(set(selected))

    def test_duplicates_are_collapsed(self):
        """Test naming a tool that a selected group already covers is a no-op."""
        assert _names("authoring,trestle_init") == _names("authoring")

    def test_whitespace_and_empty_tokens_are_tolerated(self):
        """Test a selector written with spaces or a trailing comma still works."""
        assert _names(" core , task ,") == _names("core,task")

    def test_unknown_name_raises_with_the_valid_names(self):
        """Test an unknown token fails loudly and lists what is valid."""
        with pytest.raises(tools.ToolSelectionError) as excinfo:
            tools.resolve_tool_specs("authoring,trestle_author_ssp_generat")

        message = str(excinfo.value)
        assert "trestle_author_ssp_generat" in message
        assert "Valid group names:" in message
        assert "Valid tool names:" in message
        # the groups and a real tool name are both offered
        for group in tools.GROUP_NAMES:
            assert group in message
        assert "trestle_author_ssp_generate" in message

    def test_unknown_group_like_name_raises(self):
        """Test a plausible-but-wrong group name is still rejected."""
        with pytest.raises(tools.ToolSelectionError):
            tools.resolve_tool_specs("authors")


class TestSelectorFromSources:
    """Test suite for selector_from_sources."""

    def test_environment_variable_is_read(self):
        """Test the env var supplies the selector when no flag is given."""
        assert (
            tools.selector_from_sources(argv=[], env={tools.ENV_TOOLS: "all"}) == "all"
        )

    def test_no_source_gives_none(self):
        """Test an unconfigured server reports no selector, so the default wins."""
        assert tools.selector_from_sources(argv=[], env={}) is None

    def test_flag_wins_over_environment_variable(self):
        """Test --tools overrides TRESTLE_MCP_TOOLS."""
        assert (
            tools.selector_from_sources(
                argv=["--tools", "core"], env={tools.ENV_TOOLS: "all"}
            )
            == "core"
        )

    def test_flag_with_equals_form(self):
        """Test --tools=VALUE is accepted as well as --tools VALUE."""
        assert (
            tools.selector_from_sources(argv=["--tools=task,core"], env={})
            == "task,core"
        )

    def test_dangling_flag_falls_back_to_environment(self):
        """Test a --tools with no value does not shadow the env var."""
        assert (
            tools.selector_from_sources(
                argv=["--tools"], env={tools.ENV_TOOLS: "author"}
            )
            == "author"
        )


class TestBuildServer:
    """Test suite for building a server from a selection."""

    def _registered(self, server):
        return [tool.name for tool in asyncio.run(server.list_tools())]

    def test_default_registers_the_authoring_preset(self):
        """Test the default selection registers 13 tools."""
        server = build_server("")
        assert self._registered(server) == _names("authoring")
        assert len(self._registered(server)) == 13
        assert server.trestle_mcp_selector == "authoring"

    def test_all_registers_every_tool(self):
        """Test 'all' registers the whole table."""
        server = build_server("all")
        assert self._registered(server) == [spec.name for spec in tools.TOOL_SPECS]
        assert server.trestle_mcp_tool_names == tuple(
            spec.name for spec in tools.TOOL_SPECS
        )

    def test_mixed_selection_registers_the_union(self):
        """Test a group plus an individual tool are both registered."""
        server = build_server("task,trestle_author_ssp_filter")
        registered = self._registered(server)
        assert "trestle_author_ssp_filter" in registered
        assert "trestle_task_run" in registered
        assert "trestle_init" not in registered

    def test_registered_tools_keep_their_metadata(self):
        """Test the title, description and annotations survive registration."""
        server = build_server("trestle_author_ssp_generate")
        tool = asyncio.run(server.list_tools())[0]
        spec = tools.TOOL_SPECS_BY_NAME["trestle_author_ssp_generate"]
        assert tool.title == spec.title
        assert tool.description == spec.handler.__doc__
        assert tool.annotations.openWorldHint is True
        assert tool.annotations.readOnlyHint is False

    def test_registered_tool_has_the_input_schema_of_its_model(self):
        """Test the schema comes from the service's pydantic input model."""
        server = build_server("trestle_merge")
        tool = asyncio.run(server.list_tools())[0]
        # the handler takes a single `params` object of the input model type
        assert "params" in tool.inputSchema["properties"]

    def test_unknown_selection_raises(self):
        """Test building with a bad selection raises rather than under-registering."""
        with pytest.raises(tools.ToolSelectionError):
            build_server("core,not-a-tool")

    def test_register_tool_rejects_a_mismatched_input_model(self):
        """Test a copy/paste error in the tool table fails at registration."""
        from mcp.server.fastmcp import FastMCP

        from trestle_mcp.services import version as version_service

        bad = tools.ToolSpec(
            name="trestle_bad",
            title="Bad",
            group="core",
            input_model=tools.TOOL_SPECS_BY_NAME["trestle_merge"].input_model,
            handler=version_service.trestle_version,
            annotations={},
        )
        with pytest.raises(TypeError, match="does not match"):
            register_tool(FastMCP("probe"), bad)
