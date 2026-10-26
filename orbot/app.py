"""Vietnamese Windows desktop interface, using native Tk controls."""

from __future__ import annotations

import queue
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Any

from orbot import demo
from orbot.controller import Controller
from orbot.launcher import launch_discord
from orbot.ui import COLORS, ProgressBar, QueueList
from orbot.workspace import build_workspace, style_workspace, sync_controls, sync_focus

STATUS = {
    "ready": "Sẵn sàng",
    "queued": "Trong hàng đợi",
    "running": "Đang xử lý",
    "claiming": "Đang nhận Orbs",
    "completed": "Hoàn thành · chờ nhận",
    "claimed": "Đã nhận thưởng",
    "unsupported": "Không thể chạy",
    "failed": "Có lỗi",
    "stopped": "Đã dừng",
    "claim_required": "Cần nhận trong Discord",
}
KINDS = {"video": "Video", "game": "Chơi game", "other": "Loại khác"}


class OrbotApp:
    table: ttk.Treeview
    queue_table: QueueList
    notebook: ttk.Notebook
    queue_tab: tk.Frame
    quests_tab: tk.Frame
    log_text: tk.Text
    activity_text: tk.StringVar
    activity_label: tk.Label
    count_label: tk.Label
    empty_label: tk.Label
    queue_empty_label: tk.Label
    refresh_button: ttk.Button
    select_button: ttk.Button
    start_button: ttk.Button
    stop_button: ttk.Button
    global_stop: ttk.Button
    add_button: ttk.Button
    up_button: ttk.Button
    down_button: ttk.Button
    remove_button: ttk.Button
    clear_button: ttk.Button
    connect_button: ttk.Button
    disconnect_button: ttk.Button
    launch_button: ttk.Button
    port_entry: ttk.Entry
    claim_check: ttk.Checkbutton
    progress: ProgressBar

    def __init__(self, root: tk.Tk, *, demo_mode: bool = False) -> None:
        self.root = root
        self.demo_mode = demo_mode
        self.controller = None if demo_mode else Controller()
        self.rows: dict[str, dict[str, Any]] = {}
        self.queue_ids: list[str] = []
        self.queue_state = "idle"
        self.queue_run = 0
        self.queue_owner: str | None = None
        self.active_id: str | None = None
        self.connected = False
        self.blocked = False
        self.account_name = "Discord Desktop"
        self.running = False
        self.busy = False
        self.closing = False
        self.port = tk.StringVar(value="9222")
        self.kind = tk.StringVar(value="Tất cả")
        self.auto_claim = tk.BooleanVar(value=True)
        self.connection_text = tk.StringVar(value="Chưa kết nối Discord")
        self.summary_text = tk.StringVar(value="Chưa chọn Quest")
        self.queue_text = tk.StringVar(value="Thêm Quest từ tab Quests để tạo hàng đợi.")
        self.detail_text = tk.StringVar(value="Chọn một Quest để xem tiến độ và trạng thái.")
        self.setup_text = tk.StringVar(
            value=(
                "Lần đầu: thoát Discord ở khay hệ thống → Mở Discord → Kết nối. "
                "Kết nối có thể mở Quest Home và tải lại giao diện Discord một lần."
            )
        )
        self._style()
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Escape>", lambda _event: self.stop())
        self.root.bind("<F5>", lambda _event: self.refresh())
        self.root.after(100, self._drain)
        if demo_mode:
            self.apply_snapshot(demo.snapshot())
            self.setup_text.set("CHẾ ĐỘ DEMO — Quest và tài khoản minh họa; không kết nối Discord.")
            self._log("Đang xem trước giao diện bằng dữ liệu minh họa.", "warning")
        else:
            self._log("Sẵn sàng. Bấm Kết nối sau khi mở Discord từ Orbot.")

    def _style(self) -> None:
        style_workspace(self)

    def _build(self) -> None:
        build_workspace(self)

    def _port(self) -> int | None:
        try:
            port = int(self.port.get())
            if not 1024 <= port <= 65535:
                raise ValueError
            return port
        except ValueError:
            self._log("Cổng phải là số từ 1024 đến 65535.", "error")
            return None

    def _log(self, text: str, level: str = "info") -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{time.strftime('%H:%M:%S')}  {text}\n", level)
        if int(self.log_text.index("end-1c").split(".")[0]) > 350:
            self.log_text.delete("1.0", "51.0")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.activity_text.set(f"{time.strftime('%H:%M:%S')}   {text[:120]}")
        self.activity_label.configure(fg=COLORS.get(level, COLORS["muted"]))

    def _controls(self) -> None:
        enabled = self.connected and not self.busy and not self.running and not self.demo_mode
        editable = self.connected and not self.busy and not self.running
        for button in (self.refresh_button, self.select_button):
            button.configure(
                state="normal"
                if self.connected and not self.running and not self.busy
                else "disabled"
            )
        self.start_button.configure(
            state="normal"
            if enabled and (self._pending_ids() or (not self.queue_ids and self.table.selection()))
            else "disabled"
        )
        self.add_button.configure(
            state="normal" if editable and self.table.selection() else "disabled"
        )
        for button in (self.up_button, self.down_button, self.remove_button):
            button.configure(
                state="normal" if editable and self.queue_table.selection() else "disabled"
            )
        self.clear_button.configure(state="normal" if editable and self.queue_ids else "disabled")
        self.stop_button.configure(
            state="normal" if self.running and not self.demo_mode else "disabled"
        )
        self.global_stop.configure(
            state="normal" if self.running and not self.demo_mode else "disabled"
        )
        self.connect_button.configure(
            state="disabled" if self.running or self.busy or self.demo_mode else "normal"
        )
        self.disconnect_button.configure(
            state="normal"
            if self.connected and not self.busy and not self.demo_mode
            else "disabled"
        )
        self.launch_button.configure(
            state="disabled" if self.running or self.busy or self.demo_mode else "normal"
        )
        self.port_entry.configure(state="disabled" if self.connected or self.busy else "normal")
        self.claim_check.configure(state="disabled" if self.running else "normal")
        sync_controls(self)

    def open_discord(self) -> None:
        port = self._port()
        if port is None:
            return
        try:
            launch_discord(port)
        except FileNotFoundError:
            chosen = filedialog.askopenfilename(
                title="Chọn Discord.exe", filetypes=[("Discord", "*.exe")]
            )
            if not chosen:
                return
            try:
                launch_discord(port, Path(chosen))
            except (OSError, ValueError) as exc:
                self._log(str(exc), "error")
                return
        except (OSError, ValueError) as exc:
            self._log(str(exc), "error")
            return
        self._log("Đã gửi lệnh mở Discord. Khi cửa sổ sẵn sàng, bấm Kết nối.")
        self._log("Nếu Discord đã chạy sẵn, hãy thoát ở khay hệ thống rồi bấm Mở Discord lại.")

    def connect(self) -> None:
        port = self._port()
        if port is not None and self.controller and not self.busy and not self.running:
            self.busy = True
            self.connection_text.set("Đang kết nối…")
            self._controls()
            self.controller.submit("connect", port)

    def disconnect(self) -> None:
        if self.controller:
            self.busy = True
            self._controls()
            self.controller.submit("disconnect")

    def refresh(self) -> None:
        if self.demo_mode:
            self.apply_snapshot(demo.snapshot())
        elif self.controller and self.connected and not self.running and not self.busy:
            self.busy = True
            self._controls()
            self.controller.submit("refresh")

    def render_rows(self) -> None:
        selected = set(self.table.selection())
        wanted = {"Video": "video", "Chơi game": "game"}.get(self.kind.get())
        visible = [row for row in self.rows.values() if not wanted or row["kind"] == wanted]
        keep = {row["id"] for row in visible}
        for ident in self.table.get_children():
            if ident not in keep:
                self.table.delete(ident)
        for row in visible:
            percent = (
                100
                if row.get("completed")
                else min(100, round(100 * row.get("progress", 0) / max(1, row.get("target", 1))))
            )
            tag = (
                "success"
                if row["status"] in {"completed", "claimed"}
                else "error"
                if row["status"] == "failed"
                else "muted"
                if not row.get("runnable")
                else ""
            )
            data = (
                row["name"],
                KINDS.get(row["kind"], "Khác"),
                str(row["orbs"]),
                f"{percent}%",
                STATUS.get(row["status"], row["status"]),
            )
            if self.table.exists(row["id"]):
                self.table.item(row["id"], values=data, tags=(tag,))
                self.table.move(row["id"], "", "end")
            else:
                self.table.insert("", "end", iid=row["id"], values=data, tags=(tag,))
        self.table.selection_set([ident for ident in selected if ident in keep])
        self.count_label.configure(text=f"Quests thưởng Orbs  ·  {len(visible)}")
        if visible:
            self.empty_label.place_forget()
        else:
            self.empty_label.configure(
                text="Không có Quest trong bộ lọc này."
                if self.rows
                else "Chưa có Quest Orbs. Kiểm tra Quest Home hoặc quét lại."
                if self.connected
                else "Kết nối Discord để tải các Quest hiện có."
            )
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        self._selection()

    def _pending_ids(self) -> list[str]:
        return [
            ident
            for ident in self.queue_ids
            if (row := self.rows.get(ident))
            and row.get("runnable")
            and not row.get("claimed")
            and (self.auto_claim.get() or not row.get("completed"))
        ]

    def render_queue(self) -> None:
        selected = set(self.queue_table.selection())
        for ident in self.queue_table.get_children():
            if ident not in self.queue_ids:
                self.queue_table.delete(ident)
        for position, ident in enumerate(self.queue_ids, 1):
            row = self.rows.get(ident)
            if row:
                percent = (
                    100
                    if row.get("completed")
                    else min(
                        100, round(100 * row.get("progress", 0) / max(1, row.get("target", 1)))
                    )
                )
                status = row["status"]
                if status == "ready":
                    status = "queued"
                tag = (
                    "success"
                    if row.get("claimed")
                    else "active"
                    if ident == self.active_id
                    else "error"
                    if status == "failed"
                    else ""
                )
                data = (
                    position,
                    row["name"],
                    KINDS.get(row["kind"], "Khác"),
                    row["orbs"],
                    f"{percent}%",
                    STATUS.get(status, status),
                )
            else:
                tag = "error"
                data = (position, ident, "—", "—", "—", "Không còn trong danh sách Quest")
            if self.queue_table.exists(ident):
                self.queue_table.item(ident, values=data, tags=(tag,))
                self.queue_table.move(ident, "", "end")
            else:
                self.queue_table.insert("", "end", iid=ident, values=data, tags=(tag,))
        self.queue_table.selection_set([ident for ident in self.queue_ids if ident in selected])
        if self.queue_ids:
            self.queue_empty_label.place_forget()
        else:
            self.queue_empty_label.place(relx=0.5, rely=0.5, anchor="center")
        pending = self._pending_ids()
        self.notebook.tab(self.queue_tab, text=f"Hàng đợi ({len(pending)})")
        state = {
            "running": "Đang chạy tuần tự",
            "finished": "Đã xử lý hết hàng đợi",
            "stopped": "Đã dừng · giữ các Quest còn chờ",
            "blocked": "Tạm dừng do lỗi Discord · xem nhật ký",
        }.get(self.queue_state, "Sẵn sàng chạy" if self.queue_ids else "Thêm Quest từ tab Quests")
        completed = sum(bool(self.rows.get(ident, {}).get("completed")) for ident in self.queue_ids)
        self.queue_text.set(
            f"{state}  ·  {completed}/{len(self.queue_ids)} hoàn thành  ·  {len(pending)} còn chờ"
        )
        self._selection()

    def _queue_changed(self) -> None:
        self.queue_state = "ready" if self.queue_ids else "idle"
        self.render_queue()

    def add_selected(self) -> None:
        if not self.connected or self.running or self.busy:
            return
        selected = set(self.table.selection())
        added = [
            ident
            for ident in self.table.get_children()
            if ident in selected
            and ident not in self.queue_ids
            and self.rows[ident].get("runnable")
            and not self.rows[ident].get("claimed")
        ]
        self.queue_ids.extend(added)
        if added:
            self._log(f"Đã thêm {len(added)} Quest. Hàng đợi có {len(self.queue_ids)} Quest.")
        self._queue_changed()
        self.notebook.select(self.queue_tab)

    def move_queue(self, direction: int) -> None:
        if self.running or self.busy:
            return
        selected = set(self.queue_table.selection())
        indices = (
            range(len(self.queue_ids)) if direction < 0 else range(len(self.queue_ids) - 1, -1, -1)
        )
        for index in indices:
            other = index + direction
            if (
                self.queue_ids[index] in selected
                and 0 <= other < len(self.queue_ids)
                and self.queue_ids[other] not in selected
            ):
                self.queue_ids[index], self.queue_ids[other] = (
                    self.queue_ids[other],
                    self.queue_ids[index],
                )
        self._queue_changed()

    def remove_selected(self) -> None:
        if not self.running and not self.busy:
            selected = set(self.queue_table.selection())
            self.queue_ids = [ident for ident in self.queue_ids if ident not in selected]
            self._queue_changed()

    def clear_queue(self) -> None:
        if not self.running and not self.busy:
            self.queue_ids.clear()
            self._queue_changed()

    def _select_all_key(self, _event: tk.Event[Any]) -> str:
        self.select_all()
        return "break"

    def select_all(self) -> None:
        self.table.selection_set(
            [
                ident
                for ident in self.table.get_children()
                if self.rows[ident].get("runnable") and not self.rows[ident].get("claimed")
            ]
        )
        self._selection()

    def _selection(self) -> None:
        table = self.queue_table if self.notebook.select() == str(self.queue_tab) else self.table
        selected = [self.rows[ident] for ident in table.selection() if ident in self.rows]
        pending = [self.rows[ident] for ident in self._pending_ids()]
        self.summary_text.set(
            f"{len(self.queue_ids)} Quest trong hàng đợi  ·  {len(pending)} còn chờ  ·  "
            f"{sum(row['orbs'] for row in pending):,} Orbs cơ bản còn lại"
        )
        if self.running and self.active_id in self.rows:
            selected = [self.rows[self.active_id]]
        if not selected and self.queue_ids:
            ident = next(iter(self._pending_ids()), self.queue_ids[0])
            if ident in self.rows:
                selected = [self.rows[ident]]
        if selected:
            row = selected[0]
            detail = row.get("detail") or row.get("reason") or STATUS.get(row["status"], "")
            self.detail_text.set(detail)
            self.progress.set_value(
                100
                if row.get("completed")
                else min(100, max(0, 100 * row.get("progress", 0) / max(1, row.get("target", 1))))
            )
        else:
            self.detail_text.set("Chọn một Quest để xem tiến độ và trạng thái.")
            self.progress.set_value(0)
        sync_focus(self, selected[0] if selected else None)
        self._controls()

    def start(self) -> None:
        if (
            self.controller
            and self.connected
            and not self.running
            and not self.busy
            and not self.demo_mode
        ):
            if not self.queue_ids:
                self.add_selected()
            ids = self._pending_ids()
            if not ids:
                self._log(
                    "Hàng đợi chưa có Quest có thể chạy hoặc nhận Orbs. Thêm Quest ở tab Quests.",
                    "warning",
                )
                return
            self.notebook.select(self.queue_tab)
            self._log(
                f"Bắt đầu hàng đợi {len(ids)} Quest; "
                f"tự nhận Orbs: {'bật' if self.auto_claim.get() else 'tắt'}."
            )
            self.busy = True
            self._controls()
            self.controller.submit("start", {"ids": ids, "autoClaim": self.auto_claim.get()})

    def stop(self) -> None:
        if self.controller and self.running:
            self.controller.submit("stop")

    def apply_snapshot(self, snapshot: dict[str, Any]) -> None:
        was_running = self.running
        self.connected = bool(snapshot.get("ready"))
        self.running = bool(snapshot.get("running"))
        self.blocked = bool(snapshot.get("blocked"))
        user = snapshot.get("user") or {}
        self.account_name = user.get("name", "Discord")
        owner = user.get("id")
        if self.queue_owner and owner != self.queue_owner:
            self.queue_ids.clear()
            self.queue_state = "idle"
            self.queue_run = 0
        self.queue_owner = owner
        engine_queue = snapshot.get("queue") or {}
        run_id = int(engine_queue.get("runId", 0))
        if engine_queue.get("owner") == owner and (
            run_id != self.queue_run or self.running or was_running
        ):
            self.queue_run = run_id
            self.queue_ids = list(engine_queue.get("ids", []))
            self.queue_state = engine_queue.get("status", "idle")
        previous_active = self.active_id
        self.active_id = snapshot.get("activeId")
        self.connection_text.set(
            ("DEMO  ·  " if self.demo_mode else "Đã kết nối  ·  ") + user.get("name", "Discord")
            if self.connected
            else "Chưa kết nối Discord"
        )
        if snapshot.get("blocked"):
            self.connection_text.set("Discord đang hạn chế Quests của tài khoản này")
        self.rows = {row["id"]: row for row in snapshot.get("quests", [])}
        self.render_rows()
        self.render_queue()
        if (
            self.active_id != previous_active
            and self.active_id
            and self.queue_table.exists(self.active_id)
        ):
            self.queue_table.see(self.active_id)
        for event in snapshot.get("events", []):
            self._log(event["message"], event.get("level", "info"))

    def _drain(self) -> None:
        if self.controller:
            while True:
                try:
                    event, payload = self.controller.events.get_nowait()
                except queue.Empty:
                    break
                if event == "snapshot":
                    if isinstance(payload, dict):
                        self.apply_snapshot(payload)
                    else:
                        self._log("Phiên Discord đã tải lại. Hãy kết nối lại.", "warning")
                        self.disconnect()
                elif event == "error":
                    self._log(payload, "error")
                    self.setup_text.set(payload)
                elif event == "status":
                    self.connection_text.set(payload)
                    self._log(payload)
                elif event == "disconnected":
                    self.connected = self.running = self.busy = False
                    self.blocked = False
                    self.connection_text.set("Chưa kết nối Discord")
                    self.rows.clear()
                    self.queue_ids.clear()
                    self.queue_state = "idle"
                    self.queue_run = 0
                    self.active_id = None
                    self.render_rows()
                    self.render_queue()
                elif event == "idle":
                    self.busy = False
                    self._controls()
                elif event == "closed" and self.closing:
                    self.root.destroy()
                    return
        if not self.closing or self.controller:
            self.root.after(100, self._drain)

    def save_log(self) -> None:
        destination = filedialog.asksaveasfilename(
            title="Lưu nhật ký Orbot",
            defaultextension=".txt",
            initialfile="orbot-log.txt",
            filetypes=[("Text", "*.txt")],
        )
        if destination:
            try:
                Path(destination).write_text(self.log_text.get("1.0", "end"), encoding="utf-8")
            except OSError as exc:
                self._log(f"Không lưu được nhật ký: {exc}", "error")

    def close(self) -> None:
        if self.closing:
            return
        self.closing = True
        if self.controller:
            self.connection_text.set("Đang dừng và khôi phục Discord…")
            self.controller.close()
            self._controls()
        else:
            self.root.destroy()
