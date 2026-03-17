# trestle task csv-to-oscal-cd

## Purpose

Convert a specially formatted CSV file into an OSCAL `component-definition` JSON file.
This task is the primary way to bulk-author component definitions from spreadsheet data.

## Key Concepts

### Component Types

| Type | Description |
|------|-------------|
| `service` | A software or infrastructure component that implements controls (e.g. a firewall, an OS) |
| `validation` | A tool or scanner that *checks* whether a service component's rules are satisfied (e.g. a compliance scanner) |

A single component-definition JSON can contain both types.

### CSV Structure

The CSV has a strict 3-row header convention:

| Row | Content |
|-----|---------|
| 1 | Column headings (used as keys) |
| 2 | Column descriptions (human-readable, not parsed) |
| 3+ | Data rows |

### Column Naming Conventions

| Prefix | Meaning |
|--------|---------|
| `$$` | Required column |
| `$` | Optional column |
| `#` | Comment column — ignored entirely |

---

## Column Reference

### Required Columns (all component types)

| Column | Notes |
|--------|-------|
| `$$Component_Title` | Display name of the component |
| `$$Component_Description` | Description of the component |
| `$$Component_Type` | `service` or `validation` |
| `$$Rule_Id` | Unique rule identifier |
| `$$Rule_Description` | Description of the rule *(ignored for `validation` type)* |
| `$$Profile_Source` | URL to the OSCAL profile/catalog *(ignored for `validation` type)* |
| `$$Profile_Description` | Human-readable profile name *(ignored for `validation` type)* |
| `$$Control_Id_List` | Space-separated control IDs e.g. `ac-3 au-2` *(ignored for `validation` type)* |
| `$$Namespace` | Namespace URI for props e.g. `https://acme.example.com` |

### Optional Columns

| Column | Notes |
|--------|-------|
| `$Check_Id` | Check identifier — **required for `validation` type** |
| `$Check_Description` | Check description — **required for `validation` type** |
| `$Target_Component` | Links a validation check to its target service component. Recommended when `Rule_Id` values may collide across components |
| `$Original_Risk_Rating` | *(ignored for `validation` type)* |
| `$Adjusted_Risk_Rating` | *(ignored for `validation` type)* |
| `$Risk_Adjustment` | *(ignored for `validation` type)* |
| `$Parameter_Id` | Parameter identifier. Multiple sets via suffix: `$Parameter_Id_1`, `$Parameter_Id_2`, ... *(ignored for `validation` type)* |
| `$Parameter_Description` | *(ignored for `validation` type)* |
| `$Parameter_Value_Alternatives` | *(ignored for `validation` type)* |

---

## CSV Examples

### Service Component (type: service)

```csv
$$Component_Title,$$Component_Description,$$Component_Type,$$Rule_Id,$$Rule_Description,$$Profile_Source,$$Profile_Description,$$Control_Id_List,$$Namespace
Component title,Component description,Component type,Rule ID,Rule description,Profile source,Profile description,Control ID list,Namespace
ACME Firewall,Network firewall component,service,rule-fw-01,Firewall must block unauthorized traffic,https://example.com/catalog.json,NIST SP 800-53 Rev 5,ac-3,https://acme.example.com
ACME Firewall,Network firewall component,service,rule-fw-02,Firewall must log all denied connections,https://example.com/catalog.json,NIST SP 800-53 Rev 5,au-2,https://acme.example.com
```

See: [`tests/data/task/csv-to-oscal-cd/components.csv`](../../../tests/data/task/csv-to-oscal-cd/components.csv)

### Validation Component (type: validation)

The `$$Rule_Description`, `$$Profile_Source`, `$$Profile_Description`, `$$Control_Id_List` columns
are **ignored** for validation type — leave them empty.
`$Check_Id` and `$Check_Description` become **required**.

```csv
$$Component_Title,$$Component_Description,$$Component_Type,$$Rule_Id,$$Rule_Description,$$Profile_Source,$$Profile_Description,$$Control_Id_List,$$Namespace,$Check_Id,$Check_Description,$Target_Component
Component title,Component description,Component type,Rule ID,ignored,ignored,ignored,ignored,Namespace,Check ID,Check description,Target component
ACME Scanner,Security scanner,validation,rule-fw-01,,,,,https://acme.example.com,check-fw-01-enabled,Check that rule-fw-01 blocks unauthorized traffic,ACME Firewall
ACME Scanner,Security scanner,validation,rule-fw-02,,,,,https://acme.example.com,check-fw-02-logging,Check that rule-fw-02 logging is active,ACME Firewall
```

See: [`tests/data/task/csv-to-oscal-cd/validation-components.csv`](../../../tests/data/task/csv-to-oscal-cd/validation-components.csv)

---

## CLI

### Usage

```bash
trestle task csv-to-oscal-cd --config <config.ini> [-tr TRESTLE_ROOT]
```

### Config file format (INI)

