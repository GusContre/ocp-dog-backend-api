import os
from typing import Iterable, Optional

import psycopg2
from psycopg2.extras import RealDictCursor


class DogRepository:
    """Handles all DB interactions for dogs."""

    def __init__(self) -> None:
        self.host = os.getenv("DB_HOST")
        self.name = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASS")
        self.port = int(os.getenv("DB_PORT", 5432))
        self.connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", 3))

    @property
    def configured(self) -> bool:
        return all([self.host, self.name, self.user, self.password])

    def get_connection(self):
        if not self.configured:
            return None
        try:
            return psycopg2.connect(
                host=self.host,
                dbname=self.name,
                user=self.user,
                password=self.password,
                port=self.port,
                connect_timeout=self.connect_timeout,
            )
        except Exception:
            return None

    def ensure_schema(self, conn) -> bool:
        if not conn:
            return False
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS dogs (
                        id SERIAL PRIMARY KEY,
                        name TEXT,
                        image TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                    """
                )
        return True

    def fetch_random(self, conn):
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT name, image FROM dogs ORDER BY random() LIMIT 1")
            return cur.fetchone()

    def insert(self, conn, name: Optional[str], image: Optional[str]):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO dogs (name, image) VALUES (%s, %s)",
                (name, image),
            )
        conn.commit()

    def list_items(self, conn):
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name, image, created_at FROM dogs ORDER BY id DESC")
            return cur.fetchall()

    def seed_if_empty(self, conn, items: Iterable[dict]) -> bool:
        payload = [
            ((item.get("name") or "").strip() or None, (item.get("image") or "").strip() or None)
            for item in items
        ]
        payload = [row for row in payload if row[0] or row[1]]
        if not payload:
            return False

        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM dogs LIMIT 1")
            if cur.fetchone():
                return False
            cur.executemany(
                "INSERT INTO dogs (name, image) VALUES (%s, %s)",
                payload,
            )
        conn.commit()
        return True
