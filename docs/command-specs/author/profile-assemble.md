# trestle author profile-assemble

## CLI

```sh
$ trestle author profile-assemble -h
usage: trestle author profile-assemble [-h] [-n NAME] -m MARKDOWN --output OUTPUT [--set-parameters] [-r] [-vn VERSION]
                                       [--sections SECTIONS] [--required-sections REQUIRED_SECTIONS] [-as ALLOWED_SECTIONS] [-v]
                                       [--trestle-root TRESTLE_ROOT]

Assemble markdown files of controls into a Profile json file.

options:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  Optional name of the profile model in the trestle workspace that is being modified. If not provided the output name is used.
  -m MARKDOWN, --markdown MARKDOWN
                        Name of the source markdown file directory
  --output OUTPUT, -o OUTPUT
                        Name of the output generated json Profile (ok to overwrite original)
  --set-parameters, -sp
                        Set parameters and properties based on the yaml header in control markdown
  -r, --regenerate      Flag to force generation of new uuids in the model
  -vn VERSION, --version VERSION
                        New version for the assembled model
  --sections SECTIONS, -s SECTIONS
                        Comma-separated list of sections as short_name_no_spaces:long name with spaces
  --required-sections REQUIRED_SECTIONS, -rs REQUIRED_SECTIONS
                        Short names of sections that must be in the assembled model, comma-separated
  -as ALLOWED_SECTIONS, --allowed-sections ALLOWED_SECTIONS
                        Short names of sections that are allowed to be in the assembled model, comma-separated
  -v, --verbose         Display verbose output
  --trestle-root TRESTLE_ROOT, -tr TRESTLE_ROOT
                        Path of trestle root dir
```

## Purpose

From a group of controls managed in Markdown (the markdown directory for a profile), assemble and output an integrated OSCAL Profile JSON (`profile.json`). Supports parameter (YAML header/frontmatter) expansion as well as fine-grained editing and automation.

## Use Cases
- Automatically generate a `profile.json` from a Markdown-managed profile
- Automatic profile assembly with YAML value expansion, CI/CD friendly
- Large-scale or multi-profile split management and unified workflows

### MCP Tool Design

**Parameters:**
- `markdown_dir` (required): str
  - Directory containing the profile control markdown files
- `output_profile` (required): str
  - Output profile directory name (profiles/<output_profile>/profile.json)
- `name` (optional): str
  - Profile name
- `set_parameters` (optional): bool
  - Perform frontmatter parameter expansion
- `regenerate` (optional): bool
  - Regenerate uuids
- `version` (optional): str
  - Specify version
- `sections` (optional): str
  - Section information (short:long format, comma-separated)
- `required_sections` (optional): str
  - Required section(s)
- `allowed_sections` (optional): str
  - Allowed section(s)
- `verbose` (optional): bool
  - Verbose output
- `trestle_root` (optional): str
  - Path to trestle root directory

**Return Value:** string
- On success: `✅ Profile assembled from markdown successfully\n\nOutput: {output_profile}\n\n{stdout}`
- On failure: `❌ Failed to assemble profile from markdown\n\nMarkdownDir: {markdown_dir}\nError: {stderr}`

### Examples

#### Example 1: Assemble profile from a simple markdown directory
```
trestle_author_profile_assemble(
    markdown_dir="md_profile",
    output_profile="myprofile_v2"
)
```
**Input:**
- Split profile.md files under md_profile/

**Result:**
- profiles/myprofile_v2/profile.json generated

**Example created file:**
- profiles/myprofile_v2/profile.json

#### Example 2: With parameter expansion and version specification
```
trestle_author_profile_assemble(
    markdown_dir="md_profile",
    output_profile="myprofile_v2",
    set_parameters=True,
    version="2.0.0"
)
```
**Input:**
- md_profile/ files

**Result:**
- Parameter-expanded, versioned profile.json

**Example created file:**
- profiles/myprofile_v2/profile.json
