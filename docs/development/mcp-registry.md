# MCP Registry Publishing

https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/quickstart.mdx

## Install
```bash
brew install mcp-publisher
```

## Initialize (first time only, creates server.json)
```bash
mcp-publisher init
```

## Publish
```bash
mcp-publisher login github
mcp-publisher publish
```

## Troubleshooting

### Ownership validation failure
If you see ownership validation failure, add `mcp-name` in README in any form.

```
$ mcp-publisher publish
Publishing to https://registry.modelcontextprotocol.io...
Error: publish failed: server returned status 400: {"title":"Bad Request","status":400,"detail":"Failed to publish server","errors":[{"message":"registry validation failed for package 0 (compliance-trestle-mcp): PyPI package 'compliance-trestle-mcp' ownership validation failed. The server name 'io.github.oscal-compass/compliance-trestle-mcp' must appear as 'mcp-name: io.github.oscal-compass/compliance-trestle-mcp' in the package README"}]}
```

**Solution**: Add the following line to README.md:
```
mcp-name: io.github.oscal-compass/compliance-trestle-mcp
```