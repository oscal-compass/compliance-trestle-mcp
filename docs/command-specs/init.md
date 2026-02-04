# trestle init

## Purpose

Initializes the current directory as a Trestle workspace. Trestle has an opinionated directory structure and creates a `.trestle` directory containing Trestle metadata, as well as the following directories for each type of OSCAL model.

### Created Directories
- `.trestle/` - Trestle metadata
- `catalogs/` - Catalog models
- `profiles/` - Profile models
- `component-definitions/` - Component Definition models
- `system-security-plans/` - SSP models
- `assessment-plans/` - Assessment Plan models
- `assessment-results/` - Assessment Result models
- `plan-of-action-and-milestones/` - POAM models

### Use Cases

Initialization of a Trestle workspace

## CLI

### Usage

```bash
$ trestle init -h
usage: trestle init [-h] [--full] [-loc] [-gd] [--verbose] [-tr TRESTLE_ROOT]

Initialize a trestle working directory.

options:
  -h, --help            show this help message and exit
  --full, -fl           Initializes Trestle workspace for local, API and governed documents usage.
  -loc, --local         Initializes Trestle workspace for local management of OSCAL models.
  -gd, --govdocs        Initializes Trestle workspace for governed documents usage only.
  --verbose, -v         Display verbose output
  -tr TRESTLE_ROOT, --trestle-root TRESTLE_ROOT
                        Path of trestle root dir
```

### MCP Tool Design

**Tool name:** `trestle_init`

**Parameters:**
- `mode` (optional): `"local"` | `"full"` | `"govdocs"` (default: `"local"`)
  - `local`: Local management only
  - `full`: Support for local, API, and governed documents
  - `govdocs`: Governed documents only
- `trestle_root` (optional): string (directory path)
  - Root path of the workspace (default: current directory)
- `verbose` (optional): boolean (default: `false`)
  - Display verbose output

**Returns:** string
- On success: `✅ Trestle workspace initialized successfully\n\n{stdout}`
- On failure: `❌ Failed to initialize trestle workspace\n\nError: {stderr}`

### Behavior

**Input:**
- Mode selection (local/full/govdocs)
- Optional custom root directory

**Process:**
1. Run the trestle CLI as `trestle init --{mode}`
2. Create the required directory structure
3. Generate `.trestle/config.ini`

**Output:**
- The Trestle workspace is created under the specified directory
- Returns a success/failure message

### Examples

#### Example 1: Basic initialization (local mode)
```python
trestle_init()
```

**Result:**
```
✅ Trestle workspace initialized successfully

Initialized trestle project successfully in /path/to/workspace
```

#### Example 2: Full mode with custom root
```python
trestle_init(
    mode="full",
    trestle_root="/path/to/workspace"
)
```

#### Example 3: Verbose output
```python
trestle_init(
    mode="local",
    verbose=True
)
```

## Implementation

**File:** [trestle_mcp/main.py](../../../trestle_mcp/main.py)

**Function:** `trestle_init(params: TrestleInitInput) -> str`

**Approach:** Phase 1 CLI Wrapper
- Executes the trestle CLI via subprocess
- Argument conversion: `mode` → `--local` / `--full` / `--govdocs`
- Captures and returns stdout/stderr

## Testing

### Unit Tests
**File:** [tests/unit/test_trestle_init.py](../../../tests/unit/test_trestle_init.py)

- ✅ test_trestle_init_default - Default parameters
- ✅ test_trestle_init_full_mode - Full mode
- ✅ test_trestle_init_govdocs_mode - Govdocs mode
- ✅ test_trestle_init_with_custom_root - Custom root
- ✅ test_trestle_init_verbose - Verbose output
- ✅ test_trestle_init_failure - Failure case
- ✅ test_trestle_init_all_options - All options specified

### E2E Tests
**File:** [tests/e2e/test_mcp_server.py](../../../tests/e2e/test_mcp_server.py)

- ✅ test_init_workflow - Actual workflow
- ✅ test_init_and_import_workflow - init→import integration

## Edge Cases

### Already Initialized
- Executing in a directory already initialized
- **Expected:** Returns an error message
- **Status:** Handled by the trestle CLI

### Permission Error
- Executing in a directory without write permissions
- **Expected:** Returns an error message
- **Status:** Handled by the trestle CLI

### Invalid Path
- Specifying a non-existent path for `trestle_root`
- **Expected:** Returns an error message
- **Status:** Handled by the trestle CLI

## Related
- **Next feature:** [F-002: trestle import](F-002-import.md) - Model import after workspace initialization
- **trestle docs:** https://ibm.github.io/compliance-trestle/
