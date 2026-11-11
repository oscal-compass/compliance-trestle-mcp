"""End-to-end tests for the tools added for the full command surface.

These run the real trestle CLI in a scratch workspace through the MCP server, so
they catch the failures a mocked argument-builder test cannot: a flag the CLI
wants positionally, a command that ignores --trestle-root, an assemble that
needs a source name.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict

import pytest
from fastmcp.client import Client

from trestle_mcp.main import build_server

DATA_DIR = Path(__file__).parent.parent / "data"

#: Workspace name the control source must be imported under.
#:
#: The Profile_Source column of tests/data/task/csv-to-oscal-cd/components.csv
#: is `trestle://catalogs/nist-sample/catalog.json`. component-generate resolves
#: that href, so the catalog has to exist in the workspace under this name. It
#: is a trestle:// href rather than a URL on purpose: the fixture used to point
#: at the NIST SP 800-53 rev5 catalog on raw.githubusercontent.com, which made
#: this suite download ~10 MB from a third party on every run and fail whenever
#: that host was unreachable.
CONTROL_SOURCE_NAME = "nist-sample"


async def call_tool(client: Client, name: str, params: Dict[str, Any]) -> str:
    """Call a tool and return its text result."""
    response = await client.call_tool(name, {"params": params}, raise_on_error=True)
    return response.content[0].text


@pytest.fixture
def workspace(tmp_path):
    """An initialized trestle workspace, with the process cwd inside it.

    The trestle CLI resolves several things against the process working
    directory, so the tests run from inside the workspace and restore the
    previous directory afterwards.
    """
    catalog = (DATA_DIR / "test-catalog.json").absolute()
    components_csv = (DATA_DIR / "task/csv-to-oscal-cd/components.csv").absolute()
    mapping_csv = (DATA_DIR / "task/csv-to-oscal-mc/mapping.csv").absolute()

    try:
        previous = Path.cwd()
    except FileNotFoundError:
        # A previous test chdir'd into a directory that has since been removed.
        previous = tmp_path
    os.chdir(tmp_path)
    try:
        yield {
            "root": tmp_path,
            "catalog": catalog,
            "components_csv": components_csv,
            "mapping_csv": mapping_csv,
        }
    finally:
        os.chdir(previous)


@pytest.mark.anyio
async def test_core_commands_round_trip(workspace):
    """Exercise the core group: create, describe, version, replicate, href, split, merge, assemble."""
    root = workspace["root"]

    async with Client(build_server("all")) as client:
        assert "✅" in await call_tool(client, "trestle_init", {"mode": "local"})

        # version, with no model: reports the trestle and OSCAL versions
        result = await call_tool(client, "trestle_version", {})
        assert "✅" in result
        assert "Trestle version" in result

        # create a model from scratch
        result = await call_tool(
            client, "trestle_create", {"model_type": "profile", "output": "newprof"}
        )
        assert "✅" in result
        assert (root / "profiles" / "newprof" / "profile.json").exists()

        # import a catalog to work on
        assert "✅" in await call_tool(
            client,
            "trestle_import",
            {"file": workspace["catalog"].as_posix(), "output": "source"},
        )

        # describe it
        result = await call_tool(
            client, "trestle_describe", {"file": "catalogs/source/catalog.json"}
        )
        assert "✅" in result
        assert "groups" in result

        # version of that specific model
        result = await call_tool(
            client, "trestle_version", {"name": "source", "model_type": "catalog"}
        )
        assert "✅" in result
        assert "source catalog" in result

        # replicate it with fresh uuids
        result = await call_tool(
            client,
            "trestle_replicate",
            {
                "model_type": "catalog",
                "name": "source",
                "output": "target",
                "regenerate": True,
            },
        )
        assert "✅" in result
        replica = root / "catalogs" / "target" / "catalog.json"
        assert replica.exists()
        original_uuid = json.loads(
            (root / "catalogs" / "source" / "catalog.json").read_text()
        )["catalog"]["uuid"]
        assert json.loads(replica.read_text())["catalog"]["uuid"] != original_uuid

        # split metadata out, then merge it back
        result = await call_tool(
            client,
            "trestle_split",
            {"file": "catalogs/source/catalog.json", "element": "catalog.metadata"},
        )
        assert "✅" in result
        assert (root / "catalogs" / "source" / "catalog" / "metadata.json").exists()

        # the split fragment validates on its own
        result = await call_tool(
            client,
            "trestle_partial_object_validate",
            {
                "file": "catalogs/source/catalog/metadata.json",
                "element": "catalog.metadata",
            },
        )
        assert "✅" in result

        # merge is run inside the model directory, not via --trestle-root
        result = await call_tool(
            client,
            "trestle_merge",
            {"element": "catalog.metadata", "model_dir": "catalogs/source"},
        )
        assert "✅" in result
        assert not (root / "catalogs" / "source" / "catalog" / "metadata.json").exists()

        # assemble to dist; the model type is positional for this command
        result = await call_tool(
            client, "trestle_assemble", {"model_type": "catalog", "name": "source"}
        )
        assert "✅" in result
        assert (root / "dist" / "catalogs" / "source.json").exists()


@pytest.mark.anyio
async def test_href_lists_and_repoints_profile_imports(workspace):
    """Exercise trestle_href in both its listing and its update mode."""
    root = workspace["root"]
    profile_src = (DATA_DIR / "test-profile.json").absolute()

    async with Client(build_server("core")) as client:
        await call_tool(client, "trestle_init", {"mode": "local"})
        await call_tool(
            client,
            "trestle_import",
            {"file": workspace["catalog"].as_posix(), "output": "source"},
        )
        await call_tool(
            client,
            "trestle_import",
            {"file": profile_src.as_posix(), "output": "prof"},
        )

        listing = await call_tool(client, "trestle_href", {"name": "prof"})
        assert "✅" in listing
        assert "imports listed" in listing
        assert "0:" in listing

        updated = await call_tool(
            client,
            "trestle_href",
            {
                "name": "prof",
                "href": "trestle://catalogs/source/catalog.json",
                "item": 0,
            },
        )
        assert "✅" in updated
        profile = json.loads((root / "profiles" / "prof" / "profile.json").read_text())
        assert profile["profile"]["imports"][0]["href"] == (
            "trestle://catalogs/source/catalog.json"
        )


@pytest.mark.anyio
async def test_catalog_markdown_round_trip(workspace):
    """Generate catalog markdown, edit a control, assemble it back into JSON."""
    root = workspace["root"]

    async with Client(build_server("authoring")) as client:
        await call_tool(client, "trestle_init", {"mode": "local"})
        await call_tool(
            client,
            "trestle_import",
            {"file": workspace["catalog"].as_posix(), "output": "source"},
        )

        assert "✅" in await call_tool(
            client,
            "trestle_author_catalog_generate",
            {"name": "source", "output": "md_cat"},
        )
        ac1 = root / "md_cat" / "ac" / "ac-1.md"
        assert ac1.exists()

        # edit the control prose, in the editable region the generator marks
        text = ac1.read_text()
        marker = "## Control Statement"
        assert marker in text
        ac1.write_text(text.replace(marker, f"{marker}\n\nEDITED BY TEST", 1))

        result = await call_tool(
            client,
            "trestle_author_catalog_assemble",
            {"markdown": "md_cat", "output": "assembled", "set_parameters": True},
        )
        assert "✅" in result
        assembled = root / "catalogs" / "assembled" / "catalog.json"
        assert assembled.exists()
        assert "EDITED BY TEST" in assembled.read_text()


@pytest.mark.anyio
async def test_component_definition_round_trip(workspace):
    """CSV to component-definition, out to markdown, and back to JSON."""
    root = workspace["root"]

    async with Client(build_server("authoring")) as client:
        await call_tool(client, "trestle_init", {"mode": "local"})

        # component-generate resolves each rule's Profile_Source, so the
        # catalog the CSV names has to be in the workspace first. See
        # CONTROL_SOURCE_NAME.
        assert "✅" in await call_tool(
            client,
            "trestle_import",
            {
                "file": workspace["catalog"].as_posix(),
                "output": CONTROL_SOURCE_NAME,
            },
        )

        result = await call_tool(
            client,
            "trestle_task_csv_to_oscal_cd",
            {
                "title": "ACME Component Definition",
                "version": "1.0.0",
                "csv_file": workspace["components_csv"].as_posix(),
                "output_dir": "component-definitions/acme",
            },
        )
        assert "✅" in result
        assert (
            root / "component-definitions" / "acme" / "component-definition.json"
        ).exists()

        result = await call_tool(
            client,
            "trestle_author_component_generate",
            {"name": "acme", "output": "md_comp"},
        )
        assert "✅" in result
        markdowns = list((root / "md_comp").rglob("*.md"))
        assert {path.name for path in markdowns} == {"ac-1.md", "ac-2.md"}

        # assembling to a new name needs the source name as well
        result = await call_tool(
            client,
            "trestle_author_component_assemble",
            {"name": "acme", "markdown": "md_comp", "output": "acme_v2"},
        )
        assert "✅" in result
        assembled = (
            root / "component-definitions" / "acme_v2" / "component-definition.json"
        )
        assert assembled.exists()
        document = json.loads(assembled.read_text())["component-definition"]
        assert document["components"][0]["title"] == "ACME Firewall"


@pytest.mark.anyio
async def test_csv_to_oscal_mapping_collection(workspace):
    """Build an OSCAL mapping-collection from a crosswalk CSV."""
    root = workspace["root"]

    async with Client(build_server("authoring")) as client:
        await call_tool(client, "trestle_init", {"mode": "local"})
        for name in ("source", "target"):
            await call_tool(
                client,
                "trestle_import",
                {"file": workspace["catalog"].as_posix(), "output": name},
            )

        # the CSV names its resources as workspace-relative paths
        csv_copy = root / "mapping.csv"
        shutil.copy(workspace["mapping_csv"], csv_copy)

        result = await call_tool(
            client,
            "trestle_task_csv_to_oscal_mc",
            {
                "title": "Test Crosswalk",
                "version": "1.0.0",
                "csv_file": csv_copy.as_posix(),
                "output_dir": "mapping-collections/test",
            },
        )
        assert "✅" in result
        output = root / "mapping-collections" / "test" / "mapping-collection.json"
        assert output.exists()

        collection = json.loads(output.read_text())["mapping-collection"]
        maps = collection["mappings"][0]["maps"]
        relationships = {entry["relationship"] for entry in maps}
        assert relationships == {"equivalent", "subset-of"}
        subset = next(e for e in maps if e["relationship"] == "subset-of")
        assert [item["id-ref"] for item in subset["targets"]] == ["ac-2", "ac-2.1"]
        # a confidence score inside the 0..1 range survives
        assert subset["confidence-score"]["percentage"] == 0.8


@pytest.mark.anyio
async def test_a_recovered_warning_reaches_the_caller(workspace):
    """A warning trestle writes to stderr on a successful run is reported.

    trestle drops a confidence score outside 0..1 and carries on, exiting 0.
    Returning stdout alone reported a clean success for a mapping collection
    that silently lost data, with nothing in the result to say so.
    """
    root = workspace["root"]

    async with Client(build_server("authoring")) as client:
        await call_tool(client, "trestle_init", {"mode": "local"})
        for name in ("source", "target"):
            await call_tool(
                client,
                "trestle_import",
                {"file": workspace["catalog"].as_posix(), "output": name},
            )

        # 80 instead of 0.8: out of range, so trestle warns and drops it
        rows = workspace["mapping_csv"].read_text(encoding="utf-8").splitlines()
        csv_copy = root / "out-of-range.csv"
        csv_copy.write_text(
            "\n".join(row.replace(",1.0", ",80") for row in rows) + "\n",
            encoding="utf-8",
        )

        result = await call_tool(
            client,
            "trestle_task_csv_to_oscal_mc",
            {
                "title": "Test Crosswalk",
                "version": "1.0.0",
                "csv_file": csv_copy.as_posix(),
                "output_dir": "mapping-collections/warned",
            },
        )

        assert "✅" in result
        assert "Percentage value out of range" in result

        # and the warning was worth having: the score really is gone
        output = root / "mapping-collections" / "warned" / "mapping-collection.json"
        maps = json.loads(output.read_text())["mapping-collection"]["mappings"][0][
            "maps"
        ]
        equivalent = next(e for e in maps if e["relationship"] == "equivalent")
        assert "confidence-score" not in equivalent


@pytest.mark.anyio
async def test_an_unresolvable_control_id_is_dropped_silently(workspace):
    """An id that does not resolve is dropped, and the run still succeeds.

    This pins the behaviour the tool description used to get wrong: it claimed a
    typo in a control id failed the run. trestle's get_id_list keeps only the
    ids it can resolve and warns about none of them, so the row is written with
    what was left and the caller is told it worked. There is no option to make
    trestle strict here, which is why the docstring has to say so.
    """
    root = workspace["root"]

    async with Client(build_server("authoring")) as client:
        await call_tool(client, "trestle_init", {"mode": "local"})
        for name in ("source", "target"):
            await call_tool(
                client,
                "trestle_import",
                {"file": workspace["catalog"].as_posix(), "output": name},
            )

        rows = workspace["mapping_csv"].read_text(encoding="utf-8").splitlines()
        csv_copy = root / "typo.csv"
        csv_copy.write_text(
            "\n".join(
                row.replace(",ac-1,ac-1,", ",ac-1,ac-1 ac-99-typo,") for row in rows
            )
            + "\n",
            encoding="utf-8",
        )

        result = await call_tool(
            client,
            "trestle_task_csv_to_oscal_mc",
            {
                "title": "Test Crosswalk",
                "version": "1.0.0",
                "csv_file": csv_copy.as_posix(),
                "output_dir": "mapping-collections/typo",
            },
        )

        assert "✅" in result

        output = root / "mapping-collections" / "typo" / "mapping-collection.json"
        maps = json.loads(output.read_text())["mapping-collection"]["mappings"][0][
            "maps"
        ]
        equivalent = next(e for e in maps if e["relationship"] == "equivalent")
        assert [item["id-ref"] for item in equivalent["targets"]] == ["ac-1"]


@pytest.mark.anyio
async def test_a_generated_mapping_collection_validates(workspace):
    """The default tool set can validate what the default tool set produces.

    csv-to-oscal-mc and trestle_validate are both in the `authoring` preset,
    and the validator's model map left out `mapping-collection`, so this chain
    failed with "Unsupported OSCAL root". Both tools run from one client here,
    which is the arrangement that made it a problem.
    """
    root = workspace["root"]

    async with Client(build_server("authoring")) as client:
        await call_tool(client, "trestle_init", {"mode": "local"})
        for name in ("source", "target"):
            await call_tool(
                client,
                "trestle_import",
                {"file": workspace["catalog"].as_posix(), "output": name},
            )

        csv_copy = root / "mapping.csv"
        shutil.copy(workspace["mapping_csv"], csv_copy)
        await call_tool(
            client,
            "trestle_task_csv_to_oscal_mc",
            {
                "title": "Test Crosswalk",
                "version": "1.0.0",
                "csv_file": csv_copy.as_posix(),
                "output_dir": "mapping-collections/test",
            },
        )

        output = root / "mapping-collections" / "test" / "mapping-collection.json"
        result = await call_tool(
            client,
            "trestle_validate",
            {"file": output.as_posix(), "expected_model_type": "mapping-collection"},
        )
        assert "✅" in result
        assert "mapping-collection" in result


@pytest.mark.anyio
async def test_generic_task_tools(workspace):
    """List the available tasks and run one through the generic runner."""
    root = workspace["root"]

    async with Client(build_server("task")) as client:
        # trestle task needs a workspace, which the fixture's cwd provides
        from trestle_mcp.services import init as init_service

        await init_service.trestle_init(init_service.TrestleInitInput(mode="local"))

        listing = await call_tool(client, "trestle_task_list", {})
        assert "✅" in listing
        assert "csv-to-oscal-cd" in listing
        assert "oscal-catalog-to-csv" in listing

        info = await call_tool(client, "trestle_task_list", {"task": "csv-to-oscal-mc"})
        assert "✅" in info
        assert "csv-file" in info

        # run a task that has no typed tool here, through the generic runner
        from trestle_mcp.services import import_ as import_service

        await import_service.trestle_import(
            import_service.TrestleImportInput(
                file=workspace["catalog"].as_posix(), output="source"
            )
        )

        result = await call_tool(
            client,
            "trestle_task_run",
            {
                "task": "oscal-catalog-to-csv",
                "config": {
                    "input-file": (
                        root / "catalogs" / "source" / "catalog.json"
                    ).as_posix(),
                    "output-dir": (root / "csv_out").as_posix(),
                    "output-name": "catalog.csv",
                },
            },
        )
        assert "✅" in result
        assert (root / "csv_out" / "catalog.csv").exists()


@pytest.mark.anyio
async def test_remove_deletes_an_element_and_is_opt_in(workspace):
    """Exercise trestle_remove against the real CLI, and its opt-in gating.

    Two things need the real server rather than a mocked runner: that the
    command actually removes the element from the file on disk, and that a
    broad selection does not expose the tool at all.
    """
    root = workspace["root"]

    # The tool is absent from the broadest group, so a client that asked for
    # everything cannot call it.
    async with Client(build_server("all")) as client:
        listed = {tool.name for tool in await client.list_tools()}
        assert "trestle_remove" not in listed

    async with Client(build_server("all,trestle_remove")) as client:
        assert "✅" in await call_tool(client, "trestle_init", {"mode": "local"})
        assert "✅" in await call_tool(
            client,
            "trestle_import",
            {"file": workspace["catalog"].as_posix(), "output": "source"},
        )

        catalog_path = root / "catalogs" / "source" / "catalog.json"
        assert "roles" in json.loads(catalog_path.read_text())["catalog"]["metadata"]

        result = await call_tool(
            client,
            "trestle_remove",
            {
                "file": "catalogs/source/catalog.json",
                "element": "catalog.metadata.roles",
            },
        )
        assert "✅" in result

        # The element is gone from the file, and the rest of the model is intact.
        metadata = json.loads(catalog_path.read_text())["catalog"]["metadata"]
        assert "roles" not in metadata
        assert metadata["title"]

        # A path that is not in the model fails rather than removing something
        # else, and says which element it could not find.
        result = await call_tool(
            client,
            "trestle_remove",
            {"file": "catalogs/source/catalog.json", "element": "catalog.nonexistent"},
        )
        assert "❌" in result
        assert "catalog.nonexistent" in result


@pytest.mark.anyio
async def test_init_overwrites_an_existing_task_config(workspace):
    """A second trestle_init replaces .trestle/config.ini and says it succeeded.

    This is why `trestle_init` is classified destructive rather than additive.
    trestle's `_copy_config_file` calls `copyfile` with no existence check, so
    the stock config lands on top of whatever the operator wrote -- and
    config.ini is where `trestle task` reads its `[task.*]` sections. Nothing
    in the output says so, which is what makes the annotation the only warning
    a client gets.
    """
    root = workspace["root"]

    async with Client(build_server("authoring")) as client:
        await call_tool(client, "trestle_init", {"mode": "local"})

        config = root / ".trestle" / "config.ini"
        config.write_text(
            "# trestle config file\n"
            "[task.csv-to-oscal-cd]\n"
            "title = my pipeline\n",
            encoding="utf-8",
        )

        result = await call_tool(client, "trestle_init", {"mode": "local"})

        assert "✅" in result
        assert "task.csv-to-oscal-cd" not in config.read_text(encoding="utf-8")
