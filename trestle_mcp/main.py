#!/usr/bin/env python3
"""
MCP Server for compliance-trestle OSCAL framework.

This server provides tools to manage OSCAL models using the trestle CLI.
"""

from mcp.server.fastmcp import FastMCP

from trestle_mcp import services

# Initialize the MCP server
mcp = FastMCP("trestle_mcp")


@mcp.tool(
    name="trestle_init",
    title="Initialize Trestle Workspace",
    description=services.init.trestle_init.__doc__,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def trestle_init(params: services.init.TrestleInitInput) -> str:
    return await services.init.trestle_init(params)


@mcp.tool(
    name="trestle_import",
    description=services.import_.trestle_import.__doc__,
    annotations={
        "title": "Import OSCAL Model",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def trestle_import(params: services.import_.TrestleImportInput) -> str:
    return await services.import_.trestle_import(params)


@mcp.tool(
    name="trestle_author_catalog_generate",
    title="Generate Catalog Markdown Controls",
    description=services.author.catalog_generate.trestle_catalog_generate.__doc__,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def trestle_catalog_generate(
    params: services.author.catalog_generate.TrestleCatalogGenerateInput,
) -> str:
    return await services.author.catalog_generate.trestle_catalog_generate(params)


@mcp.tool(
    name="trestle_author_profile_generate",
    title="Generate Profile Markdown Controls",
    description=services.author.profile_generate.trestle_author_profile_generate.__doc__,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def trestle_author_profile_generate(
    params: services.author.profile_generate.TrestleAuthorProfileGenerateInput,
) -> str:
    return await services.author.profile_generate.trestle_author_profile_generate(
        params
    )


@mcp.tool(
    name="trestle_author_profile_resolve",
    title="Resolve Profile to Catalog",
    description=services.author.profile_resolve.trestle_author_profile_resolve.__doc__,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def trestle_author_profile_resolve(
    params: services.author.profile_resolve.TrestleAuthorProfileResolveInput,
) -> str:
    return await services.author.profile_resolve.trestle_author_profile_resolve(params)


@mcp.tool(
    name="trestle_author_profile_assemble",
    title="Assemble Profile JSON from Markdown Directory",
    description=services.author.profile_assemble.trestle_author_profile_assemble.__doc__,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def trestle_author_profile_assemble(
    params: services.author.profile_assemble.TrestleAuthorProfileAssembleInput,
) -> str:
    return await services.author.profile_assemble.trestle_author_profile_assemble(
        params
    )


def main():
    """Main entry point for the trestle MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
