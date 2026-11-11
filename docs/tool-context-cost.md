# What each tool selection costs in context

An MCP client loads the server's `tools/list` result into the model's context
window on every session, before the model has done anything. That result carries
each tool's name, title, description and input schema, so the size of the
selection is a fixed cost paid by every conversation with the server attached —
which is why this server lets you choose how much of the trestle surface to
expose (see [Choosing which tools are exposed](../README.md#choosing-which-tools-are-exposed)).

This page records what each selection currently costs, and how to measure it
again.

## Measuring it

[`scripts/tool_context_cost.py`](../scripts/tool_context_cost.py) builds a
server for each selection and measures the JSON it would actually return, rather
than estimating from the source:

```sh
python scripts/tool_context_cost.py                 # one row per selection
python scripts/tool_context_cost.py --per-tool      # also break down by tool
python scripts/tool_context_cost.py --format json   # machine-readable
python scripts/tool_context_cost.py --select core,trestle_author_ssp_generate
```

The measured quantity is **characters of JSON**. Tokens depend on the client's
tokenizer, so the token column below is characters divided by four — a rough
guide, not a number to plan against. The figures move whenever a tool
description or input model is edited, so re-run the script rather than trusting
this page after a change.

## Current cost per selection

Measured on the tool set in this repository:

| Selection | Tools | Characters | ~Tokens |
|---|---:|---:|---:|
| `core` | 12 | 36,381 | ~9,095 |
| `author` | 11 | 39,695 | ~9,923 |
| `task` | 5 | 19,848 | ~4,962 |
| `authoring` (default) | 13 | 46,137 | ~11,534 |
| `all` | 28 | 95,922 | ~23,980 |
| `all,trestle_remove` | 29 | 98,685 | ~24,671 |

The default, `authoring`, is **less than half** of `all`. That is the point of
the selector: the whole trestle surface is available, but a session that only
authors OSCAL does not carry the cost of the parts it will not call.

Selections combine, so you pay only for what you name. `authoring` plus the one
SSP tool you need costs far less than `all`:

```sh
python scripts/tool_context_cost.py --select authoring,trestle_author_ssp_generate
```

## Cost per tool

Largest first — these are the descriptions worth trimming if the total needs to
come down.

| Tool | Characters |
|---|---:|
| `trestle_task_csv_to_oscal_mc` | 5,097 |
| `trestle_create` | 4,687 |
| `trestle_author_ssp_generate` | 4,629 |
| `trestle_task_xlsx_to_oscal_poam` | 4,530 |
| `trestle_task_csv_to_oscal_cd` | 4,363 |
| `trestle_author_ssp_filter` | 4,253 |
| `trestle_author_component_assemble` | 3,788 |
| `trestle_assemble` | 3,763 |
| `trestle_author_profile_resolve` | 3,745 |
| `trestle_author_catalog_assemble` | 3,727 |
| `trestle_author_profile_assemble` | 3,702 |
| `trestle_author_ssp_assemble` | 3,529 |
| `trestle_author_profile_generate` | 3,385 |
| `trestle_replicate` | 3,362 |
| `trestle_task_run` | 3,273 |
| `trestle_validate` | 3,161 |
| `trestle_author_profile_inherit` | 3,148 |
| `trestle_version` | 3,082 |
| `trestle_author_component_generate` | 3,070 |
| `trestle_href` | 2,947 |
| `trestle_merge` | 2,898 |
| `trestle_remove` | 2,762 |
| `trestle_partial_object_validate` | 2,761 |
| `trestle_author_catalog_generate` | 2,707 |
| `trestle_import` | 2,697 |
| `trestle_task_list` | 2,579 |
| `trestle_split` | 2,495 |
| `trestle_describe` | 2,364 |
| `trestle_init` | 2,151 |

The descriptions are long on purpose: each one states when to reach for the tool
and when not to, which is what keeps a model from calling `trestle_assemble`
when it wanted `trestle_author_profile_assemble`. Trimming them trades context
against that guidance, so prefer narrowing the selection first.

## A note on the default

The default is `authoring`, not the smallest possible set. The authoring
lifecycle — initialize, import, generate markdown, assemble back to JSON,
validate — is what the server is for, and a selection that left out a step of it
would mean every operator had to configure the server before it was useful.

If you want a smaller set than `authoring`, name the tools you need:

```sh
python scripts/tool_context_cost.py --select trestle_init,trestle_import,trestle_validate
```

## Tools no group selects

`trestle_remove` is registered only when a selection names it exactly — no
group, `all` included, selects it. It deletes an element from a model in place,
with no backup, so it is not something an operator should acquire by asking for
a broad group. To use it, name it alongside whatever else you want:

```json
{ "env": { "TRESTLE_MCP_TOOLS": "authoring,trestle_remove" } }
```
