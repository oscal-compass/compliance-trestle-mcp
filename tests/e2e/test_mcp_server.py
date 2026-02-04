import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml
from fastmcp.client import Client
from trestle.oscal.catalog import Catalog
from trestle.oscal.profile import Profile

from trestle_mcp.main import mcp


def extract_frontmatter(markdown_text):
    match = re.match(r"^---\n(.*?\n)---", markdown_text, re.DOTALL)
    if match:
        return match.group(1)
    return None


def replace_frontmatter(md: str, new_header: str) -> str:
    # Ensure new_header does not include --- delimiters
    new_header = new_header.strip("\n")
    # Replace frontmatter using regex
    tag = r"---\n(.*?)\n---"
    replacement = f"---\n{new_header}\n---"
    if re.match(tag, md, re.DOTALL):
        return re.sub(tag, replacement, md, count=1, flags=re.DOTALL)
    # If no frontmatter, just prepend
    return replacement + "\n" + md


async def call_tool(client: Client, name: str, params: Dict[str, Any]):
    return await client.call_tool(name, {"params": params}, raise_on_error=True)


@pytest.mark.anyio
async def test_trestle_catalog_generate_tool():
    with tempfile.TemporaryDirectory() as tmp_workspace:
        # Prepare test catalog.json for import
        import_catalog_path = Path("tests/data/test-catalog.json").absolute().as_posix()
        import_profile_path = Path("tests/data/test-profile.json").absolute().as_posix()

        os.chdir(tmp_workspace)
        async with Client(mcp) as client:

            init_params = {"mode": "local"}
            init_resp = await call_tool(client, "trestle_init", init_params)
            assert "✅" in init_resp.content[0].text

            import_params = {
                "file": import_catalog_path,
                "output": "test",
            }
            import_resp = await call_tool(client, "trestle_import", import_params)
            assert "✅" in import_resp.content[0].text
            assert Path(tmp_workspace, "catalogs", "test", "catalog.json").exists()

            import_params = {
                "file": import_profile_path,
                "output": "test",
            }
            import_resp = await call_tool(client, "trestle_import", import_params)
            assert "✅" in import_resp.content[0].text
            assert Path(tmp_workspace, "profiles", "test", "profile.json").exists()

            generate_catalog_params = {
                "name": "test",
                "output": "md_catalog_test",
            }
            generate_catalog_resp = await call_tool(
                client, "trestle_author_catalog_generate", generate_catalog_params
            )
            # It should succeed or at least run without a crash
            assert (
                "Catalog controls generated" in generate_catalog_resp.content[0].text
                or "Failed to generate catalog markdowns"
                in generate_catalog_resp.content[0].text
            )
            # Check result markdown tree (we expect ac/ac-1.md etc.; real output needs the cli to run ok)
            md_dir = Path(tmp_workspace) / "md_catalog_test"
            found_markdown = list(md_dir.rglob("*.md")) if md_dir.exists() else []
            expected = {"ac-1.md", "ac-2.md", "ac-2.1.md", "ac-2.2.md"}
            assert all(p.suffix == ".md" for p in found_markdown)
            assert len(found_markdown) == len(expected)
            actual = {p.name for p in found_markdown}
            assert actual == expected

            generate_profile_params = {
                "name": "test",
                "output": "md_profile_test",
            }
            generate_profile_resp = await call_tool(
                client, "trestle_author_profile_generate", generate_profile_params
            )

            assert (
                "Profile-based markdown controls generated"
                in generate_profile_resp.content[0].text
                or "Failed to generate profile-based markdowns"
                in generate_profile_resp.content[0].text
            )
            # Check result markdown tree (we expect only ac/ac-1.md)
            md_dir = Path(tmp_workspace) / "md_profile_test"
            found_markdown = list(md_dir.rglob("*.md")) if md_dir.exists() else []
            assert len(found_markdown) == 1
            assert found_markdown[0].name == "ac-1.md"

            # Edit parameters in profile
            ac1_path = md_dir / "ac" / "ac-1.md"
            with ac1_path.open("r") as f:
                ac1_md = f.read()
            header = extract_frontmatter(ac1_md)
            header_dict = yaml.safe_load(header)
            header_dict["x-trestle-set-params"]["ac-01_odp.01"]["profile-values"] = [
                "CISO"
            ]
            ac1_md = replace_frontmatter(ac1_md, yaml.safe_dump(header_dict))
            with ac1_path.open("w") as f:
                f.write(ac1_md)

            # Assemble profile (overwrite existing profile)
            assemble_profile_params = {
                "name": "test",
                "markdown_dir": "md_profile_test",
                "output_profile": "test",
                "set_parameters": True,
            }
            assemble_profile_resp = await call_tool(
                client, "trestle_author_profile_assemble", assemble_profile_params
            )
            assert (
                "Profile assembled from markdown"
                in assemble_profile_resp.content[0].text
                or "Failed to assemble profile" in assemble_profile_resp.content[0].text
            )
            profile_path = Path(tmp_workspace) / "profiles" / "test" / "profile.json"
            profile_oscal: Profile = Profile.oscal_read(profile_path)
            assert len(profile_oscal.modify.set_parameters) > 0
            assert [
                x
                for x in profile_oscal.modify.set_parameters
                if x.param_id == "ac-01_odp.01" and x.values == ["CISO"]
            ]

            # Resolve profile
            resolve_profile_params = {
                "name": "test",
                "output": "catalog_resolved",
                "bracket_format": '"."',
                "show_values": True,
            }
            resolve_profile_resp = await call_tool(
                client, "trestle_author_profile_resolve", resolve_profile_params
            )
            catalog_resolved_path = (
                Path(tmp_workspace) / "catalogs" / "catalog_resolved" / "catalog.json"
            )

            catalog_resolved_oscal: Catalog = Catalog.oscal_read(catalog_resolved_path)
            ac1_control = [
                x for x in catalog_resolved_oscal.groups[0].controls if x.id == "ac-1"
            ]
            assert len(ac1_control) == 1
            param = [x for x in ac1_control[0].params if x.id == "ac-01_odp.01"]
            assert len(param) == 1
            assert param[0].values == ["CISO"]
