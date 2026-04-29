# MCP Simple Server

A minimal [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server built with **FastMCP** and managed with **uv**. Can run locally via stdio or as a Docker container via SSE (HTTP).

## What's included

| Type | Name | Description |
|------|------|-------------|
| Tool | `add` | Adds two numbers |
| Tool | `multiply` | Multiplies two numbers |
| Tool | `greet` | Returns a greeting for a given name |
| Tool | `server_info` | Fetches HTTP headers, body preview and DNS info (A + NS records) for a URL |
| Prompt | `calculate_prompt` | Generates a calculation prompt |

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Docker (optional, for container mode)

## Setup

```bash
# Install dependencies (creates .venv automatically)
uv sync
```

## Running the server

### STDIO mode (default — local clients, Claude Desktop)

```bash
export MCP_TRANSPORT="sse" # stdio by default
export FASTMCP_HOST="127.0.0.1"
export FASTMCP_PORT="8080"

uv run python mcp_server.py
```

### Interactive dev inspector (browser UI)

```bash
uv run mcp dev mcp_server.py
```

Open the URL printed in the terminal (usually `http://localhost:5173`) to interact with the server through the MCP Inspector.

## Running with Docker

### Build and run

```bash
docker build -t poxstone/mcp_simple_server .
docker run --rm -d -p 8080:8080 --name mcp-simple-server poxstone/mcp_simple_server

# push
docker push poxstone/mcp_simple_server
```

### With Docker Compose

```bash
docker compose up -d        # start in background
docker compose logs -f      # follow logs
docker compose down         # stop and remove
```

The container starts in SSE mode by default, listening on `0.0.0.0:8080`.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `sse` | `sse` for HTTP, `stdio` for local clients |
| `FASTMCP_HOST` | `0.0.0.0` | Bind address |
| `FASTMCP_PORT` | `8080` | Port |

## Testing

### Test client (stdio)

```bash

uv run python test_client.py --mcp_host https://localhost:8080 --test_url https://eltiempo.com
```

### Test client against the container (SSE)

```python
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def main():
    async with sse_client("http://localhost:8080/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("add", {"a": 3, "b": 4})
            print(result.content[0].text)  # 7.0

asyncio.run(main())
```

### Example tool calls

| Tool | Parameters | Result |
|------|------------|--------|
| `add` | `a=3`, `b=4` | `7.0` |
| `multiply` | `a=6`, `b=7` | `42.0` |
| `greet` | `name="World"` | `"Hello, World! ..."` |
| `server_info` | `url="https://ipinfo.io/"` | JSON con headers, body preview, IPs y NS records |

## Connecting to Claude Desktop

Add the following block to your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**STDIO (local install):**

```json
{
  "mcpServers": {
    "simple-server": {
      "command": "uv",
      "args": [
        "run",
        "--project", "/absolute/path/to/mcp-simple-server",
        "python", "/absolute/path/to/mcp-simple-server/mcp_server.py"
      ]
    }
  }
}
```

**SSE (container running on localhost):**

```json
{
  "mcpServers": {
    "simple-server": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

## Connecting to Claude Code (CLI)

```bash
# Local (stdio)
claude mcp add simple-server -- uv run --project /absolute/path/to/mcp-simple-server python /absolute/path/to/mcp-simple-server/mcp_server.py

# Container (SSE)
claude mcp add simple-server --transport sse http://localhost:8080/sse
```

## Project structure

```
mcp-simple-server/
├── mcp_server.py          # MCP server definition
├── test_client.py     # stdio test client
├── pyproject.toml     # Project metadata and dependencies
├── uv.lock            # Locked dependency versions
├── Dockerfile
├── .dockerignore
├── docker-compose.yml
└── README.md
```

## Adding new tools

Edit `mcp_server.py` and add a decorated function:

```python
@mcp.tool()
def square(n: float) -> float:
    """Return the square of a number."""
    return n * n
```

Restart the server — the new tool is immediately available to any connected client.
