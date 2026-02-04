# trestle import

## CLI

```sh
$ trestle import -h
usage: trestle import [-h] -f FILE --output OUTPUT [--regenerate] [-v] [--trestle-root TRESTLE_ROOT]

Import an existing full OSCAL model into the trestle workspace.

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  OSCAL file to import - either file path or url.
  --output OUTPUT, -o OUTPUT
                        Name of output element.
  --regenerate, -r      Flag to force generation of new uuids in the model
  --verbose, -v         Display verbose output
  --trestle-root TRESTLE_ROOT, -tr TRESTLE_ROOT
                        Path of trestle root dir
```

## Purpose

Import an existing OSCAL model (JSON/YAML file) into the Trestle workspace. You can specify either a URL or a local file path. The OSCAL type of the file is automatically detected and the file is placed in the appropriate directory.

## Use Cases
- Importing the NIST SP800-53 catalog
- Importing NIST baseline profiles
- Importing custom OSCAL models
- Migrating existing compliance documents

### MCP Tool Design

**Parameters:**
- `file` (required): string
  - URL or local file path of the OSCAL file. Supports both JSON and YAML
- `output` (required): string
  - Output directory name for the imported model
- `regenerate` (optional): bool
  - Flag to force regeneration of UUIDs
- `trestle_root` (optional): string
  - Path to the trestle root directory
- `verbose` (optional): bool
  - Verbose output

**Return Value:** string
- On success: `✅ OSCAL model imported successfully\n\nOutput: {output}\n\n{stdout}`
- On failure: `❌ Failed to import OSCAL model\n\nFile: {file}\nError: {stderr}`

### Examples

#### Example 1: Importing the NIST Catalog
```
trestle_import(
    file="https://raw.githubusercontent.com/usnistgov/oscal-content/refs/heads/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json",
    output="nist_sp800_53_rev5"
)
```
**Result:**
- catalogs/nist_sp800_53_rev5/catalog.json

#### Example 2: Importing the NIST Low Baseline Profile
```
trestle_import(
    file="https://raw.githubusercontent.com/usnistgov/oscal-content/refs/heads/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_LOW-baseline_profile.json",
    output="nist_low_baseline"
)
```
**Result:**
- profiles/nist_low_baseline/profile.json

#### Example 3: Importing a Local File
```
trestle_import(
    file="./resources/catalogs/your_catalog.json",
    output="mycatalog"
)
```
**Result:**
- catalogs/mycatalog/catalog.json

#### Example 4: Importing with UUID Regeneration
```
trestle_import(
    file="https://example.com/catalog.json",
    output="mycatalog",
    regenerate=True
)
```
**Result:**
- catalogs/mycatalog/catalog.json (IDs are newly generated)
