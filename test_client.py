"""
MCP test client.

Usage:
    uv run python test_client.py                                                             # stdio (local)
    uv run python test_client.py --mcp_host localhost                                       # SSE container
    uv run python test_client.py --mcp_host localhost:9000                                  # SSE custom port
    uv run python test_client.py --mcp_host localhost:8080 --test_url https://eltiempo.com  # custom server_info URL
"""
import argparse
import asyncio
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MCP simple server test client")
    parser.add_argument(
        "--mcp_host",
        default=None,
        metavar="HOST[:PORT]",
        help="Connect via SSE to this host (e.g. localhost or localhost:9000). "
             "Omit to use stdio (local server).",
    )
    parser.add_argument(
        "--test_url",
        default="https://example.com",
        metavar="URL",
        help="URL to pass to the server_info tool (default: https://example.com).",
    )
    return parser.parse_args()


@asynccontextmanager
async def get_session(host: str | None):
    if host:
        if host.startswith("http://") or host.startswith("https://"):
            # Full URL provided — append /sse if not already present
            url = host if host.endswith("/sse") else host.rstrip("/") + "/sse"
        else:
            # HOST[:PORT] shorthand → http
            if ":" not in host:
                host = f"{host}"
            url = f"http://{host}/sse"
        print(f"Connecting via SSE → {url}\n")
        async with sse_client(url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    else:
        params = StdioServerParameters(command="uv", args=["run", "python", "mcp_server.py"])
        print("Connecting via stdio (local)\n")
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


async def main(args) -> None:
    host = args.mcp_host
    test_url = args.test_url

    async with get_session(host) as session:
        # List available tools
        tools = await session.list_tools()
        print("=== Tools disponibles ===")
        for t in tools.tools:
            print(f"  • {t.name}: {t.description}")

        # List resources
        resources = await session.list_resources()
        print("\n=== Resources disponibles ===")
        for r in resources.resources:
            print(f"  • {r.uri}: {r.name}")

        # List prompts
        prompts = await session.list_prompts()
        print("\n=== Prompts disponibles ===")
        for p in prompts.prompts:
            print(f"  • {p.name}: {p.description}")

        # Test tools
        print("\n=== Pruebas de tools ===")

        result = await session.call_tool("add", {"a": 3, "b": 4})
        print(f"  add(3, 4)        → {result.content[0].text}")

        result = await session.call_tool("multiply", {"a": 6, "b": 7})
        print(f"  multiply(6, 7)   → {result.content[0].text}")

        result = await session.call_tool("greet", {"name": "MCP"})
        print(f"  greet('MCP')     → {result.content[0].text}")

        # Test server_info tool
        print(f"\n=== Tool server_info ({test_url}) ===")
        result = await session.call_tool("server_info", {"url": test_url})
        print(result.content[0].text)

        # Test prompt
        prompt = await session.get_prompt(
            "calculate_prompt", {"operation": "+", "a": "10", "b": "5"}
        )
        print(f"\n=== Prompt calculate_prompt ===")
        print(f"  {prompt.messages[0].content.text}")

        print("\n✓ Todas las pruebas pasaron correctamente.")


args = parse_args()
asyncio.run(main(args))
