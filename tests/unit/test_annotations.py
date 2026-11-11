#!/usr/bin/env python3
"""Test the MCP annotation hints, in particular `destructiveHint`.

A client may auto-approve tools that advertise themselves as non-destructive.
Twenty tools here can overwrite or remove content a caller already has and said
they were not destructive, so `trestle_author_component_generate` with
`force_overwrite=True` ran without a prompt and took the hand-written
implementation prose with it.

Per the MCP specification, `destructiveHint=False` means the tool performs only
*additive* updates. So the line drawn here is: can a successful run leave the
workspace without something that was in it before? Each entry below records the
answer and how it was checked against the real trestle CLI.
"""

import pytest

from trestle_mcp import tools

#: Tools whose successful run can replace or remove existing content.
DESTRUCTIVE = {
    "trestle_init": "re-copies .trestle/config.ini over the operator's task config",
    "trestle_remove": "deletes an element from a model, with no backup",
    "trestle_assemble": "writes dist/<name>.json over any existing one",
    "trestle_split": "moves an element out of the model file into its own file",
    "trestle_merge": "folds the split files back in and removes them",
    "trestle_href": "rewrites a profile's import href in place",
    "trestle_author_catalog_generate": "overwrites the markdown, hand edits included",
    "trestle_author_profile_generate": "overwrites the markdown, hand edits included",
    "trestle_author_component_generate": "overwrites the markdown, hand edits included",
    "trestle_author_ssp_generate": "overwrites the markdown, hand edits included",
    "trestle_author_catalog_assemble": "writes into the destination model if it exists",
    "trestle_author_profile_assemble": "writes into the destination model if it exists",
    "trestle_author_component_assemble": "writes into the destination model if it exists",
    "trestle_author_ssp_assemble": "writes into the destination model if it exists",
    "trestle_author_profile_resolve": "overwrites the output catalog",
    "trestle_author_profile_inherit": "saves over an existing profile of that name",
    "trestle_author_ssp_filter": "saves over an existing SSP of that name",
    "trestle_task_csv_to_oscal_cd": "output_overwrite defaults to true",
    "trestle_task_csv_to_oscal_mc": "output_overwrite defaults to true",
    "trestle_task_xlsx_to_oscal_poam": "output_overwrite defaults to true",
    "trestle_task_run": "runs any task, to any output path, with any config",
}

#: Tools that only add, or only read. Each refusal below was checked by running
#: the command twice against the real CLI.
ADDITIVE = {
    "trestle_import": "refuses: 'Cannot import because file ... already exists'",
    "trestle_create": "refuses: 'OSCAL file to be created here ... exists'",
    "trestle_replicate": "refuses: 'OSCAL file to be replicated here ... exists'",
    "trestle_validate": "reads only",
    "trestle_describe": "reads only",
    "trestle_partial_object_validate": "reads only",
    "trestle_version": "reads only",
    "trestle_task_list": "reads only",
}


class TestDestructiveHint:
    """Test suite for destructiveHint across the tool table."""

    def test_every_tool_is_classified(self):
        """Test the two lists together cover the table exactly.

        A tool added without a decision here is the failure this catches: the
        default is False, which is the permissive answer.
        """
        classified = set(DESTRUCTIVE) | set(ADDITIVE)
        assert set(tools.TOOL_SPECS_BY_NAME) == classified
        assert not (set(DESTRUCTIVE) & set(ADDITIVE))

    @pytest.mark.parametrize("name", sorted(DESTRUCTIVE))
    def test_a_destructive_tool_says_so(self, name):
        """Test each overwriting tool advertises destructiveHint."""
        spec = tools.TOOL_SPECS_BY_NAME[name]
        assert spec.annotations["destructiveHint"] is True, (
            f"{name} {DESTRUCTIVE[name]}, so a client that auto-approves "
            f"non-destructive tools would run it without asking"
        )

    @pytest.mark.parametrize("name", sorted(ADDITIVE))
    def test_an_additive_tool_is_not_marked_destructive(self, name):
        """Test the hint keeps its meaning by not being set everywhere."""
        spec = tools.TOOL_SPECS_BY_NAME[name]
        assert spec.annotations["destructiveHint"] is False, (
            f"{name} {ADDITIVE[name]}, so marking it destructive would make "
            f"the hint useless to a client deciding what to prompt for"
        )

    def test_a_read_only_tool_is_never_destructive(self):
        """Test the two hints cannot contradict each other."""
        for spec in tools.TOOL_SPECS:
            if spec.annotations["readOnlyHint"]:
                assert spec.annotations["destructiveHint"] is False, spec.name
