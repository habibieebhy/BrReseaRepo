"""Knowledge-base discovery and semantic retrieval."""

from runtime.knowledge.service import (
    KnowledgeBaseError,
    describe_knowledge_base,
    fetch_chunk,
    list_knowledge_bases,
    search_knowledge_base,
)
from runtime.knowledge.access import KnowledgeAccessRepository

__all__ = [
    "KnowledgeBaseError",
    "describe_knowledge_base",
    "fetch_chunk",
    "list_knowledge_bases",
    "search_knowledge_base",
    "KnowledgeAccessRepository",
]
