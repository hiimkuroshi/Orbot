"""Presentation widgets for the Focus Flow desktop workspace."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, ImageTk

COLORS = {
    "primary": "#FFCB83",
    "on-primary": "#221B12",
    "hover": "#FFDAA6",
    "canvas": "#151A23",
    "surface": "#1C2330",
    "elevated": "#242E3C",
    "text": "#F5F7FA",
    "muted": "#B0BAC8",
    "border": "#374455",
    "success": "#83D6AA",
    "error": "#FF9298",
    "warning": "#FFCB83",
}


def rounded(canvas: tk.Canvas, box: tuple[int, int, int, int], color: str) -> None:
    x1, y1, x2, y2 = box
    r = 8
    canvas.create_polygon(
        x1 + r,
        y1,
        x2 - r,
        y1,
        x2,
        y1,
        x2,
        y1 + r,
        x2,
        y2 - r,
        x2,
        y2,
        x2 - r,
        y2,
        x1 + r,
        y2,
        x1,
        y2,
        x1,
        y2 - r,
        x1,
        y1 + r,
        x1,
        y1,
        smooth=True,
        fill=color,
        outline="",
    )


class QueueList(tk.Canvas):
    """Ordered, keyboard-selectable queue exposing the item API used by the app."""

    row_height = 116

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(
            master,
            bg=COLORS["surface"],
            highlightthickness=1,
            highlightbackground=COLORS["surface"],
            highlightcolor=COLORS["primary"],
            takefocus=True,
            width=300,
            height=240,
        )
        self.entries: dict[str, tuple[Any, ...]] = {}
        self.order: list[str] = []
        self.selected: tuple[str, ...] = ()
        self.selection_anchor: str | None = None
        self.active_id: str | None = None
        self.redraw_id: str | None = None
        self.title_font = tkfont.Font(self, family="Segoe UI", size=11, weight="bold")
        self.bind("<Configure>", self._schedule)
        self.bind("<Button-1>", self._click)
        self.bind("<Up>", lambda event: self._key(event, -1))
        self.bind("<Down>", lambda event: self._key(event, 1))
        self.bind("<Home>", lambda event: self._key(event, -len(self.order)))
        self.bind("<End>", lambda event: self._key(event, len(self.order)))
        self.bind("<Control-a>", self._select_all)
        self.bind("<MouseWheel>", self._wheel)

    def _wheel(self, event: tk.Event[Any]) -> str:
        self.yview_scroll(-int(event.delta / 120), "units")
        return "break"

    def _select_all(self, _event: tk.Event[Any]) -> str:
        self.selection_set(self.order)
        return "break"

    def _key(self, event: tk.Event[Any], offset: int) -> str:
        if self.order:
            current = self.selected[-1] if self.selected else self.order[0]
            index = min(len(self.order) - 1, max(0, self.order.index(current) + offset))
            ident = self.order[index]
            self._choose(ident, bool(int(event.state) & 4), bool(int(event.state) & 1))
            self.see(ident)
        return "break"

    def _click(self, event: tk.Event[Any]) -> None:
        self.focus_set()
        index = int(self.canvasy(event.y)) // self.row_height
        if 0 <= index < len(self.order):
            self._choose(self.order[index], bool(int(event.state) & 4), bool(int(event.state) & 1))

    def _choose(self, ident: str, control: bool, shift: bool) -> None:
        if shift and self.selection_anchor in self.order:
            first, last = sorted((self.order.index(self.selection_anchor), self.order.index(ident)))
            self.selection_set(self.order[first : last + 1])
        elif control:
            self.selection_set(
                [value for value in self.selected if value != ident]
                if ident in self.selected
                else [*self.selected, ident]
            )
            self.selection_anchor = ident
        else:
            self.selection_set(ident)
            self.selection_anchor = ident

    def get_children(self) -> tuple[str, ...]:
        return tuple(self.order)

    def exists(self, ident: str) -> bool:
        return ident in self.entries

    def selection(self) -> tuple[str, ...]:
        return self.selected

    def selection_set(self, values: str | list[str] | tuple[str, ...]) -> None:
        selected = (values,) if isinstance(values, str) else tuple(values)
        selected = tuple(ident for ident in selected if ident in self.entries)
        if selected != self.selected:
            self.selected = selected
            self._schedule()
            self.event_generate("<<TreeviewSelect>>", when="tail")

    def insert(  # type: ignore[override]  # Queue item API, not Canvas text insertion.
        self,
        _parent: str,
        _index: str,
        *,
        iid: str,
        values: tuple[Any, ...],
        tags: tuple[str, ...] = (),
    ) -> None:
        self.entries[iid] = values
        self.order.append(iid)
        self._schedule()

    def item(
        self,
        ident: str,
        *,
        values: tuple[Any, ...],
        tags: tuple[str, ...] = (),
    ) -> None:
        if self.entries[ident] != values:
            self.entries[ident] = values
            self._schedule()

    def delete(self, ident: str) -> None:  # type: ignore[override]
        self.entries.pop(ident, None)
        self.order.remove(ident)
        self.selected = tuple(value for value in self.selected if value != ident)
        self._schedule()

    def move(self, ident: str, _parent: str, _index: str) -> None:
        self.order.remove(ident)
        self.order.append(ident)
        self._schedule()

    def see(self, ident: str) -> None:
        self.update_idletasks()
        top = self.order.index(ident) * self.row_height
        visible_top = self.canvasy(0)
        extent = max(1, len(self.order) * self.row_height)
        if top < visible_top:
            self.yview_moveto(top / extent)
        elif top + self.row_height > visible_top + self.winfo_height():
            self.yview_moveto((top + self.row_height - self.winfo_height()) / extent)

    def set_active(self, ident: str | None) -> None:
        if self.active_id != ident:
            self.active_id = ident
            self._schedule()

    def _schedule(self, _event: tk.Event[Any] | None = None) -> None:
        if self.redraw_id is None:
            self.redraw_id = self.after_idle(self._draw)

    def _title_lines(self, text: str, width: int) -> list[str]:
        lines = [""]
        for word in text.split():
            candidate = (lines[-1] + " " + word).strip()
            if self.title_font.measure(candidate) <= width:
                lines[-1] = candidate
            else:
                lines.append(word)
        if len(lines) > 2:
            lines = lines[:2]
            while self.title_font.measure(lines[1] + "…") > width and lines[1]:
                lines[1] = lines[1][:-1]
            lines[1] += "…"
        return lines

    def _draw(self) -> None:
        self.redraw_id = None
        super().delete("all")
        width = self.winfo_width()
        self.configure(
            scrollregion=(0, 0, width, len(self.order) * self.row_height),
            yscrollincrement=24,
        )
        for index, ident in enumerate(self.order):
            order, name, kind, orbs, percent, status = self.entries[ident]
            y = index * self.row_height
            active = ident == self.active_id
            selected = ident in self.selected
            success = status == "Đã nhận thưởng"
            ink = COLORS["success"] if success else COLORS["primary"] if active else COLORS["muted"]
            if active or selected:
                rounded(self, (5, y + 3, width - 5, y + 111), COLORS["elevated"])
                self.create_line(6, y + 16, 6, y + 100, fill=COLORS["primary"], width=2)
            if index < len(self.order) - 1:
                self.create_line(26, y + 54, 26, y + 134, fill=COLORS["border"], width=2)
            self.create_oval(
                12,
                y + 24,
                40,
                y + 52,
                outline=ink,
                width=2,
                fill=COLORS["elevated"] if active or selected else COLORS["surface"],
            )
            self.create_text(
                26,
                y + 38,
                text="✓" if success else str(order),
                fill=ink,
                font=("Segoe UI", 10, "bold"),
            )
            title = "\n".join(self._title_lines(str(name), max(80, width - 74)))
            self.create_text(
                56,
                y + 17,
                text=title,
                anchor="nw",
                fill=COLORS["text"],
                font=self.title_font,
            )
            self.create_text(
                56,
                y + 64,
                text=f"{kind}  ·  {orbs} Orbs cơ bản",
                anchor="nw",
                fill=COLORS["muted"],
                font=("Segoe UI", 10),
            )
            status_ink = (
                COLORS["error"]
                if status
                in {
                    "Có lỗi",
                    "Không còn trong danh sách Quest",
                }
                else ink
            )
            self.create_text(
                56,
                y + 87,
                text=f"{status}  ·  {percent}"
                if active
                else str(status).replace(
                    "Hoàn thành · chờ nhận",
                    "Chờ nhận",
                ),
                width=max(80, width - 74),
                anchor="nw",
                fill=status_ink,
                font=("Segoe UI", 10, "bold"),
            )


class Banner(tk.Canvas):
    """Fit a local decorative panorama to the available focus-panel bounds."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=COLORS["surface"], height=140, highlightthickness=0)
        source = Path(__file__).with_name("assets") / "focus-landscape.png"
        self.source: Image.Image | None = None
        self.photo: ImageTk.PhotoImage | None = None
        self.resize_id: str | None = None
        if source.is_file():
            with Image.open(source) as original:
                self.source = original.convert("RGB")
        self.bind("<Configure>", self._resize)

    def _resize(self, _event: tk.Event[Any]) -> None:
        if self.resize_id:
            self.after_cancel(self.resize_id)
        self.resize_id = self.after(60, self._draw)

    def _draw(self) -> None:
        self.resize_id = None
        width, height = self.winfo_width(), self.winfo_height()
        self.delete("all")
        if self.source and width > 1 and height > 1:
            fitted = ImageOps.fit(
                self.source,
                (width, height),
                method=Image.Resampling.LANCZOS,
            )
            self.photo = ImageTk.PhotoImage(fitted, master=self)
            self.create_image(0, 0, image=self.photo, anchor="nw")


