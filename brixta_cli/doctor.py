"""Preflight checks for local and production BRIXTA operation."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
import platform
import sys
from typing import Callable
from dotenv import load_dotenv

load_dotenv()
load_dotenv("storage/control-plane/runtime.env", override=True)


@dataclass
class Check:
    label: str
    ok: bool
    detail: str = ""


def _dependency_check() -> Check:
    modules = {
        "FastAPI": "fastapi",
        "Celery": "celery",
        "PostgreSQL": "psycopg",
        "pgvector": "pgvector",
        "FastMCP": "fastmcp",
        "Sentence Transformers": "sentence_transformers",
        "einops": "einops",
    }
    missing = [name for name, module in modules.items() if importlib.util.find_spec(module) is None]
    return Check(
        "Python dependencies",
        not missing,
        "missing: " + ", ".join(missing) if missing else "all required modules found",
    )


def collect_checks(*, semantic: bool = True) -> list[Check]:
    checks = [
        Check(
            "Python runtime",
            (3, 11) <= sys.version_info[:2] < (3, 14),
            f"{platform.python_version()} (supported: 3.11–3.13)",
        ),
        _dependency_check(),
        Check("DATABASE_URL configured", bool(os.getenv("DATABASE_URL")), "loaded from environment/.env"),
    ]
    if not all(check.ok for check in checks):
        return checks
    try:
        from core.database import get_connection

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        checks.append(Check("PostgreSQL", True, "connection and pgvector registration succeeded"))
    except Exception as exc:
        checks.append(Check("PostgreSQL", False, str(exc)))
        return checks
    try:
        from runtime.knowledge import list_knowledge_bases

        knowledge = list_knowledge_bases(limit=500)
        checks.append(Check("Knowledge bases", True, f"{len(knowledge)} ready"))
    except Exception as exc:
        checks.append(Check("Knowledge bases", False, str(exc)))
        return checks
    if semantic and knowledge:
        try:
            from runtime.knowledge import search_knowledge_base

            first = knowledge[0]
            result = search_knowledge_base(
                first["id"],
                "BRIXTA semantic health check",
                limit=1,
                tenant_id=first["tenant_id"],
            )
            checks.append(Check("Semantic retrieval", bool(result), f"{len(result)} result returned"))
        except Exception as exc:
            checks.append(Check("Semantic retrieval", False, str(exc)))
    elif semantic:
        checks.append(Check("Semantic retrieval", True, "skipped: no completed knowledge bases"))
    return checks


def print_checks(checks: list[Check]) -> bool:
    for check in checks:
        symbol = "✓" if check.ok else "✗"
        detail = f" — {check.detail}" if check.detail else ""
        print(f"{symbol} {check.label}{detail}")
    return all(check.ok for check in checks)


def run_doctor(*, semantic: bool = True) -> bool:
    print("BRIXTA doctor\n")
    return print_checks(collect_checks(semantic=semantic))