```ini
[task.csv-to-oscal-cd]
title                = (required) the component definition title
version              = (required) the component definition version
csv-file             = (required) path to the CSV file
output-dir           = (required) path to the output directory
component-definition = (optional) path to an existing component-definition to update
output-overwrite     = (optional) true [default] | false
validate-controls    = (optional) off [default] | warn | on
class.Rule_Id        = (optional) associate a CSS class with a column, e.g. scc_class
```

See: [`tests/data/task/csv-to-oscal-cd/config.ini`](../../../tests/data/task/csv-to-oscal-cd/config.ini)

---

## MCP Tool Design

**Tool name:** `trestle_task_csv_to_oscal_cd`

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `title` | string | yes | — | Component definition title |
| `version` | string | yes | — | Component definition version |
| `csv_file` | string | yes | — | Absolute path to the CSV file |
| `output_dir` | string | yes | — | Absolute path to the output directory |
| `component_definition` | string | no | `null` | Path to existing component-definition to update |
| `output_overwrite` | boolean | no | `true` | Overwrite existing output |
| `validate_controls` | string | no | `"off"` | `"on"` / `"warn"` / `"off"` |
| `class_column_mappings` | dict | no | `null` | e.g. `{"Rule_Id": "scc_class"}` |
| `trestle_root` | string | no | `null` | Trestle workspace root path |
| `verbose` | boolean | no | `false` | Display verbose output |

**Returns:** string
- On success: `✅ CSV converted to OSCAL component definition successfully\n\nOutput directory: {output_dir}\n\n{stdout}`
- On failure: `❌ Failed to convert CSV to OSCAL component definition\n\nCSV file: {csv_file}\nError: {stderr}`

### Behavior

The MCP wrapper generates a temporary INI config file from the input parameters,
calls `trestle task csv-to-oscal-cd --config <tmpfile>`, then deletes the temp file.
The INI file is never persisted — callers pass parameters directly, not a config path.

### Examples

#### Example 1: Service component definition

```python
trestle_task_csv_to_oscal_cd(
    title="ACME Component Definition",
    version="1.0.0",
    csv_file="/workspace/components.csv",
    output_dir="/workspace/component-definitions",
    trestle_root="/workspace"
)
```

#### Example 2: Update an existing component-definition

```python
trestle_task_csv_to_oscal_cd(
    title="ACME Component Definition",
    version="1.1.0",
    csv_file="/workspace/components.csv",
    output_dir="/workspace/component-definitions",
    component_definition="/workspace/component-definitions/component-definition.json",
    trestle_root="/workspace"
)
```

#### Example 3: With column class mapping

```python
trestle_task_csv_to_oscal_cd(
    title="ACME Component Definition",
    version="1.0.0",
    csv_file="/workspace/components.csv",
    output_dir="/workspace/component-definitions",
    class_column_mappings={"Rule_Id": "scc_class"},
    trestle_root="/workspace"
)
```

---

## Implementation

**File:** [`trestle_mcp/services/task/csv_to_oscal_cd.py`](../../../trestle_mcp/services/task/csv_to_oscal_cd.py)

**Approach:** Config-file task wrapper
- Builds a `configparser` INI in memory from input params
- Writes to a `tempfile.NamedTemporaryFile` (auto-deleted via `try/finally`)
- Calls `trestle task csv-to-oscal-cd --config <tmpfile>`

## Testing

### Unit Tests

**File:** [`tests/unit/services/task/test_csv_to_oscal_cd.py`](../../../tests/unit/services/task/test_csv_to_oscal_cd.py)

- ✅ test_success_required_params_only
- ✅ test_config_file_contents
- ✅ test_config_file_required_fields
- ✅ test_optional_component_definition
- ✅ test_output_overwrite_false
- ✅ test_validate_controls_on
- ✅ test_class_column_mappings
- ✅ test_trestle_root_and_verbose
- ✅ test_failure_returns_error_message
- ✅ test_config_file_cleaned_up_on_success
- ✅ test_config_file_cleaned_up_on_failure

### Test Data

| File | Description |
|------|-------------|
| [`tests/data/task/csv-to-oscal-cd/components.csv`](../../../tests/data/task/csv-to-oscal-cd/components.csv) | Service component example (2 data rows) |
| [`tests/data/task/csv-to-oscal-cd/validation-components.csv`](../../../tests/data/task/csv-to-oscal-cd/validation-components.csv) | Validation component example (2 data rows) |
| [`tests/data/task/csv-to-oscal-cd/config.ini`](../../../tests/data/task/csv-to-oscal-cd/config.ini) | Sample INI config for manual CLI use |

---

## Edge Cases

### Multiple components in one CSV

Multiple `$$Component_Title` values in one CSV produce multiple components in a single
`component-definition.json`. Rows with the same title are merged into one component,
with each row becoming a separate `rule_set_N` group in `props`.

### Rule_Id collision across components

When a validation component targets multiple service components that share the same
`$$Rule_Id`, use `$Target_Component` to disambiguate.

### Updating an existing component-definition

Pass `component_definition` pointing to the existing JSON.
New rules are added; existing ones are updated. Use `output_overwrite=true`.
