from datetime import datetime
from threading import Lock
from typing import Any
from uuid import uuid4


_notification_lock = Lock()
_notifications: list[dict[str, Any]] = []


def add_notification(
    title: str,
    message: str,
    source: str = "DeskSync",
) -> dict[str, Any]:
    """Add a notification to the in-memory queue."""

    notification = {
        "id": str(uuid4()),
        "title": title.strip(),
        "message": message.strip(),
        "source": source.strip(),
        "created_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "read": False,
    }

    with _notification_lock:
        _notifications.insert(0, notification)

        # Keep only the newest 50 notifications.
        del _notifications[50:]

    return notification


def get_notifications() -> list[dict[str, Any]]:
    """Return all notifications."""

    with _notification_lock:
        return [
            item.copy()
            for item in _notifications
        ]


def get_notification(
    index: int = 0,
) -> dict[str, Any] | None:
    """Return one notification by safe list index."""

    with _notification_lock:
        if not _notifications:
            return None

        safe_index = max(
            0,
            min(index, len(_notifications) - 1),
        )

        return {
            **_notifications[safe_index],
            "index": safe_index,
            "count": len(_notifications),
        }


def mark_notification_read(
    notification_id: str,
) -> dict[str, Any] | None:
    """Mark one notification as read."""

    with _notification_lock:
        for notification in _notifications:
            if notification["id"] == notification_id:
                notification["read"] = True
                return notification.copy()

    return None


def clear_notifications() -> int:
    """Remove all notifications."""

    with _notification_lock:
        count = len(_notifications)
        _notifications.clear()

    return count


def unread_count() -> int:
    """Return the number of unread notifications."""

    with _notification_lock:
        return sum(
            1
            for notification in _notifications
            if not notification["read"]
        )