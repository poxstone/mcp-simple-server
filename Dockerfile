FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Install dependencies leveraging layer cache
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

COPY server.py .

# MCP transport mode: "sse" for HTTP, "stdio" for local clients
ENV MCP_TRANSPORT=sse
# FastMCP reads FASTMCP_HOST and FASTMCP_PORT automatically
ENV FASTMCP_HOST=0.0.0.0
ENV FASTMCP_PORT=8080

EXPOSE 8080

CMD ["uv", "run", "python", "server.py"]
