import psycopg

from shared.config import DATABASE_URL


def get_connection():
    """
    Creates and returns a fresh PostgreSQL connection.
    Each request gets its own connection.
    """

    try:
        return psycopg.connect(
            DATABASE_URL,
            autocommit=True,
        )

    except Exception as e:
        raise RuntimeError(
            f"Failed to connect to Neon PostgreSQL: {e}"
        )


def test_connection():
    """
    Opens a temporary connection and verifies connectivity.
    """

    try:
        print("🔌 Connecting to Neon PostgreSQL...")

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                row = cur.fetchone()

        if row is None:
            raise RuntimeError("No version information returned.")

        print("✅ Connected to Neon successfully!")
        print(row[0])

    except Exception as e:
        print(f"❌ Connection test failed: {e}")


if __name__ == "__main__":
    test_connection()