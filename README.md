# Trestle MCP

MCP server to easily use [compliance-trestle](https://github.com/oscal-compass/compliance-trestle) (OSCAL tool) from Claude, Roo, or any MCP-compliant client.

## Getting Started

This project can be used in the following two ways:

- **[Usage from Coding Agent (Roo Code)](#usage-from-roocode)**: Use Trestle-MCP from Roo Code via MCP.
- **[Usage from CLI (MCP Client)](#usage-from-cli-mcp-client)**: Invoke Trestle-MCP directly using an MCP CLI client.

Choose the option that best fits your workflow.

## Usage from RooCode

1. Add the following JSON to `.roo/mcp.json` (Roo workspace):
    
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

2. Open Roo, confirm `trestle` tools are listed in the MCP panel, and execute as needed.

    https://github.com/user-attachments/assets/59215549-cad9-4101-baa4-ecba77ac3904

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
6 Available Tools
┌─────────┬─────────────────────────────────┬───────────────────────────────────────────────────────────────────┐
│ Server  │ Tool                            │ Description                                                       │
├─────────┼─────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ trestle │ trestle_init                    │ Initialize a trestle working directory.                           │
│ trestle │ trestle_import                  │ Import an existing OSCAL model into the trestle workspace.        │
│ trestle │ trestle_author_catalog_generate │ Generate Catalog controls in markdown form from a catalog         │
│ trestle │ trestle_author_profile_generate │ Generate markdown documentation set for controls defined in profile│
│ trestle │ trestle_author_profile_resolve  │ Resolve an OSCAL profile to a resolved profile catalog.           │
│ trestle │ trestle_author_profile_assemble │ Assemble markdown controls into a Profile JSON file.              │
└─────────┴─────────────────────────────────┴───────────────────────────────────────────────────────────────────┘
```

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

## Tool List & Quick Reference

- `trestle_init`: Initialize a trestle workspace
- `trestle_import`: Import OSCAL models (Catalog/Profile/etc.) from a file or URL
- `trestle_author_catalog_generate`: Generate markdown controls from a catalog
- `trestle_author_profile_generate`: Generate markdown for profiles
- `trestle_author_profile_resolve`: Resolve profile to catalog
- `trestle_author_profile_assemble`: Assemble markdown controls into profile JSON

For advanced use, refer to official [compliance-trestle docs](https://oscal-compass.dev/compliance-trestle/latest/) or [developer documents](docs/command-specs-development.md) in this repo.

## Troubleshooting & Help

- Make sure [uvx](https://docs.astral.sh/uv/getting-started/installation/) is installed and on your PATH.
- If you see command/module errors, check the MCP server path in `mcp.json` is correct.
