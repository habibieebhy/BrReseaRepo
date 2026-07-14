"""Backward-compatible entry point for the shared BRIXTA MCP gateway."""

from brixta_mcp.server import main, mcp

__all__ = ["main", "mcp"]


if __name__ == "__main__":
    main()
