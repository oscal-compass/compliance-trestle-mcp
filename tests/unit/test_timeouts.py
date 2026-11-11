#!/usr/bin/env python3
"""Test which tools get the long timeout, and that the list is deliberate.

`ssp-generate` had `LONG_TIMEOUT` while `component-generate`,
`component-assemble`, `ssp-assemble`, `ssp-filter` and `profile-inherit` --
which resolve the same profiles over the same catalogs -- were left on the 60s
default, so the same input succeeded through one tool and timed out through
another. Nothing caught that, because the choice was made per service with
nothing comparing them.

This test is that comparison. It is a ratchet, not a derivation: there is no way
to read "this command resolves a profile" out of the CLI, so the list is written
down and a change to it has to be a change here too.
"""

import inspect

import pytest

from trestle_mcp import tools
from trestle_mcp.libs.trestle import DEFAULT_TIMEOUT, LONG_TIMEOUT

#: Tools whose command resolves a profile, walks a whole catalog, or fetches
#: remote content, with the reason. Anything here must pass LONG_TIMEOUT.
#:
#: Judge it by what trestle ends up doing. trestle's prof.py calls
#: `ProfileResolver` from four classes, all unconditionally -- Generate,
#: Assemble, Resolve and Inherit -- so all four cost what profile resolution
#: costs, however their commands are named.
SLOW_TOOLS = {
    "trestle_import": "fetches the model, which may be a remote catalog",
    "trestle_author_profile_resolve": "walks every control in the imported catalog",
    "trestle_author_profile_generate": "resolves the profile before writing markdown",
    "trestle_author_profile_assemble": "resolves the profile when reading markdown back",
    "trestle_author_catalog_generate": "writes a markdown file per control",
    "trestle_author_catalog_assemble": "reads a markdown file per control",
    "trestle_author_profile_inherit": "resolves the parent profile and the leveraged SSP's",
    "trestle_author_component_generate": "resolves each rule's Profile_Source",
    "trestle_author_component_assemble": "re-resolves each rule's Profile_Source",
    "trestle_author_ssp_generate": "resolves the profile it generates from",
    "trestle_author_ssp_assemble": "loads markdown for every control in the baseline",
    "trestle_author_ssp_filter": "resolves the profile it filters by",
    "trestle_task_csv_to_oscal_cd": "reads a spreadsheet and may resolve a profile",
    "trestle_task_csv_to_oscal_mc": "resolves the profile on either side of a mapping",
    "trestle_task_xlsx_to_oscal_poam": "reads a spreadsheet",
    "trestle_task_run": "runs an arbitrary task, so assume the slowest",
}


def handler_source(name: str) -> str:
    """Return the source of a tool's handler function."""
    return inspect.getsource(tools.TOOL_SPECS_BY_NAME[name].handler)


def passes_long_timeout(name: str) -> bool:
    """Report whether a tool's handler asks for the long timeout."""
    return "timeout=LONG_TIMEOUT" in handler_source(name)


class TestTheLongTimeoutIsAppliedConsistently:
    """Test suite for the timeout each tool asks for."""

    def test_the_long_timeout_is_actually_longer(self):
        """Test the two constants are not accidentally equal."""
        assert LONG_TIMEOUT > DEFAULT_TIMEOUT

    def test_every_slow_tool_is_a_real_tool(self):
        """Test the list below does not name a tool that no longer exists."""
        unknown = sorted(set(SLOW_TOOLS) - set(tools.TOOL_SPECS_BY_NAME))
        assert not unknown, f"SLOW_TOOLS names tools that do not exist: {unknown}"

    @pytest.mark.parametrize("name", sorted(SLOW_TOOLS))
    def test_a_slow_tool_asks_for_the_long_timeout(self, name):
        """Test each tool that resolves or fetches passes LONG_TIMEOUT."""
        assert passes_long_timeout(name), (
            f"{name} {SLOW_TOOLS[name]}, so it needs timeout=LONG_TIMEOUT; "
            f"the 60s default fails on a real baseline"
        )

    def test_no_other_tool_asks_for_the_long_timeout(self):
        """Test a tool outside the list is not quietly given ten minutes.

        The long timeout is how long a stuck command holds its worker thread, so
        it is not a free default -- a tool that takes it should be listed above
        with the reason.
        """
        unexpected = sorted(
            name
            for name in tools.TOOL_SPECS_BY_NAME
            if name not in SLOW_TOOLS and passes_long_timeout(name)
        )
        assert not unexpected, (
            f"these tools pass LONG_TIMEOUT but are not listed in SLOW_TOOLS "
            f"with a reason: {unexpected}"
        )
