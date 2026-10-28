"""Exercise the real desktop widgets using explicitly labeled sample data."""

import socket
import sys
import tkinter as tk
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from orbot import demo  # noqa: E402
from orbot.app import OrbotApp  # noqa: E402
from orbot.ui import COLORS  # noqa: E402
from orbot.workspace import show_settings, toggle_log  # noqa: E402

root = tk.Tk()
app = OrbotApp(root, demo_mode=True)
root.update()
assert len(app.table.get_children()) == 4
assert len(app.notebook.tabs()) == 3
assert app.auto_claim.get(), "Auto-claim should be enabled by default"
app.select_all()
assert len(app.table.selection()) == 3
app.add_selected()
assert app.queue_ids == ["demo-video", "demo-game", "demo-done"]
root.update()
app.queue_table.event_generate("<Button-1>", x=80, y=30)
root.update()
assert app.queue_table.selection() == ("demo-video",)
app.queue_table.event_generate("<Button-1>", x=80, y=260, state=4)
root.update()
assert set(app.queue_table.selection()) == {"demo-video", "demo-done"}
app.queue_table.event_generate("<Button-1>", x=80, y=145, state=1)
root.update()
assert set(app.queue_table.selection()) == {"demo-game", "demo-done"}
assert app.focus_title.cget("text") == "Chơi game cùng bạn bè"
app.add_selected()
assert len(app.queue_ids) == 3, "Adding again must not duplicate a Quest"
app.kind.set("Video")
app.render_rows()
root.update()
assert len(app.table.get_children()) == 2
assert app.queue_ids == ["demo-video", "demo-game", "demo-done"], (
    "Filtering must not truncate the queue"
)
app.queue_table.selection_set("demo-game")
app.move_queue(-1)
assert app.queue_ids[0] == "demo-game"
assert app.queue_table.get_children()[0] == "demo-game"
app.move_queue(1)
assert app.queue_ids[1] == "demo-game"
app.queue_table.selection_set("demo-done")
app.remove_selected()
assert app.queue_ids == ["demo-video", "demo-game"]
app.apply_snapshot(demo.snapshot())
assert app.queue_ids == ["demo-video", "demo-game"], "An idle poll must preserve queue edits"
assert app.start_button.instate(["disabled"]), "Demo must never run real operations"
assert len(app._pending_ids()) == 2
app.queue_ids.append("demo-done")
app.auto_claim.set(False)
assert len(app._pending_ids()) == 2, "Completed Quests need only the claim step"
app.auto_claim.set(True)
assert len(app._pending_ids()) == 3
app.clear_queue()
assert not app.queue_table.get_children()
app.kind.set("Tất cả")
app.render_rows()
app.select_all()
app.add_selected()
# A fake worker proves that Run receives the whole queue, despite a single selected row/filter.
app.kind.set("Video")
app.render_rows()
app.table.selection_set("demo-video")
worker = Mock()
app.controller = worker
app.start()
worker.submit.assert_not_called()
app.demo_mode = False
app.start()
worker.submit.assert_called_once_with(
    "start", {"ids": ["demo-video", "demo-game", "demo-done"], "autoClaim": True}
)
app.controller = None
app.demo_mode = True
app.busy = False
app.kind.set("Tất cả")
app.render_rows()
app.render_queue()
active = demo.snapshot()
active["running"] = True
active["activeId"] = "demo-game"
active["queue"] = {"runId": 1, "owner": "demo", "ids": list(app.queue_ids), "status": "running"}
active["quests"][0].update(completed=True, claimed=True, runnable=False, status="claimed")
active["quests"][1]["status"] = "running"
app.apply_snapshot(active)
assert app.queue_ids == ["demo-video", "demo-game", "demo-done"]
assert app._pending_ids() == ["demo-game", "demo-done"]
assert app.add_button.instate(["disabled"])
assert app.clear_button.instate(["disabled"])
root.update()
assert app.focus_percent.cget("text") == "27%"
assert app.focus_time.cget("text") == "04:00 / 15:00"
app.queue_table.selection_set("demo-video")
root.update()
assert app.focus_title.cget("text") == "Chơi game cùng bạn bè", (
    "The active task should stay in focus while running"
)
app.notebook.select(app.quests_tab)
root.update()
assert app.global_stop.winfo_ismapped(), "Stop must remain visible outside the queue view"
app.notebook.select(app.queue_tab)
root.update()
assert app.stop_button.winfo_ismapped()
assert not app.global_stop.winfo_ismapped(), "Do not duplicate Stop in the same view"
active["quests"][1]["progress"] = 900
app.apply_snapshot(active)
assert app.steps.phase == 1, "Client progress alone must not confirm completion"
active["quests"][1]["progress"] = 240
app.apply_snapshot(active)
app.clear_queue()
assert len(app.queue_ids) == 3, "A running queue must not be editable"
active["running"] = False
active["activeId"] = None
active["queue"]["status"] = "finished"
for row in active["quests"][:3]:
    row.update(completed=True, claimed=True, runnable=False, status="claimed")
