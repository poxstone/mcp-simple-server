# CLAUDE.md — contexto del proyecto

## Qué es esto

Servidor MCP minimalista construido con **FastMCP** y gestionado con **uv**.
Desplegado como contenedor Docker en Google Cloud Run.

## Stack

- Python 3.12
- `mcp[cli] >= 1.27.0` (FastMCP)
- `dnspython` — resolución DNS (registros A + NS)
- `httpx` — peticiones HTTP (dependencia transitiva de mcp)
- Docker — imagen base `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`

## Estructura

```
server.py          # Definición del servidor MCP
test_client.py     # Cliente de prueba (stdio y SSE)
pyproject.toml     # Dependencias uv
uv.lock            # Versiones pinneadas
Dockerfile
.dockerignore
docker-compose.yml
```

## Tools implementados

| Tool | Descripción |
|------|-------------|
| `add(a, b)` | Suma dos números |
| `multiply(a, b)` | Multiplica dos números |
| `greet(name)` | Saludo personalizado |
| `server_info(url)` | HTTP GET a la URL → JSON con headers relevantes, body preview (800 chars) y DNS (A + NS) |

**Prompt:** `calculate_prompt(operation, a, b)`

## Transporte y puertos

El modo se controla con `MCP_TRANSPORT`:

| Valor | Uso |
|-------|-----|
| `stdio` (default local) | Clientes locales, Claude Desktop |
| `sse` (default en contenedor) | HTTP, Docker, Cloud Run |

Puerto por defecto: **8080** — parametrizable con `FASTMCP_PORT`.

## Variables de entorno

| Variable | Default (local) | Default (contenedor) |
|----------|----------------|----------------------|
| `MCP_TRANSPORT` | `stdio` | `sse` |
| `FASTMCP_HOST` | `127.0.0.1` | `0.0.0.0` |
| `FASTMCP_PORT` | `8080` | `8080` |

## Quirk importante — FastMCP y env vars

`FastMCP.__init__` pasa `host` y `port` **explícitamente** al constructor de `Settings`,
lo que sobreescribe las variables de entorno de pydantic-settings (`FASTMCP_HOST`, `FASTMCP_PORT`).
Por eso en `server.py` se leen manualmente:

```python
mcp = FastMCP(
    "simple-server",
    host=os.getenv("FASTMCP_HOST", "127.0.0.1"),
    port=int(os.getenv("FASTMCP_PORT", "8080")),
)
```

Si se actualiza `mcp`, verificar si esto fue corregido upstream.

## Docker

```bash
# Build
docker build -t poxstone/mcp_simple_server .

# Run
docker run -d -p 8080:8080 poxstone/mcp_simple_server

# Compose
docker compose up -d
```

Imagen publicada en Docker Hub: `poxstone/mcp_simple_server`

## Despliegue en producción

- **Cloud Run URL:** `https://mcp-simple-server-8326844300.us-central1.run.app`
- **SSE endpoint:** `https://mcp-simple-server-8326844300.us-central1.run.app/sse`
- **Región:** `us-central1`

## Test client

```bash
# stdio (local)
uv run python test_client.py

# SSE — host:puerto
uv run python test_client.py --host localhost:8080

# SSE — solo host (agrega :8080 por defecto)
uv run python test_client.py --host localhost

# SSE — URL completa (Cloud Run, HTTPS)
uv run python test_client.py --host https://mcp-simple-server-8326844300.us-central1.run.app
```
