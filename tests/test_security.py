from __future__ import annotations

import json
import os
import queue
import socket
import sys
import tempfile
import time
import unittest
from pathlib import PureWindowsPath
from unittest.mock import patch

from orbot import ports
from orbot.cdp import (
    NOT_FOUND,
    ConnectionError,
    DiscordConnection,
    discover_targets,
    port_status,
    verify_listener,
)
from orbot.controller import Controller
from orbot.settings import load_port, save_port, settings_file

DISCORD = PureWindowsPath(r"C:\Users\user\AppData\Local\Discord\app-1.0.9263\Discord.exe")
STRANGER = PureWindowsPath(r"C:\Users\user\Downloads\listener.exe")
TARGET = {"url": "https://discord.com/", "webSocketDebuggerUrl": "ws://127.0.0.1:9222/page"}


class MalformedReplyTests(unittest.TestCase):
    def client(self, *replies: object) -> DiscordConnection:
        connect = patch("orbot.cdp.websocket.create_connection").start()
        self.addCleanup(patch.stopall)
        page_enable = {"id": 1, "result": {}}
        connect.return_value.recv.side_effect = [json.dumps(page_enable)] + [
            json.dumps(reply) for reply in replies
        ]
        return DiscordConnection(TARGET, 9222)

    def test_text_error_is_reported_instead_of_crashing(self) -> None:
        client = self.client({"id": 2, "error": "not-an-object"})
        with self.assertRaises(ConnectionError):
            client.call("Runtime.evaluate")

    def test_non_object_result_is_rejected(self) -> None:
        client = self.client({"id": 2, "result": ["unexpected"]})
        with self.assertRaises(ConnectionError):
            client.call("Runtime.evaluate")

    def test_non_object_remote_value_is_rejected(self) -> None:
        client = self.client({"id": 2, "result": {"result": "unexpected"}})
        with self.assertRaises(ConnectionError):
            client.evaluate("1")

    def test_non_object_messages_are_ignored(self) -> None:
        connect = patch("orbot.cdp.websocket.create_connection").start()
        self.addCleanup(patch.stopall)
        connect.return_value.recv.side_effect = [
            json.dumps({"id": 1, "result": {}}),
            json.dumps([1, 2, 3]),
            json.dumps({"id": 2, "result": {"ok": True}}),
        ]
        client = DiscordConnection(TARGET, 9222)
        self.assertEqual(client.call("Runtime.evaluate"), {"ok": True})


class WorkerTests(unittest.TestCase):
    def test_worker_survives_unexpected_errors_and_still_closes(self) -> None:
        with patch("orbot.controller.discover_targets", side_effect=AttributeError("fixture")):
            controller = Controller()
            controller.submit("connect", 9222)
            events = self.collect(controller, until="idle")
            errors = [payload for kind, payload in events if kind == "error"]
            self.assertTrue(errors and "Lỗi không mong đợi" in errors[0])
            self.assertTrue(controller.thread.is_alive(), "The worker must keep running")
            controller.close()
            events = self.collect(controller, until="closed")
            self.assertEqual(events[-1][0], "closed")

    def collect(self, controller: Controller, *, until: str) -> list[tuple[str, object]]:
        events: list[tuple[str, object]] = []
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                events.append(controller.events.get(timeout=0.2))
            except queue.Empty:
                continue
            if events[-1][0] == until:
                return events
        self.fail(f"No {until!r} event; received {events}")


class OwnerCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        patch("orbot.ports.OWNER_CHECK", True).start()
        self.addCleanup(patch.stopall)

    def owners(self, *paths: PureWindowsPath) -> None:
        patch("orbot.ports.listening_executables", return_value=list(paths)).start()

    def test_discord_listener_is_accepted(self) -> None:
        self.owners(DISCORD)
        verify_listener(34567)

    def test_other_program_is_refused_and_named(self) -> None:
        self.owners(STRANGER)
        with self.assertRaises(ConnectionError) as caught:
            verify_listener(34567)
        self.assertIn("listener.exe", str(caught.exception))

    def test_any_extra_listener_is_refused(self) -> None:
        self.owners(DISCORD, STRANGER)
        with self.assertRaises(ConnectionError):
            verify_listener(34567)

    def test_unknown_owner_is_refused(self) -> None:
        patch("orbot.ports.listening_executables", side_effect=OSError(5, "denied")).start()
        with self.assertRaises(ConnectionError):
            verify_listener(34567)

    def test_missing_listener_reports_how_to_open_discord(self) -> None:
        self.owners()
        with self.assertRaises(ConnectionError) as caught:
            verify_listener(34567)
        self.assertEqual(str(caught.exception), NOT_FOUND)

    def test_discovery_checks_the_owner_before_any_request(self) -> None:
        self.owners(STRANGER)
        with patch("orbot.cdp.build_opener") as opener, self.assertRaises(ConnectionError):
            discover_targets(34567)
        opener.assert_not_called()

    def test_port_status_classifies_listeners(self) -> None:
        with patch("orbot.ports.port_in_use", return_value=False):
            self.assertEqual(port_status(34567), "free")
        with patch("orbot.ports.port_in_use", return_value=True):
            self.owners(DISCORD)
            self.assertEqual(port_status(34567), "discord")
            self.owners(STRANGER)
            self.assertEqual(port_status(34567), "other")
            patch("orbot.ports.listening_executables", side_effect=OSError()).start()
            self.assertEqual(port_status(34567), "other")


@unittest.skipUnless(sys.platform == "win32", "Reads the Windows TCP table")
class WindowsListenerTests(unittest.TestCase):
    def test_reports_the_real_listening_program(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen()
            port = server.getsockname()[1]
            owners = ports.listening_executables(port)
            self.assertTrue(owners)
            self.assertTrue(all(path.name.lower().startswith("python") for path in owners))
            with self.assertRaises(ConnectionError) as caught:
                verify_listener(port)
            self.assertIn(owners[0].name, str(caught.exception))
            self.assertEqual(port_status(port), "other")

    def test_free_port_has_no_listener(self) -> None:
        port = ports.choose_port()
        self.assertEqual(ports.listening_executables(port), [])
        self.assertEqual(port_status(port), "free")


class PortSettingsTests(unittest.TestCase):
    def test_port_round_trip_and_invalid_values(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {"LOCALAPPDATA": folder}):
                self.assertIsNone(load_port())
                self.assertTrue(save_port(34567))
                self.assertEqual(load_port(), 34567)
                for content in ('{"port": true}', '{"port": 80}', '["port"]', "not json"):
                    settings_file().write_text(content, encoding="utf-8")
                    self.assertIsNone(load_port(), content)

    def test_chosen_port_is_free_and_not_the_default(self) -> None:
        low, high = ports.PORT_RANGE
        for _ in range(5):
            port = ports.choose_port()
            self.assertTrue(low <= port <= high)
            self.assertNotEqual(port, 9222)
            self.assertFalse(ports.port_in_use(port))


if __name__ == "__main__":
    unittest.main()
