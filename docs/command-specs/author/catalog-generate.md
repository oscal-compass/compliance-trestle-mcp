# trestle author catalog-generate

## CLI

```bash
$ trestle author catalog-generate -h
usage: trestle author catalog-generate [-h] -n NAME -o OUTPUT [--force-overwrite] [--yaml-header YAML_HEADER] [-ohv] [-v] [--trestle-root TRESTLE_ROOT]

Generate Catalog controls in markdown form from a catalog in the trestle workspace.

options:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  Name of the catalog model in the trestle workspace
  -o OUTPUT, --output OUTPUT
                        Name of the output generated catalog markdown folder
  --force-overwrite, -fo
                        Overwrites the content of all markdowns in the output folder.
  --yaml-header YAML_HEADER, -y YAML_HEADER
                        Path to the optional yaml header file
  -ohv, --overwrite-header-values
                        Flag to overwrite values in a markdown control header. If a separate yaml header is passed in with -y, any items in the markdown header
                        that are common with the provided header will be overwritten by the new values. But new items passed in will always be added to the
                        markdown header.
  -v, --verbose         Display verbose output
  --trestle-root TRESTLE_ROOT, -tr TRESTLE_ROOT
                        Path of trestle root dir
```

## Purpose

Allows splitting a large OSCAL catalog (e.g., NIST SP800-53) catalog.json into a human-readable directory hierarchy of markdown files by control, making editing and review by control easier. This enables easy collaborative editing and version control for large catalogs and improves operational efficiency for security frameworks.

## Use Cases
- Split catalogs such as NIST or other frameworks into md files per control for finer editing and review
- Re-convert edited markdown files back into catalog.json (reverse operation planned for the future)
- Assign parts for review/editing to specific people
- Manage catalogs in directory hierarchies

### MCP Tool Design

**Parameters:**
- `name` (required): string
  - Catalog name (e.g., nist). Targets `catalogs/{name}/catalog.json`
- `output` (required): string
  - Output directory name for the generated markdown files (e.g., md_catalog_nist)
- `force_overwrite` (optional): bool
  - Force overwrite contents in the output directory
- `yaml_header` (optional): string
  - Path to the additional yaml header file
- `overwrite_header_values` (optional): bool
  - Overwrite header values (with new and old entries merged)
- `trestle_root` (optional): string
  - Path to trestle workspace root
- `verbose` (optional): bool
  - Verbose output

**Returns:** string
- On success: `✅ Catalog controls generated as markdown successfully\n\nOutput: {output}\n\n{stdout}`
- On failure: `❌ Failed to generate catalog markdowns\n\nCatalog: {name}\nError: {stderr}`

### Examples
#### Example 1: Split NIST catalog into markdown files
```
trestle_catalog_generate(
    name="nist",
    output="md_catalog_nist"
)
```

**Input:**
- catalogs/nist/catalog.json (pre-existing)

**Result:**
- A multi-level directory of markdown files is generated under ./md_catalog_nist/, and each control can be edited individually

**Created files:**
- md_catalog_nist/ac/ac-1.md
- md_catalog_nist/ca/ca1.md, ca-2.md
- ... (actual hierarchy/multiple md files)
