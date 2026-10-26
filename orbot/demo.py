"""Explicit offline preview data; never used by the real connection path."""

from __future__ import annotations

from typing import Any


def snapshot() -> dict[str, Any]:
    rows = [
        ("demo-video", "Khám phá thế giới mới", "video", 200, 90, 0, "ready"),
        ("demo-game", "Chơi game cùng bạn bè", "game", 700, 900, 240, "ready"),
        ("demo-done", "Xem trailer ra mắt", "video", 200, 60, 60, "completed"),
        ("demo-other", "Thành tích trong game", "other", 700, 1, 0, "unsupported"),
    ]
    return {
        "ready": True,
        "running": False,
        "blocked": False,
        "user": {"id": "demo", "name": "Bản xem trước — dữ liệu minh họa"},
        "quests": [
            {
                "id": ident,
                "name": name,
                "kind": kind,
                "orbs": orbs,
                "target": target,
                "progress": progress,
                "status": status,
                "runnable": status != "unsupported",
                "completed": status == "completed",
                "claimed": False,
                "reason": "Loại Quest chưa hỗ trợ" if kind == "other" else "",
            }
            for ident, name, kind, orbs, target, progress, status in rows
        ],
        "events": [],
        "activeId": None,
    }
