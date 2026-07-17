import os

from dotenv import load_dotenv

# Explicit process/container variables must win over persisted local settings.
# This is required by local MCP and isolated simulation workers.
load_dotenv("storage/control-plane/runtime.env", override=False)
load_dotenv(override=False)


def _csv(name: str, default: str = "") -> tuple[str, ...]:
    return tuple(
        item.strip()
        for item in os.getenv(name, default).split(",")
        if item.strip()
    )


DATABASE_URL = os.getenv("DATABASE_URL", "")

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)

# ---------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------

EMBEDDING_PLUGIN = os.getenv(
    "EMBEDDING_PLUGIN",
    "sentence_transformers",
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "nomic-ai/nomic-embed-text-v1.5",
)

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    "",
)

# ---------------------------------------------------------------------
# Environment and HTTP authentication
# ---------------------------------------------------------------------

BRIXTA_ENVIRONMENT = os.getenv("BRIXTA_ENVIRONMENT", "development").strip().lower()
BRIXTA_AUTH_MODE = os.getenv("BRIXTA_AUTH_MODE", "none").strip().lower()
BRIXTA_AUTH_JWKS_URL = os.getenv("BRIXTA_AUTH_JWKS_URL", "").strip()
BRIXTA_AUTH_ISSUER = os.getenv("BRIXTA_AUTH_ISSUER", "").strip()
BRIXTA_AUTH_AUDIENCE = os.getenv("BRIXTA_AUTH_AUDIENCE", "").strip()
BRIXTA_AUTH_ALGORITHMS = _csv("BRIXTA_AUTH_ALGORITHMS", "RS256")
BRIXTA_AUTH_TENANT_CLAIM = os.getenv("BRIXTA_AUTH_TENANT_CLAIM", "tenant_id").strip()
BRIXTA_AUTH_ROLES_CLAIM = os.getenv("BRIXTA_AUTH_ROLES_CLAIM", "roles").strip()
BRIXTA_AUTH_EMAIL_CLAIM = os.getenv("BRIXTA_AUTH_EMAIL_CLAIM", "email").strip()
BRIXTA_DEFAULT_TENANT_ID = os.getenv("BRIXTA_DEFAULT_TENANT_ID", "").strip()
BRIXTA_ADMIN_ROLES = frozenset(_csv("BRIXTA_ADMIN_ROLES", "admin,brixta-admin"))
BRIXTA_ADMIN_EMAILS = frozenset(
    value.lower() for value in _csv("BRIXTA_ADMIN_EMAILS")
)
BRIXTA_CORS_ORIGINS = _csv(
    "BRIXTA_CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
BRIXTA_CONTROL_PLANE_BACKEND = os.getenv(
    "BRIXTA_CONTROL_PLANE_BACKEND",
    "file",
).strip().lower()

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
)

# ---------------------------------------------------------------------
# Job recovery
# ---------------------------------------------------------------------

MAX_TASK_ATTEMPTS = max(1, int(os.getenv("MAX_TASK_ATTEMPTS", "3")))
TASK_RETRY_BACKOFF_SECONDS = max(
    1,
    int(os.getenv("TASK_RETRY_BACKOFF_SECONDS", "15")),
)
ORPHAN_TIMEOUT_SECONDS = max(
    60,
    int(os.getenv("ORPHAN_TIMEOUT_SECONDS", "1800")),
)
MAX_JOB_RUNS = max(1, int(os.getenv("MAX_JOB_RUNS", "3")))

# Public URLs are returned in knowledge manifests. Local defaults are useful for
# development; production deployments should set HTTPS URLs explicitly.
BRIXTA_API_PUBLIC_URL = os.getenv(
    "BRIXTA_API_PUBLIC_URL",
    "http://localhost:8000",
).rstrip("/")
BRIXTA_DASHBOARD_PUBLIC_URL = os.getenv(
    "BRIXTA_DASHBOARD_PUBLIC_URL",
    "http://localhost:3000",
).rstrip("/")
BRIXTA_MCP_PUBLIC_URL = os.getenv(
    "BRIXTA_MCP_PUBLIC_URL",
    "http://localhost:8001/mcp",
).rstrip("/")

# ---------------------------------------------------------------------
# Shared MCP gateway
# ---------------------------------------------------------------------

BRIXTA_MCP_AUTH_MODE = os.getenv("BRIXTA_MCP_AUTH_MODE", "static").strip().lower()
BRIXTA_MCP_TOKEN = os.getenv("BRIXTA_MCP_TOKEN", "")
BRIXTA_MCP_TENANT_ID = os.getenv("BRIXTA_MCP_TENANT_ID", "")
BRIXTA_MCP_JWKS_URI = os.getenv("BRIXTA_MCP_JWKS_URI", "")
BRIXTA_MCP_JWT_PUBLIC_KEY = os.getenv("BRIXTA_MCP_JWT_PUBLIC_KEY", "")
BRIXTA_MCP_JWT_ISSUER = os.getenv("BRIXTA_MCP_JWT_ISSUER", "")
BRIXTA_MCP_JWT_AUDIENCE = os.getenv("BRIXTA_MCP_JWT_AUDIENCE", "")

#----------------------------------------------------------------------
#Artifact
#----------------------------------------------------------------------

ARTIFACT_BACKEND = os.getenv(
    "ARTIFACT_BACKEND",
    "local",
)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_CONSOLE_URL = os.getenv("MINIO_CONSOLE_URL", "http://localhost:9001")
# Application credentials take precedence. Root credentials are accepted only
# as a backwards-compatible local fallback and should not reach app pods.
MINIO_ACCESS_KEY = os.getenv(
    "MINIO_ACCESS_KEY",
    os.getenv("MINIO_ROOT_USER", "minioadmin"),
)
MINIO_SECRET_KEY = os.getenv(
    "MINIO_SECRET_KEY",
    os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
)
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "brixta")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# ---------------------------------------------------------------------
# Structural & Material Lab
# ---------------------------------------------------------------------

CALCULIX_EXECUTABLE = os.getenv("CALCULIX_EXECUTABLE", "ccx").strip() or "ccx"
OPENFOAM_BLOCKMESH_EXECUTABLE = (
    os.getenv("OPENFOAM_BLOCKMESH_EXECUTABLE", "blockMesh").strip() or "blockMesh"
)
OPENFOAM_CHECKMESH_EXECUTABLE = (
    os.getenv("OPENFOAM_CHECKMESH_EXECUTABLE", "checkMesh").strip() or "checkMesh"
)
OPENFOAM_RUN_EXECUTABLE = os.getenv("OPENFOAM_RUN_EXECUTABLE", "foamRun").strip() or "foamRun"
OPENFOAM_VTK_EXECUTABLE = (
    os.getenv("OPENFOAM_VTK_EXECUTABLE", "foamToVTK").strip() or "foamToVTK"
)
SIMULATION_TIMEOUT_SECONDS = max(
    30,
    min(int(os.getenv("SIMULATION_TIMEOUT_SECONDS", "1800")), 86_400),
)
