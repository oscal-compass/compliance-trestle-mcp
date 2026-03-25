# Architecture

## High-Level Overview

![High-Level Architecture](images/architecture.png)

**compliance-trestle-mcp** is an [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that bridges AI coding agents with [compliance-trestle](https://github.com/oscal-compass/compliance-trestle), an OSCAL-based compliance automation tool.

The coding agent workspace doubles as the `trestle_root` — the directory that compliance-trestle uses to store and manage OSCAL artifacts. This means the AI agent can read and edit OSCAL files (catalogs, profiles, component definitions, markdown control docs) directly alongside the MCP tools that operate on them.

**Request flow:**
1. The user asks the coding agent (Roo Code, Claude, etc.) to perform an OSCAL operation in natural language.
2. The coding agent calls the appropriate MCP tool exposed by the Trestle MCP Server.
3. The server translates the call into a `compliance-trestle` CLI command and runs it as a subprocess.
4. The CLI reads from and writes to the `trestle_root/` directory inside the workspace.

## System Overview

```mermaid
graph TB
    subgraph Clients["MCP Clients"]
        C1[Claude Desktop]
        C2[Roo Code]
        C3[Other MCP Clients]
    end

    subgraph Server["compliance-trestle-mcp (MCP Server)"]
        direction TB
        Main["main.py\nFastMCP Server\n@mcp.tool() handlers"]

        subgraph Services["trestle_mcp/services/"]
            Init["init.py\ntrestle_init"]
            Import["import_.py\ntrestle_import"]

            subgraph Author["author/"]
                CatalogGen["catalog_generate.py\ntrestle_author_catalog_generate"]
                ProfileGen["profile_generate.py\ntrestle_author_profile_generate"]
                ProfileRes["profile_resolve.py\ntrestle_author_profile_resolve"]
                ProfileAsm["profile_assemble.py\ntrestle_author_profile_assemble"]
            end

            subgraph Task["task/"]
                CsvCD["csv_to_oscal_cd.py\ntrestle_task_csv_to_oscal_cd"]
            end
        end

        Lib["libs/trestle.py\nrun_trestle_command()\nfind_trestle_bin()"]
    end

    subgraph OSCAL["OSCAL Workspace (trestle_root/)"]
        direction LR
        Catalogs["catalogs/\n*.json"]
        Profiles["profiles/\n*.json"]
        CompDefs["component-definitions/\n*.json"]
        Markdown["markdown/\n*.md"]
    end

    TrestleCLI["compliance-trestle CLI\n(subprocess)"]

    Clients -- "MCP stdio transport" --> Main
    Main --> Init & Import & Author & Task
    Init & Import & Author & Task --> Lib
    Lib -- "subprocess.run()" --> TrestleCLI
    TrestleCLI --> OSCAL
```

The server is structured around a thin service layer. Each MCP tool has a dedicated service module under `trestle_mcp/services/` that validates inputs via Pydantic and constructs the appropriate CLI arguments. All subprocess execution is centralized in `libs/trestle.py`, which locates the `trestle` binary and runs it with a 60-second timeout.

## MCP Tools

```mermaid
graph LR
    subgraph Tools["7 MCP Tools"]
        T1["trestle_init\nInitialize workspace"]
        T2["trestle_import\nImport OSCAL model"]
        T3["trestle_author_catalog_generate\nCatalog → Markdown"]
        T4["trestle_author_profile_generate\nProfile → Markdown"]
        T5["trestle_author_profile_resolve\nResolve profile → Catalog"]
        T6["trestle_author_profile_assemble\nMarkdown → Profile JSON"]
        T7["trestle_task_csv_to_oscal_cd\nCSV → Component Definition"]
    end
```

| Tool | Description |
|------|-------------|
| `trestle_init` | Initializes a new trestle workspace, creating the directory structure for OSCAL artifacts. |
| `trestle_import` | Imports an OSCAL model (catalog, profile, component definition, etc.) from a URL or local file. |
| `trestle_author_catalog_generate` | Generates editable Markdown from an OSCAL catalog JSON. |
| `trestle_author_profile_generate` | Generates editable Markdown from an OSCAL profile, scoped to the controls it selects. |
| `trestle_author_profile_resolve` | Resolves a profile against its source catalog(s) and outputs a resolved catalog with parameter values substituted. |
| `trestle_author_profile_assemble` | Assembles a directory of edited Markdown control files back into a Profile JSON. |
| `trestle_task_csv_to_oscal_cd` | Converts a CSV file containing control implementation data into an OSCAL Component Definition JSON. |

## Data Flow

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant MCP as main.py (FastMCP)
    participant Svc as Service Module
    participant Lib as libs/trestle.py
    participant CLI as trestle CLI
    participant FS as Filesystem (OSCAL)

    Client->>MCP: Tool call (JSON args)
    MCP->>Svc: Call service function(params)
    Svc->>Svc: Pydantic validation
    Svc->>Lib: run_trestle_command(args, cwd)
    Lib->>CLI: subprocess.run(timeout=60s)
    CLI->>FS: Write OSCAL JSON & Markdown
    FS-->>CLI: Read OSCAL JSON & Markdown
    CLI-->>Lib: stdout / stderr
    Lib-->>Svc: CompletedProcess result
    Svc-->>MCP: "✅ success..." or "❌ error..."
    MCP-->>Client: Tool result (string)
```

Tool handlers are all `async def` to support concurrent MCP calls. Errors are returned as formatted strings (never raised as exceptions) so the MCP client always receives a readable result. Some tools (e.g. `csv_to_oscal_cd`, `profile_assemble`) generate temporary config files required by the underlying CLI command and clean them up after execution.

## Dependency Stack

```mermaid
graph BT
    trestle_mcp --> mcp["mcp>=1.0.0\n(Model Context Protocol)"]
    trestle_mcp --> pydantic["pydantic>=2.0.0\n(Validation)"]
    trestle_mcp --> compliance_trestle["compliance-trestle>=3.11.0\n(OSCAL Tool)"]
    trestle_mcp --> ruamel["ruamel.yaml>=0.19.0\n(YAML)"]
    compliance_trestle --> oscal["OSCAL\n(Open Security Controls\nAssessment Language)"]
```

`compliance-trestle-mcp` is intentionally a thin wrapper — it adds no OSCAL logic of its own. All compliance semantics live in `compliance-trestle`, keeping this package focused solely on exposing that functionality over the MCP protocol.
