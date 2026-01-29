#!/usr/bin/env python3
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

from pynput import mouse

CLICK_BUTTON = {
    "Left": "1",
    "Middle": "2",
    "Right": "3",
}

def xdotool(args):
    return subprocess.check_output(["xdotool"] + args, text=True).strip()

def get_mouse_xy():
    out = xdotool(["getmouselocation"])
    parts = dict(p.split(":", 1) for p in out.split() if ":" in p)
    return int(parts["x"]), int(parts["y"])

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("MultiClicker")
        self.root.minsize(330, 420)
        self.root.resizable(False, False)

        self.points = []
        self.running = False
        self.stop_event = threading.Event()
        self.worker = None

        # Capture state
        self.capture_mode = False
        self.mouse_listener = mouse.Listener(on_click=self._on_global_click)
        self.mouse_listener.start()

        # --- UI ---
        self._setup_style()

        main = ttk.Frame(root, padding=8, style="App.TFrame")
        main.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        controls = ttk.LabelFrame(main, text="Controls", padding=12, style="Card.TLabelframe")
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure(0, weight=1)

        actions = ttk.Frame(controls, style="App.TFrame")
        actions.grid(row=0, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        actions.columnconfigure(2, weight=1)

        self.btn_get = ttk.Button(
            actions,
            text="Capture next click",
            command=self.on_get,
            width=16,
        )
        self.btn_get.grid(row=0, column=0, padx=(0, 6), pady=(0, 6), sticky="ew")

        self.btn_remove = ttk.Button(actions, text="Remove", command=self.on_remove, width=16)
        self.btn_remove.grid(row=0, column=1, padx=(0, 6), pady=(0, 6), sticky="ew")
        self.btn_clear = ttk.Button(actions, text="Clear", command=self.on_clear, width=16)
        self.btn_clear.grid(row=0, column=2, padx=(0, 0), pady=(0, 6), sticky="ew")

        timing = ttk.Frame(controls, style="App.TFrame")
        timing.grid(row=1, column=0, sticky="ew")
        timing.columnconfigure(5, weight=1)

        ttk.Label(timing, text="Click:", style="Muted.TLabel").grid(row=0, column=0, sticky="e")
        self.click_type = tk.StringVar(value="Left")
        ttk.Combobox(
            timing, textvariable=self.click_type,
            values=list(CLICK_BUTTON.keys()), state="readonly", width=8
        ).grid(row=0, column=1, padx=(6, 16), pady=(0, 8), sticky="w")

        ttk.Label(timing, text="Interval:", style="Muted.TLabel").grid(row=0, column=2, sticky="e")
        self.interval_ms = tk.StringVar(value="200")
        ttk.Entry(timing, textvariable=self.interval_ms, width=6).grid(
            row=0, column=3, padx=(6, 6), pady=(0, 8)
        )
        ttk.Label(timing, text="ms", style="Muted.TLabel").grid(row=0, column=4, sticky="w")

        ttk.Label(timing, text="Delay:", style="Muted.TLabel").grid(row=1, column=0, sticky="e")
        self.start_delay = tk.StringVar(value="0")
        ttk.Entry(timing, textvariable=self.start_delay, width=6).grid(
            row=1, column=1, padx=(6, 2), pady=(0, 8), sticky="w"
        )
        ttk.Label(timing, text="ms", style="Muted.TLabel").grid(row=1, column=2, padx=(0, 12), sticky="w")

        ttk.Label(timing, text="Repeat:", style="Muted.TLabel").grid(row=1, column=3, sticky="e")
        self.repeat_count = tk.StringVar(value="0")
        ttk.Entry(timing, textvariable=self.repeat_count, width=5).grid(
            row=1, column=4, padx=(6, 0), pady=(0, 8), sticky="w"
        )

        self.restore_mouse = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            controls, text="Restore mouse positions", variable=self.restore_mouse
        ).grid(row=2, column=0, pady=(2, 0), sticky="w")

        points_card = ttk.LabelFrame(main, text="Click points", padding=12, style="Card.TLabelframe")
        points_card.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        points_card.columnconfigure(0, weight=1)
        points_card.rowconfigure(1, weight=1)

        order_row = ttk.Frame(points_card, style="App.TFrame")
        order_row.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        order_row.columnconfigure(0, weight=1)
        ttk.Label(
            order_row,
            text="Order matters. Use the arrows to reorder points.",
            style="Muted.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(order_row, text="Move up", command=self.on_move_up, style="Small.TButton").grid(
            row=0, column=1, padx=(8, 4)
        )
        ttk.Button(order_row, text="Move down", command=self.on_move_down, style="Small.TButton").grid(
            row=0, column=2
        )

        table_frame = ttk.Frame(points_card, style="App.TFrame")
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.points_table = ttk.Treeview(
            table_frame,
            columns=("x", "y"),
            show="headings",
            height=5,
            selectmode="extended",
        )
        self.points_table.heading("x", text="X")
        self.points_table.heading("y", text="Y")
        self.points_table.column("x", width=60, anchor="center")
        self.points_table.column("y", width=60, anchor="center")
        self.points_table.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.points_table.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.points_table.configure(yscrollcommand=sb.set)

        run_actions = ttk.Frame(main, style="App.TFrame")
        run_actions.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        run_actions.columnconfigure(0, weight=1)
        buttons = ttk.Frame(run_actions, style="App.TFrame")
        buttons.grid(row=0, column=0)
        self.btn_start = ttk.Button(buttons, text="Start", command=self.on_start, width=12)
        self.btn_start.grid(row=0, column=0, padx=(0, 8))
        self.btn_stop = ttk.Button(buttons, text="Stop", command=self.on_stop, state="disabled", width=12)
        self.btn_stop.grid(row=0, column=1)
        ttk.Label(buttons, text="F9", style="Hint.TLabel").grid(row=1, column=0, columnspan=2, pady=(2, 0))

        status_bar = ttk.Frame(main, style="Status.TFrame")
        status_bar.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        status_bar.columnconfigure(0, weight=1)
        self.status = tk.StringVar(value="Ready to capture your first point.")
        ttk.Label(status_bar, textvariable=self.status, style="Status.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )

        # Dependency sanity check
        try:
            xdotool(["--version"])
        except Exception:
            messagebox.showerror("Missing dependency", "xdotool not found. Install: sudo apt install xdotool")
            self.status.set("xdotool missing.")

        self.root.bind_all("<F9>", self.on_toggle_hotkey)

    def on_get(self):
        # Arm capture mode: next LEFT click anywhere will be captured
        if self.capture_mode:
            return
        self.capture_mode = True
        self.status.set("Capture mode: click anywhere to add a point.")
        # Make sure our window doesn't steal focus semantics too much
        try:
            self.root.attributes("-topmost", True)
            self.root.after(200, lambda: self.root.attributes("-topmost", False))
        except Exception:
            pass

    def _on_global_click(self, x, y, button, pressed):
        # Called from listener thread. We must hand off UI updates to Tk thread via root.after.
        if not self.capture_mode:
            return

        # We capture on press (pressed=True) of LEFT button only
        if pressed and button == mouse.Button.left:
            self.capture_mode = False
            self.root.after(0, lambda: self._add_point_from_listener(x, y))
            # Stop propagation: returning False stops the listener, not the OS click.
            # Still useful to avoid double-captures; we re-arm listener continuously anyway.
            return

    def _add_point_from_listener(self, x, y):
        self.points.append((int(x), int(y)))
        self.points_table.insert("", tk.END, values=(int(x), int(y)))
        self.status.set(f"Added point: {int(x)}, {int(y)}")

    def on_remove(self):
        sel = list(self.points_table.selection())
        if not sel:
            return
        indexed = sorted(((self.points_table.index(item), item) for item in sel), reverse=True)
        for idx, item in indexed:
            self.points_table.delete(item)
            del self.points[idx]
        self.status.set("Removed selected point(s).")

    def on_clear(self):
        self.points.clear()
        for item in self.points_table.get_children():
            self.points_table.delete(item)
        self.status.set("Cleared all points.")

    def on_move_up(self):
        selection = self.points_table.selection()
        if not selection:
            return
        for item in selection:
            index = self.points_table.index(item)
            if index == 0:
                continue
            self.points_table.move(item, "", index - 1)
            self.points.insert(index - 1, self.points.pop(index))

    def on_move_down(self):
        selection = self.points_table.selection()
        if not selection:
            return
        total = len(self.points_table.get_children())
        for item in reversed(selection):
            index = self.points_table.index(item)
            if index >= total - 1:
                continue
            self.points_table.move(item, "", index + 1)
            self.points.insert(index + 1, self.points.pop(index))

    def on_start(self):
        if self.running:
            return
        if not self.points:
            messagebox.showwarning("No points", "Add at least one point.")
            return
        try:
            interval = int(self.interval_ms.get())
            if interval < 0:
                raise ValueError
            delay_ms = int(self.start_delay.get())
            if delay_ms < 0:
                raise ValueError
            repeats = int(self.repeat_count.get())
            if repeats < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid timing",
                "Interval must be a non-negative integer (milliseconds).\n"
                "Delay must be a non-negative integer (milliseconds).\n"
                "Repeat must be 0 (forever) or a positive integer.",
            )
            return

        self.stop_event.clear()
        self.running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.status.set("Running click sequence...")

        self.worker = threading.Thread(
            target=self.loop,
            args=(interval, delay_ms / 1000.0, repeats),
            daemon=True,
        )
        self.worker.start()

    def on_stop(self):
        if not self.running:
            return
        self.stop_event.set()
        self.running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status.set("Stopped.")

    def on_toggle_hotkey(self, _event=None):
        if self.running:
            self.on_stop()
        else:
            self.on_start()

    def loop(self, interval_ms, delay_s, repeat_count):
        btn = CLICK_BUTTON.get(self.click_type.get(), "1")
        interval_s = max(interval_ms / 1000.0, 0)

        if delay_s > 0:
            self.root.after(0, lambda: self.status.set(f"Starting in {delay_s:.1f}s..."))
            time.sleep(delay_s)

        cycle = 0
        while not self.stop_event.is_set():
            if repeat_count and cycle >= repeat_count:
                break
            cycle += 1
            self.root.after(0, lambda c=cycle: self.status.set(f"Running cycle {c}..."))

            ox = oy = None
            if self.restore_mouse.get():
                try:
                    ox, oy = get_mouse_xy()
                except Exception:
                    ox = oy = None

            for x, y in list(self.points):
                if self.stop_event.is_set():
                    break
                try:
                    xdotool(["mousemove", "--sync", str(x), str(y)])
                    xdotool(["click", btn])
                except Exception:
                    self.root.after(0, lambda: self.status.set("xdotool command failed."))
                    self.root.after(0, self.on_stop)
                    return
                time.sleep(interval_s)

            if ox is not None and oy is not None:
                try:
                    xdotool(["mousemove", "--sync", str(ox), str(oy)])
                except Exception:
                    pass

        self.root.after(0, self.on_stop)

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        self.root.configure(bg="#f1f5f9")

        style.configure("App.TFrame", background="#f1f5f9")
        style.configure("Card.TLabelframe", background="#ffffff", foreground="#0f172a")
        style.configure("Card.TLabelframe.Label", background="#ffffff", foreground="#0f172a")
        style.configure(
            "Header.TLabel", background="#f1f5f9", foreground="#0f172a", font=("Segoe UI", 13, "bold")
        )
        style.configure(
            "Subheader.TLabel", background="#f1f5f9", foreground="#475569", font=("Segoe UI", 8)
        )
        style.configure("Muted.TLabel", background="#ffffff", foreground="#64748b", font=("Segoe UI", 8))
        style.configure("Status.TFrame", background="#e2e8f0")
        style.configure(
            "Status.TLabel", background="#e2e8f0", foreground="#334155", font=("Segoe UI", 8)
        )
        style.configure(
            "Accent.TButton", background="#2563eb", foreground="#f8fafc", font=("Segoe UI", 8, "bold")
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#3b82f6")],
            foreground=[("active", "#f8fafc")],
        )
        style.configure("Small.TButton", padding=(3, 1), font=("Segoe UI", 7))
        style.configure("TButton", padding=(4, 3))
        style.configure("TEntry", fieldbackground="#ffffff", foreground="#0f172a")
        style.configure("TCombobox", fieldbackground="#ffffff", foreground="#0f172a")
        style.configure("Hint.TLabel", background="#f1f5f9", foreground="#64748b", font=("Segoe UI", 7))
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#ffffff")],
            foreground=[("readonly", "#0f172a")],
        )
        style.configure(
            "Treeview",
            background="#ffffff",
            foreground="#0f172a",
            fieldbackground="#ffffff",
            rowheight=18,
        )
        style.configure("Treeview.Heading", background="#e2e8f0", foreground="#0f172a")

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
