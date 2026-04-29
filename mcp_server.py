import json
import os
from urllib.parse import urlparse

import dns.resolver
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "simple-server",
    host=os.getenv("FASTMCP_HOST", "127.0.0.1"),
    port=int(os.getenv("FASTMCP_PORT", "8080")),
)


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    print(f"[add] IN  a={a}, b={b}")
    result = a + b
    print(f"[add] OUT {result}")
    return result


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    print(f"[multiply] IN  a={a}, b={b}")
    result = a * b
    print(f"[multiply] OUT {result}")
    return result


@mcp.tool()
def greet(name: str) -> str:
    """Return a greeting for the given name."""
    print(f"[greet] IN  name={name!r}")
    result = f"Hello, {name}! Welcome to the MCP simple server."
    print(f"[greet] OUT {result!r}")
    return result


@mcp.tool()
async def server_info(url: str) -> str:
    """Fetch HTTP headers, body preview, and DNS info (A + NS records) for a URL."""
    print(f"[server_info] IN  url={url!r}")
    parsed = urlparse(url)
    hostname = parsed.hostname

    # DNS — A record (IP that responds)
    try:
        a_records = dns.resolver.resolve(hostname, "A")
        ip_addresses = [r.to_text() for r in a_records]
    except Exception as exc:
        ip_addresses = [f"error: {exc}"]

    # DNS — NS records (nameservers that resolve the domain)
    try:
        ns_records = dns.resolver.resolve(hostname, "NS")
        nameservers = [r.to_text() for r in ns_records]
    except Exception as exc:
        nameservers = [f"error: {exc}"]

    # HTTP request
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            response = await client.get(url)

        relevant_headers = {
            k: v
            for k, v in response.headers.items()
            if k.lower()
            in {
                "content-type",
                "content-length",
                "server",
                "x-powered-by",
                "cache-control",
                "last-modified",
                "etag",
                "location",
                "strict-transport-security",
                "x-frame-options",
                "x-content-type-options",
            }
        }

        body_preview = response.text[:800].strip() if response.text else ""

        http_info = {
            "status_code": response.status_code,
            "final_url": str(response.url),
            "headers": relevant_headers,
            "body_preview": body_preview,
        }
    except Exception as exc:
        http_info = {"error": str(exc)}

    result = {
        "url": url,
        "dns": {
            "hostname": hostname,
            "a_records": ip_addresses,
            "ns_records": nameservers,
        },
        "http": http_info,
    }

    output = json.dumps(result, indent=2, ensure_ascii=False)
    print(f"[server_info] OUT status={result['http'].get('status_code', 'error')} dns_a={result['dns']['a_records']}")
    return output


@mcp.prompt()
def calculate_prompt(operation: str, a: float, b: float) -> str:
    """Generate a prompt to perform a calculation."""
    return f"Please calculate {a} {operation} {b} and explain the result."


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)  # type: ignore[arg-type]
