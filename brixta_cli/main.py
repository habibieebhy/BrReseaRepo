"""BRIXTA command-line entry point."""

from __future__ import annotations

import argparse
import os
import signal
import sys
from typing import Any


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="brixta",
        description="Operate and connect BRIXTA.",
    )
    commands = root.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser(
        "doctor",
        help="Validate the complete local runtime.",
    )
    doctor.add_argument("--skip-semantic", action="store_true")

    serve = commands.add_parser("serve", help="Run a BRIXTA service.")
    serve.add_argument("service", choices=["mcp"])

    connect = commands.add_parser(
        "connect",
        help="Connect BRIXTA to an AI client.",
    )
    connect.add_argument("target", choices=["chatgpt", "client"])
    connect.add_argument("--local", action="store_true")
    connect.add_argument("--tenant")
    connect.add_argument("--no-browser", action="store_true")

    commands.add_parser(
        "disconnect",
        help="Stop locally managed MCP/tunnel processes.",
    )

    knowledge = commands.add_parser(
        "knowledge",
        help="Inspect and search knowledge bases.",
    )
    knowledge_commands = knowledge.add_subparsers(
        dest="knowledge_command",
        required=True,
    )
    knowledge_list = knowledge_commands.add_parser("list")
    knowledge_list.add_argument("--tenant")

    knowledge_search = knowledge_commands.add_parser("search")
    knowledge_search.add_argument("handle")
    knowledge_search.add_argument("query")
    knowledge_search.add_argument("--tenant")
    knowledge_search.add_argument("--limit", type=int, default=5)
    return root


def _stop_managed_processes(state: dict[str, Any]) -> None:
    for key in ("mcp_pid", "tunnel_pid", "tunnel_client_pid"):
        value = state.get(key)
        if not isinstance(value, (int, str)):
            continue
        try:
            pid = int(value)
        except ValueError:
            continue
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "doctor":
            from brixta_cli.doctor import run_doctor

            return 0 if run_doctor(semantic=not args.skip_semantic) else 1

        if args.command == "serve":
            from brixta_mcp.server import main as serve_mcp

            serve_mcp()
            return 0

        if args.command == "connect":
            from brixta_cli.connect import (
                connect_local,
                connect_local_client,
                connect_production,
            )

            if args.target == "client":
                if not args.local:
                    raise RuntimeError(
                        "Generic client startup currently requires --local."
                    )
                return connect_local_client(tenant_id=args.tenant)

            if args.local:
                return connect_local(
                    tenant_id=args.tenant,
                    open_browser=not args.no_browser,
                )
            return connect_production(open_browser=not args.no_browser)

        if args.command == "disconnect":
            from brixta_cli.config import load_state

            _stop_managed_processes(load_state())
            print("✓ Local BRIXTA connection stopped")
            return 0

        if args.command == "knowledge":
            if args.knowledge_command == "list":
                from brixta_cli.knowledge import list_command

                return list_command(args.tenant)

            from brixta_cli.knowledge import search_command

            return search_command(
                args.handle,
                args.query,
                args.tenant,
                args.limit,
            )

        raise RuntimeError(f"Unsupported command: {args.command}")
    except (RuntimeError, PermissionError, ValueError) as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
