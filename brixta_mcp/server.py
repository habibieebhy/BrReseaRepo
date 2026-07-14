"""Shared MCP server for all knowledge bases in an authenticated tenant."""

from __future__ import annotations

import os
from typing import Literal, cast

# A server process must not depend on PyPI being reachable just to print its
# startup banner. Operators can explicitly opt back in if they want checks.
os.environ.setdefault("FASTMCP_CHECK_FOR_UPDATES", "off")

from fastmcp import FastMCP

from brixta_mcp.auth import build_auth_provider
from brixta_mcp.tools import register_knowledge_tools, register_source_tools


McpTransport = Literal["stdio", "http", "sse", "streamable-http"]
ALLOWED_TRANSPORTS: tuple[McpTransport, ...] = (
    "stdio",
    "http",
    "sse",
    "streamable-http",
)


def configured_transport() -> McpTransport:
    value = os.getenv("BRIXTA_MCP_TRANSPORT", "http").strip().lower()
    if value not in ALLOWED_TRANSPORTS:
        raise RuntimeError(
            "Unsupported BRIXTA_MCP_TRANSPORT. Choose one of: "
            + ", ".join(ALLOWED_TRANSPORTS)
        )
    return cast(McpTransport, value)


def create_server() -> FastMCP:
    server = FastMCP(
        name="BRIXTA Knowledge Gateway",
        instructions=(
            "Discover the user's BRIXTA knowledge bases, search the most relevant "
            "one, then fetch supporting chunks before answering. Cite returned URLs."
        ),
        auth=build_auth_provider(),
    )
    register_knowledge_tools(server)
    register_source_tools(server)
    return server


mcp = create_server()


def main() -> None:
    host = os.getenv("BRIXTA_MCP_HOST", "127.0.0.1")
    if os.getenv("BRIXTA_MCP_AUTH_MODE", "static") == "none" and host not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        raise RuntimeError("Unauthenticated MCP may only bind to a loopback address.")
    mcp.run(
        transport=configured_transport(),
        host=host,
        port=int(os.getenv("BRIXTA_MCP_PORT", "8001")),
    )


if __name__ == "__main__":
    main()
