"""Verification helpers for local and OAuth-protected MCP gateways."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx


EXPECTED_TOOLS = {
    "brixta_list_knowledge_bases",
    "brixta_search",
    "brixta_get_chunk",
    "brixta_list_sources",
    "brixta_sync_source",
}


def _http_client() -> httpx.Client:
    """Honor ordinary proxy settings and tolerate unavailable SOCKS extras."""
    try:
        return httpx.Client(follow_redirects=False, timeout=20)
    except ImportError:
        return httpx.Client(
            follow_redirects=False,
            timeout=20,
            trust_env=False,
        )


def _jsonrpc_payload(response: httpx.Response) -> dict[str, Any]:
    """Decode either legal JSON or SSE Streamable HTTP responses."""
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("The MCP endpoint returned a non-object JSON response.")
        return payload

    for line in response.text.splitlines():
        if line.startswith("data:"):
            payload = json.loads(line.removeprefix("data:").strip())
            if isinstance(payload, dict):
                return payload
    raise RuntimeError("The MCP endpoint returned no JSON-RPC payload.")


def _list_tools(
    client: httpx.Client,
    mcp_url: str,
    request_headers: dict[str, str],
) -> set[str]:
    headers = dict(request_headers)
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
                "clientInfo": {"name": "brixta-cli", "version": "2.0.0"},
            },
        },
    )
    _jsonrpc_payload(initialized)

    session_id = initialized.headers.get("mcp-session-id")
    if not session_id:
        raise RuntimeError("The MCP gateway did not create a session.")
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
    raw_tools = listed.get("result", {}).get("tools", [])
    tools = {
        item["name"]
        for item in raw_tools
        if isinstance(item, dict)
        and isinstance(item.get("name"), str)
        and item["name"]
    }
    missing = EXPECTED_TOOLS - tools
    if missing:
        raise RuntimeError(
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
        raise RuntimeError("The public MCP URL must be HTTPS and end in /mcp.")
    return f"{parsed.scheme}://{parsed.netloc}"


def verify_local_gateway(mcp_url: str) -> set[str]:
    """Verify an unauthenticated gateway that is restricted to loopback."""
    parsed = urlparse(mcp_url)
    if parsed.scheme != "http" or parsed.hostname not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        raise RuntimeError(
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


def verify_oauth_discovery(mcp_url: str) -> None:
    """Verify resource metadata and the protected public MCP boundary."""
    root = _public_root(mcp_url)
    with _http_client() as client:
        metadata = client.get(
            f"{root}/.well-known/oauth-protected-resource/mcp"
        )
        metadata.raise_for_status()
        resource = metadata.json()
        if resource.get("resource") != mcp_url or not resource.get(
            "authorization_servers"
        ):
            raise RuntimeError("OAuth resource metadata is incomplete.")

        protected = client.get(mcp_url)
        authenticate = protected.headers.get("www-authenticate", "").lower()
        if protected.status_code != 401 or "resource_metadata" not in authenticate:
            raise RuntimeError(
                "The public MCP endpoint is not enforcing discoverable OAuth."
            )


def verify_public_gateway(mcp_url: str) -> set[str]:
    """Use DCR and PKCE to verify tools through a public OAuth gateway."""
    root = _public_root(mcp_url)
    redirect_uri = "http://127.0.0.1:18999/brixta-verify"

    with _http_client() as client:
        metadata = client.get(
            f"{root}/.well-known/oauth-protected-resource/mcp"
        )
        metadata.raise_for_status()
        resource = metadata.json()
        if resource.get("resource") != mcp_url or not resource.get(
            "authorization_servers"
        ):
            raise RuntimeError(
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
            raise RuntimeError(
                "The OAuth authorization endpoint did not redirect."
            )

        location = authorization.headers.get("location", "")
        callback = parse_qs(urlparse(location).query)
        if callback.get("state", [""])[0] != state or not callback.get("code"):
            raise RuntimeError("OAuth authorization returned an invalid callback.")

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
