# Development guide

How to add or change a tool in this server. If you are looking for what the
tools do, start from the [README](../../README.md); for how the pieces fit together,
[architecture.md](../architecture.md).

This replaces the older `docs/command-specs/` directory and its development
guide, which described a spec-first workflow from before the server had a tool
table: you wrote a markdown spec per command, then implemented it. The specs
duplicated what the code now states — the input model is the parameter list, and
the service docstring is the tool description shipped to clients — and the
copies drifted. Everything a tool promises now lives next to the code that keeps
the promise.

---

## Layout

```
trestle_mcp/
  main.py                  build_server(), register_tool(), the CLI entry point
  tools.py                 TOOL_SPECS: one row per tool, and the startup selector
  libs/
    trestle.py             run_trestle_command(), find_trestle_bin(), timeouts
    oscal_types.py         OscalModelType, FileExtension — shared CLI choices
    oscal_validate.py      in-process OSCAL validation (trestle_validate only)
  services/                one module per trestle command
    <command>.py           top-level commands: init, import_, create, split, ...
    author/<subcommand>.py trestle author ...
    task/<task>.py         trestle task ...
tests/
  unit/                    mocked; fast; run by CI
  e2e/                     real trestle CLI through an in-process server; run by CI
  data/                    fixtures — see tests/data/README.md
scripts/
  tool_context_cost.py     what each tool selection costs the caller
  check_versions.py        pyproject.toml and server.json agree
docs/
  architecture.md          structure, data flow, dependencies — not dev-only
  images/                  diagrams referenced from architecture.md
  development/             this directory: everything needed to work on the server
    README.md              this guide
    tool-context-cost.md   what each selection costs, and the current figures
    task-csv-formats.md    the CSV layouts the task tools accept
    mcp-registry.md        publishing a release to the MCP registry
```

The services tree mirrors the trestle CLI: `trestle author catalog-generate`
lives in `services/author/catalog_generate.py`.

---

## Adding a tool

### 1. Read the real CLI first

```sh
trestle <command> --help
```

Do not copy that output into a document. It changes between trestle releases —
the old specs pasted it and went stale — so treat the installed CLI as the only
authority and encode what you learn in the input model.

### 2. Write the service module

One module per command, with a Pydantic input model and an async handler:

```python
"""Trestle split command service.

This module implements splitting a trestle model into subcomponent files.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from trestle_mcp.libs.trestle import run_trestle_command


class TrestleSplitInput(BaseModel):
    """Input model for trestle split command."""

    model_config = ConfigDict(str_strip_whitespace=True)

    file: str = Field(..., description="Path of the model file to split")
    trestle_root: Optional[str] = Field(
        default=None,
        description="Path to trestle root directory (default: current directory)",
    )
    verbose: bool = Field(default=False, description="Display verbose output")


async def trestle_split(params: TrestleSplitInput) -> str:
    """One-line summary, then what the command is for.

    Args:
        params (TrestleSplitInput): Input parameters with:
            - file (str): Model file to split (required)
            - trestle_root (Optional[str]): Trestle workspace root path
            - verbose (bool): Display verbose output

    Returns:
        str: Success or error message

    Examples:
        - Use when: "Split the metadata out of this catalog"
          file="catalogs/mycat/catalog.json", element="catalog.metadata"
        - Don't use when: The model is already split at that element.
    """
    args = ["split", "--file", params.file]

    if params.trestle_root:
        args.extend(["--trestle-root", params.trestle_root])
    if params.verbose:
        args.append("--verbose")

    result = run_trestle_command(args)

    if result["success"]:
        return f"✅ Model split successfully\n\n{result['stdout'].strip()}"
    error = result["stderr"].strip()
    return f"❌ Failed to split model\n\nFile: {params.file}\nError: {error}"
```

Then import the module in the matching `services/__init__.py` — modules only,
by full package path, one level down.

**Pass `--trestle-root` whenever the command takes it.** It is not only a flag
for trestle: `run_trestle_command` makes the value absolute and runs the
subprocess *in* that directory. That is what lets a caller pass a relative
`file` or `output_dir` and have it mean a path inside the workspace. The
process's own working directory is wherever the MCP client launched the server,
which is almost never the workspace, so a service that omits the flag resolves
every relative path argument somewhere the caller never named. Only
`trestle merge` passes an explicit `cwd`, because it resolves its destination
model from the working directory rather than from the root.

### 3. The docstring is the tool description

