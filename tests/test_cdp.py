from __future__ import annotations

import base64
import hashlib
import json
import struct
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import websocket

from orbot.cdp import ConnectionError, DiscordConnection, discover_targets, valid_discord_url


class FixtureHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        pass

    def do_GET(self) -> None:
        port = self.server.server_port
        if self.path == "/json/list":
            payload = json.dumps(
                [
                    {
                        "type": "page",
                        "url": "https://discord.com/channels/@me",
                        "webSocketDebuggerUrl": f"ws://127.0.0.1:{port}/devtools/page/fixture",
                    },
                    {
                        "type": "page",
                        "url": "https://discord.com.evil.test/",
                        "webSocketDebuggerUrl": "ws://evil.test",
                    },
                ]
            ).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.headers.get("Upgrade", "").lower() != "websocket":
            self.send_error(404)
            return
        challenge = self.headers["Sec-WebSocket-Key"] + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        accept = base64.b64encode(
            hashlib.sha1(challenge.encode(), usedforsecurity=False).digest()
        ).decode()
        self.send_response(101)
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()
        while True:
            header = self.rfile.read(2)
            if len(header) < 2 or header[0] & 15 == 8:
                return
            length = header[1] & 127
            if length == 126:
                length = struct.unpack("!H", self.rfile.read(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self.rfile.read(8))[0]
            mask = self.rfile.read(4)
            data = self.rfile.read(length)
            request = json.loads(bytes(value ^ mask[i % 4] for i, value in enumerate(data)))
            event = {"method": "Runtime.consoleAPICalled", "params": {}}
            self.send_frame(event)
            expression = request.get("params", {}).get("expression", "")
            if expression == "throw_error":
                result = {"exceptionDetails": {"text": "Fixture exception"}}
            else:
                result = {"result": {"type": "object", "value": {"ready": True, "quests": []}}}
            self.send_frame({"id": request["id"], "result": result})

    def send_frame(self, payload: dict) -> None:
        encoded = json.dumps(payload).encode()
        header = (
            bytes([129, len(encoded)])
            if len(encoded) < 126
            else b"\x81\x7e" + struct.pack("!H", len(encoded))
        )
        self.wfile.write(header + encoded)
        self.wfile.flush()


class CDPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def test_discovers_only_real_discord_targets_and_handles_events(self) -> None:
        targets = discover_targets(self.server.server_port)
        self.assertEqual(len(targets), 1)
        connection = DiscordConnection(targets[0], self.server.server_port)
        self.assertTrue(connection.evaluate("fixture")["ready"])
        self.assertTrue(connection.command("discover")["ready"])
        connection.close()

    def test_rejects_remote_or_mismatched_debugger(self) -> None:
        for url in ("ws://example.com:9222/page", "ws://127.0.0.1:9223/page"):
            with self.assertRaises(ConnectionError):
                DiscordConnection(
                    {"url": "https://discord.com/", "webSocketDebuggerUrl": url}, 9222
                )

    def test_url_validation_does_not_accept_suffix_spoofing(self) -> None:
        self.assertTrue(valid_discord_url("https://canary.discord.com/channels/@me"))
        self.assertFalse(valid_discord_url("https://discord.com.evil.test/"))
        self.assertFalse(valid_discord_url("http://discord.com/"))

    def test_ports_and_unexpected_commands_fail_without_network(self) -> None:
        for port in (0, 80, 65536):
            with self.assertRaises(ConnectionError):
                discover_targets(port)
        with patch("orbot.cdp.websocket.create_connection") as connect:
            connect.return_value.recv.return_value = json.dumps({"id": 1, "result": {}})
            client = DiscordConnection(
                {"url": "https://discord.com/", "webSocketDebuggerUrl": "ws://127.0.0.1:9222/page"},
                9222,
            )
            with self.assertRaises(ValueError):
                client.command("arbitrary")

    def test_renderer_exception_is_reported(self) -> None:
        connection = DiscordConnection(
            discover_targets(self.server.server_port)[0], self.server.server_port
        )
        with self.assertRaises(ConnectionError):
            connection.evaluate("throw_error")
        connection.close()

    def test_preload_enables_page_domain_and_reloads_existing_renderer(self) -> None:
        responses = [
            json.dumps({"id": 1, "result": {}}),
            json.dumps({"id": 2, "result": {"identifier": "preload-fixture"}}),
            json.dumps({"id": 3, "result": {}}),
        ]
        with patch("orbot.cdp.websocket.create_connection") as connect:
            connect.return_value.recv.side_effect = responses
            client = DiscordConnection(
                {
                    "url": "https://discord.com/quest-home",
                    "webSocketDebuggerUrl": "ws://127.0.0.1:9222/page",
                },
                9222,
            )
            client.prepare_reload()
            sent = [json.loads(call.args[0]) for call in connect.return_value.send.call_args_list]
            self.assertEqual(
                [item["method"] for item in sent],
                ["Page.enable", "Page.addScriptToEvaluateOnNewDocument", "Page.reload"],
            )
            self.assertEqual(client.preload_id, "preload-fixture")

    def test_short_socket_timeout_does_not_abort_pending_cdp_request(self) -> None:
        with patch("orbot.cdp.websocket.create_connection") as connect:
            connect.return_value.recv.side_effect = [
                websocket.WebSocketTimeoutException(),
                json.dumps({"id": 1, "result": {}}),
            ]
            DiscordConnection(
                {
                    "url": "https://discord.com/quest-home",
                    "webSocketDebuggerUrl": "ws://127.0.0.1:9222/page",
                },
                9222,
            )
            self.assertEqual(connect.return_value.send.call_count, 1)
            self.assertEqual(connect.return_value.recv.call_count, 2)


if __name__ == "__main__":
    unittest.main()
