import os

from dotenv import load_dotenv

load_dotenv()
load_dotenv("storage/control-plane/runtime.env", override=True)


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
