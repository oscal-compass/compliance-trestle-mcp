# trestle author profile-generate

## CLI

```sh
$ trestle author profile-generate -n <profile-name> --output <output-dir> [--yaml-header <header-path>] [--force-overwrite] [--overwrite-header-values] [--sections <sections>] [--required-sections <short_names>] [--trestle-root <root>]

options:
  -n, --name NAME                  Profile name to transform (profiles/<name>/profile.json)
  --output OUTPUT, -o OUTPUT       Output directory for generated markdown
  --yaml-header YAML_HEADER, -y    Optional YAML to insert as markdown header
  --force-overwrite, -fo           Overwrite all markdown files in output directory
  --overwrite-header-values, -ohv  Overwrite only YAML header values in markdown controls
  --sections SECTIONS, -s SECTIONS Sections to split in each control markdown file
  --required-sections REQUIRED_SECTIONS, -rs Section short names required in the output, comma-separated
  --trestle-root TRESTLE_ROOT, -tr Trestle workspace root path
  -v, --verbose                    Display verbose output
```

## Purpose

Generates a set of markdown documents that extract only the controls defined in the specified profile model (profiles/{profile}/profile.json). This enables organizations to focus documentation, reviews, and customization efforts on their unique profile-based control sets.

## Use Cases
- Generate markdown documentation for only the controls specified in a profile
- Document custom control sets defined by organization-specific profiles
- Output a specific profile as implementation guidance or evidence template

### MCP Tool Design

**Parameters:**
- `name` (Required): str
  - Profile name (targets profiles/<name>/profile.json)
- `output` (Required): str
  - Output directory (one markdown file per control)
- `yaml_header` (Optional): str
  - Path to additional YAML header to insert
- `force_overwrite` (Optional): bool
  - Force overwrite output directory
- `overwrite_header_values` (Optional): bool
  - Overwrite only existing header values in control markdown
- `sections` (Optional): str
  - Target sections to split per markdown file (e.g., implementation, statement, comma-separated)
- `required_sections` (Optional): str
  - Required section names (comma-separated)
- `trestle_root` (Optional): str
  - Path to the trestle workspace root
- `verbose` (Optional): bool
  - Verbose output

**Return value:** string
- On success: `✅ Profile-based markdown controls generated successfully\n\nOutput: {output}\n\n{stdout}`
- On failure: `❌ Failed to generate profile-based markdowns\n\nProfile: {name}\nError: {stderr}`

### Examples

#### Example 1: Generate markdown with only profile specified
```
trestle_author_profile_generate(
    name="myprofile",
    output="md_profile"
)
```
**Inputs:**
- profiles/myprofile/profile.json
- Related catalog (e.g., /catalogs/.../catalog.json)

**Output:**
- md_profile/control-xxx.md (one per profile control)

**Sample Files:**
- md_profile/control-ac-1.md
- md_profile/control-ac-2.md

#### Example 2: Specify required sections & overwrite header
```
trestle_author_profile_generate(
    name="myprofile",
    output="md_profile",
    required_sections="statement,assessment",
    overwrite_header_values=True
)
```
**Inputs:**
- profiles/myprofile/profile.json

**Output:**
- Markdown files in md_profile reflecting the specified sections and updated header values

**Sample Files:**
- md_profile/control-ac-1.md
- md_profile/control-ac-2.md