FastMCP ships the handler's docstring to the client as the tool's description,
and derives the input schema from the `params` annotation. The docstring is the
specification; there is nowhere else to write one.

Sections, in this order:

- **Summary and body.** What the command does, and what it is for. Name the
  tools before and after it in a workflow — this is what stops a model reaching
  for `trestle_assemble` when it wanted `trestle_author_profile_assemble`.
- **`Args:`** one bullet per field, `- name (Type): description`, marking
  required ones. Every field must appear; a test enforces it.
- **`Returns:`**
- **`Examples:`** `Use when:` lines with a realistic phrasing and the arguments
  it maps to, and at least one `Don't use when:` naming the tool to use instead.

Write the body for a reader who has the control framework in mind but not the
trestle CLI. Say what the command needs to already exist, and what it leaves
behind.

### 4. Conventions that are not obvious

**Return errors, do not raise.** The client should always get a readable string.
One deliberate exception: input that cannot form a valid command fails Pydantic
validation before the subprocess starts. `trestle task <name>` takes the name
positionally, so `task="--help"` was read as a flag — trestle printed usage,
exited 0, and the tool reported success for a task that never ran. Both task
tools now pin the name with `pattern=r"^[a-z0-9][a-z0-9-]*$"`. If a field's value
reaches a positional slot, constrain its shape.

**Prefer `--flag value` over positional arguments.** Where the CLI insists on a
positional (`trestle assemble <type>`, `trestle task <name>`), use an enum from
`libs/oscal_types.py` or a validated pattern.

**Timeouts.** `run_trestle_command` applies `DEFAULT_TIMEOUT` (60s). Pass
`timeout=LONG_TIMEOUT` (600s) for commands that fetch remote content or walk a
whole catalog — `import`, `author profile-resolve`, `author ssp-generate` and
the four `task` tools that run a task do.

**Tasks take an INI file.** Every `trestle task` is driven by a
`[task.<name>]` section. Write it to a `NamedTemporaryFile` and remove it in a
`finally`. Values are safe to interpolate: `configparser` indents continuation
lines, so a newline in a value cannot inject another section.

**Reuse the shared enums.** `OscalModelType` and `FileExtension` in
`libs/oscal_types.py` are the model-type and file-extension choices the CLI
accepts. Declare them once.

### 5. Register it

Add a `ToolSpec` row to `TOOL_SPECS` in `trestle_mcp/tools.py`, in the section
for its group. Registration order follows the table.

```python
    ToolSpec(
        name="trestle_split",
        title="Split Model into Subcomponents",
        group="core",
        input_model=services.split.TrestleSplitInput,
        handler=services.split.trestle_split,
        annotations=_annotations(),
        presets=_AUTHORING,
    ),
```

- **`group`** is structural: `core`, `author` or `task`, mirroring the CLI. Which
  tool is in which group should follow from the CLI, not from a taxonomy
  invented here.
- **`input_model`** must match the handler's `params` annotation, or startup
  fails. Better a `TypeError` at launch than a wrong schema at call time.
- **`annotations`** are the MCP hints. Set `read_only=True` for a command that
  only reads, `idempotent=True` when running it twice is the same as once, and
  `destructive=True` when it removes content.
- **`presets=_AUTHORING`** puts the tool in the default selection. See below.
- **`opt_in=True`** takes it out of every group, `all` included.

### 6. Decide how visible it should be

Every registered tool's name, schema and description is loaded into the client's
context window on every session. Tool count is a cost paid by the caller, not a
feature. Measure it:

```sh
python scripts/tool_context_cost.py --per-tool
```

Implementing a command is cheap; putting it in `authoring` is not. A new tool
should default to **no preset**, and join `authoring` only when the authoring
lifecycle is incomplete without it. Record the new figures in
[tool-context-cost.md](tool-context-cost.md).

### 7. Test it

**Unit tests** (`tests/unit/services/...`) patch `run_trestle_command` and
assert on the argument list. Cover the minimal call, every optional argument,
the failure path, and that nothing optional leaks into the command line when it
was not asked for:

```python
assert args[args.index("--name") + 1] == "myssp"
assert len(args) == 6  # nothing optional leaked in
```

These verify what we emit, **not that trestle accepts it** — a wrong flag name
passes every unit test. So also check against the installed CLI, which is what
the e2e tests are for.

**End-to-end tests** (`tests/e2e/`) drive the real CLI through an in-process
server:

```python
async with Client(build_server("all")) as client:
    assert "✅" in await call_tool(client, "trestle_init", {"mode": "local"})
```

