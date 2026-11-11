#!/usr/bin/env python3
"""Unit tests for the tool registry and the startup tool selection."""

import asyncio

import pytest

from trestle_mcp import tools
from trestle_mcp.main import _build_arg_parser, build_server, register_tool


def _names(selector):
    return [spec.name for spec in tools.resolve_tool_specs(selector)]


def _selectable_names():
    """Every tool a group can select, i.e. the table minus the opt-in tools."""
    return [spec.name for spec in tools.TOOL_SPECS if not spec.opt_in]


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

    def test_structural_groups_partition_the_selectable_table(self):
        """Test core, author and task cover every selectable tool, once each."""
        total = sum(
            len(tools.group_members(group)) for group in tools.STRUCTURAL_GROUPS
        )
        assert total == len(_selectable_names())

    def test_opt_in_tools_still_have_a_structural_group(self):
        """Test an opt-in tool is documented with its peers even though no group
        selects it."""
        for spec in tools.TOOL_SPECS:
            if spec.opt_in:
                assert spec.group in tools.STRUCTURAL_GROUPS

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

    def test_all_selects_every_selectable_tool(self):
        """Test 'all' selects the whole table except the opt-in tools."""
        assert _names("all") == _selectable_names()

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


class TestSelectorFromEnvironment:
    """Test suite for selector_from_environment."""

    def test_environment_variable_is_read(self):
        """Test the env var supplies the selector."""
        assert tools.selector_from_environment(env={tools.ENV_TOOLS: "all"}) == "all"

    def test_no_source_gives_none(self):
        """Test an unconfigured server reports no selector, so the default wins."""
        assert tools.selector_from_environment(env={}) is None

    def test_the_flag_is_not_read_here(self):
        """Test the selector helper no longer parses the command line.

        It used to scan sys.argv, which made it a second parser disagreeing with
        the argparse one in main. The flag now arrives only through the parsed
        arguments -- see TestToolsFlagHasOneParser.
        """
        assert not hasattr(tools, "selector_from_sources")


class TestToolsFlagHasOneParser:
    """Test the --tools flag means the same thing to parsing and registration.

    Two parsers used to read this flag: argparse in main, for validation and
    --help, and an exact-match scan of sys.argv, for the value actually used.
    argparse accepts prefix abbreviations and keeps the last of a repeated flag,
    the scan did neither, so a selection could validate as one thing and be
    applied as another -- the silent misconfiguration the startup check exists
    to prevent.
    """

    def test_an_abbreviated_flag_is_rejected(self):
        """Test `--tool core` is an error rather than a guess.

        It used to parse cleanly as `--tools core` and then register the default
        selection, because the scan found no exact `--tools`.
        """
        parser = _build_arg_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--tool", "core"])

    def test_a_repeated_flag_keeps_the_last_value(self):
        """Test the parsed value is what main applies.

        argparse has always kept the last; the scan took the first, so
        `--tools core --tools task` validated `task` and registered `core`.
        """
        args = _build_arg_parser().parse_args(["--tools", "core", "--tools", "task"])
        assert args.tools == "task"

    def test_a_dangling_flag_is_rejected(self):
        """Test `--tools` with no value is an error, not a fall-through.

        The scan ignored a valueless flag and quietly used the environment.
        """
        parser = _build_arg_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--tools"])

    def test_the_equals_form_still_works(self):
        """Test `--tools=VALUE` is accepted, as the README documents."""
        args = _build_arg_parser().parse_args(["--tools=task,core"])
        assert args.tools == "task,core"

    def test_no_flag_leaves_the_environment_to_decide(self):
        """Test an absent flag parses to None, which main reads as 'use the env'."""
        assert _build_arg_parser().parse_args([]).tools is None


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

    def test_all_registers_every_selectable_tool(self):
        """Test 'all' registers the whole table except the opt-in tools."""
        server = build_server("all")
        assert self._registered(server) == _selectable_names()
        assert server.trestle_mcp_tool_names == tuple(_selectable_names())

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


class TestOptInTools:
    """Test suite for tools that no group selects.

    An opt-in tool must be unreachable through any group, `all` included, so
    that a broad selection cannot hand an agent a tool that destroys content.
    """

    def test_there_is_at_least_one_opt_in_tool(self):
        """Test the opt-in mechanism is actually exercised by the table."""
        assert tools.OPT_IN_TOOL_NAMES

    def test_remove_is_opt_in(self):
        """Test trestle_remove is the destructive tool kept behind a name."""
        assert "trestle_remove" in tools.OPT_IN_TOOL_NAMES
        assert tools.TOOL_SPECS_BY_NAME["trestle_remove"].opt_in is True

    def test_remove_is_annotated_destructive(self):
        """Test the client is told what the tool does before it is called."""
        annotations = tools.TOOL_SPECS_BY_NAME["trestle_remove"].annotations
        assert annotations["destructiveHint"] is True
        assert annotations["readOnlyHint"] is False

    @pytest.mark.parametrize("group", tools.GROUP_NAMES)
    def test_no_group_selects_an_opt_in_tool(self, group):
        """Test every group, 'all' included, leaves the opt-in tools out."""
        members = tools.group_members(group)
        for name in tools.OPT_IN_TOOL_NAMES:
            assert name not in members, f"{group} selects {name}"

    @pytest.mark.parametrize("group", tools.GROUP_NAMES)
    def test_no_group_registers_an_opt_in_tool(self, group):
        """Test the same holds end to end, through a built server."""
        server = build_server(group)
        for name in tools.OPT_IN_TOOL_NAMES:
            assert name not in server.trestle_mcp_tool_names

    def test_default_selection_omits_opt_in_tools(self):
        """Test an operator who configures nothing does not get them."""
        assert "trestle_remove" not in _names(None)

    def test_an_opt_in_tool_is_selected_by_its_exact_name(self):
        """Test naming it is the one way in."""
        assert _names("trestle_remove") == ["trestle_remove"]

    def test_an_opt_in_tool_combines_with_a_group(self):
        """Test the documented 'all,trestle_remove' form registers everything."""
        names = _names("all,trestle_remove")
        assert names == [spec.name for spec in tools.TOOL_SPECS]
        assert "trestle_remove" in names

    def test_opt_in_tools_are_listed_in_the_error_message(self):
        """Test a bad selector still tells the reader the tool exists.

        A tool no group selects is easy to miss, so the valid-names help has to
        name it, and to say that only naming it works.
        """
        with pytest.raises(tools.ToolSelectionError) as error:
            tools.resolve_tool_specs("nope")
        message = str(error.value)
        assert "trestle_remove" in message
        assert "only by name" in message
