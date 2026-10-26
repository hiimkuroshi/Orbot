from __future__ import annotations

import argparse
import tkinter as tk

from orbot.app import OrbotApp


def main() -> None:
    parser = argparse.ArgumentParser(description="Orbot — Discord Quest desktop console")
    parser.add_argument("--demo", action="store_true", help="Open offline sample data")
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = tk.Tk()
    app = OrbotApp(root, demo_mode=args.demo)
    if args.smoke_test:
        root.after(1200, app.close)
    root.mainloop()


if __name__ == "__main__":
    main()