app.apply_snapshot(active)
assert app.queue_state == "finished" and not app._pending_ids()
app.clear_queue()
app.apply_snapshot(active)
assert not app.queue_ids, "An idle engine snapshot must not undo Clear"
# Restore the explicitly labeled preview for visual inspection.
app.apply_snapshot(demo.snapshot())
app.select_all()
app.add_selected()
app.notebook.select(app.queue_tab)
root.update()
assert root.winfo_width() >= 1040
assert not app.log_open, "Activity log should start collapsed"
toggle_log(app)
root.update()
assert app.log_text.winfo_height() > 50
toggle_log(app)
root.update()
assert app.queue_table.winfo_height() > 140
root.geometry("1040x740")
root.update()
assert (
    app.start_button.winfo_rooty() + app.start_button.winfo_height()
    <= root.winfo_rooty() + root.winfo_height()
)
assert app.queue_table.winfo_height() > 60
toggle_log(app)
root.update()
assert app.log_text.winfo_height() > 100
assert app.log_text.winfo_rooty() + app.log_text.winfo_height() <= (
    root.winfo_rooty() + root.winfo_height()
)
toggle_log(app)
show_settings(app)
root.update()
assert app.connect_button.instate(["disabled"]), "Demo must not connect to Discord"
assert app.port_entry.winfo_viewable()
assert app.help_label.winfo_rooty() + app.help_label.winfo_height() < (
    app.settings.winfo_rooty() + app.settings.winfo_height()
)
app.settings.withdraw()
assert app.port.get() == "", "Demo must not load or reuse a saved debugging port"


def show_open_port_reminder() -> socket.socket:
    """Simulate Discord still listening on the session's debugging port, then close Orbot."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    app.demo_mode = False
    app.debug_port = listener.getsockname()[1]
    app._controls()
    app.close()
    root.update()
    return listener


def dismiss_open_port_reminder(listener: socket.socket) -> None:
    app.close_cancel_button.invoke()
    root.update()
    listener.close()
    app.demo_mode = True
    app.debug_port = None
    app._controls()


listener = show_open_port_reminder()
assert str(app.debug_port) in app.footer_note.cget("text"), "Footer must show the open port"
assert app.close_dialog.winfo_exists() and app.close_confirm_button.winfo_viewable()
assert not app.closing, "Closing must wait while Discord's debugging port is open"
dismiss_open_port_reminder(listener)
assert not app.close_dialog.winfo_exists() and not app.closing
assert "minh họa" in app.footer_note.cget("text")
app._log("Thông báo lỗi kiểm thử giao diện.", "error")
assert app.activity_label.cget("fg") == COLORS["error"]
assert "Thông báo lỗi" in app.activity_text.get()
root.geometry("1360x900")
root.update()
if "--screenshot" in sys.argv:
    from PIL import ImageGrab

    active = demo.snapshot()
    active["running"] = True
    active["activeId"] = "demo-game"
    active["queue"] = {"runId": 2, "owner": "demo", "ids": list(app.queue_ids), "status": "running"}
    active["quests"][0].update(completed=True, claimed=True, runnable=False, status="claimed")
    active["quests"][1]["status"] = "running"
    app.apply_snapshot(active)
    app._log("Đã chuyển sang Quest 2 / 3 · Chơi game cùng bạn bè.")
    root.update()
    root.after(200, root.quit)
    root.mainloop()
    output_dir = Path(__file__).resolve().parents[1] / "docs" / "images"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "focus-flow.png"
    # Capture this application's HWND, never a rectangle of the user's desktop.
    ImageGrab.grab(window=int(root.frame(), 0)).save(output)
    print(f"Screenshot: {output.resolve()}")
    root.geometry("1040x740")
    root.update()
    root.after(150, root.quit)
    root.mainloop()
    assert app.stop_button.winfo_rooty() + app.stop_button.winfo_height() <= (
        app.focus_panel.winfo_rooty() + app.focus_panel.winfo_height()
    ), "Stop must fit completely in the focus panel at minimum window size"
    ImageGrab.grab(window=int(root.frame(), 0)).save(output_dir / "focus-flow-small.png")
    app.notebook.select(app.quests_tab)
    app.table.selection_remove(app.table.selection())
    root.update()
    ImageGrab.grab(window=int(root.frame(), 0)).save(output_dir / "catalog.png")
    show_settings(app)
    root.update()
    ImageGrab.grab(window=int(app.settings.frame(), 0)).save(
        output_dir / "connection-settings.png"
    )
    app.settings.withdraw()
    listener = show_open_port_reminder()
    root.after(200, root.quit)
    root.mainloop()
    ImageGrab.grab(window=int(app.close_dialog.frame(), 0)).save(output_dir / "close-reminder.png")
    dismiss_open_port_reminder(listener)
root.destroy()
print(
    "GUI smoke: queue editing/order, full-queue submission, "
    "filter/poll isolation, tabs and demo passed"
)
