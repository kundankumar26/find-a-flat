"""
Database Module - SQLite for tracking seen listings (deduplication)
"""

import sqlite3
import logging
from datetime import datetime

log = logging.getLogger(__name__)
DB_PATH = "seen_listings.db"


def init_db():
    """Creates the database and tables if they don't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_listings (
                id TEXT PRIMARY KEY,
                url TEXT,
                title TEXT,
                price INTEGER,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    log.info("Database initialized")


def get_new_listings(listings: list[dict]) -> list[dict]:
    """
    Filters listings to only those not seen before.
    Returns list of new listings.
    """
    if not listings:
        return []

    with sqlite3.connect(DB_PATH) as conn:
        new = []
        for listing in listings:
            lid = listing.get("id", "")
            if not lid:
                continue
            row = conn.execute(
                "SELECT id FROM seen_listings WHERE id = ?", (lid,)
            ).fetchone()
            if not row:
                new.append(listing)
    return new


def mark_as_seen(listing_id: str):
    """Marks a listing ID as seen in the database."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO seen_listings (id, last_seen)
            VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET last_seen = excluded.last_seen
            """,
            (listing_id, datetime.now())
        )
        conn.commit()


def get_all_seen_ids() -> set:
    """Returns all seen listing IDs."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT id FROM seen_listings").fetchall()
        return {row[0] for row in rows}


def get_stats() -> dict:
    """Returns basic stats about tracked listings."""
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM seen_listings").fetchone()[0]
        return {"total_seen": total}
