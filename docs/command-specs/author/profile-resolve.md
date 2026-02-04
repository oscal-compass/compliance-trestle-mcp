# trestle author profile-resolve

## CLI

```sh
$ trestle author profile-resolve [-h] --name NAME -o OUTPUT [--show-values] [--show-labels]
                                      [--bracket-format BRACKET_FORMAT] [-vap VALUE_ASSIGNED_PREFIX]
                                      [--value-not-assigned-prefix VALUE_NOT_ASSIGNED_PREFIX]
                                      [--label-prefix LABEL_PREFIX] [--verbose] [-tr TRESTLE_ROOT]

Resolve profile to resolved profile catalog.

options:
  -h, --help            show this help message and exit
  --name NAME, -n NAME  Name of the source profile model in the trestle workspace
  -o OUTPUT, --output OUTPUT
                        Name of the output resolved profile catalog
  --show-values, -sv    Show values for parameters in prose
  --show-labels, -sl    Show labels for parameters in prose instead of values
  --bracket-format BRACKET_FORMAT, -bf BRACKET_FORMAT
                        With -sv, allows brackets around value, e.g. [.] or ((.)), with the dot
                        representing the value.
  -vap VALUE_ASSIGNED_PREFIX, --value-assigned-prefix VALUE_ASSIGNED_PREFIX
                        With -sv, places a prefix in front of the parameter string if a value has been
                        assigned.
  --value-not-assigned-prefix VALUE_NOT_ASSIGNED_PREFIX, -vnap VALUE_NOT_ASSIGNED_PREFIX
                        With -sv, places a prefix in front of the parameter string if a value has *not*
                        been assigned.
  --label-prefix LABEL_PREFIX, -lp LABEL_PREFIX
                        With -sl, places a prefix in front of the parameter label.
  --verbose, -v         Display verbose output
  -tr TRESTLE_ROOT, --trestle-root TRESTLE_ROOT
                        Path of trestle root dir
```

## Purpose

Generates a parameter-resolved OSCAL catalog (for actual use) for the specified profile name (e.g., myprofile), with fine-grained customizations possible for output format, prefixes, etc.

## Use Cases

- Standard generation of catalog with profile applied
- Automatic creation of resolved catalogs for organizational operations
- Automated flexible control of output format and labels
- Catalog generation for integration with other workflows

### MCP Tool Design

**Parameters:**
- `name` (required): str
  - Name of the target profile (corresponds to profiles/<name>/profile.json)
- `output` (required): str
  - Name of output directory (catalogs/<output>/catalog.json)
- `show_values` (optional): bool
  - Output parameter values in prose
- `show_labels` (optional): bool
  - Output parameter labels in prose
- `bracket_format` (optional): str
  - Bracket format to surround value (e.g., [.] or ((.)), where "." is the value)
- `value_assigned_prefix` (optional): str
  - Prefix for parameters with values assigned
- `value_not_assigned_prefix` (optional): str
  - Prefix for parameters *without* values assigned
- `label_prefix` (optional): str
  - Prefix for label output
- `verbose` (optional): bool
  - Verbose output
- `trestle_root` (optional): str
  - Path to trestle workspace root

**Returns:** string
- On success: `✅ Catalog controls generated as markdown successfully\n\nOutput: {output}\n\n{stdout}`
- On failure: `❌ Failed to generate catalog markdowns\n\nCatalog: {name}\nError: {stderr}`

### Examples

#### Example 1: Minimal profile-resolve command

```
trestle_author_profile_resolve(
    name="myprofile",
    output="catalog_resolved"
)
```

**Input:**
- profiles/myprofile/profile.json (existing)

**Result:**
- catalogs/catalog_resolved/catalog.json (resolved catalog generated)

**Example of created file:**
- catalogs/catalog_resolved/catalog.json

#### Example 2: With output formatting options

```
trestle_author_profile_resolve(
    name="myprofile",
    output="catalog_resolved",
    show_values=True,
    bracket_format="(.)"
)
```

**Input:**
- profiles/myprofile/profile.json (existing)

**Result:**
- Catalog with embedded values generated in the specified format
- catalogs/catalog_resolved/catalog.json

**Example of created file:**
- catalogs/catalog_resolved/catalog.json
