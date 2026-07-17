"""JWT authentication and tenant context for the BRIXTA HTTP API."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from core.config import (
    BRIXTA_ADMIN_EMAILS,
    BRIXTA_ADMIN_ROLES,
    BRIXTA_AUTH_ALGORITHMS,
    BRIXTA_AUTH_AUDIENCE,
    BRIXTA_AUTH_EMAIL_CLAIM,
    BRIXTA_AUTH_ISSUER,
    BRIXTA_AUTH_JWKS_URL,
    BRIXTA_AUTH_MODE,
    BRIXTA_AUTH_ROLES_CLAIM,
    BRIXTA_AUTH_TENANT_CLAIM,
    BRIXTA_DEFAULT_TENANT_ID,
    BRIXTA_ENVIRONMENT,
)


PUBLIC_PATHS = frozenset({"/health", "/openapi.json"})
PUBLIC_PREFIXES = ("/docs", "/redoc")
SUPPORTED_AUTH_MODES = frozenset({"none", "cloudflare-access", "jwt"})


@dataclass(frozen=True)
class Principal:
    subject: str
    email: str
    tenant_id: str
    roles: frozenset[str]
    claims: dict[str, Any]
    authenticated: bool

    @property
    def is_admin(self) -> bool:
        return bool(self.roles & BRIXTA_ADMIN_ROLES) or self.email.lower() in BRIXTA_ADMIN_EMAILS

    def tenant_for(self, requested: str | None = None) -> str:
        candidate = (requested or "").strip()
        if BRIXTA_AUTH_MODE == "none":
            return candidate or self.tenant_id
        if candidate and candidate != self.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The requested tenant is outside the authenticated scope.",
            )
        return self.tenant_id

    def require_admin(self) -> None:
        if not self.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator permission is required.",
            )


def validate_auth_configuration() -> None:
    if BRIXTA_AUTH_MODE not in SUPPORTED_AUTH_MODES:
        raise RuntimeError("BRIXTA_AUTH_MODE must be one of: none, cloudflare-access, jwt.")
    if BRIXTA_ENVIRONMENT == "production" and BRIXTA_AUTH_MODE == "none":
        raise RuntimeError("Production refuses to start with BRIXTA_AUTH_MODE=none.")
    if BRIXTA_AUTH_MODE != "none":
        missing = [
            name
            for name, value in (
                ("BRIXTA_AUTH_JWKS_URL", BRIXTA_AUTH_JWKS_URL),
                ("BRIXTA_AUTH_ISSUER", BRIXTA_AUTH_ISSUER),
                ("BRIXTA_AUTH_AUDIENCE", BRIXTA_AUTH_AUDIENCE),
            )
            if not value
        ]
        if missing:
            raise RuntimeError("Authenticated API mode is missing: " + ", ".join(missing))
        if not BRIXTA_AUTH_TENANT_CLAIM and not BRIXTA_DEFAULT_TENANT_ID:
            raise RuntimeError("Set BRIXTA_AUTH_TENANT_CLAIM or BRIXTA_DEFAULT_TENANT_ID.")


@lru_cache(maxsize=1)
def _jwk_client() -> PyJWKClient:
    return PyJWKClient(BRIXTA_AUTH_JWKS_URL, cache_keys=True, lifespan=300)


def _roles(value: object) -> frozenset[str]:
    if isinstance(value, str):
        return frozenset(part.strip() for part in value.replace(",", " ").split() if part.strip())
    if isinstance(value, (list, tuple, set)):
        return frozenset(str(part).strip() for part in value if str(part).strip())
    return frozenset()


def _token_from_request(request: Request) -> str:
    if BRIXTA_AUTH_MODE == "cloudflare-access":
        assertion = request.headers.get("cf-access-jwt-assertion", "").strip()
        if assertion:
            return assertion
        return request.cookies.get("CF_Authorization", "").strip()
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    return token.strip() if scheme.lower() == "bearer" else ""


def _decode_token(token: str) -> dict[str, Any]:
    signing_key = _jwk_client().get_signing_key_from_jwt(token).key
    return jwt.decode(
        token,
        signing_key,
        algorithms=list(BRIXTA_AUTH_ALGORITHMS),
        audience=BRIXTA_AUTH_AUDIENCE,
        issuer=BRIXTA_AUTH_ISSUER,
        options={"require": ["exp", "iat", "iss", "sub"]},
    )


def _principal_from_claims(claims: dict[str, Any]) -> Principal:
    tenant = str(claims.get(BRIXTA_AUTH_TENANT_CLAIM) or BRIXTA_DEFAULT_TENANT_ID).strip()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Token has no '{BRIXTA_AUTH_TENANT_CLAIM}' tenant claim.",
        )
    return Principal(
        subject=str(claims.get("sub") or "").strip(),
        email=str(claims.get(BRIXTA_AUTH_EMAIL_CLAIM) or "").strip(),
        tenant_id=tenant,
        roles=_roles(claims.get(BRIXTA_AUTH_ROLES_CLAIM)),
        claims=claims,
        authenticated=True,
    )


def _local_principal() -> Principal:
    return Principal(
        subject="local-development",
        email="local@brixta.invalid",
        tenant_id=BRIXTA_DEFAULT_TENANT_ID or "default",
        roles=frozenset({"admin"}),
        claims={},
        authenticated=False,
    )


class ApiAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any) -> None:
        super().__init__(app)
        validate_auth_configuration()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if request.url.path in PUBLIC_PATHS or request.url.path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)
        if BRIXTA_AUTH_MODE == "none":
            request.state.principal = _local_principal()
            return await call_next(request)
        token = _token_from_request(request)
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication is required."},
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            request.state.principal = _principal_from_claims(_decode_token(token))
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        except (PyJWTError, ValueError, OSError) as exc:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Invalid authentication token: {type(exc).__name__}"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await call_next(request)


def current_principal(request: Request) -> Principal:
    principal = getattr(request.state, "principal", None)
    if not isinstance(principal, Principal):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication context is unavailable.",
        )
    return principal


def admin_principal(principal: Annotated[Principal, Depends(current_principal)]) -> Principal:
    principal.require_admin()
    return principal


CurrentPrincipal = Annotated[Principal, Depends(current_principal)]
AdminPrincipal = Annotated[Principal, Depends(admin_principal)]
