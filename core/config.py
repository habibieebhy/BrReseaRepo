import os

from dotenv import load_dotenv

# Explicit process/container variables must win over persisted local settings.
# This is required by local MCP and isolated simulation workers.
load_dotenv("storage/control-plane/runtime.env", override=False)
load_dotenv(override=False)


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
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", os.getenv("MINIO_ACCESS_KEY", "minioadmin"))
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", os.getenv("MINIO_SECRET_KEY", "minioadmin"))
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
