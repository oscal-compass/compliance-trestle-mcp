# Trestle MCP

MCP server to easily use [compliance-trestle](https://github.com/oscal-compass/compliance-trestle) (OSCAL tool) from OpenCode, Claude, or any MCP-compliant client.

mcp-name: io.github.oscal-compass/compliance-trestle-mcp

## Getting Started

This project can be used in the following two ways:

- **[Usage from a coding agent (OpenCode)](#usage-from-opencode)**: Use Trestle-MCP from OpenCode via MCP.
- **[Usage from CLI (MCP Client)](#usage-from-cli-mcp-client)**: Invoke Trestle-MCP directly using an MCP CLI client.

Choose the option that best fits your workflow.

## Usage from OpenCode

1. Add the following to `opencode.json` in your workspace:

    ```json
    {
        "mcp": {
            "trestle": {
                "type": "local",
                "command": ["uvx", "--from", "compliance-trestle-mcp==<version>", "trestle-mcp"],
                "environment": { "TRESTLE_MCP_TOOLS": "all" },
                "enabled": true
            }
        }
    }
    ```

    Replace `<version>` with the release you want; drop `==<version>` to track the
    latest. `TRESTLE_MCP_TOOLS` chooses how much of the command surface to expose —
    `all` is every tool, and the default without it is the authoring lifecycle. See
    [Choosing which tools are exposed](#choosing-which-tools-are-exposed).

2. Open OpenCode, confirm the `trestle` tools are listed, and execute as needed.

    https://github.com/user-attachments/assets/86c0abce-7285-4539-a7ae-90bbc1d2a66c

---

## Usage from CLI (MCP Client)

#### Step 1: Write your `mcp.json` config

```json
{
    "mcpServers": {
        "trestle": {
            "command": "uvx",
            "args": ["--from", "./trestle-mcp-tmp", "trestle-mcp"]
        }
    }
}
```

Save this as `mcp.json` in your current directory.

#### Step 2: List Available Tools

```
uvx mcp-cli tools --config-file mcp.json
```

Sample output (tools available):

```
13 Available Tools
┌─────────┬───────────────────────────────────┬───────────────────────────────────────────────────────────────────┐
│ Server  │ Tool                              │ Description                                                       │
├─────────┼───────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ trestle │ trestle_init                      │ Initialize a trestle working directory.                           │
│ trestle │ trestle_import                    │ Import an existing OSCAL model into the trestle workspace.        │
│ trestle │ trestle_validate                  │ Validate a standalone OSCAL file against the OSCAL schema.        │
│ trestle │ trestle_author_catalog_generate   │ Generate Catalog controls in markdown form from a catalog.        │
│ trestle │ trestle_author_catalog_assemble   │ Assemble markdown files of controls into a Catalog json file.     │
│ trestle │ trestle_author_profile_generate   │ Generate markdown documentation set for controls in a profile.    │
│ trestle │ trestle_author_profile_assemble   │ Assemble markdown controls into a Profile JSON file.              │
│ trestle │ trestle_author_profile_resolve    │ Resolve an OSCAL profile to a resolved profile catalog.           │
│ trestle │ trestle_author_component_generate │ Generate component markdown from a component-definition.          │
│ trestle │ trestle_author_component_assemble │ Assemble markdown controls into a component-definition json file. │
│ trestle │ trestle_task_csv_to_oscal_cd      │ Convert a CSV file to an OSCAL component definition.              │
│ trestle │ trestle_task_csv_to_oscal_mc      │ Convert a CSV file to an OSCAL mapping collection.                │
│ trestle │ trestle_task_xlsx_to_oscal_poam   │ Convert a FedRAMP XLSX spreadsheet to an OSCAL POA&M.             │
└─────────┴───────────────────────────────────┴───────────────────────────────────────────────────────────────────┘
```

Those 13 are the default selection. The server implements 29 tools in all: 28
that groups can select, plus `trestle_remove`, which is registered only when
named explicitly. See
[Choosing which tools are exposed](#choosing-which-tools-are-exposed), and
[Commands deliberately not covered](docs/development/README.md#commands-deliberately-not-covered)
for the parts of the trestle CLI that have no tool and why.

#### Step 3: Execute a Tool (e.g., `trestle_init`)

Start MCP interactive shell:

```
uvx mcp-cli interactive --config-file mcp.json
```

Then run, for example:

```
> execute trestle_init '{"params": {}}'
```

Typical result:

```
✓ ✅ Tool executed successfully
{
  "result": {
    ...
    "content": [
      {
        "type": "text",
        "text": "✅ Trestle workspace initialized successfully"
      }
    ]
  }
}
```

You'll see folders as follows: 
```
assessment-plans    catalogs               plan-of-action-and-milestones  system-security-plans
assessment-results  component-definitions  profiles
```

---

## Choosing which tools are exposed

Every tool a server registers costs the caller context: an MCP client loads each
tool's name, input schema and description into the model's context window on
every session. This server covers the trestle command surface an agent should
drive, but exposes only the authoring lifecycle unless you ask for more, so a
session carries the part of that surface it will actually call and the rest is
one setting away.

The selection is a comma-separated list of group names and/or individual tool
names, read from the `--tools` flag or the `TRESTLE_MCP_TOOLS` environment
variable. The flag wins over the environment variable. Naming something that
does not exist fails at startup with the list of valid names, rather than
starting up with the tool quietly missing — and the flag has to be spelled in
full, so a config file carrying `--tool` is rejected instead of guessed at.

| Value | Tools | `tools/list` chars | Meaning |
|---|---:|---:|---|
| `authoring` | 13 | 46,137 | The curated authoring lifecycle. **The default.** |
| `core` | 12 | 36,381 | The top-level trestle commands |
| `author` | 11 | 39,695 | Every `trestle author` subcommand wrapper |
| `task` | 5 | 19,848 | Every `trestle task` wrapper, including the generic runner |
| `all` | 28 | 95,922 | Everything a group can select |
| `trestle_author_ssp_generate` | 1 | 4,629 | Any single tool, by its registered name |

The default is less than half the size of `all`, and selections combine, so you
pay only for what you name. Measure any selection yourself with
`python scripts/tool_context_cost.py`; see
[What each tool selection costs in context](docs/development/tool-context-cost.md) for the
current figures per selection and per tool, and for how to narrow the default
further.

`core`, `author` and `task` mirror the trestle CLI's own command structure, so
which tool is in which group follows from the CLI. `authoring` is the one
curated preset that cuts across them.

**Tools no group selects.** `trestle_remove` deletes an element from a model in
place, with no backup, so no group selects it — `all` included. It is registered
only when the selection names it exactly, e.g. `authoring,trestle_remove`.

**Default (the authoring lifecycle) — no configuration needed:**

```json
{
    "mcpServers": {
        "trestle": {
            "command": "uvx",
            "args": ["--from", "compliance-trestle-mcp", "trestle-mcp"]
        }
    }
}
```

**Everything, via the environment variable:**

```json
{
    "mcpServers": {
        "trestle": {
            "command": "uvx",
            "args": ["--from", "compliance-trestle-mcp", "trestle-mcp"],
            "env": { "TRESTLE_MCP_TOOLS": "all" }
        }
    }
}
```

**A mixed selection, via the flag — the authoring lifecycle plus SSP generation
and the generic task runner:**

```json
{
    "mcpServers": {
        "trestle": {
            "command": "uvx",
            "args": [
                "--from", "compliance-trestle-mcp", "trestle-mcp",
                "--tools", "authoring,trestle_author_ssp_generate,trestle_task_run"
            ]
        }
    }
}
```

The examples above use the `mcpServers` shape most MCP clients take. OpenCode
spells the same things differently — `mcp` rather than `mcpServers`, `command`
as one array instead of a `command` plus `args`, and `environment` rather than
`env` — so the "everything" selection looks like
[the entry at the top of this README](#usage-from-opencode).

Run `trestle-mcp --help` for the group list, and watch stderr on startup for the
line reporting the selection and how many tools it registered.

## Tool List & Quick Reference

Tools marked **(default)** are in the `authoring` preset.

### `core` — top-level trestle commands

- `trestle_init` **(default)**: Initialize a trestle workspace
- `trestle_import` **(default)**: Import OSCAL models (Catalog/Profile/etc.) from a file or URL
- `trestle_validate` **(default)**: Validate a standalone OSCAL file (any top-level model, e.g. POA&M) against the OSCAL schema (and trestle's semantic checks)
- `trestle_create`: Create a sample OSCAL model, or a new element inside an existing model file
- `trestle_assemble`: Assemble a split model into a single file under `dist`
- `trestle_split`: Split subcomponents of a model into separate files
- `trestle_merge`: Merge split subcomponents back into a model
- `trestle_describe`: Describe the contents of a model file, optionally at an element path
- `trestle_replicate`: Copy a top-level model to a new name, optionally with fresh uuids
- `trestle_href`: List or repoint the import hrefs of a profile
- `trestle_partial_object_validate`: Validate a single OSCAL object held in a file
- `trestle_version`: Report the trestle and OSCAL versions, or a model's OSCAL version

### `author` — `trestle author` subcommands

- `trestle_author_catalog_generate` **(default)**: Generate markdown controls from a catalog
- `trestle_author_catalog_assemble` **(default)**: Assemble markdown controls back into a catalog JSON
- `trestle_author_profile_generate` **(default)**: Generate markdown for profiles
- `trestle_author_profile_assemble` **(default)**: Assemble markdown controls into profile JSON
- `trestle_author_profile_resolve` **(default)**: Resolve a profile to a catalog
- `trestle_author_profile_inherit`: Derive a profile from a parent profile and a leveraged SSP
- `trestle_author_component_generate` **(default)**: Generate markdown from a component definition
- `trestle_author_component_assemble` **(default)**: Assemble markdown back into a component definition
- `trestle_author_ssp_generate`: Generate SSP markdown from a profile and component definitions
- `trestle_author_ssp_assemble`: Assemble SSP markdown into a system-security-plan JSON
- `trestle_author_ssp_filter`: Filter an SSP by profile, components, implementation status or control origination

### `task` — `trestle task` wrappers

- `trestle_task_csv_to_oscal_cd` **(default)**: Convert a CSV mapping file into an OSCAL component definition
- `trestle_task_csv_to_oscal_mc` **(default)**: Convert a CSV crosswalk into an OSCAL mapping collection
- `trestle_task_xlsx_to_oscal_poam` **(default)**: Convert a FedRAMP-format XLSX spreadsheet into an OSCAL Plan of Action and Milestones (POA&M)
- `trestle_task_list`: List the available trestle tasks, or describe one task's configuration keys
- `trestle_task_run`: Run any trestle task from a configuration dictionary

`trestle_task_run` covers every task the installed trestle provides, including
ones with no typed tool here. Prefer the typed tools where they exist: they
validate their arguments and document the input format.

### Not covered

The signing and provenance commands (`sign`, `verify`, `generate-manifest`,
`sign-manifest`, `verify-manifest`, `canonicalize`), the `beta` feature-flag
command, and the markdown governance commands (`author docs`, `author folders`,
`author headers`, `author jinja`) have no tools here. The reasons are recorded
in the [development guide](docs/development/README.md#commands-deliberately-not-covered).

For advanced use, refer to the official [compliance-trestle docs](https://oscal-compass.dev/compliance-trestle/latest/); to add or change a tool here, see the [development guide](docs/development/README.md).

## Troubleshooting & Help

- Make sure [uvx](https://docs.astral.sh/uv/getting-started/installation/) is installed and on your PATH.
- If you see command/module errors, check the MCP server path in `mcp.json` is correct.

______________________________________________________________________

We are a Cloud Native Computing Foundation sandbox project.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://www.cncf.io/wp-content/uploads/2022/07/cncf-white-logo.svg">
  <img src="https://www.cncf.io/wp-content/uploads/2022/07/cncf-color-bg.svg" width=300 />
</picture>

The Linux Foundation® (TLF) has registered trademarks and uses trademarks. For a list of TLF trademarks, see [Trademark Usage](https://www.linuxfoundation.org/legal/trademark-usage).

*OSCAL Compass is an independent open source project. It is not affiliated with, endorsed by, or sponsored by the National Institute of Standards and Technology (NIST) or any other government agency.*

*OSCAL Compass was originally contributed by IBM.*
