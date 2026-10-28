"""A serial CDP client restricted to a local Discord renderer."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener

import websocket

from orbot import ports

DISCORD_HOSTS = {"discord.com", "canary.discord.com", "ptb.discord.com", "discordapp.com"}
NOT_FOUND = (
    "Chưa tìm thấy cổng kết nối. Thoát Discord ở khay hệ thống, bấm Mở Discord, rồi bấm Kết nối."
)
INVALID_REPLY = "Discord trả về phản hồi không hợp lệ. Hãy kết nối lại."


class ConnectionError(RuntimeError):
    """An actionable local connection error."""


def verify_listener(port: int) -> None:
    """Refuse a port that is held by any program other than Discord (Windows only)."""
    if not ports.OWNER_CHECK:
        return
    try:
        owners = ports.listening_executables(port)
    except OSError as exc:
        raise ConnectionError(
            f"Không xác minh được chương trình đang giữ cổng {port}, nên Orbot không kết nối. "
            "Hãy thoát Discord ở khay hệ thống rồi bấm Mở Discord."
        ) from exc
    if not owners:
        raise ConnectionError(NOT_FOUND)
    strangers = sorted({path.name for path in owners if not ports.is_discord(path)})
    if strangers:
        raise ConnectionError(
            f"Cổng {port} đang do {', '.join(strangers)} giữ, không phải Discord. "
            "Orbot từ chối kết nối. Xóa ô cổng rồi bấm Mở Discord để chọn cổng khác."
        )


def port_status(port: int) -> str:
    """Classify a port as "free", "discord" or "other" without changing anything."""
    if not ports.port_in_use(port):
        return "free"
    if ports.OWNER_CHECK:
        try:
            owners = ports.listening_executables(port)
        except OSError:
            return "other"
        return "discord" if owners and all(map(ports.is_discord, owners)) else "other"
    try:
        discover_targets(port)
    except ConnectionError:
        return "other"
    return "discord"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        raise ConnectionError("Từ chối chuyển hướng khỏi cổng kết nối cục bộ.")


def valid_discord_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.hostname in DISCORD_HOSTS


def discover_targets(port: int) -> list[dict[str, Any]]:
    if not 1024 <= port <= 65535:
        raise ConnectionError("Cổng phải nằm trong khoảng 1024–65535.")
    verify_listener(port)
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        # The URL has a fixed loopback host; neither a proxy nor a remote host is accepted.
        with opener.open(f"http://127.0.0.1:{port}/json/list", timeout=3) as response:
            payload = json.loads(response.read(2_000_000))
    except (OSError, ValueError) as exc:
        raise ConnectionError(NOT_FOUND) from exc
    if not isinstance(payload, list):
        raise ConnectionError("Cổng này không trả về danh sách cửa sổ Discord.")
    targets = [
        item
        for item in payload
        if isinstance(item, dict)
        and item.get("type") == "page"
        and valid_discord_url(str(item.get("url", "")))
        and item.get("webSocketDebuggerUrl")
    ]
    if not targets:
        raise ConnectionError(
            "Đã thấy cổng gỡ lỗi nhưng chưa có cửa sổ Discord. Hãy đợi Discord mở."
        )
    return targets


class DiscordConnection:
    def __init__(self, target: dict[str, Any], port: int) -> None:
        url = str(target["webSocketDebuggerUrl"])
        parsed = urlparse(url)
        if (
            parsed.scheme != "ws"
            or parsed.hostname != "127.0.0.1"
            or parsed.port != port
            or parsed.username
            or parsed.password
            or not valid_discord_url(str(target.get("url", "")))
        ):
            raise ConnectionError("Từ chối kết nối: đích phải là Discord trên máy này.")
        self.socket = websocket.create_connection(
            url, timeout=4, suppress_origin=True, http_no_proxy=["127.0.0.1", "localhost"]
        )
        self.sequence = 0
        self.preload_id: str | None = None
        self.quest_url = f"https://{urlparse(str(target['url'])).hostname}/quest-home"
        try:
            self.call("Page.enable")
        except (OSError, RuntimeError, ValueError, websocket.WebSocketException):
            self.socket.close(timeout=1)
            raise

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.sequence += 1
        request_id = self.sequence
        self.socket.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            try:
                self.socket.settimeout(min(1, max(0.1, deadline - time.monotonic())))
                raw = self.socket.recv()
            except websocket.WebSocketTimeoutException:
                continue
            if not raw:
                raise ConnectionError("Discord đã đóng kết nối.")
            message = json.loads(raw)
            if not isinstance(message, dict) or message.get("id") != request_id:
                continue
            if "error" in message:
                error = message["error"]
                detail = error.get("message") if isinstance(error, dict) else error
                raise ConnectionError(str(detail or "CDP error")[:300])
            result = message.get("result", {})
            if not isinstance(result, dict):
                raise ConnectionError(INVALID_REPLY)
            return result
        raise ConnectionError("Hết thời gian chờ Discord phản hồi.")

    def evaluate(self, expression: str, *, await_promise: bool = False) -> Any:
        result = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": await_promise,
            },
        )
        if result.get("exceptionDetails"):
            raise ConnectionError("Mã kết nối chưa tương thích với bản Discord này.")
        remote = result.get("result", {})
        if not isinstance(remote, dict):
            raise ConnectionError(INVALID_REPLY)
        if remote.get("subtype") == "error":
            raise ConnectionError("Discord từ chối thao tác kết nối.")
        return remote.get("value")

    def install(self) -> dict[str, Any]:
        source = Path(__file__).with_name("engine.js").read_text(encoding="utf-8")
        self.evaluate(source)
        result = self.command("discover")
        if not isinstance(result, dict):
            raise ConnectionError(INVALID_REPLY)
        return result

    def prepare_reload(self) -> None:
        source = Path(__file__).with_name("capture.js").read_text(encoding="utf-8")
        result = self.call("Page.addScriptToEvaluateOnNewDocument", {"source": source})
        self.preload_id = result.get("identifier")
        self.call("Page.reload", {"ignoreCache": False})

    def remove_preload(self) -> None:
        if self.preload_id:
            self.call("Page.removeScriptToEvaluateOnNewDocument", {"identifier": self.preload_id})
            self.preload_id = None

    def command(self, method: str, argument: Any = None) -> Any:
        if method not in {"discover", "snapshot", "start", "stop", "shutdown"}:
            raise ValueError("Unknown engine method")
        encoded = json.dumps(argument, ensure_ascii=True)
        expression = f"globalThis.__orbot.{method}({encoded})"
        return self.evaluate(expression, await_promise=method == "discover")

    def close(self) -> None:
        try:
            self.command("shutdown")
        except (OSError, RuntimeError, websocket.WebSocketException, ValueError):
            pass  # A closed renderer discards its in-memory engine and patches itself.
        finally:
            try:
                self.remove_preload()
            except (OSError, RuntimeError, websocket.WebSocketException, ValueError):
                pass
            finally:
                self.socket.close(timeout=1)
