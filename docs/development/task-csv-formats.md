# CSV formats the task tools accept

These are **trestle's** input formats, not anything this server defines. They
are recorded here because they cannot be derived from this repository's code —
the tools pass a CSV path through to the trestle task, which does the parsing.

The authoritative source is the task's own help text, which
`trestle_task_list` returns for a named task:

```
trestle_task_list(task="csv-to-oscal-cd")
```

Each tool's description covers what you need for the common case; this page is
the longer reference, including the parts that bite.

---

## `csv-to-oscal-cd` — component definitions

Used by `trestle_task_csv_to_oscal_cd`.

### Row convention

| Row | Content |
|-----|---------|
| 1 | Column headings (used as keys) |
| 2 | Column descriptions (human-readable, not parsed) |
| 3+ | Data rows |

### Column name prefixes

| Prefix | Meaning |
|--------|---------|
| `$$` | Required column |
| `$` | Optional column |
| `#` | Comment column — ignored entirely |

### Component types

| Type | Description |
|------|-------------|
| `service` | A software or infrastructure component that implements controls (e.g. a firewall, an OS) |
| `validation` | A tool or scanner that *checks* whether a service component's rules are satisfied (e.g. a compliance scanner) |

A single component-definition JSON can contain both types.

### Required columns

| Column | Notes |
|--------|-------|
| `$$Component_Title` | Display name of the component |
| `$$Component_Description` | Description of the component |
| `$$Component_Type` | `service` or `validation` |
| `$$Rule_Id` | Unique rule identifier |
| `$$Rule_Description` | Description of the rule *(ignored for `validation` type)* |
| `$$Profile_Source` | href to the OSCAL profile or catalog *(ignored for `validation` type)* |
| `$$Profile_Description` | Human-readable profile name *(ignored for `validation` type)* |
| `$$Control_Id_List` | Space-separated control ids, e.g. `ac-3 au-2` *(ignored for `validation` type)* |
| `$$Namespace` | Namespace URI for props, e.g. `https://acme.example.com` |

### Optional columns

| Column | Notes |
|--------|-------|
| `$Check_Id` | Check identifier — **required for `validation` type** |
| `$Check_Description` | Check description — **required for `validation` type** |
| `$Target_Component` | Links a validation check to its target service component. Needed when `Rule_Id` values collide across components |
| `$Original_Risk_Rating` | *(ignored for `validation` type)* |
| `$Adjusted_Risk_Rating` | *(ignored for `validation` type)* |
| `$Risk_Adjustment` | *(ignored for `validation` type)* |
| `$Parameter_Id` | Parameter identifier. Several sets via a suffix: `$Parameter_Id_1`, `$Parameter_Id_2`, … *(ignored for `validation` type)* |
| `$Parameter_Description` | *(ignored for `validation` type)* |
| `$Parameter_Value_Alternatives` | *(ignored for `validation` type)* |

### A service component

```csv
$$Component_Title,$$Component_Description,$$Component_Type,$$Rule_Id,$$Rule_Description,$$Profile_Source,$$Profile_Description,$$Control_Id_List,$$Namespace
Component title,Component description,Component type,Rule ID,Rule description,Profile source,Profile description,Control ID list,Namespace
ACME Firewall,Network firewall component,service,rule-fw-01,Firewall must block unauthorized traffic,trestle://catalogs/nist-sample/catalog.json,NIST SP 800-53 sample,ac-1,https://acme.example.com
```

See [`tests/data/task/csv-to-oscal-cd/components.csv`](../../tests/data/task/csv-to-oscal-cd/components.csv).

### A validation component

`$$Rule_Description`, `$$Profile_Source`, `$$Profile_Description` and
`$$Control_Id_List` are **ignored** for the `validation` type — leave them
empty — and `$Check_Id` and `$Check_Description` become **required**.

```csv
$$Component_Title,$$Component_Description,$$Component_Type,$$Rule_Id,$$Rule_Description,$$Profile_Source,$$Profile_Description,$$Control_Id_List,$$Namespace,$Check_Id,$Check_Description,$Target_Component
Component title,Component description,Component type,Rule ID,ignored,ignored,ignored,ignored,Namespace,Check ID,Check description,Target component
ACME Scanner,Security scanner,validation,rule-fw-01,,,,,https://acme.example.com,check-fw-01-enabled,Check that rule-fw-01 blocks unauthorized traffic,ACME Firewall
```

See [`tests/data/task/csv-to-oscal-cd/validation-components.csv`](../../tests/data/task/csv-to-oscal-cd/validation-components.csv).

### Things that bite

- **Several components in one CSV.** Multiple `$$Component_Title` values produce
  multiple components in one `component-definition.json`. Rows sharing a title
  are merged into one component, each row becoming a separate `rule_set_N` group
  in `props`.
- **`Rule_Id` collisions.** When a validation component targets several service
  components that share a `$$Rule_Id`, use `$Target_Component` to disambiguate.
- **Updating an existing definition.** Pass `component_definition` pointing at
  the existing JSON: new rules are added and existing ones updated. Use
  `output_overwrite=true`.
- **`$$Profile_Source` is resolved.** `author component-generate` follows that
  href later. A URL there means a network fetch every time — prefer a
  `trestle://` href into the workspace. This is what kept the end-to-end suite
  off the network; see [tests/data/README.md](../../tests/data/README.md).

---

## `csv-to-oscal-mc` — mapping collections

Used by `trestle_task_csv_to_oscal_mc`. Same three-row convention and `$$`/`$`
prefixes.

The tool's own description is the fuller reference for this one — it covers the
columns, the NIST IR 8477 relationship vocabulary, how to declare a control
unmapped, and the percentage range. Two points worth repeating because they fail
quietly or confusingly:

- **`$$Map_Confidence_Score` and `$$Map_Coverage` are 0 to 1, not 0 to 100.** A
  value of `80` is dropped with a "Percentage value out of range" warning and the
  map entry is written without it. Write `0.8`.
- **An empty `$$Map_Relationship` declares a control unmapped.** It is then
  recorded in the gap summary instead of producing a map entry.

See [`tests/data/task/csv-to-oscal-mc/mapping.csv`](../../tests/data/task/csv-to-oscal-mc/mapping.csv).

---

## Other tasks

`trestle_task_xlsx_to_oscal_poam` takes a FedRAMP XLSX workbook rather than a
CSV; its tool description covers the sheet it expects.

For any task without a typed tool, `trestle_task_run` runs it from a
configuration dictionary. Get the configuration keys from `trestle_task_list`
with a `task` argument — that help text is authoritative, and an unrecognised
key is ignored silently.
