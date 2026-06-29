import os

from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.environ["DATABASE_URL"]

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    "",
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "text-embedding-3-small",
)

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
)