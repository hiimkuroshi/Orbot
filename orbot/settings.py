"""Remember the private debugging port between Orbot sessions. Nothing else is stored."""

from __future__ import annotations

import json
import os
from pathlib import Path


def settings_file() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "Orbot" / "settings.json"


def load_port() -> int | None:
    try:
        data = json.loads(settings_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    port = data.get("port") if isinstance(data, dict) else None
    if isinstance(port, int) and not isinstance(port, bool) and 1024 <= port <= 65535:
        return port
    return None


def save_port(port: int) -> bool:
    path = settings_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"port": port}), encoding="utf-8")
    except OSError:
        return False
    return True