They must stay **offline**. Every fixture is local, and a URL in a fixture puts
the suite back on the network: `component-generate` resolving a `Profile_Source`
once downloaded ~10 MB from a third party on every run. Use `trestle://` or
workspace-relative hrefs. Verify with:

```sh
unshare -rn python -m pytest tests/e2e
```

Both suites run in CI (`.github/workflows/validate.yml`). Unit tests take
seconds; e2e takes about 80 and needs no model and no network.

`tests/unit/test_command_coverage.py` derives what is covered from the command
line each tool builds and compares it against the installed trestle's own CLI
classes. A new trestle command fails it until someone decides whether to wrap it
or write it into the two sections below.

### 8. Update the docs that are not derivable

- [README](../../README.md) — the tool table, if the default selection changed.
- [tool-context-cost.md](tool-context-cost.md) — the figures.
- [architecture.md](../architecture.md) — only if the structure changed.
  Do not add a per-tool list there; it drifted once already.
- This file — if you added a convention.

Keep contributor references in this directory — one that lives elsewhere is one
nobody updates. [architecture.md](../architecture.md) is the deliberate
exception: it describes the server itself, not how to work on it, so it sits
beside the README's audience rather than in here.

---

## Commands deliberately not covered

These have no tools, and the reasons are worth keeping:

- **Signing and provenance**: `sign`, `verify`, `sign-manifest`,
  `verify-manifest`, `generate-manifest`, `canonicalize`. `sign` and
  `sign-manifest` take a path to a PEM private key and the name of an
  environment variable holding its password; handing key material to a tool an
  agent invokes on a model's judgement is a different trust decision from
  editing OSCAL, and should be made deliberately rather than inherited by
  default. They are also `--beta`-gated in trestle, so their interface is not
  stable. `canonicalize` is only meaningful alongside them.
- **`beta`**: manages trestle's own feature flags for a workspace. It changes
  what other commands do rather than acting on a model.
- **`author docs`, `author folders`, `author headers`, `author jinja`**:
  markdown governance for arbitrary document trees, unrelated to OSCAL models.
  Nothing else in this server operates on non-OSCAL content.
- **The CLI `trestle validate`**: `trestle_validate` here validates a standalone
  OSCAL file through the trestle model classes, which also works outside a
  workspace — see
  [`trestle_mcp/libs/oscal_validate.py`](../../trestle_mcp/libs/oscal_validate.py).
  Workspace-wide validation (`trestle validate -a`) is not exposed.
- **Individual `trestle task` wrappers**: the task set belongs to the installed
  trestle version and is open-ended, so `trestle_task_run` covers all of them
  generically. Add a typed wrapper only when a task needs real input validation
  or format guidance, as `csv-to-oscal-cd` does.

## Commands behind an explicit opt-in

A command whose effect cannot be undone from inside the workspace gets
`opt_in=True` instead of a group. No group selects it, `all` included, so an
operator who asks for a broad group does not hand an agent a tool that destroys
content, and reaching for it is a deliberate act recorded in the server
configuration.

- **`remove`** (`trestle_remove`): deletes an element and everything under it
  from a model file in place. trestle keeps no backup, so the only way back is
  version control. It is the inverse of `trestle_create`'s element mode, which
  is why it is covered at all rather than left out.

Use this sparingly. A tool that merely writes files — `generate`, `assemble`,
`import` — is not in this category: its output is reviewable and re-derivable.
The test is whether a mistaken call loses information that was not written by
the same tool.

---

## Reference

- [architecture.md](../architecture.md) — structure, data flow, dependencies
- [tool-context-cost.md](tool-context-cost.md) — what each selection costs
- [task-csv-formats.md](task-csv-formats.md) — the CSV layouts the
  `trestle task` tools accept, which are trestle's input formats rather than
  anything this server defines
- [tests/data/README.md](../../tests/data/README.md) — where the fixtures came from
- [mcp-registry.md](mcp-registry.md) — publishing

## Running the checks

```sh
pip install -e ".[dev]"

pytest tests/unit                  # fast, mocked
pytest tests/e2e                   # real trestle CLI, offline
unshare -rn pytest tests/e2e       # prove it is offline
black . && isort .
python scripts/check_versions.py
python scripts/tool_context_cost.py
```

Do not bump the version in a feature branch. The version is bumped once, as the
last commit, after review; `scripts/check_versions.py` keeps `pyproject.toml`
and `server.json` in step, and the release workflow verifies the tag against
them.
