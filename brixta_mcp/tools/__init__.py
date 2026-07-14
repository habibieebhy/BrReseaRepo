"""Tool registration for the shared BRIXTA MCP gateway."""

from brixta_mcp.tools.knowledge import register_knowledge_tools
from brixta_mcp.tools.sources import register_source_tools

__all__ = ["register_knowledge_tools", "register_source_tools"]
