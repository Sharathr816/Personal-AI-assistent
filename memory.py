"""
Mio Memory MVP
--------------
SQLite-based memory storage for profile, preference, and explicit memories.

The database is created automatically beside this file as:
    mio_memory.db

No external packages are required.
"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# --------------------------------------------------
# Configuration
# --------------------------------------------------

DB_PATH = Path(__file__).resolve().with_name("mio_memory.db")

VALID_CATEGORIES = {"profile", "preference", "explicit"}


# --------------------------------------------------
# Memory model
# --------------------------------------------------

@dataclass
class Memory:
    id: int
    category: str
    content: str
    created_at: str
    updated_at: str


# --------------------------------------------------
# Database initialization
# --------------------------------------------------

def initialize_db() -> None:
    """Create the database and memories table if they do not exist."""

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL
                    CHECK (category IN ('profile', 'preference', 'explicit')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
                    DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                updated_at TEXT NOT NULL
                    DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_category
            ON memories(category)
        """)


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _validate_category(category: str) -> None:
    if category not in VALID_CATEGORIES:
        allowed = ", ".join(sorted(VALID_CATEGORIES))
        raise ValueError(f"Invalid category '{category}'. Use: {allowed}.")


def _row_to_memory(row: sqlite3.Row) -> Memory:
    return Memory(
        id=row["id"],
        category=row["category"],
        content=row["content"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# --------------------------------------------------
# Create
# --------------------------------------------------

def save_memory(category: str, content: str) -> Memory:
    """Save a new memory and return the created Memory object."""

    _validate_category(category)

    content = content.strip()
    if not content:
        raise ValueError("Memory content cannot be empty.")

    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO memories (category, content)
            VALUES (?, ?)
            """,
            (category, content),
        )

        row = connection.execute(
            "SELECT * FROM memories WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return _row_to_memory(row)


# --------------------------------------------------
# Read
# --------------------------------------------------

def get_memory(memory_id: int) -> Optional[Memory]:
    """Get one memory by ID. Return None if it does not exist."""

    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM memories WHERE id = ?",
            (memory_id,),
        ).fetchone()

    return _row_to_memory(row) if row else None


def get_all_memories(category: Optional[str] = None) -> list[Memory]:
    """Get all memories, optionally filtered by category."""

    if category is not None:
        _validate_category(category)

    with _connect() as connection:
        if category is None:
            rows = connection.execute(
                "SELECT * FROM memories ORDER BY id"
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM memories WHERE category = ? ORDER BY id",
                (category,),
            ).fetchall()

    return [_row_to_memory(row) for row in rows]


# --------------------------------------------------
# Update
# --------------------------------------------------

def update_memory(
    memory_id: int,
    content: Optional[str] = None,
    category: Optional[str] = None,
) -> Optional[Memory]:
    """
    Update a memory's content and/or category.

    Return the updated Memory, or None if the ID does not exist.
    """

    if content is None and category is None:
        raise ValueError("Provide content, category, or both to update.")

    if category is not None:
        _validate_category(category)

    if content is not None:
        content = content.strip()
        if not content:
            raise ValueError("Memory content cannot be empty.")

    updates = []
    values = []

    if content is not None:
        updates.append("content = ?")
        values.append(content)

    if category is not None:
        updates.append("category = ?")
        values.append(category)

    updates.append("updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')")
    values.append(memory_id)

    with _connect() as connection:
        connection.execute(
            f"UPDATE memories SET {', '.join(updates)} WHERE id = ?",
            values,
        )

        row = connection.execute(
            "SELECT * FROM memories WHERE id = ?",
            (memory_id,),
        ).fetchone()

    return _row_to_memory(row) if row else None


# --------------------------------------------------
# Delete
# --------------------------------------------------

def delete_memory(memory_id: int) -> bool:
    """Delete a memory by ID. Return True if a row was deleted."""

    with _connect() as connection:
        cursor = connection.execute(
            "DELETE FROM memories WHERE id = ?",
            (memory_id,),
        )

    return cursor.rowcount > 0


# --------------------------------------------------
# Initialize database when this module is imported
# --------------------------------------------------

initialize_db()


if __name__ == "__main__":
    print(f"Mio memory database ready: {DB_PATH}")
    print(f"Stored memories: {len(get_all_memories())}")
