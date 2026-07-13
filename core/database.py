import psycopg
from pgvector.psycopg import register_vector

from core.config import DATABASE_URL


def get_connection():
    """
    Returns a PostgreSQL connection with pgvector support enabled.
    """

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required for database operations.")

    try:
        conn = psycopg.connect(
            DATABASE_URL,
            autocommit=True,
        )

        register_vector(conn)

        return conn

    except Exception as e:
        raise RuntimeError(
            f"Failed to connect to Neon PostgreSQL: {e}"
        )
