"""Focus Flow layout and presentation updates, independent of Discord operations."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

from PIL import Image, ImageDraw, ImageTk

from orbot import __version__
from orbot.ui import COLORS, Banner, ProgressBar, QueueList, Steps


def label(
    parent: tk.Misc,
    text: str = "",
    *,
    color: str = "text",
    size: int = 11,
    bold: bool = False,
    bg: str = "surface",
    **options: Any,
) -> tk.Label:
    return tk.Label(
        parent,
        text=text,
        bg=COLORS[bg],
        fg=COLORS[color],
        font=("Segoe UI", size, "bold" if bold else "normal"),
        anchor="w",
        **options,
    )


def style_workspace(app: Any) -> None:
    root = app.root
    icon = Path(__file__).with_name("icon.ico")
    if icon.is_file():
        root.iconbitmap(str(icon))
    root.title(f"Orbot {__version__} · Focus Flow" + (" · DEMO" if app.demo_mode else ""))
    x = max(0, (root.winfo_screenwidth() - 1360) // 2)
    y = max(0, (root.winfo_screenheight() - 940) // 2)
    root.geometry(f"1360x900+{x}+{y}")
    root.minsize(1040, 740)
    root.configure(bg=COLORS["canvas"])
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(
        ".",
        background=COLORS["canvas"],
        foreground=COLORS["text"],
        font=("Segoe UI", 11),
    )
    style.configure("TFrame", background=COLORS["canvas"])
    style.configure("TLabel", background=COLORS["canvas"], foreground=COLORS["text"])
    style.configure(
        "TButton",
        background=COLORS["elevated"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        padding=(14, 8),
        borderwidth=1,
        relief="flat",
        focusthickness=2,
        focuscolor=COLORS["primary"],
    )
    style.map(
        "TButton",
        background=[("active", "#303D4F")],
        bordercolor=[("focus", COLORS["primary"])],
        foreground=[("disabled", "#8591A2")],
    )
    style.configure(
        "Primary.TButton",
        background=COLORS["primary"],
        foreground=COLORS["on-primary"],
        font=("Segoe UI", 10, "bold"),
        bordercolor=COLORS["primary"],
        lightcolor=COLORS["primary"],
        darkcolor=COLORS["primary"],
    )
    style.map(
        "Primary.TButton",
        background=[("disabled", COLORS["surface"]), ("active", COLORS["hover"])],
        foreground=[("disabled", "#8591A2")],
        bordercolor=[("disabled", COLORS["border"]), ("focus", COLORS["text"])],
    )
    style.configure(
        "Stop.TButton",
        foreground=COLORS["error"],
        bordercolor=COLORS["error"],
        lightcolor=COLORS["error"],
        darkcolor=COLORS["error"],
    )
    style.configure(
        "Nav.TButton",
        background=COLORS["canvas"],
        borderwidth=0,
        padding=(16, 12),
        bordercolor=COLORS["canvas"],
        lightcolor=COLORS["canvas"],
        darkcolor=COLORS["canvas"],
        foreground=COLORS["muted"],
    )
    style.configure("Active.Nav.TButton", foreground=COLORS["primary"])
    style.configure("Compact.TButton", padding=(10, 5), font=("Segoe UI", 10))
    style.map("Nav.TButton", background=[("active", COLORS["surface"])])
    style.configure(
        "Focus.TNotebook",
        background=COLORS["canvas"],
        borderwidth=0,
        bordercolor=COLORS["canvas"],
        lightcolor=COLORS["canvas"],
        darkcolor=COLORS["canvas"],
    )
    style.layout("Focus.TNotebook.Tab", [])
    style.configure(
        "Treeview",
        background=COLORS["surface"],
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
        rowheight=54,
        borderwidth=0,
        bordercolor=COLORS["surface"],
        lightcolor=COLORS["surface"],
        darkcolor=COLORS["surface"],
        font=("Segoe UI", 11),
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["elevated"],
        foreground=COLORS["muted"],
        relief="flat",
        padding=(12, 12),
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "Treeview",
        background=[("selected", "#3A3B3D")],
        foreground=[("selected", COLORS["primary"])],
    )
    style.configure(
        "TEntry",
        fieldbackground=COLORS["canvas"],
        foreground=COLORS["text"],
        padding=9,
        insertcolor=COLORS["text"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
    )
    style.configure(
        "TCombobox",
        fieldbackground=COLORS["surface"],
        background=COLORS["elevated"],
        foreground=COLORS["text"],
        padding=7,
        arrowcolor=COLORS["muted"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLORS["surface"])],
        foreground=[("readonly", COLORS["text"])],
    )
    style.configure(
        "TCheckbutton",
        background=COLORS["elevated"],
        foreground=COLORS["text"],
        padding=(0, 5),
        indicatorbackground=COLORS["canvas"],
        indicatorforeground=COLORS["primary"],
    )
    style.map("TCheckbutton", background=[("active", COLORS["elevated"])])
    style.configure(
        "TProgressbar",
        background=COLORS["primary"],
        troughcolor=COLORS["border"],
        borderwidth=0,
        lightcolor=COLORS["primary"],
        darkcolor=COLORS["primary"],
    )
    style.configure(
        "Vertical.TScrollbar",
        background=COLORS["border"],
        troughcolor=COLORS["surface"],
        borderwidth=0,
        arrowcolor=COLORS["muted"],
        bordercolor=COLORS["surface"],
        lightcolor=COLORS["surface"],
        darkcolor=COLORS["surface"],
    )


def style_switch(app: Any) -> None:
    style = ttk.Style(app.root)
    app.switch_images = []
    for fill, on in ((COLORS["border"], False), (COLORS["primary"], True), ("#77634B", True)):
        image = Image.new("RGBA", (104, 56))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((0, 0, 103, 55), radius=28, fill=fill)
        x = 54 if on else 6
        draw.ellipse((x, 6, x + 44, 50), fill=COLORS["text"])
        app.switch_images.append(
            ImageTk.PhotoImage(image.resize((52, 28), Image.Resampling.LANCZOS), master=app.root)
        )
    style.element_create(
        "Focus.Switch",
        "image",
        app.switch_images[0],
        ("selected", "disabled", app.switch_images[2]),
        ("selected", app.switch_images[1]),
        width=62,
        sticky="w",
    )
    style.layout(
        "Switch.TCheckbutton",
        [
            (
                "Checkbutton.padding",
                {
                    "sticky": "nswe",
                    "children": [
                        ("Focus.Switch", {"side": "left", "sticky": "w"}),
                        (
                            "Checkbutton.focus",
                            {
                                "side": "left",
                                "sticky": "w",
                                "children": [
                                    ("Checkbutton.label", {"sticky": "nswe"}),
                                ],
                            },
                        ),
                    ],
                },
            ),
        ],
    )
    style.configure("Switch.TCheckbutton", padding=(0, 5))
    style.map("Switch.TCheckbutton", foreground=[("disabled", COLORS["muted"])])
    style.map(
        "Stop.TButton",
        foreground=[("disabled", "#C78D93")],
        bordercolor=[("disabled", "#765159"), ("focus", COLORS["error"])],
    )


def notice(parent: tk.Misc, title: str, body: str, *, wrap: int = 430) -> tk.Frame:
    """An amber-edged callout for security guidance."""
    frame = tk.Frame(parent, bg=COLORS["elevated"])
    tk.Frame(frame, bg=COLORS["warning"], width=3).pack(side="left", fill="y")
    inner = tk.Frame(frame, bg=COLORS["elevated"], padx=14, pady=11)
    inner.pack(side="left", fill="both", expand=True)
    label(inner, title, color="warning", size=10, bold=True, bg="elevated").pack(fill="x")
    label(
        inner,
        body,
        size=10,
        bg="elevated",
        wraplength=wrap,
        justify="left",
    ).pack(fill="x", pady=(4, 0))
    return frame


def show_close_reminder(app: Any, port: int, on_confirm: Any) -> None:
    """Explain that Discord keeps its debugging port open after Orbot closes."""
    existing = getattr(app, "close_dialog", None)
    if existing is not None and existing.winfo_exists():
        existing.deiconify()
        existing.lift()
        return
    dialog = tk.Toplevel(app.root)
    app.close_dialog = dialog
    dialog.title("Đóng Orbot")
    dialog.configure(bg=COLORS["surface"])
    dialog.resizable(False, False)
    dialog.transient(app.root)
    content = tk.Frame(dialog, bg=COLORS["surface"], padx=28, pady=24)
    content.pack(fill="both", expand=True)
    label(content, "Discord vẫn đang mở cổng gỡ lỗi", size=17, bold=True).pack(fill="x")
    label(
        content,
        f"Cổng {port} chỉ đóng khi Discord thoát hẳn. Trong lúc đó, chương trình khác "
        "trên máy cũng có thể điều khiển Discord.",
        color="muted",
        wraplength=480,
        justify="left",
    ).pack(fill="x", pady=(8, 18))
    notice(
        content,
        "Sau khi đóng Orbot",
        "1. Chuột phải biểu tượng Discord ở khay hệ thống → Thoát Discord.\n"
        "2. Mở lại Discord như bình thường, không qua Orbot.",
        wrap=450,
    ).pack(fill="x")
    buttons = tk.Frame(content, bg=COLORS["surface"])
    buttons.pack(fill="x", pady=(22, 0))

    def cancel(_event: object = None) -> str:
        dialog.destroy()
        return "break"

    def confirm(_event: object = None) -> str:
        dialog.destroy()
        on_confirm()
        return "break"

    app.close_confirm_button = ttk.Button(
        buttons, text="Đã hiểu, đóng Orbot", style="Primary.TButton", command=confirm
    )
    app.close_confirm_button.pack(side="right")
    app.close_cancel_button = ttk.Button(buttons, text="Quay lại", command=cancel)
    app.close_cancel_button.pack(side="right", padx=(0, 10))
    dialog.protocol("WM_DELETE_WINDOW", cancel)
    dialog.bind("<Escape>", cancel)
    dialog.bind("<Return>", confirm)
    dialog.update_idletasks()
    root = app.root
    x = root.winfo_rootx() + max(0, (root.winfo_width() - dialog.winfo_reqwidth()) // 2)
    y = root.winfo_rooty() + max(0, (root.winfo_height() - dialog.winfo_reqheight()) // 3)
    dialog.geometry(f"+{x}+{y}")
    app.close_confirm_button.focus_set()


def toggle_log(app: Any) -> None:
    if app.log_open:
        app.notebook.select(app.log_return_tab)
    else:
        app.log_return_tab = app.notebook.select()
        app.notebook.select(app.log_tab)
    app._selection()


def show_settings(app: Any) -> None:
    app.settings.deiconify()
    app.settings.lift()
    app.settings.focus_set()


def build_settings(app: Any) -> None:
    app.settings = tk.Toplevel(app.root)
    app.settings.withdraw()
    app.settings.title("Kết nối Discord · Orbot")
    app.settings.configure(bg=COLORS["surface"])
    app.settings.geometry("540x520")
    app.settings.resizable(False, False)
    app.settings.transient(app.root)
    app.settings.protocol("WM_DELETE_WINDOW", app.settings.withdraw)
    app.settings.bind("<Escape>", lambda _event: (app.settings.withdraw(), "break")[1])
    content = tk.Frame(app.settings, bg=COLORS["surface"], padx=26, pady=24)
    content.pack(fill="both", expand=True)
    label(content, "Kết nối Discord", size=20, bold=True).pack(fill="x")
    label(
        content,
        "Dùng phiên đã đăng nhập trên Discord Desktop.",
        color="muted",
    ).pack(fill="x", pady=(6, 20))
    port_row = tk.Frame(content, bg=COLORS["surface"])
    port_row.pack(fill="x")
    label(port_row, "Cổng cục bộ", color="muted").pack(side="left", padx=(0, 16))
    app.port_entry = ttk.Entry(port_row, textvariable=app.port, width=8)
    app.port_entry.pack(side="left")
    label(port_row, "Tự chọn ngẫu nhiên khi mở Discord", color="muted", size=9).pack(
        side="left", padx=(12, 0)
    )
    notice(
        content,
        "Lưu ý bảo mật",
        "Khi Discord mở cổng này, chương trình khác trên máy cũng có thể điều khiển "
        "Discord. Dùng xong, hãy thoát Discord ở khay hệ thống rồi mở lại như bình "
        "thường để đóng cổng.",
    ).pack(fill="x", pady=(16, 0))
    buttons = tk.Frame(content, bg=COLORS["surface"])
    buttons.pack(fill="x", pady=18)
    app.launch_button = ttk.Button(buttons, text="Mở Discord", command=app.open_discord)
    app.launch_button.pack(side="left")
    app.connect_button = ttk.Button(
        buttons,
        text="Kết nối",
        style="Primary.TButton",
        command=app.connect,
    )
    app.connect_button.pack(side="left", padx=8)
    app.disconnect_button = ttk.Button(
        buttons,
        text="Ngắt kết nối",
        command=app.disconnect,
    )
    app.disconnect_button.pack(side="left")
    app.help_label = label(
        content,
        color="muted",
        textvariable=app.setup_text,
        wraplength=470,
        justify="left",
    )
    app.help_label.pack(fill="x", pady=(0, 12))
    ttk.Button(content, text="Đóng", command=app.settings.withdraw).pack(anchor="e")


def build_workspace(app: Any) -> None:
    root = app.root
    style_switch(app)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(2, weight=1)
    top = tk.Frame(root, bg=COLORS["canvas"], padx=26, pady=10)
    top.grid(row=0, column=0, sticky="ew")
    label(top, "Orbot", size=21, bold=True, bg="canvas").pack(side="left")
    label(top, "Discord Quests", color="muted", size=10, bg="canvas").pack(
        side="left",
        padx=(14, 32),
    )
    app.quest_nav = ttk.Button(
        top,
        text="Quests",
        style="Nav.TButton",
        command=lambda: app.notebook.select(app.quests_tab),
    )
    app.quest_nav.pack(side="left")
    app.queue_nav = ttk.Button(
        top,
        text="Hàng đợi  0",
        style="Active.Nav.TButton",
        command=lambda: app.notebook.select(app.queue_tab),
    )
    app.queue_nav.pack(side="left")
    app.log_nav = ttk.Button(
        top,
        text="Nhật ký",
        style="Nav.TButton",
        command=lambda: toggle_log(app),
    )
    app.log_nav.pack(side="left")
    app.settings_button = ttk.Button(
        top,
        text="Cài đặt",
        command=lambda: show_settings(app),
    )
    app.settings_button.pack(side="right", padx=(16, 0))
    account = tk.Frame(top, bg=COLORS["canvas"])
    account.pack(side="right")
    app.connection_badge = label(
        account,
        "●  Chưa kết nối",
        color="muted",
        size=10,
        bg="canvas",
    )
    app.connection_badge.pack(anchor="w")
    app.account_label = label(
        account,
        "Discord Desktop",
        color="muted",
        size=9,
        bg="canvas",
    )
    app.account_label.pack(anchor="w")
    tk.Frame(root, bg=COLORS["border"], height=1).grid(row=1, column=0, sticky="new")

    shell = tk.Frame(root, bg=COLORS["canvas"], padx=24, pady=18)
    shell.grid(row=2, column=0, sticky="nsew")
    shell.columnconfigure(0, weight=1)
    shell.rowconfigure(1, weight=1)
    header = tk.Frame(shell, bg=COLORS["canvas"])
    header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
    heading = tk.Frame(header, bg=COLORS["canvas"])
    heading.pack(side="left")
    app.page_title = label(
        heading,
        "Hàng đợi của bạn",
        size=22,
        bold=True,
        bg="canvas",
    )
    app.page_title.pack(anchor="w")
    app.page_subtitle = label(heading, color="muted", bg="canvas")
    app.page_subtitle.pack(anchor="w", pady=(4, 0))
    total = tk.Frame(header, bg=COLORS["canvas"])
    total.pack(side="right")
    app.reward_total = label(total, size=17, bold=True, color="primary", bg="canvas")
    app.reward_total.pack(anchor="e")
    label(total, "Tổng thưởng cơ bản trong hàng đợi", color="muted", size=9, bg="canvas").pack(
        anchor="e",
        pady=(4, 0),
    )

    app.notebook = ttk.Notebook(shell, style="Focus.TNotebook")
    app.notebook.grid(row=1, column=0, sticky="nsew")
    app.quests_tab = tk.Frame(app.notebook, bg=COLORS["canvas"])
    app.queue_tab = tk.Frame(app.notebook, bg=COLORS["canvas"])
    app.notebook.add(app.quests_tab, text="Quests")
    app.notebook.add(app.queue_tab, text="Hàng đợi")
    app.notebook.select(app.queue_tab)
    app.notebook.bind("<<NotebookTabChanged>>", lambda _event: app._selection())
    build_catalog(app)
    build_queue(app)
    build_log(app, shell)
    footer = tk.Frame(root, bg=COLORS["canvas"], padx=26, pady=8)
    footer.grid(row=3, column=0, sticky="ew")
    label(
        footer,
        f"Orbot {__version__}  ·  Focus Flow",
        color="muted",
        size=9,
        bg="canvas",
    ).pack(side="left")
    app.footer_note = label(footer, color="muted", size=9, bg="canvas")
    app.footer_note.pack(side="right")
    build_settings(app)
    app._controls()


def build_catalog(app: Any) -> None:
    tab = app.quests_tab
    tab.columnconfigure(0, weight=1)
    tab.rowconfigure(1, weight=1)
    toolbar = tk.Frame(tab, bg=COLORS["canvas"])
    toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 14))
    app.count_label = label(toolbar, "Quests thưởng Orbs", bold=True, bg="canvas")
    app.count_label.pack(side="left")
    app.refresh_button = ttk.Button(toolbar, text="Quét lại · F5", command=app.refresh)
    app.refresh_button.pack(side="right", padx=(12, 0))
    app.filter = ttk.Combobox(
        toolbar,
        textvariable=app.kind,
        state="readonly",
        width=14,
        values=["Tất cả", "Video", "Chơi game"],
    )
    app.filter.pack(side="right")
    app.filter.bind("<<ComboboxSelected>>", lambda _event: app.render_rows())
    frame = tk.Frame(tab, bg=COLORS["surface"])
    frame.grid(row=1, column=0, sticky="nsew")
    columns = ("name", "kind", "orbs", "progress", "status")
    app.table = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
    for name, title, width, stretch in (
        ("name", "Nhiệm vụ", 310, True),
        ("kind", "Loại", 110, False),
        ("orbs", "Orbs cơ bản", 110, False),
        ("progress", "Tiến độ", 100, False),
        ("status", "Trạng thái", 220, True),
    ):
        app.table.heading(name, text=title)
        app.table.column(name, width=width, minwidth=75, stretch=stretch)
    app.table.tag_configure("success", foreground=COLORS["success"])
    app.table.tag_configure("error", foreground=COLORS["error"])
    app.table.tag_configure("muted", foreground=COLORS["muted"])
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=app.table.yview)
    app.table.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    app.table.pack(side="left", fill="both", expand=True)
    app.table.bind("<<TreeviewSelect>>", lambda _event: app._selection())
    app.table.bind("<Control-a>", app._select_all_key)
    app.empty_label = label(
        app.table,
        "Kết nối Discord để tải các Quest hiện có.",
        color="muted",
    )
    app.empty_label.place(relx=0.5, rely=0.5, anchor="center")
    actions = tk.Frame(tab, bg=COLORS["canvas"], pady=14)
    actions.grid(row=2, column=0, sticky="ew")
    app.select_button = ttk.Button(
        actions,
        text="Chọn tất cả có thể chạy",
        command=app.select_all,
    )
    app.select_button.pack(side="left")
    app.add_button = ttk.Button(
        actions,
        text="Thêm vào hàng đợi →",
        command=app.add_selected,
        style="Primary.TButton",
    )
    app.add_button.pack(side="right")
    label(
        actions,
        "Ctrl / Shift để chọn nhiều Quest",
        color="muted",
        size=9,
        bg="canvas",
    ).pack(side="left", padx=16)


def build_queue(app: Any) -> None:
    tab = app.queue_tab
    tab.columnconfigure(0, weight=34, minsize=330, uniform="workspace")
    tab.columnconfigure(1, weight=66, minsize=590, uniform="workspace")
    tab.rowconfigure(0, weight=1)
    left = tk.Frame(
        tab,
        bg=COLORS["surface"],
        highlightbackground=COLORS["border"],
        highlightthickness=1,
    )
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
    left.columnconfigure(0, weight=1)
    left.rowconfigure(1, weight=1)
    label(left, "Thứ tự thực hiện", bold=True, size=12).grid(
        row=0,
        column=0,
        sticky="ew",
        padx=20,
        pady=(20, 12),
    )
    list_frame = tk.Frame(left, bg=COLORS["surface"])
    list_frame.grid(row=1, column=0, sticky="nsew", padx=10)
    list_frame.columnconfigure(0, weight=1)
    list_frame.rowconfigure(0, weight=1)
    app.queue_table = QueueList(list_frame)
    app.queue_table.grid(row=0, column=0, sticky="nsew")
    scroll = ttk.Scrollbar(list_frame, orient="vertical", command=app.queue_table.yview)
    scroll.grid(row=0, column=1, sticky="ns")

    def scroll_queue(first: str, last: str) -> None:
        scroll.set(first, last)
        if float(first) <= 0 and float(last) >= 1:
            scroll.grid_remove()
        else:
            scroll.grid()

    app.queue_table.configure(yscrollcommand=scroll_queue)
    app.queue_table.bind("<<TreeviewSelect>>", lambda _event: app._selection())
    app.queue_table.bind("<Alt-Up>", lambda _event: app.move_queue(-1))
    app.queue_table.bind("<Alt-Down>", lambda _event: app.move_queue(1))
    app.queue_table.bind("<Delete>", lambda _event: app.remove_selected())
    app.queue_empty_label = label(
        app.queue_table,
        "Hàng đợi đang trống.\nThêm Quest để bắt đầu.",
        color="muted",
        justify="center",
    )
    app.queue_empty_label.place(relx=0.5, rely=0.4, anchor="center")
    controls = tk.Frame(left, bg=COLORS["surface"], padx=16, pady=14)
    controls.grid(row=2, column=0, sticky="ew")
    app.queue_hint = label(controls, "Sắp xếp trước khi chạy.", color="muted", size=9)
    app.queue_hint.pack(anchor="w", pady=(0, 10))
    edit = tk.Frame(controls, bg=COLORS["surface"])
    edit.pack(fill="x")
    app.up_button = ttk.Button(
        edit,
        text="↑",
        width=3,
        style="Compact.TButton",
        command=lambda: app.move_queue(-1),
    )
    app.up_button.pack(side="left")
    app.down_button = ttk.Button(
        edit,
        text="↓",
        width=3,
        style="Compact.TButton",
        command=lambda: app.move_queue(1),
    )
    app.down_button.pack(side="left", padx=6)
    app.remove_button = ttk.Button(
        edit,
        text="Bỏ Quest",
        style="Compact.TButton",
        command=app.remove_selected,
    )
    app.remove_button.pack(side="left")
    app.clear_button = ttk.Button(
        edit,
        text="Xóa hết",
        style="Compact.TButton",
        command=app.clear_queue,
    )
    app.clear_button.pack(side="right")
    ttk.Button(
        controls,
        text="Xem danh sách Quests →",
        command=lambda: app.notebook.select(app.quests_tab),
    ).pack(fill="x", pady=(12, 0))

    focus = tk.Frame(
        tab,
        bg=COLORS["elevated"],
        padx=24,
        pady=20,
        highlightbackground=COLORS["border"],
        highlightthickness=1,
    )
    focus.grid(row=0, column=1, sticky="nsew")
    app.focus_panel = focus
    focus.columnconfigure(0, weight=1)
    focus.rowconfigure(1, weight=1, minsize=60)
    intro = tk.Frame(focus, bg=COLORS["elevated"])
    intro.grid(row=0, column=0, sticky="ew", pady=(0, 14))
    app.focus_state = label(
        intro,
        "SẴN SÀNG",
        color="primary",
        size=10,
        bold=True,
        bg="elevated",
    )
    app.focus_state.pack(anchor="w")
    app.focus_title = label(
        intro,
        "Chọn Quest để bắt đầu",
        size=21,
        bold=True,
        bg="elevated",
        justify="left",
        wraplength=620,
    )
    app.focus_title.pack(anchor="w", pady=(7, 4))
    app.focus_meta = label(
        intro,
        "Mọi nhiệm vụ, trong một hàng đợi rõ ràng.",
        color="muted",
        bg="elevated",
    )
    app.focus_meta.pack(anchor="w")
    app.banner = Banner(focus)
    app.banner.grid(row=1, column=0, sticky="nsew", pady=(0, 16))
    progress_area = tk.Frame(focus, bg=COLORS["elevated"])
    progress_area.grid(row=2, column=0, sticky="ew")
    percent_row = tk.Frame(progress_area, bg=COLORS["elevated"])
    percent_row.pack(fill="x")
    app.focus_percent = label(percent_row, "0%", size=26, bold=True, bg="elevated")
    app.focus_percent.pack(side="left")
    timing = tk.Frame(percent_row, bg=COLORS["elevated"])
    timing.pack(side="right")
    app.focus_time = label(timing, "00:00 / 00:00", size=15, bg="elevated")
    app.focus_time.pack(anchor="e")
    label(timing, "Tiến độ / Mục tiêu", color="muted", size=9, bg="elevated").pack(anchor="e")
    app.progress = ProgressBar(progress_area)
    app.progress.pack(fill="x", pady=(8, 10))
    app.focus_detail = label(
        progress_area,
        color="muted",
        size=9,
        bg="elevated",
        textvariable=app.detail_text,
        wraplength=620,
        justify="left",
    )
    app.focus_detail.pack(fill="x")
    app.steps = Steps(focus)
    app.steps.grid(row=3, column=0, sticky="ew", pady=(12, 8))
    actions = tk.Frame(focus, bg=COLORS["elevated"])
    actions.grid(row=4, column=0, sticky="ew", pady=(8, 0))
    tk.Frame(actions, height=1, bg=COLORS["border"]).pack(fill="x", pady=(0, 10))
    app.action_row = tk.Frame(actions, bg=COLORS["elevated"])
    app.action_row.pack(fill="x")
    app.claim_check = ttk.Checkbutton(
        app.action_row,
        text="Tự nhận Orbs",
        style="Switch.TCheckbutton",
        variable=app.auto_claim,
        command=app.render_queue,
    )
    app.claim_check.pack(side="left")
    app.start_button = ttk.Button(
        app.action_row,
        text="Chạy hàng đợi →",
        style="Primary.TButton",
        command=app.start,
    )
    app.start_button.pack(side="right")
    app.stop_button = ttk.Button(
        app.action_row,
        text="■  Dừng   Esc",
        style="Stop.TButton",
        command=app.stop,
    )

    def resize_focus(event: tk.Event[Any]) -> None:
        width = max(180, event.width - 52)
        app.focus_title.configure(wraplength=width)
        app.focus_detail.configure(wraplength=width)
        if event.height < 490:
            app.banner.grid_remove()
            focus.rowconfigure(1, minsize=0)
        else:
            app.banner.grid()
            focus.rowconfigure(1, minsize=60)

    focus.bind("<Configure>", resize_focus)


def build_log(app: Any, shell: tk.Frame) -> None:
    app.log_open = False
    app.log_panel = tk.Frame(
        shell,
        bg=COLORS["surface"],
        highlightbackground=COLORS["border"],
        highlightthickness=1,
    )
    app.log_panel.grid(row=2, column=0, sticky="ew", pady=(14, 0))
    bar = tk.Frame(app.log_panel, bg=COLORS["surface"], padx=8, pady=3)
    bar.pack(fill="x")
    app.log_toggle = ttk.Button(
        bar,
        text="›  Nhật ký phiên",
        style="Nav.TButton",
        command=lambda: toggle_log(app),
    )
    app.log_toggle.pack(side="left")
    app.global_stop = ttk.Button(
        bar,
        text="■  Dừng   Esc",
        style="Stop.TButton",
        command=app.stop,
    )
    app.activity_text = tk.StringVar(value="Sẵn sàng.")
    app.activity_label = label(
        bar,
        textvariable=app.activity_text,
        color="muted",
        size=10,
        wraplength=840,
    )
    app.activity_label.pack(side="left", padx=16, fill="x", expand=True)
    app.log_tab = tk.Frame(app.notebook, bg=COLORS["surface"])
    app.notebook.add(app.log_tab, text="Nhật ký")
    app.log_return_tab = str(app.queue_tab)
    app.log_body = tk.Frame(app.log_tab, bg=COLORS["surface"], padx=18, pady=16)
    app.log_body.pack(fill="both", expand=True)
    ttk.Button(
        app.log_body,
        text="Lưu nhật ký",
        command=app.save_log,
    ).pack(anchor="e", pady=(0, 6))
    app.log_text = tk.Text(
        app.log_body,
        height=4,
        wrap="word",
        bg=COLORS["canvas"],
        fg=COLORS["muted"],
        relief="flat",
        padx=12,
        pady=10,
        font=("Consolas", 10),
        state="disabled",
        insertbackground=COLORS["text"],
    )
    scroll = ttk.Scrollbar(app.log_body, orient="vertical", command=app.log_text.yview)
    scroll.pack(side="right", fill="y")
    app.log_text.configure(yscrollcommand=scroll.set)
    app.log_text.pack(fill="both", expand=True)
    for tag in ("success", "error", "warning"):
        app.log_text.tag_configure(tag, foreground=COLORS[tag])


def sync_controls(app: Any) -> None:
    queued_view = app.notebook.select() == str(app.queue_tab)
    app.log_open = app.notebook.select() == str(app.log_tab)
    app.quest_nav.configure(
        style="Active.Nav.TButton"
        if app.notebook.select() == str(app.quests_tab)
        else "Nav.TButton",
    )
    app.log_nav.configure(style="Active.Nav.TButton" if app.log_open else "Nav.TButton")
    app.log_toggle.configure(text=("‹  Quay lại" if app.log_open else "›  Nhật ký phiên"))
    app.queue_nav.configure(
        text=f"Hàng đợi  {len(app.queue_ids)}",
        style="Active.Nav.TButton" if queued_view else "Nav.TButton",
    )
    app.settings_button.configure(
        text="Cài đặt" if app.connected else "Kết nối Discord",
        style="TButton" if app.connected else "Primary.TButton",
    )
    if app.running:
        app.start_button.pack_forget()
        app.stop_button.pack(side="right")
    else:
        app.stop_button.pack_forget()
        app.start_button.pack(side="right")
    if app.running and not queued_view:
        app.global_stop.pack(side="right", padx=(12, 0))
    else:
        app.global_stop.pack_forget()
    app.queue_hint.configure(
        text="Có thể sắp xếp lại sau khi dừng."
        if app.running
        else "Ctrl / Shift chọn nhiều · ↑ ↓ di chuyển",
    )
    claimed = sum(bool(app.rows.get(ident, {}).get("claimed")) for ident in app.queue_ids)
    title = {
        "running": "Hàng đợi đang chạy",
        "finished": "Đã xử lý hết hàng đợi",
        "stopped": "Hàng đợi đã dừng",
        "blocked": "Hàng đợi cần kiểm tra",
    }.get(app.queue_state, "Hàng đợi của bạn")
    app.page_title.configure(
        text="Nhật ký phiên" if app.log_open else title if queued_view else "Quests của bạn",
    )
    app.page_subtitle.configure(
        text="Theo dõi hoạt động và lưu nhật ký khi cần."
        if app.log_open
        else f"{claimed} / {len(app.queue_ids)} Quest đã nhận thưởng"
        if queued_view and app.queue_ids
        else "Thêm nhiệm vụ từ danh sách Quests để bắt đầu."
        if queued_view
        else "Chọn nhiệm vụ và thêm vào hàng đợi theo thứ tự bạn muốn.",
    )
    reward = sum(app.rows.get(ident, {}).get("orbs", 0) for ident in app.queue_ids)
    app.reward_total.configure(text=f"{reward:,} Orbs cơ bản".replace(",", "."))
    app.connection_badge.configure(
        text="●  Dữ liệu minh họa"
        if app.demo_mode
        else "●  Discord cần kiểm tra"
        if app.blocked
        else "●  Đang kết nối…"
        if app.busy and not app.connected
        else "●  Discord đã kết nối"
        if app.connected
        else "○  Chưa kết nối Discord",
        fg=COLORS["primary"]
        if app.demo_mode or app.busy or app.blocked
        else COLORS["success"]
        if app.connected
        else COLORS["muted"],
    )
    account = "Tài khoản demo" if app.demo_mode else app.account_name
    app.account_label.configure(text=account[:28] if app.connected else "Discord Desktop")
    if app.demo_mode:
        note, ink = "Dữ liệu minh họa · Không chạy Quest thật", "primary"
    elif app.connected and app.debug_port:
        note = f"Cổng gỡ lỗi {app.debug_port} đang mở · Thoát Discord khi dùng xong"
        ink = "warning"
    else:
        note, ink = "Phiên đăng nhập giữ trong Discord", "muted"
    app.footer_note.configure(text=note, fg=COLORS[ink])
    app.queue_table.set_active(app.active_id)


def sync_focus(app: Any, row: dict[str, Any] | None) -> None:
    if not row:
        app.focus_title.configure(
            text="Chọn Quest để bắt đầu" if app.connected else "Kết nối Discord để bắt đầu",
        )
        app.focus_state.configure(text="HÀNG ĐỢI TRỐNG", fg=COLORS["primary"])
        app.focus_meta.configure(text="Thêm nhiệm vụ, sắp xếp và chạy tuần tự.")
        app.focus_percent.configure(text="0%")
        app.focus_time.configure(text="00:00 / 00:00")
        app.steps.set_phase(-1)
        return
    status = row.get("status", "ready")
    names = {
        "ready": "SẴN SÀNG",
        "queued": "TRONG HÀNG ĐỢI",
        "running": "ĐANG XỬ LÝ",
        "claiming": "ĐANG NHẬN ORBS",
        "completed": "HOÀN THÀNH · CHỜ NHẬN",
        "claimed": "ĐÃ NHẬN THƯỞNG",
        "unsupported": "CHƯA HỖ TRỢ",
        "failed": "CÓ LỖI",
        "stopped": "ĐÃ DỪNG",
        "claim_required": "CẦN NHẬN TRONG DISCORD",
    }
    ink = "error" if status == "failed" else "success" if row.get("claimed") else "primary"
    app.focus_state.configure(text=names.get(status, status.upper()), fg=COLORS[ink])
    app.focus_title.configure(text=row["name"])
    kind = {"video": "Video", "game": "Chơi game"}.get(row["kind"], "Loại khác")
    app.focus_meta.configure(text=f"{kind}  ·  {row['orbs']:,} Orbs cơ bản".replace(",", "."))
    target = max(1, row.get("target", 1))
    value = target if row.get("completed") else max(0, row.get("progress", 0))
    app.focus_percent.configure(text=f"{min(100, round(100 * value / target))}%")
    if row["kind"] in {"video", "game"}:

        def clock(seconds: float) -> str:
            seconds = int(seconds)
            return f"{seconds // 60:02d}:{seconds % 60:02d}"

        app.focus_time.configure(text=f"{clock(value)} / {clock(target)}")
    else:
        app.focus_time.configure(text=f"{value:g} / {target:g}")
    phase = (
        3
        if row.get("claimed")
        else 2
        if row.get("completed")
        else 1
        if (status == "running" or value > 0)
        else 0
    )
    app.steps.set_phase(phase)
