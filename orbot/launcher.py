"""Find and open the user's existing Discord installation without ending it."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


def find_discord() -> Path | None:
    local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    for folder, executable in (
        ("Discord", "Discord.exe"),
        ("DiscordCanary", "DiscordCanary.exe"),
        ("DiscordPTB", "DiscordPTB.exe"),
    ):
        root = local / folder
        versions = sorted(
            root.glob("app-*"),
            key=lambda path: tuple(int(n) for n in re.findall(r"\d+", path.name)),
            reverse=True,
        )
        for version in versions:
            candidate = version / executable
            if candidate.is_file():
                return candidate
    return None


def launch_discord(port: int, executable: Path | None = None) -> subprocess.Popen[bytes]:
    path = executable or find_discord()
    if path is None or not path.is_file():
        raise FileNotFoundError("Chưa tìm thấy Discord Desktop. Hãy chọn file Discord.exe.")
    if not 1024 <= port <= 65535:
        raise ValueError("Cổng không hợp lệ.")
    return subprocess.Popen(  # noqa: S603 - explicit executable, argument list, no shell.
        [
            str(path.resolve()),
            f"--remote-debugging-port={port}",
            "--remote-debugging-address=127.0.0.1",
        ],
        cwd=str(path.parent),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