class ProgressBar(tk.Canvas):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, height=8, bg=COLORS["elevated"], highlightthickness=0)
        self.value = 0.0
        self.bind("<Configure>", lambda _event: self._draw())

    def set_value(self, value: float) -> None:
        self.value = min(100.0, max(0.0, value))
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        width = max(8, self.winfo_width())
        self.create_line(4, 4, width - 4, 4, width=8, capstyle="round", fill=COLORS["border"])
        if self.value:
            self.create_line(
                4,
                4,
                max(4, (width - 8) * self.value / 100 + 4),
                4,
                width=8,
                capstyle="round",
                fill=COLORS["primary"],
            )


class Steps(tk.Canvas):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, height=66, bg=COLORS["elevated"], highlightthickness=0)
        self.phase = 0
        self.bind("<Configure>", lambda _event: self.draw())

    def set_phase(self, phase: int) -> None:
        self.phase = phase
        self.draw()

    def draw(self) -> None:
        self.delete("all")
        points = [int(self.winfo_width() * ratio) for ratio in (0.16, 0.5, 0.84)]
        for index in range(2):
            self.create_line(
                points[index] + 13,
                15,
                points[index + 1] - 13,
                15,
                fill=COLORS["primary"] if self.phase > index else COLORS["border"],
            )
        for index, (x, label) in enumerate(
            zip(points, ("Bắt đầu", "Thực hiện", "Nhận Orbs"), strict=True),
        ):
            done, current = self.phase > index, self.phase == index
            ink = COLORS["primary"] if done or current else COLORS["muted"]
            self.create_oval(x - 12, 3, x + 12, 27, outline=ink, width=2)
            self.create_text(
                x,
                15,
                text="✓" if done else "•" if current else "",
                fill=ink,
                font=("Segoe UI", 12),
            )
            self.create_text(x, 47, text=label, fill=ink, font=("Segoe UI", 10))
