import sqlite3

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4


DATA_DIRECTORY = (
    Path(__file__).resolve().parent
    / "data"
)

DATABASE_PATH = (
    DATA_DIRECTORY
    / "desksync.db"
)


@contextmanager
def database_connection() -> Iterator[
    sqlite3.Connection
]:
    """Create and safely close a SQLite connection."""

    DATA_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10,
    )

    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def initialise_database() -> None:
    """Create the notification table when required."""

    with database_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                id TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL,
                read INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_notifications_read
            ON notifications(read)
            """
        )


def row_to_notification(
    row: sqlite3.Row,
) -> dict[str, Any]:
    """Convert one SQLite row to an API dictionary."""

    return {
        "id": row["id"],
        "title": row["title"],
        "message": row["message"],
        "source": row["source"],
        "created_at": row["created_at"],
        "read": bool(row["read"]),
    }


def add_notification(
    title: str,
    message: str,
    source: str = "DeskSync",
) -> dict[str, Any]:
    """Store a notification permanently."""

    notification = {
        "id": str(uuid4()),
        "title": title.strip(),
        "message": message.strip(),
        "source": source.strip() or "DeskSync",
        "created_at": (
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        ),
        "read": False,
    }

    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO notifications (
                id,
                title,
                message,
                source,
                created_at,
                read
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                notification["id"],
                notification["title"],
                notification["message"],
                notification["source"],
                notification["created_at"],
                0,
            ),
        )

        # Keep only the newest 50 notifications.
        connection.execute(
            """
            DELETE FROM notifications
            WHERE sequence NOT IN (
                SELECT sequence
                FROM notifications
                ORDER BY sequence DESC
                LIMIT 50
            )
            """
        )

    return notification


def get_notifications() -> list[
    dict[str, Any]
]:
    """Return all notifications, newest first."""

    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                title,
                message,
                source,
                created_at,
                read
            FROM notifications
            ORDER BY sequence DESC
            """
        ).fetchall()

    return [
        row_to_notification(row)
        for row in rows
    ]


def get_notification(
    index: int = 0,
) -> dict[str, Any] | None:
    """Return one notification using a safe index."""

    with database_connection() as connection:
        count_row = connection.execute(
            """
            SELECT COUNT(*) AS notification_count
            FROM notifications
            """
        ).fetchone()

        notification_count = int(
            count_row["notification_count"]
        )

        if notification_count == 0:
            return None

        safe_index = max(
            0,
            min(
                index,
                notification_count - 1,
            ),
        )

        row = connection.execute(
            """
            SELECT
                id,
                title,
                message,
                source,
                created_at,
                read
            FROM notifications
            ORDER BY sequence DESC
            LIMIT 1 OFFSET ?
            """,
            (safe_index,),
        ).fetchone()

    if row is None:
        return None

    return {
        **row_to_notification(row),
        "index": safe_index,
        "count": notification_count,
    }


def mark_notification_read(
    notification_id: str,
) -> dict[str, Any] | None:
    """Mark one notification as read."""

    with database_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE notifications
            SET read = 1
            WHERE id = ?
            """,
            (notification_id,),
        )

        if cursor.rowcount == 0:
            return None

        row = connection.execute(
            """
            SELECT
                id,
                title,
                message,
                source,
                created_at,
                read
            FROM notifications
            WHERE id = ?
            """,
            (notification_id,),
        ).fetchone()

    if row is None:
        return None

    return row_to_notification(row)


def clear_notifications() -> int:
    """Delete every stored notification."""

    with database_connection() as connection:
        count_row = connection.execute(
            """
            SELECT COUNT(*) AS notification_count
            FROM notifications
            """
        ).fetchone()

        deleted_count = int(
            count_row["notification_count"]
        )

        connection.execute(
            """
            DELETE FROM notifications
            """
        )

    return deleted_count


def unread_count() -> int:
    """Return the number of unread notifications."""

    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS unread_total
            FROM notifications
            WHERE read = 0
            """
        ).fetchone()

    return int(row["unread_total"])


initialise_database()