# interactive_gui.py
# Interactive Disk Scheduling Simulator (Tkinter)
# Features:
#  - Simulation engine: FCFS, SSTF, SCAN, C-SCAN
#  - Interactive Tkinter UI with Canvas track visualization
#  - Play / Pause / Step / Back / Reset
#  - Speed slider, random request generator, Compare All (matplotlib)
#  - Export trace to CSV
#
# Requirements:
#  - Python 3.8+
#  - matplotlib
#
# Run:
#   pip install matplotlib
#   python interactive_gui.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import copy
import csv
import math
import time
from dataclasses import dataclass, field
from typing import List, Optional
import matplotlib.pyplot as plt

# -----------------------------
# Simulation Engine (self-contained)
# -----------------------------
@dataclass
class Request:
    id: int
    cylinder: int
    arrival_time: float = 0.0

@dataclass
class TraceStep:
    step: int
    time: float
    head: int
    served_id: Optional[int]
    moved: int
    cumulative: int

class SimulationEngine:
    def __init__(self, num_cylinders: int = 200, initial_head: int = 0, initial_direction: int = 1,
                 time_per_cylinder: float = 1.0):
        self.num_cylinders = int(num_cylinders)
        self.initial_head = int(initial_head)
        self.initial_direction = 1 if initial_direction >= 0 else -1
        self.time_per_cylinder = float(time_per_cylinder)

    def run(self, requests: List[Request], algorithm: str = "FCFS", serve_until: Optional[int] = None) -> List[TraceStep]:
        """
        Returns a list of TraceStep (trace).
        algorithm: "FCFS", "SSTF", "SCAN", "C-SCAN" (case-insensitive)
        serve_until: optional limit to number of served requests
        """
        algo = algorithm.strip().upper()
        if algo not in ("FCFS", "SSTF", "SCAN", "C-SCAN", "CSCAN"):
            raise ValueError("Unsupported algorithm: " + algorithm)

        # Working copy
        pending = [copy.deepcopy(r) for r in requests]
        current_head = int(self.initial_head)
        direction = int(self.initial_direction)
        steps: List[TraceStep] = []
        cumulative = 0
        t = 0.0
        served_count = 0

        def serve(req: Request):
            nonlocal current_head, cumulative, t, served_count
            moved = abs(req.cylinder - current_head)
            cumulative += moved
            t += moved * self.time_per_cylinder
            current_head = int(req.cylinder)
            step = TraceStep(step=served_count, time=t, head=current_head, served_id=req.id, moved=moved, cumulative=cumulative)
            steps.append(step)

        def pop_fcfs():
            if not pending: return None
            return pending.pop(0)

        def pop_sstf():
            if not pending: return None
            # find nearest by linear scan (fine for small lists)
            best_idx = 0
            best_d = abs(pending[0].cylinder - current_head)
            for i in range(1, len(pending)):
                d = abs(pending[i].cylinder - current_head)
                if d < best_d or (d == best_d and pending[i].id < pending[best_idx].id):
                    best_d = d
                    best_idx = i
            return pending.pop(best_idx)

        def pop_scan():
            nonlocal direction
            if not pending: return None
            pending.sort(key=lambda r: (r.cylinder, r.id))
            if direction > 0:
                # find first >= head
                idx = None
                for i, r in enumerate(pending):
                    if r.cylinder >= current_head:
                        idx = i
                        break
                if idx is not None:
                    return pending.pop(idx)
                else:
                    # reverse direction and pick the farthest on other side
                    direction = -1
                    return pending.pop(-1)
            else:
                # direction < 0
                idx = None
                for i in range(len(pending)-1, -1, -1):
                    if pending[i].cylinder <= current_head:
                        idx = i
                        break
                if idx is not None:
                    return pending.pop(idx)
                else:
                    direction = 1
                    return pending.pop(0)

        def pop_cscan():
            nonlocal current_head
            if not pending: return None
            pending.sort(key=lambda r: (r.cylinder, r.id))
            # moving right by design. If no candidate >= head, wrap to 0 (jump without cost)
            idx = None
            for i, r in enumerate(pending):
                if r.cylinder >= current_head:
                    idx = i
                    break
            if idx is not None:
                return pending.pop(idx)
            else:
                # wrap to 0 (no cost)
                current_head = 0
                # try again
                return pop_cscan()

        # Run loop
        if algo == "FCFS":
            while pending and (serve_until is None or served_count < serve_until):
                req = pop_fcfs()
                serve(req)
                served_count += 1
        elif algo == "SSTF":
            while pending and (serve_until is None or served_count < serve_until):
                req = pop_sstf()
                serve(req)
                served_count += 1
        elif algo == "SCAN":
            while pending and (serve_until is None or served_count < serve_until):
                req = pop_scan()
                serve(req)
                served_count += 1
        elif algo in ("C-SCAN", "CSCAN"):
            while pending and (serve_until is None or served_count < serve_until):
                req = pop_cscan()
                serve(req)
                served_count += 1

        return steps

    def compute_metrics(self, trace: List[TraceStep]):
        if not trace:
            return {"total_head_movement": 0, "average_seek": 0.0, "total_time": 0.0, "throughput": 0.0, "num_requests": 0}
        total = trace[-1].cumulative
        num = len(trace)
        avg = total / num if num else 0.0
        total_time = trace[-1].time
        throughput = num / total_time if total_time > 0 else float('inf')
        return {"total_head_movement": int(total), "average_seek": float(avg), "total_time": float(total_time), "throughput": float(throughput), "num_requests": int(num)}

