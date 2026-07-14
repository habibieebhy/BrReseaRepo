"""BRIXTA MCP startup and client handoff workflows."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import webbrowser
from urllib.parse import urlparse

from brixta_cli.config import STATE_DIR, save_state
from brixta_cli.doctor import collect_checks, print_checks
from brixta_cli.tunnel import start_cloudflare_tunnel
from brixta_cli.verify import (
    verify_local_gateway,
    verify_oauth_discovery,
    verify_public_gateway,
)


def _choose_tenant(requested: str | None) -> str:
    if requested:
        return requested

    from runtime.knowledge import list_knowledge_bases

    tenants = sorted(
        {item["tenant_id"] for item in list_knowledge_bases(limit=500)}
    )
    if not tenants:
        raise RuntimeError("No ready knowledge bases exist yet.")
    if len(tenants) == 1:
        return tenants[0]
    if not sys.stdin.isatty():
        raise RuntimeError("Multiple tenants exist. Pass --tenant TENANT_ID.")

    print("\nChoose the tenant the client may access:")
    for index, tenant in enumerate(tenants, start=1):
        print(f"  {index}. {tenant}")
    while True:
        value = input("Tenant number: ").strip()
        if value.isdigit() and 1 <= int(value) <= len(tenants):
            return tenants[int(value) - 1]


def _wait_for_port(host: str, port: int, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.25)
    raise RuntimeError(
        f"MCP gateway did not open {host}:{port} within {timeout:.0f}s."
    )


def _print_failed_checks() -> bool:
    checks = collect_checks(semantic=True)
    if all(check.ok for check in checks):
        return False
    print("BRIXTA doctor\n")
    print_checks(checks)
    print("\nFix the failed checks before starting the MCP gateway.")
    return True


def connect_local(*, tenant_id: str | None, open_browser: bool = True) -> int:
    """Legacy public-tunnel development flow for ChatGPT.

    Quick Tunnel availability is external to BRIXTA. Prefer a stable named
    tunnel or OpenAI Secure MCP Tunnel for dependable development.
    """
    checks = collect_checks(semantic=True)
    if not all(check.ok for check in checks):
        print("BRIXTA doctor\n")
        print_checks(checks)
        print("\nFix the failed checks before exposing BRIXTA.")
        return 1

    tenant = _choose_tenant(tenant_id)
    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    mcp_log = STATE_DIR / "mcp.log"
    tunnel_log = STATE_DIR / "tunnel.log"
    tunnel_process, public_url = start_cloudflare_tunnel(
        "http://127.0.0.1:8001",
        tunnel_log,
    )
    public_host = urlparse(public_url).hostname or ""
    environment = {
        **os.environ,
        "BRIXTA_MCP_AUTH_MODE": "oauth-local",
        "BRIXTA_MCP_TENANT_ID": tenant,
        "BRIXTA_MCP_PUBLIC_URL": public_url,
        "BRIXTA_MCP_HOST": "127.0.0.1",
        "BRIXTA_MCP_PORT": "8001",
        "BRIXTA_MCP_TRANSPORT": "http",
        "FASTMCP_CHECK_FOR_UPDATES": "off",
        "MCP_ALLOWED_HOSTS": public_host,
        "MCP_ALLOWED_ORIGINS": f"https://{public_host}",
    }
    mcp_process: subprocess.Popen[bytes] | None = None
    try:
        with mcp_log.open("a", encoding="utf-8") as output:
            mcp_process = subprocess.Popen(
                [sys.executable, "-m", "api.mcp_server"],
                env=environment,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        _wait_for_port("127.0.0.1", 8001)
        verified_tools = verify_public_gateway(public_url)
    except Exception:
        tunnel_process.terminate()
        if mcp_process is not None:
            mcp_process.terminate()
        raise

    if mcp_process is None:
        tunnel_process.terminate()
        raise RuntimeError("The MCP gateway process did not start.")

    save_state(
        {
            "mode": "local-chatgpt",
            "tenant_id": tenant,
            "mcp_url": public_url,
            "auth_mode": "oauth-local",
            "mcp_pid": mcp_process.pid,
            "tunnel_pid": tunnel_process.pid,
        }
    )
    knowledge_check = next(
        check for check in checks if check.label == "Knowledge bases"
    )
    knowledge_count = knowledge_check.detail.split(" ", 1)[0]
    print("\n✓ BRIXTA configuration valid")
    print("✓ PostgreSQL connected")
    print(f"✓ {knowledge_count} knowledge bases ready")
    print("✓ Semantic retrieval operational")
    print("✓ MCP gateway running")
    print("✓ Secure HTTPS endpoint available")
    print("✓ OAuth authentication enabled")
    print(f"✓ {len(verified_tools)} MCP tools verified")
    print(f"\nChatGPT MCP URL:\n{public_url}")
    print("\nComplete the one-time connection approval in ChatGPT.")
    if open_browser:
        webbrowser.open(
            os.getenv(
                "BRIXTA_CHATGPT_CONNECT_URL",
                "https://chatgpt.com/plugins",
            )
        )
    return 0


def connect_production(*, open_browser: bool = True) -> int:
    url = os.getenv("BRIXTA_MCP_PUBLIC_URL", "").strip()
    if not url.startswith("https://") or not url.rstrip("/").endswith("/mcp"):
        raise RuntimeError(
            "Set BRIXTA_MCP_PUBLIC_URL to the deployed HTTPS /mcp endpoint."
        )
    verify_oauth_discovery(url)
    print("✓ Production MCP URL configured")
    print("✓ OAuth discovery operational")
    print("✓ Authentication is enforced by the deployed gateway")
    print(f"\nMCP URL:\n{url}")
    print("\nComplete the unavoidable one-time approval in your AI client.")
    if open_browser:
        webbrowser.open(
            os.getenv(
                "BRIXTA_CHATGPT_CONNECT_URL",
                "https://chatgpt.com/plugins",
            )
        )
    return 0


def connect_local_client(*, tenant_id: str | None) -> int:
    """Start a verified loopback gateway for any local MCP-capable client."""
    if _print_failed_checks():
        return 1

    tenant = _choose_tenant(tenant_id)
    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    mcp_log = STATE_DIR / "mcp.log"
    mcp_url = "http://127.0.0.1:8001/mcp"
    environment = {
        **os.environ,
        "BRIXTA_MCP_AUTH_MODE": "none",
        "BRIXTA_MCP_TENANT_ID": tenant,
        "BRIXTA_MCP_PUBLIC_URL": mcp_url,
        "BRIXTA_MCP_HOST": "127.0.0.1",
        "BRIXTA_MCP_PORT": "8001",
        "BRIXTA_MCP_TRANSPORT": "http",
        "FASTMCP_CHECK_FOR_UPDATES": "off",
    }
    with mcp_log.open("a", encoding="utf-8") as output:
        process = subprocess.Popen(
            [sys.executable, "-m", "api.mcp_server"],
            env=environment,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    try:
        _wait_for_port("127.0.0.1", 8001)
        tools = verify_local_gateway(mcp_url)
    except Exception:
        process.terminate()
        raise

    save_state(
        {
            "mode": "local-client",
            "tenant_id": tenant,
            "mcp_url": mcp_url,
            "auth_mode": "none",
            "mcp_pid": process.pid,
        }
    )
    print("\n✓ BRIXTA configuration valid")
    print("✓ PostgreSQL connected")
    print("✓ Semantic retrieval operational")
    print(f"✓ {len(tools)} MCP tools available")
    print("✓ Loopback-only MCP gateway running")
    print(f"\nMCP URL:\n{mcp_url}")
    print(
        "\nGeneric client configuration:\n"
        '{\n  "mcpServers": {\n    "brixta": {\n'
        f'      "url": "{mcp_url}"\n'
        "    }\n  }\n}"
    )
    print("\nUse `brixta disconnect` when finished.")
    return 0
