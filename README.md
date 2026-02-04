# trestle-mcp

MCP (Model Context Protocol) server for [compliance-trestle](https://github.com/IBM/compliance-trestle) - OSCAL framework management tool.

This MCP server enables seamless access to trestle commands from Claude Code, making OSCAL (Open Security Controls Assessment Language) compliance documentation management more efficient.

## Features

### Implemented Tools

- **trestle_init**: Initialize a Trestle workspace
- **trestle_import**: Import OSCAL models (Catalogs, Profiles, Component Definitions, etc.) from URLs or local files

### Supported OSCAL Model Types

- Catalog
- Profile
- Component Definition
- System Security Plan (SSP)
- Assessment Plan
- Assessment Result
- Plan of Action and Milestones (POAM)

## Installation

### Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Install with uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/trestle-mcp.git
cd trestle-mcp

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Install with pip

```bash
# Clone the repository
git clone https://github.com/yourusername/trestle-mcp.git
cd trestle-mcp

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Configuration

### Claude Desktop Configuration

Add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "trestle": {
      "command": "pipx",
      "args": ["--from", "trestle_mcp"]
    }
  }
}
```

Replace `/path/to/trestle-mcp/` with the actual path to your installation.

## Usage

### Initialize a Trestle Workspace

```python
# Basic initialization (local mode)
trestle_init()

# Full mode initialization
trestle_init(mode="full")

# Initialize with custom workspace path
trestle_init(mode="local", trestle_root="/path/to/workspace")
```

### Import OSCAL Models

#### Import NIST SP800-53 Rev5 Catalog

```python
trestle_import(
    file="https://raw.githubusercontent.com/usnistgov/oscal-content/refs/heads/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json",
    output="nist_sp800_53_rev5"
)
```

This creates: `catalogs/nist_sp800_53_rev5/catalog.json`

#### Import NIST Profile (Low Baseline)

```python
trestle_import(
    file="https://raw.githubusercontent.com/usnistgov/oscal-content/refs/heads/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_LOW-baseline_profile.json",
    output="nist_low_baseline"
)
```

This creates: `profiles/nist_low_baseline/profile.json`

#### Import from Local File

```python
trestle_import(
    file="./resources/catalogs/your_catalog.json",
    output="mycatalog"
)
```

#### Import with UUID Regeneration

```python
trestle_import(
    file="https://example.com/catalog.json",
    output="mycatalog",
    regenerate=True
)
```

## Development

### Running Tests

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run E2E tests only
pytest tests/e2e/

# Run with verbose output
pytest -v
```

### Project Structure

```
trestle-mcp/
├── trestle_mcp/           # Source code
│   └── __init__.py        # MCP server implementation
├── tests/
│   ├── unit/              # Unit tests (mirrors source structure)
│   │   ├── test_trestle_init.py
│   │   └── test_trestle_import.py
│   └── e2e/               # E2E tests (actual MCP server tests)
│       └── test_mcp_server.py
├── pyproject.toml         # Project configuration
├── README.md
└── LICENSE
```

## Implementation Details

### Phase 1: CLI Wrapper Approach (Current)

The current implementation uses a subprocess-based approach:
- MCP tool parameters are converted to trestle CLI arguments
- Commands are executed via subprocess
- stdout/stderr are captured and returned through MCP

### Phase 2: Library Import Approach (Future)

Future enhancement will use compliance-trestle as a Python library:
- Direct Python API calls instead of subprocess
- Better error handling and type safety
- Improved performance

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Related Projects

- [compliance-trestle](https://github.com/IBM/compliance-trestle) - OSCAL framework management tool
- [OSCAL](https://pages.nist.gov/OSCAL/) - Open Security Controls Assessment Language
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol

## References

- [compliance-trestle Documentation](https://ibm.github.io/compliance-trestle/)
- [NIST OSCAL Content Repository](https://github.com/usnistgov/oscal-content)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/trestle-mcp/issues
- compliance-trestle: https://github.com/IBM/compliance-trestle/issues
