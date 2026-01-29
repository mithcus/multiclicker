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
        self.root.title("Multi Auto Clicker (X11 + xdotool)")

        self.points = []
        self.running = False
        self.stop_event = threading.Event()
        self.worker = None

        # Capture state
        self.capture_mode = False
        self.mouse_listener = mouse.Listener(on_click=self._on_global_click)
        self.mouse_listener.start()

        # --- UI ---
        main = ttk.Frame(root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        controls = ttk.Frame(main)
        controls.grid(row=0, column=0, sticky="ew")

        self.btn_get = ttk.Button(controls, text="Get location (next click)", command=self.on_get)
        self.btn_get.grid(row=0, column=0, padx=(0, 8))

        ttk.Button(controls, text="Remove selected", command=self.on_remove).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(controls, text="Clear", command=self.on_clear).grid(row=0, column=2, padx=(0, 16))

        ttk.Label(controls, text="Click:").grid(row=0, column=3, sticky="e")
        self.click_type = tk.StringVar(value="Left")
        ttk.Combobox(
            controls, textvariable=self.click_type,
            values=list(CLICK_BUTTON.keys()), state="readonly", width=8
        ).grid(row=0, column=4, padx=(6, 16))

        ttk.Label(controls, text="Interval (ms):").grid(row=0, column=5, sticky="e")
        self.interval_ms = tk.StringVar(value="200")
        ttk.Entry(controls, textvariable=self.interval_ms, width=8).grid(row=0, column=6, padx=(6, 16))

        self.restore_mouse = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, text="Restore mouse position", variable=self.restore_mouse)\
            .grid(row=0, column=7, padx=(0, 16))

        self.btn_start = ttk.Button(controls, text="Start", command=self.on_start)
        self.btn_start.grid(row=0, column=8, padx=(0, 8))
        self.btn_stop = ttk.Button(controls, text="Stop", command=self.on_stop, state="disabled")
        self.btn_stop.grid(row=0, column=9)

        lf = ttk.LabelFrame(main, text="Points (in order)")
        lf.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(lf, height=12)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(lf, orient="vertical", command=self.listbox.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=sb.set)

        self.status = tk.StringVar(value="Ready.")
        ttk.Label(main, textvariable=self.status).grid(row=2, column=0, sticky="ew", pady=(10, 0))

        # Dependency sanity check
        try:
            xdotool(["--version"])
        except Exception:
            messagebox.showerror("Missing dependency", "xdotool not found. Install: sudo apt install xdotool")
            self.status.set("xdotool missing.")

    def on_get(self):
        # Arm capture mode: next LEFT click anywhere will be captured
        if self.capture_mode:
            return
        self.capture_mode = True
        self.status.set("Capture mode: click anywhere to add a point (Left click).")
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
        self.listbox.insert(tk.END, f"{int(x)}, {int(y)}")
        self.status.set(f"Added point: {int(x)}, {int(y)}")

    def on_remove(self):
        sel = list(self.listbox.curselection())
        if not sel:
            return
        for idx in reversed(sel):
            self.listbox.delete(idx)
            del self.points[idx]
        self.status.set("Removed selected point(s).")

    def on_clear(self):
        self.points.clear()
        self.listbox.delete(0, tk.END)
        self.status.set("Cleared.")

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
        except ValueError:
            messagebox.showerror("Invalid interval", "Interval must be a non-negative integer (milliseconds).")
            return

        self.stop_event.clear()
        self.running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.status.set("Running...")

        self.worker = threading.Thread(target=self.loop, daemon=True)
        self.worker.start()

    def on_stop(self):
        if not self.running:
            return
        self.stop_event.set()
        self.running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status.set("Stopped.")

    def loop(self):
        btn = CLICK_BUTTON.get(self.click_type.get(), "1")
        try:
            interval_s = int(self.interval_ms.get()) / 1000.0
        except Exception:
            interval_s = 0.2

        while not self.stop_event.is_set():
            ox = oy = None
            if self.restore_mouse.get():
                try:
                    ox, oy = get_mouse_xy()
                except Exception:
                    ox = oy = None

            for x, y in self.points:
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

def main():
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()

