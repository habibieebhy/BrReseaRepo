"""Verification for local and public BRIXTA MCP gateways."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

import httpx


EXPECTED_TOOLS = {
    "brixta_list_knowledge_bases",
    "brixta_search",
    "brixta_get_chunk",
    "brixta_list_sources",
    "brixta_sync_source",
    "brixta_list_simulation_runs",
    "brixta_get_simulation_report",
}

TRANSIENT_HTTP_STATUSES = {
    404,
    408,
    425,
    429,
    500,
    502,
    503,
    504,
    520,
    521,
    522,
    523,
    524,
}


class McpVerificationError(RuntimeError):
    """The reachable MCP/OAuth service returned an invalid configuration."""


class PublicGatewayTimeout(RuntimeError):
    """The public hostname did not become ready before the local deadline."""


def _http_client() -> httpx.Client:
    """Honor normal proxies, but tolerate an unusable optional SOCKS setting."""
    timeout = httpx.Timeout(
        float(os.getenv("BRIXTA_PUBLIC_REQUEST_TIMEOUT", "15"))
    )
    try:
        return httpx.Client(follow_redirects=False, timeout=timeout)
    except ImportError:
        return httpx.Client(
            follow_redirects=False,
            timeout=timeout,
            trust_env=False,
        )


def _jsonrpc_payload(response: httpx.Response) -> dict[str, Any]:
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        payload = response.json()
        if isinstance(payload, dict):
            return payload

    for line in response.text.splitlines():
        if line.startswith("data:"):
            value = json.loads(line.partition(":")[2].strip())
            if isinstance(value, dict):
                return value
    raise McpVerificationError(
        "The MCP endpoint returned no JSON-RPC response event."
    )


def _list_tools(
    client: httpx.Client,
    mcp_url: str,
    base_headers: dict[str, str],
) -> set[str]:
    headers = dict(base_headers)
    initialized = client.post(
        mcp_url,
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "brixta-cli", "version": "2.1.1"},
            },
        },
    )
    _jsonrpc_payload(initialized)
    session_id = initialized.headers.get("mcp-session-id")
    if not session_id:
        raise McpVerificationError(
            "The MCP gateway did not create a session."
        )

    headers["Mcp-Session-Id"] = session_id
    client.post(
        mcp_url,
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        },
    ).raise_for_status()
    listed = _jsonrpc_payload(
        client.post(
            mcp_url,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            },
        )
    )
    tools = {
        item["name"]
        for item in listed.get("result", {}).get("tools", [])
        if item.get("name")
    }
    missing = EXPECTED_TOOLS - tools
    if missing:
        raise McpVerificationError(
            "MCP tool verification failed; missing: "
            + ", ".join(sorted(missing))
        )
    return tools


def _public_root(mcp_url: str) -> str:
    parsed = urlparse(mcp_url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.path.rstrip("/") != "/mcp"
    ):
        raise McpVerificationError(
            "The public MCP URL must be HTTPS and end in /mcp."
        )
    return f"{parsed.scheme}://{parsed.netloc}"


def verify_oauth_discovery(mcp_url: str) -> None:
    """Verify public resource metadata and the protected MCP boundary."""
    root = _public_root(mcp_url)
    with _http_client() as client:
        metadata = client.get(
            f"{root}/.well-known/oauth-protected-resource/mcp"
        )
        metadata.raise_for_status()
        resource = metadata.json()
        if (
            resource.get("resource") != mcp_url
            or not resource.get("authorization_servers")
        ):
            raise McpVerificationError(
                "OAuth resource metadata is incomplete."
            )
        protected = client.get(mcp_url)
        challenge = protected.headers.get("www-authenticate", "")
        if protected.status_code != 401 or "resource_metadata" not in challenge:
            raise McpVerificationError(
                "The public MCP endpoint is not enforcing discoverable OAuth."
            )


def verify_local_gateway(mcp_url: str) -> set[str]:
    """Verify all tools on an unauthenticated loopback-only endpoint."""
    parsed = urlparse(mcp_url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
    ):
        raise McpVerificationError(
            "Unauthenticated MCP verification is restricted to loopback HTTP."
        )
    with _http_client() as client:
        return _list_tools(
            client,
            mcp_url,
            {
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
        )


def verify_public_gateway(mcp_url: str) -> set[str]:
    """Use DCR, PKCE and streamable HTTP to list tools publicly."""
    root = _public_root(mcp_url)
    redirect_uri = "http://127.0.0.1:18999/brixta-verify"

    with _http_client() as client:
        metadata = client.get(
            f"{root}/.well-known/oauth-protected-resource/mcp"
        )
        metadata.raise_for_status()
        resource = metadata.json()
        if (
            resource.get("resource") != mcp_url
            or not resource.get("authorization_servers")
        ):
            raise McpVerificationError(
                "OAuth resource metadata does not identify the MCP URL."
            )

        registration = client.post(
            f"{root}/register",
            json={
                "client_name": "BRIXTA CLI verifier",
                "redirect_uris": [redirect_uri],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "client_secret_post",
                "scope": "brixta:read brixta:write",
            },
        )
        registration.raise_for_status()
        client_info = registration.json()

        verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(48)
        ).rstrip(b"=").decode()
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).rstrip(b"=").decode()
        state = secrets.token_urlsafe(20)
        authorization = client.get(
            f"{root}/authorize",
            params={
                "response_type": "code",
                "client_id": client_info["client_id"],
                "redirect_uri": redirect_uri,
                "scope": "brixta:read brixta:write",
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )
        if authorization.status_code not in {302, 303, 307, 308}:
            raise McpVerificationError(
                "The OAuth authorization endpoint did not redirect."
            )
        callback = parse_qs(urlparse(authorization.headers["location"]).query)
        if callback.get("state", [""])[0] != state or not callback.get("code"):
            raise McpVerificationError(
                "OAuth authorization returned an invalid callback."
            )

        token_response = client.post(
            f"{root}/token",
            data={
                "grant_type": "authorization_code",
                "code": callback["code"][0],
                "redirect_uri": redirect_uri,
                "client_id": client_info["client_id"],
                "client_secret": client_info["client_secret"],
                "code_verifier": verifier,
            },
        )
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]
        return _list_tools(
            client,
            mcp_url,
            {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
        )


def _transient_public_error(error: BaseException) -> bool:
    if isinstance(error, httpx.TransportError):
        return True
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code in TRANSIENT_HTTP_STATUSES
    return False


def wait_for_public_gateway(
    mcp_url: str,
    *,
    timeout: float = 180,
    gateway_alive: Callable[[], bool] | None = None,
    on_retry: Callable[[int, BaseException, float], None] | None = None,
) -> set[str]:
    """Wait through transient DNS/edge readiness without hiding fatal errors."""
    deadline = time.monotonic() + timeout
    attempt = 0
    delay = 1.0
    last_error: BaseException | None = None

    while time.monotonic() < deadline:
        if gateway_alive is not None and not gateway_alive():
            raise RuntimeError(
                "The local MCP or cloudflared process exited during verification."
            )
        attempt += 1
        try:
            return verify_public_gateway(mcp_url)
        except Exception as error:
            if not _transient_public_error(error):
                raise
            last_error = error
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            sleep_for = min(delay, remaining)
            if on_retry is not None:
                on_retry(attempt, error, sleep_for)
            time.sleep(sleep_for)
            delay = min(delay * 1.6, 8.0)

    detail = f" Last error: {last_error}" if last_error else ""
    raise PublicGatewayTimeout(
        f"The public MCP route did not become ready within {timeout:.0f} seconds."
        + detail
    ) from last_error