# -----------------------------
# GUI
# -----------------------------
class DiskSimulatorGUI:
    def __init__(self, root):
        self.root = root
        root.title("Interactive Disk Scheduling Simulator")

        # Default params
        self.num_cylinders = tk.IntVar(value=200)
        self.initial_head = tk.IntVar(value=50)
        self.speed_ms = tk.IntVar(value=300)  # ms per step animation
        self.algorithm = tk.StringVar(value="FCFS")
        self.is_playing = False
        self.trace: List[TraceStep] = []
        self.trace_index = 0
        self.engine = SimulationEngine(num_cylinders=self.num_cylinders.get(), initial_head=self.initial_head.get())
        self.requests: List[Request] = []
        self.current_head_pos = self.initial_head.get()

        self._build_ui()
        self._draw_empty_track()

    def _build_ui(self):
        top = tk.Frame(self.root)
        top.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        # Left: inputs
        left = tk.Frame(top)
        left.pack(side=tk.LEFT, padx=6)

        tk.Label(left, text="Requests (comma separated):").grid(row=0, column=0, sticky="w")
        self.req_entry = tk.Entry(left, width=40)
        self.req_entry.grid(row=0, column=1, columnspan=3, padx=4)

        tk.Label(left, text="Cylinders:").grid(row=1, column=0, sticky="w")
        tk.Entry(left, width=8, textvariable=self.num_cylinders).grid(row=1, column=1, sticky="w")

        tk.Label(left, text="Initial Head:").grid(row=1, column=2, sticky="w")
        tk.Entry(left, width=8, textvariable=self.initial_head).grid(row=1, column=3, sticky="w")

        tk.Label(left, text="Algorithm:").grid(row=2, column=0, sticky="w", pady=(6,0))
        alg_box = ttk.Combobox(left, values=["FCFS", "SSTF", "SCAN", "C-SCAN"], textvariable=self.algorithm, state="readonly", width=10)
        alg_box.grid(row=2, column=1, sticky="w", pady=(6,0))
        alg_box.current(0)

        tk.Button(left, text="Load Requests", command=self.load_requests_from_entry).grid(row=2, column=2, padx=4)
        tk.Button(left, text="Random 8", command=lambda: self.generate_random(8)).grid(row=2, column=3, padx=4)

        # Middle: controls
        mid = tk.Frame(top)
        mid.pack(side=tk.LEFT, padx=8)

        btn_frame = tk.Frame(mid)
        btn_frame.pack()

        self.play_btn = tk.Button(btn_frame, text="▶ Play", width=8, command=self.toggle_play)
        self.play_btn.grid(row=0, column=0, padx=3)
        tk.Button(btn_frame, text="⏸ Pause", width=8, command=self.pause).grid(row=0, column=1, padx=3)
        tk.Button(btn_frame, text="↶ Reset", width=8, command=self.reset).grid(row=0, column=2, padx=3)
        tk.Button(btn_frame, text="⤺ Step", width=8, command=self.step_forward).grid(row=0, column=3, padx=3)
        tk.Button(btn_frame, text="⤼ Back", width=8, command=self.step_back).grid(row=0, column=4, padx=3)

        tk.Label(mid, text="Speed (ms per step):").pack(pady=(8,0))
        speed = tk.Scale(mid, from_=50, to=1000, orient=tk.HORIZONTAL, variable=self.speed_ms, length=240)
        speed.pack()

        # Right: misc
        right = tk.Frame(top)
        right.pack(side=tk.LEFT, padx=6)

        tk.Button(right, text="Run Simulation", command=self.run_simulation).pack(pady=2, fill=tk.X)
        tk.Button(right, text="Compare All", command=self.plot_compare_all).pack(pady=2, fill=tk.X)
        tk.Button(right, text="Export Trace CSV", command=self.export_trace_csv).pack(pady=2, fill=tk.X)

        # Canvas for track
        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=False, padx=8, pady=6)
        self.canvas_w = 900
        self.canvas_h = 120
        self.canvas = tk.Canvas(canvas_frame, width=self.canvas_w, height=self.canvas_h, bg="#ffffff", bd=1, relief=tk.SUNKEN)
        self.canvas.pack()

        # Metrics display
        metrics_frame = tk.Frame(self.root)
        metrics_frame.pack(fill=tk.X, padx=8, pady=(0,8))
        self.metrics_label = tk.Label(metrics_frame, text="Total: 0   |   Average: 0.00   |   Served: 0", font=("Arial", 10))
        self.metrics_label.pack(side=tk.LEFT)

        # Info / legend
        legend = tk.Label(self.root, text="Track: 0 (left) → N-1 (right). Head shown as filled circle. Requests shown as ticks.", fg="gray")
        legend.pack(padx=8, pady=(0,8))

        # Bind canvas resize to redraw
        self.root.bind("<Configure>", self._on_resize)

    # ------------------------
    # Request handling & run
    # ------------------------
    def load_requests_from_entry(self):
        text = self.req_entry.get().strip()
        if not text:
            messagebox.showinfo("No input", "Enter requests like: 82,170,43,140,24,16,190")
            return
        try:
            nums = [int(x.strip()) for x in text.split(",") if x.strip() != ""]
        except ValueError:
            messagebox.showerror("Invalid input", "Requests must be integers separated by commas.")
            return
        # clamp to cylinder range
        n = self.num_cylinders.get()
        for x in nums:
            if x < 0 or x >= n:
                messagebox.showerror("Out of range", f"Request {x} outside range 0..{n-1}")
                return
        self.requests = [Request(id=i, cylinder=val) for i, val in enumerate(nums)]
        self.current_head_pos = self.initial_head.get()
        self._draw_track()
        messagebox.showinfo("Loaded", f"Loaded {len(self.requests)} requests.")

    def generate_random(self, count=8):
        n = self.num_cylinders.get()
        vals = [random.randint(0, n-1) for _ in range(count)]
        self.req_entry.delete(0, tk.END)
        self.req_entry.insert(0, ",".join(map(str, vals)))
        self.load_requests_from_entry()

    def run_simulation(self):
        if not self.requests:
            self.load_requests_from_entry()
            if not self.requests:
                return
        # update engine params
        self.engine = SimulationEngine(num_cylinders=self.num_cylinders.get(), initial_head=self.initial_head.get(), initial_direction=1)
        alg = self.algorithm.get()
        self.trace = self.engine.run(self.requests, algorithm=alg)
        # reset indices and head
        self.trace_index = 0
        self.current_head_pos = self.initial_head.get()
        self.is_playing = False
        self.update_metrics()
        self._draw_track()
        messagebox.showinfo("Simulation ready", f"Simulation for {alg} ready with {len(self.trace)} steps.\nUse Play/Step to animate.")

    # ------------------------
    # Animation & stepping
    # ------------------------
    def toggle_play(self):
        if not self.trace:
            self.run_simulation()
            if not self.trace:
                return
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_btn.config(text="⏸ Playing")
            self._animate_step()
        else:
            self.play_btn.config(text="▶ Play")

    def pause(self):
        self.is_playing = False
        self.play_btn.config(text="▶ Play")

    def reset(self):
        self.is_playing = False
        self.play_btn.config(text="▶ Play")
        self.trace_index = 0
        self.current_head_pos = self.initial_head.get()
        self._draw_track()
        self.update_metrics()

    def step_forward(self):
        if not self.trace:
            self.run_simulation()
            if not self.trace:
                return
        if self.trace_index < len(self.trace):
            step = self.trace[self.trace_index]
            # move head to step.head
            self.current_head_pos = step.head
            self.trace_index += 1
            self._draw_track()
            self.update_metrics()
        else:
            self.is_playing = False
            self.play_btn.config(text="▶ Play")

    def step_back(self):
        # Step back: recompute head from previous trace index
        if not self.trace:
            return
        if self.trace_index > 0:
            self.trace_index -= 1
            if self.trace_index == 0:
                self.current_head_pos = self.initial_head.get()
            else:
                self.current_head_pos = self.trace[self.trace_index-1].head
            self._draw_track()
            self.update_metrics()

    def _animate_step(self):
        if not self.is_playing:
            return
        if self.trace_index >= len(self.trace):
            self.is_playing = False
            self.play_btn.config(text="▶ Play")
            return
        # animate instantaneous (move head to next step)
        step = self.trace[self.trace_index]
        self.current_head_pos = step.head
        self.trace_index += 1
        self._draw_track()
        self.update_metrics()
        # schedule next
        ms = max(10, self.speed_ms.get())
        self.root.after(ms, self._animate_step)

    # ------------------------
    # Drawing track & markers
    # ------------------------
    def _on_resize(self, event):
        # simple redraw when main window changes
        self.canvas_w = max(400, self.root.winfo_width() - 40)
        self.canvas.config(width=self.canvas_w)
        self._draw_track()

    def _draw_empty_track(self):
        self.canvas.delete("all")
        pad = 20
        self.track_x0 = pad
        self.track_x1 = self.canvas_w - pad
        self.track_y = self.canvas_h // 2
        self.canvas.create_rectangle(self.track_x0, self.track_y-12, self.track_x1, self.track_y+12, fill="#f0f0f0", outline="#444", tags="track")
        # endpoints
        self.canvas.create_text(self.track_x0, self.track_y+28, text="0", anchor="n", font=("Arial", 9))
        self.canvas.create_text(self.track_x1, self.track_y+28, text=str(max(0, self.num_cylinders.get()-1)), anchor="n", font=("Arial", 9))

    def _draw_track(self):
        self.canvas.delete("all")
        self._draw_empty_track()
        # draw requests as small ticks
        n = self.num_cylinders.get()
        if n <= 0:
            return
        def x_for(cyl):
            # map cylinder to x coordinate
            return self.track_x0 + (self.track_x1 - self.track_x0) * (cyl / max(1, n-1))
        # draw request ticks
        for r in self.requests:
            x = x_for(r.cylinder)
            self.canvas.create_line(x, self.track_y-10, x, self.track_y+10, fill="#cc0000", width=1)
            # small label above
            self.canvas.create_text(x, self.track_y-18, text=str(r.cylinder), anchor="s", font=("Arial", 7), fill="#555")
        # draw head
        hx = x_for(self.current_head_pos)
        self.canvas.create_oval(hx-9, self.track_y-9, hx+9, self.track_y+9, fill="#0b6", outline="#064", width=2, tags="head")
        self.canvas.create_text(hx, self.track_y, text="H", fill="white", font=("Arial", 9, "bold"))
        # if some steps have been served, draw served ones differently (a small circle)
        for i in range(min(self.trace_index, len(self.trace))):
            s = self.trace[i]
            rx = x_for(s.head)
            self.canvas.create_oval(rx-5, self.track_y-5, rx+5, self.track_y+5, fill="#555", outline="#333")
        # optionally draw next target with arrow
        if self.trace_index < len(self.trace):
            nxt = self.trace[self.trace_index]
            nx = x_for(nxt.head)
            # arrow line from head to next
            self.canvas.create_line(hx, self.track_y-24, nx, self.track_y-24, arrow=tk.LAST, dash=(4,2))
            self.canvas.create_text((hx+nx)/2, self.track_y-34, text=f"Next: {nxt.head} (Δ{nxt.moved})", font=("Arial", 8), fill="#333")

    # ------------------------
    # Metrics & export
    # ------------------------
    def update_metrics(self):
        if not self.trace:
            txt = f"Total: 0   |   Average: 0.00   |   Served: 0"
            self.metrics_label.config(text=txt)
            return
        # cumulative at last served index or 0
        last_cum = self.trace[self.trace_index-1].cumulative if self.trace_index>0 else 0
        served = self.trace_index
        avg = last_cum / served if served else 0.0
        txt = f"Total: {last_cum}   |   Average: {avg:.2f}   |   Served: {served}/{len(self.trace)}"
        self.metrics_label.config(text=txt)

    def export_trace_csv(self):
        if not self.trace:
            messagebox.showinfo("No trace", "Run a simulation first to export its trace.")
            return
        fname = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv"), ("All files","*.*")])
        if not fname:
            return
        try:
            with open(fname, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["step","time","head","served_id","moved","cumulative"])
                for st in self.trace:
                    w.writerow([st.step, st.time, st.head, st.served_id, st.moved, st.cumulative])
            messagebox.showinfo("Saved", f"Trace exported to {fname}")
        except Exception as e:
            messagebox.showerror("Error saving", str(e))

    # ------------------------
    # Comparison Plot (matplotlib)
    # ------------------------
    def plot_compare_all(self):
        if not self.requests:
            self.load_requests_from_entry()
            if not self.requests:
                return
        engine = SimulationEngine(num_cylinders=self.num_cylinders.get(), initial_head=self.initial_head.get())
        algos = ["FCFS", "SSTF", "SCAN", "C-SCAN"]
        plt.figure(figsize=(10, 5))
        for alg in algos:
            tr = engine.run(self.requests, algorithm=alg)
            if not tr:
                continue
            steps = list(range(1, len(tr)+1))
            heads = [s.head for s in tr]
            plt.plot(steps, heads, marker='o', label=f"{alg} (total={tr[-1].cumulative})")
        plt.xlabel("Served request index")
        plt.ylabel("Cylinder")
        plt.title("Compare algorithms — head position per served request")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

# -----------------------------
# Main
# -----------------------------
def main():
    root = tk.Tk()
    app = DiskSimulatorGUI(root)
    root.geometry("980x400")
    root.mainloop()

if __name__ == "__main__":
    main()
