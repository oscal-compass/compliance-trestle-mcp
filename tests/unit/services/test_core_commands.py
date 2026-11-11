#!/usr/bin/env python3
"""Unit tests for the top-level trestle command services.

These cover the argument builders of the `core` group. The commands whose
argument shape is unusual — a positional model type, a cwd-sensitive command, a
command with no required arguments — are the point of this file: a flag written
as an option when the CLI wants it positionally fails only at call time.
"""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from trestle_mcp.services import (
    assemble,
    create,
    describe,
    href,
    merge,
    partial_object_validate,
    replicate,
    split,
    version,
)

SUCCESS = {"success": True, "stdout": "ok", "stderr": "", "returncode": 0}
FAILURE = {"success": False, "stdout": "", "stderr": "boom", "returncode": 1}


class TestTrestleCreate:
    """Test suite for trestle_create tool."""

    @pytest.mark.asyncio
    async def test_create_new_model(self):
        """Test creating a new model from a type and output name."""
        with patch("trestle_mcp.services.create.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = create.TrestleCreateInput(
                model_type="component-definition", output="mycomp"
            )
            result = await create.trestle_create(params)
            assert "✅" in result and "mycomp" in result
            args = mock_run.call_args[0][0]
            assert args[0] == "create"
            assert args[args.index("--type") + 1] == "component-definition"
            assert args[args.index("--output") + 1] == "mycomp"

    @pytest.mark.asyncio
    async def test_create_element_in_existing_file(self):
        """Test the second mode: an element inside an existing file."""
        with patch("trestle_mcp.services.create.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = create.TrestleCreateInput(
                file="catalogs/mycat/catalog.json",
                element="catalog.groups",
                include_optional_fields=True,
                extension="yaml",
                trestle_root="/ws",
                verbose=True,
            )
            result = await create.trestle_create(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert "--type" not in args
            assert args[args.index("--file") + 1] == "catalogs/mycat/catalog.json"
            assert args[args.index("--element") + 1] == "catalog.groups"
            assert args[args.index("--extension") + 1] == "yaml"
            assert "--include-optional-fields" in args
            assert args[args.index("--trestle-root") + 1] == "/ws"
            assert "--verbose" in args

    @pytest.mark.asyncio
    async def test_create_rejects_unknown_model_type(self):
        """Test the model type is constrained to the OSCAL model types."""
        with pytest.raises(ValueError):
            create.TrestleCreateInput(model_type="not-a-model", output="x")

    @pytest.mark.asyncio
    async def test_create_failure(self):
        """Test the error path reports stderr."""
        with patch("trestle_mcp.services.create.run_trestle_command") as mock_run:
            mock_run.return_value = FAILURE
            params = create.TrestleCreateInput(model_type="catalog", output="c")
            result = await create.trestle_create(params)
            assert "❌" in result and "boom" in result


class TestTrestleAssemble:
    """Test suite for trestle_assemble tool."""

    @pytest.mark.asyncio
    async def test_model_type_is_positional(self):
        """Test the model type is passed positionally, not as --type."""
        with patch("trestle_mcp.services.assemble.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = assemble.TrestleAssembleInput(model_type="catalog", name="mycat")
            result = await assemble.trestle_assemble(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[:2] == ["assemble", "catalog"]
            assert args[args.index("--name") + 1] == "mycat"
            # --type on this command is a flag meaning "all models of the type"
            assert "--type" not in args

    @pytest.mark.asyncio
    async def test_all_of_type_passes_bare_type_flag(self):
        """Test all_of_type becomes the bare --type flag."""
        with patch("trestle_mcp.services.assemble.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = assemble.TrestleAssembleInput(
                model_type="profile", all_of_type=True, extension="json"
            )
            result = await assemble.trestle_assemble(params)
            assert "✅" in result and "all profile models" in result
            args = mock_run.call_args[0][0]
            assert args[:2] == ["assemble", "profile"]
            assert "--type" in args
            # the flag takes no value
            assert args[args.index("--type") + 1] == "--extension"

    @pytest.mark.asyncio
    async def test_assemble_failure(self):
        """Test the error path reports the model type."""
        with patch("trestle_mcp.services.assemble.run_trestle_command") as mock_run:
            mock_run.return_value = FAILURE
            params = assemble.TrestleAssembleInput(model_type="catalog", name="mycat")
            result = await assemble.trestle_assemble(params)
            assert "❌" in result and "catalog" in result and "boom" in result


class TestTrestleSplit:
    """Test suite for trestle_split tool."""

    @pytest.mark.asyncio
    async def test_split_minimal(self):
        """Test the required file and element arguments."""
        with patch("trestle_mcp.services.split.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = split.TrestleSplitInput(
                file="catalogs/mycat/catalog.json", element="catalog.metadata"
            )
            result = await split.trestle_split(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[0] == "split"
            assert args[args.index("--file") + 1] == "catalogs/mycat/catalog.json"
            assert args[args.index("--element") + 1] == "catalog.metadata"

    @pytest.mark.asyncio
    async def test_split_failure(self):
        """Test the error path reports the file."""
        with patch("trestle_mcp.services.split.run_trestle_command") as mock_run:
            mock_run.return_value = FAILURE
            params = split.TrestleSplitInput(file="f.json", element="catalog.metadata")
            result = await split.trestle_split(params)
            assert "❌" in result and "f.json" in result


class TestTrestleMerge:
    """Test suite for trestle_merge tool."""

    @pytest.mark.asyncio
    async def test_merge_runs_in_the_model_directory_under_the_root(self, tmp_path):
        """Test a relative model_dir is resolved against trestle_root.

        trestle merge resolves the destination model relative to its working
        directory and uses --trestle-root only for model type lookup, so merge
        needs its own cwd. That cwd has to be the model directory *inside the
        workspace*: passing the bare relative path would resolve it against
        whatever directory the client started this server in.
        """
        root = tmp_path / "ws"
        (root / "catalogs" / "mycat").mkdir(parents=True)
        with patch("trestle_mcp.services.merge.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = merge.TrestleMergeInput(
                element="catalog.metadata",
                model_dir="catalogs/mycat",
                trestle_root=str(root),
            )
            result = await merge.trestle_merge(params)
            assert "✅" in result and "catalogs/mycat" in result
            args = mock_run.call_args[0][0]
            assert args[0] == "merge"
            assert args[args.index("--element") + 1] == "catalog.metadata"
            assert mock_run.call_args[1]["cwd"] == str(root / "catalogs" / "mycat")

    @pytest.mark.asyncio
    async def test_merge_keeps_an_absolute_model_dir(self, tmp_path):
        """Test an absolute model_dir is used as given, root or no root."""
        root = tmp_path / "ws"
        root.mkdir()
        elsewhere = tmp_path / "elsewhere" / "catalogs" / "mycat"
        elsewhere.mkdir(parents=True)
        with patch("trestle_mcp.services.merge.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = merge.TrestleMergeInput(
                element="catalog.metadata",
                model_dir=str(elsewhere),
                trestle_root=str(root),
            )
            await merge.trestle_merge(params)
            assert mock_run.call_args[1]["cwd"] == str(elsewhere)

    @pytest.mark.asyncio
    async def test_merge_without_a_root_uses_the_model_dir_as_given(
        self, tmp_path, monkeypatch
    ):
        """Test the no-root case is unchanged: cwd is the model_dir itself."""
        (tmp_path / "catalogs" / "mycat").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)
        with patch("trestle_mcp.services.merge.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = merge.TrestleMergeInput(
                element="catalog.metadata", model_dir="catalogs/mycat"
            )
            await merge.trestle_merge(params)
            assert mock_run.call_args[1]["cwd"] == "catalogs/mycat"

    @pytest.mark.asyncio
    async def test_a_missing_model_dir_is_reported_as_such(self, tmp_path):
        """Test a mistyped model_dir names the path, and does not reach trestle.

        The runner declines a working directory that is not there and falls
        back to the trestle root. Everywhere else that is right -- the root is
        what the caller got wrong. For merge the model directory is what is
        wrong, and running in the root makes trestle report "Trestle workspace
        not found at path <root>" about a workspace that is fine, because merge
        expects its working directory to be inside a model.
        """
        root = tmp_path / "ws"
        root.mkdir()
        with patch("trestle_mcp.services.merge.run_trestle_command") as mock_run:
            params = merge.TrestleMergeInput(
                element="catalog.metadata",
                model_dir="catalogs/nope",
                trestle_root=str(root),
            )
            result = await merge.trestle_merge(params)

            assert "❌" in result
            assert "catalogs/nope" in result
            assert "Model directory not found" in result
            mock_run.assert_not_called()

    @pytest.mark.asyncio
    async def test_the_looked_for_path_is_absolute_without_a_root(
        self, tmp_path, monkeypatch
    ):
        """Test the error names an absolute path even with no trestle_root.

        With no root there is no join to do, so a bare `model_dir` would just
        repeat the `Model:` line and add nothing -- in the one case where the
        caller cannot work the absolute path out themselves, because they do
        not know which directory the client started this server in.
        """
        monkeypatch.chdir(tmp_path)
        with patch("trestle_mcp.services.merge.run_trestle_command") as mock_run:
            params = merge.TrestleMergeInput(
                element="catalog.metadata", model_dir="catalogs/nope"
            )
            result = await merge.trestle_merge(params)

            assert f"Looked for: {tmp_path / 'catalogs' / 'nope'}" in result
            mock_run.assert_not_called()

    @pytest.mark.asyncio
    async def test_an_existing_model_dir_still_shells_out(self, tmp_path):
        """Test the guard does not block the normal case."""
        root = tmp_path / "ws"
        (root / "catalogs" / "mycat").mkdir(parents=True)
        with patch("trestle_mcp.services.merge.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = merge.TrestleMergeInput(
                element="catalog.metadata",
                model_dir="catalogs/mycat",
                trestle_root=str(root),
            )
            result = await merge.trestle_merge(params)

            assert "✅" in result
            assert mock_run.call_args[1]["cwd"] == str(root / "catalogs" / "mycat")

    @pytest.mark.asyncio
    async def test_merge_failure(self):
        """Test the error path reports the model directory and element."""
        with patch("trestle_mcp.services.merge.run_trestle_command") as mock_run:
            mock_run.return_value = FAILURE
            params = merge.TrestleMergeInput(
                element="catalog.metadata", model_dir="catalogs/mycat"
            )
            result = await merge.trestle_merge(params)
            assert "❌" in result and "catalog.metadata" in result


class TestTrestleDescribe:
    """Test suite for trestle_describe tool."""

    @pytest.mark.asyncio
    async def test_describe_minimal_and_element(self):
        """Test the file argument, and the optional element."""
        with patch("trestle_mcp.services.describe.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = describe.TrestleDescribeInput(file="catalogs/mycat/catalog.json")
            await describe.trestle_describe(params)
            assert "--element" not in mock_run.call_args[0][0]

            params = describe.TrestleDescribeInput(
                file="catalogs/mycat/catalog.json", element="catalog.metadata"
            )
            result = await describe.trestle_describe(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[args.index("--element") + 1] == "catalog.metadata"

    @pytest.mark.asyncio
    async def test_describe_failure(self):
        """Test the error path reports the file."""
        with patch("trestle_mcp.services.describe.run_trestle_command") as mock_run:
            mock_run.return_value = FAILURE
            params = describe.TrestleDescribeInput(file="missing.json")
            result = await describe.trestle_describe(params)
            assert "❌" in result and "missing.json" in result


class TestTrestleReplicate:
    """Test suite for trestle_replicate tool."""

    @pytest.mark.asyncio
    async def test_model_type_is_positional(self):
        """Test the model type is passed positionally."""
        with patch("trestle_mcp.services.replicate.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = replicate.TrestleReplicateInput(
                model_type="profile",
                name="nist_moderate",
                output="my_moderate",
                regenerate=True,
            )
            result = await replicate.trestle_replicate(params)
            assert "✅" in result and "my_moderate" in result
            args = mock_run.call_args[0][0]
            assert args[:2] == ["replicate", "profile"]
            assert args[args.index("--name") + 1] == "nist_moderate"
            assert args[args.index("--output") + 1] == "my_moderate"
            assert "--regenerate" in args

    @pytest.mark.asyncio
    async def test_replicate_failure(self):
        """Test the error path reports the source model."""
        with patch("trestle_mcp.services.replicate.run_trestle_command") as mock_run:
            mock_run.return_value = FAILURE
            params = replicate.TrestleReplicateInput(
                model_type="catalog", name="src", output="dst"
            )
            result = await replicate.trestle_replicate(params)
            assert "❌" in result and "src" in result


class TestTrestleHref:
    """Test suite for trestle_href tool."""

    def test_a_negative_item_is_rejected(self):
        """Test item must be >= 0.

        trestle only checks the upper bound, so item=-1 reached a Python list
        index and silently rewrote the *last* import while reporting success.
        A caller counting indexes off a listing never means that.
        """
        with pytest.raises(ValidationError):
            href.TrestleHrefInput(
                name="p", href="trestle://catalogs/c/catalog.json", item=-1
            )

    def test_the_first_import_is_still_addressable(self):
        """Test the bound does not exclude index 0, the default."""
        assert href.TrestleHrefInput(name="p", item=0).item == 0

    @pytest.mark.asyncio
    async def test_listing_mode_omits_href(self):
        """Test that without an href the command lists the imports."""
        with patch("trestle_mcp.services.href.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = href.TrestleHrefInput(name="myprofile")
            result = await href.trestle_href(params)
            assert "✅" in result and "imports listed" in result
            args = mock_run.call_args[0][0]
            assert args[:3] == ["href", "--name", "myprofile"]
            assert "--href" not in args

    @pytest.mark.asyncio
    async def test_update_mode_passes_href_and_item(self):
        """Test item 0 is passed, rather than dropped as a falsy value."""
        with patch("trestle_mcp.services.href.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = href.TrestleHrefInput(
                name="myprofile",
                href="trestle://catalogs/mycat/catalog.json",
                item=0,
            )
            result = await href.trestle_href(params)
            assert "href updated" in result
            args = mock_run.call_args[0][0]
            assert args[args.index("--href") + 1] == (
                "trestle://catalogs/mycat/catalog.json"
            )
            assert args[args.index("--item") + 1] == "0"

    @pytest.mark.asyncio
    async def test_href_failure(self):
        """Test the error path reports the profile."""
        with patch("trestle_mcp.services.href.run_trestle_command") as mock_run:
            mock_run.return_value = FAILURE
            params = href.TrestleHrefInput(name="myprofile")
            result = await href.trestle_href(params)
            assert "❌" in result and "myprofile" in result


class TestTrestlePartialObjectValidate:
    """Test suite for trestle_partial_object_validate tool."""

    @pytest.mark.asyncio
    async def test_required_and_optional_arguments(self):
        """Test the file, element and no_validators arguments."""
        module = "trestle_mcp.services.partial_object_validate.run_trestle_command"
        with patch(module) as mock_run:
            mock_run.return_value = SUCCESS
            params = partial_object_validate.TrestlePartialObjectValidateInput(
                file="catalogs/mycat/catalog/metadata.json",
                element="catalog.metadata",
                no_validators=True,
            )
            result = await partial_object_validate.trestle_partial_object_validate(
                params
            )
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[0] == "partial-object-validate"
            assert args[args.index("--file") + 1] == (
                "catalogs/mycat/catalog/metadata.json"
            )
            assert args[args.index("--element") + 1] == "catalog.metadata"
            assert "--no-validators" in args

    @pytest.mark.asyncio
    async def test_failure(self):
        """Test the error path reports the file and element."""
        module = "trestle_mcp.services.partial_object_validate.run_trestle_command"
        with patch(module) as mock_run:
            mock_run.return_value = FAILURE
            params = partial_object_validate.TrestlePartialObjectValidateInput(
                file="m.json", element="catalog.metadata"
            )
            result = await partial_object_validate.trestle_partial_object_validate(
                params
            )
            assert "❌" in result and "boom" in result


class TestTrestleVersion:
    """Test suite for trestle_version tool."""

    @pytest.mark.asyncio
    async def test_bare_version(self):
        """Test that with no arguments only the subcommand is passed."""
        with patch("trestle_mcp.services.version.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = version.TrestleVersionInput()
            result = await version.trestle_version(params)
            assert "✅" in result
            assert mock_run.call_args[0][0] == ["version"]

    @pytest.mark.asyncio
    async def test_model_version(self):
        """Test querying a single model's document version."""
        with patch("trestle_mcp.services.version.run_trestle_command") as mock_run:
            mock_run.return_value = SUCCESS
            params = version.TrestleVersionInput(name="mycat", model_type="catalog")
            result = await version.trestle_version(params)
            assert "✅" in result
            args = mock_run.call_args[0][0]
            assert args[args.index("--name") + 1] == "mycat"
            assert args[args.index("--type") + 1] == "catalog"

    @pytest.mark.asyncio
    async def test_a_model_version_is_labelled_as_the_document_version(self):
        """Test the result says which version it is.

        trestle prints "Version of OSCAL object of <name> <type> is: X", where X
        is metadata.version. Passed through as-is, an agent asked "what OSCAL
        version is this catalog?" answers with the document's version instead --
        5.2.0 for a catalog whose oscal-version is 1.1.3.
        """
        with patch("trestle_mcp.services.version.run_trestle_command") as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Version of OSCAL object of mycat catalog is: 5.2.0.",
                "stderr": "",
                "returncode": 0,
            }
            params = version.TrestleVersionInput(name="mycat", model_type="catalog")
            result = await version.trestle_version(params)
            assert "metadata.version" in result
            assert "not its OSCAL version" in result
            assert "metadata.oscal-version" in result

    @pytest.mark.asyncio
    async def test_the_bare_version_is_not_relabelled(self):
        """Test the note is only added where it applies.

        With no model named, the output really is the trestle and OSCAL
        versions, so the caveat would be wrong.
        """
        with patch("trestle_mcp.services.version.run_trestle_command") as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Trestle version v5.2.0 based on OSCAL version 1.1.3",
                "stderr": "",
                "returncode": 0,
            }
            result = await version.trestle_version(version.TrestleVersionInput())
            assert "metadata.version" not in result

    @pytest.mark.asyncio
    async def test_version_failure(self):
        """Test the error path reports stderr."""
        with patch("trestle_mcp.services.version.run_trestle_command") as mock_run:
            mock_run.return_value = FAILURE
            result = await version.trestle_version(version.TrestleVersionInput())
            assert "❌" in result and "boom" in result
