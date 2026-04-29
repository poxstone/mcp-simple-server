"""
MCP test client.

Usage:
    uv run python test_client.py                                                             # stdio (local)
    uv run python test_client.py --mcp_host localhost                                       # SSE container
    uv run python test_client.py --mcp_host localhost:9000                                  # SSE custom port
    uv run python test_client.py --mcp_host localhost:8080 --test_url https://eltiempo.com  # custom server_info URL
"""
import json
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


async def async_main(host, test_url):
    """
    Conecta al servidor MCP y ejecuta las pruebas.
    Retorna el resultado como diccionario.
    """
    response_dict = {
        "tools": {},
        "resources": {},
        "prompts": {},
        "tools_results": {
            "add_request": {"a": 3, "b": 4},
            "multiply_request": {"a": 6, "b": 7},
            "greet_request": {"name": "MCP"},
            "server_info_request": {"url": test_url},
            "calculate_prompt_request": {"operation": "+", "a": "10", "b": "5"},
        },
        "prompts_results": {}
    }
    async with get_session(host) as session:
        # List available tools
        try:
            tools = await session.list_tools()
            for t in tools.tools:
                response_dict["tools"][t.name] = t
        except Exception as exc:
            print(f"Error listing tools: {exc}")

        # List resources
        try:
            resources = await session.list_resources()
            for r in resources.resources:
                response_dict["resources"][r.uri] = r.name
        except Exception as exc:
            print(f"Error listing resources: {exc}")

        # List prompts
        try:
            prompts = await session.list_prompts()
            for p in prompts.prompts:
                response_dict["prompts"][p.name] = p.description
        except Exception as exc:
            print(f"Error listing prompts: {exc}")

        # Test tools
        try:
            result = await session.call_tool("add", response_dict["tools_results"]["add_request"])
            response_dict["tools_results"]["add_response"] = result.content[0].text

            result = await session.call_tool("multiply", response_dict["tools_results"]["multiply_request"])
            response_dict["tools_results"]["multiply_response"] = result.content[0].text

            result = await session.call_tool("greet", response_dict["tools_results"]["greet_request"])
            response_dict["tools_results"]["greet_response"] = result.content[0].text

            # Test server_info tool
            result = await session.call_tool("server_info", response_dict["tools_results"]["server_info_request"])
            response_dict["tools_results"]["server_info_response"] = json.loads(result.content[0].text)

            # Test prompt
            prompt = await session.get_prompt("calculate_prompt", response_dict["tools_results"]["calculate_prompt_request"])
            response_dict["tools_results"]["calculate_response"] = prompt.messages[0].content.text
        except Exception as exc:
            print(f"Error calling tools: {exc}")

        return response_dict


async def main(args) -> None:
    host = args.mcp_host
    test_url = args.test_url
    response_mcp = await async_main(host, test_url)
    print(response_mcp)


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
