"""Pick a private debugging port and identify which local program is listening on it."""

from __future__ import annotations

import secrets
import socket
import struct
import sys
from pathlib import Path

DISCORD_EXECUTABLES = frozenset({"discord.exe", "discordcanary.exe", "discordptb.exe"})
# Stay below the default Windows dynamic range (49152+) used for outgoing connections.
PORT_RANGE = (20000, 48999)
# Only Windows can report the program behind a port; other platforms are for development.
OWNER_CHECK = sys.platform == "win32"


def port_in_use(port: int) -> bool:
    """Return True when something accepts connections on 127.0.0.1:port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        # Windows waits about two seconds before refusing a closed loopback port.
        probe.settimeout(0.3)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def choose_port() -> int:
    """Pick an unpredictable free loopback port instead of the well-known 9222."""
    low, high = PORT_RANGE
    for _ in range(40):
        port = low + secrets.randbelow(high - low + 1)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue  # In use, or reserved by Windows (excluded port ranges).
        return port
    raise OSError("Không tìm được cổng trống. Hãy nhập một cổng trong ô Cổng cục bộ.")


def is_discord(path: Path) -> bool:
    return path.name.lower() in DISCORD_EXECUTABLES


if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    _AF_INET = 2
    _TCP_TABLE_OWNER_PID_LISTENER = 3
    _ERROR_INSUFFICIENT_BUFFER = 122
    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    # Addresses are only compared with the TCP table here; nothing binds to them.
    _LOOPBACK_OR_ANY = {"127.0.0.1", "0.0.0.0"}  # nosec B104

    class _TcpRow(ctypes.Structure):
        _fields_ = [
            ("state", wintypes.DWORD),
            ("local_addr", wintypes.DWORD),
            ("local_port", wintypes.DWORD),
            ("remote_addr", wintypes.DWORD),
            ("remote_port", wintypes.DWORD),
            ("pid", wintypes.DWORD),
        ]

    _iphlpapi = ctypes.WinDLL("iphlpapi")
    _get_tcp_table = _iphlpapi.GetExtendedTcpTable
    _get_tcp_table.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.BOOL,
        wintypes.ULONG,
        ctypes.c_int,
        wintypes.ULONG,
    ]
    _get_tcp_table.restype = wintypes.DWORD

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _open_process = _kernel32.OpenProcess
    _open_process.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _open_process.restype = wintypes.HANDLE
    _query_image = _kernel32.QueryFullProcessImageNameW
    _query_image.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    _query_image.restype = wintypes.BOOL
    _close_handle = _kernel32.CloseHandle
    _close_handle.argtypes = [wintypes.HANDLE]
    _close_handle.restype = wintypes.BOOL

    def _listening_pids(port: int) -> set[int]:
        size = wintypes.DWORD(0)
        buffer = ctypes.create_string_buffer(1)
        for _ in range(5):
            status = _get_tcp_table(
                buffer, ctypes.byref(size), False, _AF_INET, _TCP_TABLE_OWNER_PID_LISTENER, 0
            )
            if status == 0:
                break
            if status != _ERROR_INSUFFICIENT_BUFFER:
                raise OSError(status, "Windows không trả về bảng kết nối TCP.")
            buffer = ctypes.create_string_buffer(size.value + 1024)
            size = wintypes.DWORD(len(buffer))
        else:
            raise OSError("Windows không trả về bảng kết nối TCP.")
        count = wintypes.DWORD.from_buffer(buffer).value
        header = ctypes.sizeof(wintypes.DWORD)
        if header + count * ctypes.sizeof(_TcpRow) > len(buffer):
            raise OSError("Bảng kết nối TCP không hợp lệ.")
        rows = (_TcpRow * count).from_buffer(buffer, header)
        return {
            int(row.pid)
            for row in rows
            # Both fields are in network byte order; only the low 16 bits hold the port.
            if socket.ntohs(row.local_port & 0xFFFF) == port
            and socket.inet_ntoa(struct.pack("<I", row.local_addr)) in _LOOPBACK_OR_ANY
        }

    def _process_path(pid: int) -> Path:
        handle = _open_process(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            length = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(length.value)
            if not _query_image(handle, 0, buffer, ctypes.byref(length)):
                raise ctypes.WinError(ctypes.get_last_error())
            return Path(buffer.value)
        finally:
            _close_handle(handle)

    def listening_executables(port: int) -> list[Path]:
        """Return the executables listening on 127.0.0.1:port (empty when nothing listens).

        Raises OSError when Windows cannot name a listener, such as another user's process.
        """
        return [_process_path(pid) for pid in sorted(_listening_pids(port))]

else:

    def listening_executables(port: int) -> list[Path]:
        raise OSError("Chỉ Windows hỗ trợ kiểm tra chương trình giữ cổng.")
