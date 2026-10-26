"""Keep all network work on one worker; communicate with Tk through a queue."""

from __future__ import annotations

import queue
import threading
import time
from typing import Any

import websocket

from orbot.cdp import ConnectionError, DiscordConnection, discover_targets


class Controller:
    def __init__(self) -> None:
        self.commands: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.closed = threading.Event()
        self.connection: DiscordConnection | None = None
        self.thread = threading.Thread(target=self._work, name="orbot-discord", daemon=True)
        self.thread.start()

    def submit(self, command: str, argument: Any = None) -> None:
        self.commands.put((command, argument))

    def _connect(self, port: int) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None
        self.events.put(("status", "Đang tìm cửa sổ Discord…"))
        targets = discover_targets(port)
        targets.sort(key=lambda item: "/channels" not in str(item.get("url", "")))
        self.connection = DiscordConnection(targets[0], port)
        status = self.connection.install()
        if not status.get("ready"):
            self.events.put(("status", "Đang chuẩn bị phiên; giao diện Discord sẽ tải lại…"))
            self.connection.prepare_reload()
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline and not self.closed.wait(0.75):
                try:
                    status = self.connection.install()
                    if status.get("ready"):
                        break
                except ConnectionError:
                    continue  # Navigation temporarily removes the JavaScript context.
            if not status.get("ready"):
                diagnostics = status.get("diagnostics", {})
                missing = [
                    name
                    for key, name in (
                        ("questStore", "QuestStore"),
                        ("userStore", "UserStore"),
                        ("api", "API"),
                    )
                    if not diagnostics.get(key)
                ]
                raise ConnectionError(
                    "Chưa kết nối được hệ thống Quests. "
                    f"Thiếu: {', '.join(missing) or 'phiên đăng nhập'}. "
                    f"Đã thu {diagnostics.get('capturedModules', 0)} module. "
                    "Mở Quest Home trong Discord rồi kết nối lại."
                )
            self.connection.remove_preload()
        self.events.put(("snapshot", status))

    def _disconnect(self) -> None:
        if self.connection:
            try:
                self.connection.close()
            except (OSError, RuntimeError, websocket.WebSocketException):
                pass
            self.connection = None

    def _work(self) -> None:
        while not self.closed.is_set():
            try:
                command, argument = self.commands.get(timeout=0.8)
            except queue.Empty:
                command, argument = "poll", None
            try:
                if command == "close":
                    self.closed.set()
                    break
                if command == "connect":
                    self._connect(int(argument))
                elif command == "disconnect":
                    self._disconnect()
                    self.events.put(("disconnected", None))
                elif self.connection:
                    operation = {"poll": "snapshot", "refresh": "discover"}.get(command, command)
                    self.events.put(("snapshot", self.connection.command(operation, argument)))
            except (
                OSError,
                RuntimeError,
                ValueError,
                TypeError,
                KeyError,
                websocket.WebSocketException,
            ) as exc:
                self.events.put(("error", str(exc)))
                self._disconnect()
                self.events.put(("disconnected", None))
            finally:
                if command != "poll":
                    self.events.put(("idle", command))
        self._disconnect()
        self.events.put(("closed", None))

    def close(self) -> None:
        # Interrupt connection setup promptly; the worker still performs engine cleanup.
        self.closed.set()
        self.commands.put(("close", None))
