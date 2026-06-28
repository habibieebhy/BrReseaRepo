import os

from dotenv import load_dotenv
import psycopg

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing.")

try:
    print("🔌 Connecting to Neon PostgreSQL...")

    conn = psycopg.connect(
        DATABASE_URL,
        autocommit=True,
    )

    print("✅ Connected to Neon successfully!")

except Exception as e:
    raise RuntimeError(f"Failed to connect: {e}")


def get_connection():
    return conn


def test_connection():
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()

        print("✅ Connected!")
        print(version)

    except Exception as e:
        print(e)


if __name__ == "__main__":
    test_connection()