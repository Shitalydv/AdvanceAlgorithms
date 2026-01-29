"""
Sensor Hub Optimization — Weiszfeld's Geometric Median Visualization
===================================================================
Problem: Find the optimal hub (geometric median) for a set of sensor coordinates
Purpose: Interactive GUI to compute and animate the geometric median using Weiszfeld's algorithm

Features:
- Input sensors via text, presets, or canvas clicks
- Iterative visualization of hub convergence (intermediate hubs + total distance)
- Real-time distance breakdown, per-sensor distances and statistics
- Progress bar, iteration controls and stop/resume
- Exports: numerical results and iteration history for reporting
- User-friendly UI with presets, random generation and CSV-friendly data
"""


import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import threading
import time

# -------------------------------
# Hub computation logic
# -------------------------------
def optimal_hub(sensor_locations, tol=1e-5, max_iter=1000, step_callback=None):
    """
    Weiszfeld's algorithm to find the geometric median (optimal hub).
    Returns hub location and total distance.
    """
    points = np.array(sensor_locations, dtype=float)
    hub = points.mean(axis=0)  # Start with centroid
    
    iteration_history = [(hub.copy(), np.sum(np.linalg.norm(points - hub, axis=1)))]
    
    for i in range(max_iter):
        distances = np.linalg.norm(points - hub, axis=1)
        distances = np.where(distances == 0, 1e-10, distances)
        weights = 1 / distances
        new_hub = np.sum(points * weights[:, None], axis=0) / np.sum(weights)
        
        movement = np.linalg.norm(new_hub - hub)
        total_dist = np.sum(np.linalg.norm(points - new_hub, axis=1))
        
        if step_callback:
            step_callback(i + 1, new_hub.copy(), total_dist, movement)
        
        iteration_history.append((new_hub.copy(), total_dist))
        
        if movement < tol:
            break
        hub = new_hub

    total_distance = np.sum(np.linalg.norm(points - hub, axis=1))
    return hub, total_distance, iteration_history

def calculate_distances(sensors, hub):
    """Calculate individual distances from each sensor to hub"""
    distances = []
    for i, sensor in enumerate(sensors):
        dist = np.linalg.norm(np.array(sensor) - np.array(hub))
        distances.append({
            'sensor': i + 1,
            'coords': sensor,
            'distance': dist
        })
    return distances

# -------------------------------
# GUI Class
# -------------------------------
class SensorHubApp:
    def __init__(self):
        self.sensors = []
        self.hub = None
        self.is_running = False
        self.stop_requested = False
        
        self._setup_colors()
        self._setup_window()
        self._setup_ui()
        
        self.root.mainloop()
    
    def _setup_colors(self):
        self.colors = {
            "bg": "#1e1e2e",
            "card": "#313244",
            "accent": "#89b4fa",
            "accent2": "#f38ba8",
            "text": "#cdd6f4",
            "success": "#a6e3a1",
            "warning": "#f9e2af",
            "surface": "#45475a",
            "sensor": "#89b4fa",
            "hub": "#f38ba8",
            "line": "#6c7086",
            "canvas_bg": "#1a1a2e"
        }
    
    def _setup_window(self):
        self.root = tk.Tk()
        self.root.title("📡 Sensor Hub Optimization - Weiszfeld Algorithm")
        self.root.geometry("1300x800")
        self.root.configure(bg=self.colors["bg"])
        
        # Force window to top
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(200, lambda: self.root.attributes('-topmost', False))
        self.root.focus_force()
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Run.TButton", font=("Arial", 11, "bold"),
                        foreground="white", background=self.colors["accent"], padding=8)
        style.configure("Stop.TButton", font=("Arial", 11, "bold"),
                        foreground="white", background=self.colors["accent2"], padding=8)
        style.configure("Secondary.TButton", font=("Arial", 10),
                        foreground="white", background=self.colors["surface"], padding=6)
        
        style.map("Run.TButton", background=[("active", "#7aa2f7")])
        style.map("Stop.TButton", background=[("active", "#f7768e")])
    
    def _setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - Input & Controls
        left_panel = tk.Frame(main_frame, bg=self.colors["card"], width=320)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_panel.pack_propagate(False)
        
        self._setup_input_panel(left_panel)
        
        # Middle panel - Visualization
        middle_panel = tk.Frame(main_frame, bg=self.colors["bg"])
        middle_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        self._setup_visualization(middle_panel)
        
        # Right panel - Results & Calculations
        right_panel = tk.Frame(main_frame, bg=self.colors["card"], width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        
        self._setup_results_panel(right_panel)
    
    def _setup_input_panel(self, parent):
        # Title
        tk.Label(parent, text="📡 Sensor Input", font=("Arial", 14, "bold"),
                 bg=self.colors["card"], fg=self.colors["accent"]).pack(pady=15)
        
        # Instructions
        tk.Label(parent, text="Enter coordinates (x y per line):",
                 font=("Arial", 10), bg=self.colors["card"], 
                 fg=self.colors["text"]).pack(anchor="w", padx=15)
        
        # Text input
        text_frame = tk.Frame(parent, bg=self.colors["card"])
        text_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.text_input = tk.Text(text_frame, height=10, width=30,
                                   font=("Consolas", 11),
                                   bg=self.colors["surface"],
                                   fg=self.colors["text"],
                                   insertbackground="white",
                                   relief="flat")
        self.text_input.pack(fill=tk.X)
        
        # Sample data
        sample_data = "0 0\n10 0\n5 8\n2 4\n8 3"
        self.text_input.insert("1.0", sample_data)
        
        # Quick presets
        preset_frame = tk.Frame(parent, bg=self.colors["card"])
        preset_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(preset_frame, text="Presets:", font=("Arial", 9),
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w")
        
        preset_btn_frame = tk.Frame(preset_frame, bg=self.colors["card"])
        preset_btn_frame.pack(fill=tk.X, pady=5)
        
        presets = [
            ("Triangle", "0 0\n10 0\n5 8.66"),
            ("Square", "0 0\n10 0\n10 10\n0 10"),
            ("Pentagon", "5 0\n9.75 3.45\n7.94 9.05\n2.06 9.05\n0.25 3.45"),
            ("Random", None)
        ]
        
        for i, (name, data) in enumerate(presets):
            btn = tk.Button(preset_btn_frame, text=name, font=("Arial", 8),
                           bg=self.colors["surface"], fg=self.colors["text"],
                           relief="flat", padx=5, pady=2,
                           command=lambda d=data, n=name: self._load_preset(d, n))
            btn.grid(row=0, column=i, padx=2)
        
        # Animation speed
        speed_frame = tk.Frame(parent, bg=self.colors["card"])
        speed_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(speed_frame, text="Animation Speed:", font=("Arial", 10),
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w")
        
        self.speed_var = tk.DoubleVar(value=0.3)
        speed_scale = ttk.Scale(speed_frame, from_=0.05, to=1.0, 
                                variable=self.speed_var, orient="horizontal")
        speed_scale.pack(fill=tk.X, pady=5)
        
        self.speed_label = tk.Label(speed_frame, text="0.3s delay", font=("Arial", 9),
                                    bg=self.colors["card"], fg=self.colors["text"])
        self.speed_label.pack()
        self.speed_var.trace("w", self._update_speed_label)
        
        # Buttons
        btn_frame = tk.Frame(parent, bg=self.colors["card"])
        btn_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.run_btn = ttk.Button(btn_frame, text="▶ Find Optimal Hub",
                                  style="Run.TButton", command=self.run_optimization)
        self.run_btn.pack(fill=tk.X, pady=3)
        
        self.stop_btn = ttk.Button(btn_frame, text="⬛ Stop",
                                   style="Stop.TButton", command=self.stop_optimization,
                                   state="disabled")
        self.stop_btn.pack(fill=tk.X, pady=3)
        
        ttk.Button(btn_frame, text="🔄 Clear All", style="Secondary.TButton",
                   command=self.clear_all).pack(fill=tk.X, pady=3)
        
        ttk.Button(btn_frame, text="🖱️ Click to Add", style="Secondary.TButton",
                   command=self.toggle_click_mode).pack(fill=tk.X, pady=3)
        
        # Click mode indicator
        self.click_mode = False
        self.click_label = tk.Label(parent, text="", font=("Arial", 9),
                                    bg=self.colors["card"], fg=self.colors["warning"])
        self.click_label.pack(pady=5)
        
        # Algorithm info
        info_frame = tk.Frame(parent, bg=self.colors["surface"])
        info_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(info_frame, text="📘 Weiszfeld Algorithm", font=("Arial", 9, "bold"),
                 bg=self.colors["surface"], fg=self.colors["warning"]).pack(pady=5, anchor="w", padx=5)
        
        algo_text = "Iteratively finds the geometric\nmedian (Fermat point) that\nminimizes total distance to\nall sensors."
        tk.Label(info_frame, text=algo_text, font=("Arial", 8),
                 bg=self.colors["surface"], fg=self.colors["text"],
                 justify="left").pack(anchor="w", padx=5, pady=5)
    
    def _setup_visualization(self, parent):
        # Title
        tk.Label(parent, text="🗺️ Sensor Network", font=("Arial", 14, "bold"),
                 bg=self.colors["bg"], fg=self.colors["accent"]).pack(pady=(0, 10))
        
        # Canvas
        canvas_frame = tk.Frame(parent, bg=self.colors["card"])
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.colors["canvas_bg"],
                                highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        
        # Status
        self.status_label = tk.Label(parent, text="Enter sensor coordinates and click 'Find Optimal Hub'",
                                     font=("Arial", 10), bg=self.colors["bg"],
                                     fg=self.colors["text"])
        self.status_label.pack(pady=10)
        
        # Progress
        self.progress = ttk.Progressbar(parent, length=400, mode='determinate')
        self.progress.pack(pady=5)
    
    def _setup_results_panel(self, parent):
        # Title
        tk.Label(parent, text="📊 Results & Calculations", font=("Arial", 14, "bold"),
                 bg=self.colors["card"], fg=self.colors["accent"]).pack(pady=15)
        
        # Optimal hub result
        result_frame = tk.Frame(parent, bg=self.colors["surface"])
        result_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(result_frame, text="Optimal Hub Location:", font=("Arial", 10, "bold"),
                 bg=self.colors["surface"], fg=self.colors["warning"]).pack(anchor="w", padx=5, pady=5)
        
        self.hub_label = tk.Label(result_frame, text="( -- , -- )", 
                                   font=("Consolas", 14, "bold"),
                                   bg=self.colors["surface"], fg=self.colors["success"])
        self.hub_label.pack(anchor="w", padx=5, pady=5)
        
        # Total distance
        tk.Label(result_frame, text="Total Distance:", font=("Arial", 10),
                 bg=self.colors["surface"], fg=self.colors["text"]).pack(anchor="w", padx=5)
        
        self.total_dist_label = tk.Label(result_frame, text="--", 
                                          font=("Consolas", 12, "bold"),
                                          bg=self.colors["surface"], fg=self.colors["accent"])
        self.total_dist_label.pack(anchor="w", padx=5, pady=5)
        
        # Iterations
        tk.Label(result_frame, text="Iterations:", font=("Arial", 10),
                 bg=self.colors["surface"], fg=self.colors["text"]).pack(anchor="w", padx=5)
        
        self.iter_label = tk.Label(result_frame, text="--", 
                                    font=("Consolas", 12),
                                    bg=self.colors["surface"], fg=self.colors["text"])
        self.iter_label.pack(anchor="w", padx=5, pady=5)
        
        # Distance breakdown
        tk.Label(parent, text="📏 Distance Breakdown:", font=("Arial", 10, "bold"),
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w", padx=15, pady=(15, 5))
        
        # Scrollable breakdown list
        breakdown_container = tk.Frame(parent, bg=self.colors["card"])
        breakdown_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        self.breakdown_canvas = tk.Canvas(breakdown_container, bg=self.colors["surface"],
                                          highlightthickness=0)
        scrollbar = ttk.Scrollbar(breakdown_container, orient="vertical",
                                  command=self.breakdown_canvas.yview)
        
        self.breakdown_frame = tk.Frame(self.breakdown_canvas, bg=self.colors["surface"])
        
        self.breakdown_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.breakdown_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.breakdown_window = self.breakdown_canvas.create_window(
            (0, 0), window=self.breakdown_frame, anchor="nw"
        )
        
        self.breakdown_frame.bind("<Configure>", self._on_breakdown_configure)
        self.breakdown_canvas.bind("<Configure>", self._on_breakdown_canvas_resize)
        
        # Summary stats
        summary_frame = tk.Frame(parent, bg=self.colors["surface"])
        summary_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(summary_frame, text="📈 Statistics", font=("Arial", 10, "bold"),
                 bg=self.colors["surface"], fg=self.colors["warning"]).pack(anchor="w", pady=5, padx=5)
        
        self.stats_labels = {}
        for stat in ["Min Distance:", "Max Distance:", "Avg Distance:", "Std Deviation:"]:
            frame = tk.Frame(summary_frame, bg=self.colors["surface"])
            frame.pack(fill=tk.X, padx=5, pady=2)
            tk.Label(frame, text=stat, font=("Arial", 9),
                     bg=self.colors["surface"], fg=self.colors["text"],
                     width=14, anchor="w").pack(side=tk.LEFT)
            lbl = tk.Label(frame, text="--", font=("Consolas", 9),
                          bg=self.colors["surface"], fg=self.colors["accent"])
            lbl.pack(side=tk.RIGHT, padx=5)
            self.stats_labels[stat] = lbl
    
    def _on_breakdown_configure(self, event):
        self.breakdown_canvas.configure(scrollregion=self.breakdown_canvas.bbox("all"))
    
    def _on_breakdown_canvas_resize(self, event):
        self.breakdown_canvas.itemconfig(self.breakdown_window, width=event.width)
    
    def _on_canvas_resize(self, event):
        self.draw_visualization()
    
    def _update_speed_label(self, *args):
        self.speed_label.config(text=f"{self.speed_var.get():.2f}s delay")
    
    def _load_preset(self, data, name):
        self.text_input.delete("1.0", tk.END)
        if data:
            self.text_input.insert("1.0", data)
        else:
            # Generate random
            import random
            n = random.randint(5, 10)
            points = []
            for _ in range(n):
                x = random.uniform(0, 20)
                y = random.uniform(0, 20)
                points.append(f"{x:.2f} {y:.2f}")
            self.text_input.insert("1.0", "\n".join(points))
        
        self.status_label.config(text=f"Loaded {name} preset")
        self._parse_and_draw()
    
    def toggle_click_mode(self):
        self.click_mode = not self.click_mode
        if self.click_mode:
            self.click_label.config(text="🖱️ Click mode ON - click canvas to add sensors")
            self.status_label.config(text="Click on the canvas to add sensor locations")
        else:
            self.click_label.config(text="")
            self.status_label.config(text="Click mode disabled")
    
    def on_canvas_click(self, event):
        if not self.click_mode:
            return
        
        # Convert canvas coords to data coords
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        margin = 50
        
        # Determine scale from existing sensors or use default
        if self.sensors:
            xs = [s[0] for s in self.sensors]
            ys = [s[1] for s in self.sensors]
            x_min, x_max = min(xs) - 2, max(xs) + 2
            y_min, y_max = min(ys) - 2, max(ys) + 2
        else:
            x_min, x_max = 0, 20
            y_min, y_max = 0, 20
        
        # Convert click to data coordinates
        x_scale = (width - 2 * margin) / (x_max - x_min)
        y_scale = (height - 2 * margin) / (y_max - y_min)
        
        data_x = x_min + (event.x - margin) / x_scale
        data_y = y_max - (event.y - margin) / y_scale
        
        # Add to text
        current = self.text_input.get("1.0", tk.END).strip()
        if current:
            self.text_input.insert(tk.END, f"\n{data_x:.2f} {data_y:.2f}")
        else:
            self.text_input.insert("1.0", f"{data_x:.2f} {data_y:.2f}")
        
        self._parse_and_draw()
    
    def _parse_and_draw(self):
        """Parse input and draw sensors"""
        try:
            raw = self.text_input.get("1.0", tk.END).strip()
            self.sensors = []
            for line in raw.split("\n"):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        x, y = float(parts[0]), float(parts[1])
                        self.sensors.append([x, y])
            
            self.hub = None
            self.draw_visualization()
            self.status_label.config(text=f"{len(self.sensors)} sensors loaded")
        except Exception as e:
            self.status_label.config(text=f"Parse error: {e}")
    
    def draw_visualization(self, iteration_hub=None):
        self.canvas.delete("all")
        
        if not self.sensors:
            self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() // 2,
                text="No sensors loaded",
                font=("Arial", 14),
                fill=self.colors["text"]
            )
            return
        
        width = self.canvas.winfo_width() or 600
        height = self.canvas.winfo_height() or 500
        margin = 50
        
        # Calculate bounds
        xs = [s[0] for s in self.sensors]
        ys = [s[1] for s in self.sensors]
        
        x_min, x_max = min(xs) - 2, max(xs) + 2
        y_min, y_max = min(ys) - 2, max(ys) + 2
        
        # Scale factors
        x_scale = (width - 2 * margin) / (x_max - x_min)
        y_scale = (height - 2 * margin) / (y_max - y_min)
        scale = min(x_scale, y_scale)
        
        def to_canvas(x, y):
            cx = margin + (x - x_min) * scale
            cy = height - margin - (y - y_min) * scale
            return cx, cy
        
        # Draw grid
        for i in range(int(x_min), int(x_max) + 1):
            cx, _ = to_canvas(i, 0)
            self.canvas.create_line(cx, margin, cx, height - margin,
                                   fill=self.colors["surface"], dash=(2, 4))
            self.canvas.create_text(cx, height - margin + 15, text=str(i),
                                   font=("Arial", 8), fill=self.colors["text"])
        
        for i in range(int(y_min), int(y_max) + 1):
            _, cy = to_canvas(0, i)
            self.canvas.create_line(margin, cy, width - margin, cy,
                                   fill=self.colors["surface"], dash=(2, 4))
            self.canvas.create_text(margin - 15, cy, text=str(i),
                                   font=("Arial", 8), fill=self.colors["text"])
        
        # Determine which hub to show
        display_hub = iteration_hub if iteration_hub is not None else self.hub
        
        # Draw lines to hub
        if display_hub is not None:
            hub_cx, hub_cy = to_canvas(display_hub[0], display_hub[1])
            for i, sensor in enumerate(self.sensors):
                sx, sy = to_canvas(sensor[0], sensor[1])
                self.canvas.create_line(sx, sy, hub_cx, hub_cy,
                                       fill=self.colors["line"], width=1, dash=(4, 2))
                
                # Distance label
                dist = np.linalg.norm(np.array(sensor) - np.array(display_hub))
                mid_x = (sx + hub_cx) / 2
                mid_y = (sy + hub_cy) / 2
                if len(self.sensors) <= 10:
                    self.canvas.create_text(mid_x, mid_y, text=f"{dist:.1f}",
                                           font=("Arial", 8), fill=self.colors["warning"])
        
        # Draw sensors
        for i, sensor in enumerate(self.sensors):
            cx, cy = to_canvas(sensor[0], sensor[1])
            r = 12
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                   fill=self.colors["sensor"], outline="white", width=2)
            self.canvas.create_text(cx, cy, text=f"S{i+1}",
                                   font=("Arial", 8, "bold"), fill="white")
        
        # Draw hub
        if display_hub is not None:
            hub_cx, hub_cy = to_canvas(display_hub[0], display_hub[1])
            r = 18
            self.canvas.create_oval(hub_cx - r, hub_cy - r, hub_cx + r, hub_cy + r,
                                   fill=self.colors["hub"], outline="white", width=3)
            self.canvas.create_text(hub_cx, hub_cy, text="★",
                                   font=("Arial", 14, "bold"), fill="white")
    
    def run_optimization(self):
        if self.is_running:
            return
        
        # Parse input
        self._parse_and_draw()
        
        if len(self.sensors) < 2:
            messagebox.showwarning("Warning", "Need at least 2 sensors")
            return
        
        self.is_running = True
        self.stop_requested = False
        self.run_btn.state(['disabled'])
        self.stop_btn.state(['!disabled'])
        self.progress["value"] = 0
        
        # Clear breakdown
        for widget in self.breakdown_frame.winfo_children():
            widget.destroy()
        
        def step_callback(iteration, hub, total_dist, movement):
            if self.stop_requested:
                return
            
            def update():
                self.draw_visualization(iteration_hub=hub)
                self.hub_label.config(text=f"( {hub[0]:.4f} , {hub[1]:.4f} )")
                self.total_dist_label.config(text=f"{total_dist:.4f}")
                self.iter_label.config(text=str(iteration))
                self.status_label.config(text=f"Iteration {iteration}: movement = {movement:.6f}")
                self.progress["value"] = min(100, iteration * 10)
            
            self.root.after(0, update)
            time.sleep(self.speed_var.get())
        
        def task():
            try:
                hub, total_dist, history = optimal_hub(
                    self.sensors, 
                    step_callback=step_callback if self.speed_var.get() > 0.05 else None
                )
                
                if not self.stop_requested:
                    self.hub = hub
                    self.root.after(0, lambda: self._on_complete(hub, total_dist, len(history)))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, self._reset_buttons)
        
        threading.Thread(target=task, daemon=True).start()
    
    def _on_complete(self, hub, total_dist, iterations):
        self.draw_visualization()
        self.progress["value"] = 100
        
        self.hub_label.config(text=f"( {hub[0]:.4f} , {hub[1]:.4f} )")
        self.total_dist_label.config(text=f"{total_dist:.4f}")
        self.iter_label.config(text=str(iterations))
        
        # Update breakdown
        distances = calculate_distances(self.sensors, hub)
        self._update_breakdown(distances)
        
        # Update stats
        dists = [d['distance'] for d in distances]
        self.stats_labels["Min Distance:"].config(text=f"{min(dists):.4f}")
        self.stats_labels["Max Distance:"].config(text=f"{max(dists):.4f}")
        self.stats_labels["Avg Distance:"].config(text=f"{np.mean(dists):.4f}")
        self.stats_labels["Std Deviation:"].config(text=f"{np.std(dists):.4f}")
        
        self.status_label.config(text=f"✅ Optimal hub found at ({hub[0]:.2f}, {hub[1]:.2f}) with total distance {total_dist:.2f}")
    
    def _update_breakdown(self, distances):
        for widget in self.breakdown_frame.winfo_children():
            widget.destroy()
        
        total = 0
        for d in distances:
            row = tk.Frame(self.breakdown_frame, bg=self.colors["surface"])
            row.pack(fill=tk.X, pady=2, padx=5)
            
            # Sensor label
            tk.Label(row, text=f"S{d['sensor']}", font=("Consolas", 9, "bold"),
                    bg=self.colors["surface"], fg=self.colors["sensor"],
                    width=4).pack(side=tk.LEFT)
            
            # Coordinates
            tk.Label(row, text=f"({d['coords'][0]:.1f}, {d['coords'][1]:.1f})",
                    font=("Consolas", 8), bg=self.colors["surface"],
                    fg=self.colors["text"], width=12).pack(side=tk.LEFT)
            
            # Distance
            tk.Label(row, text=f"{d['distance']:.4f}",
                    font=("Consolas", 9), bg=self.colors["surface"],
                    fg=self.colors["success"], width=10).pack(side=tk.LEFT)
            
            total += d['distance']
            
            # Cumulative
            tk.Label(row, text=f"Σ {total:.2f}",
                    font=("Consolas", 8), bg=self.colors["surface"],
                    fg=self.colors["warning"]).pack(side=tk.RIGHT)
        
        # Total row
        total_row = tk.Frame(self.breakdown_frame, bg=self.colors["accent"])
        total_row.pack(fill=tk.X, pady=5, padx=5)
        tk.Label(total_row, text=f"TOTAL: {total:.4f}",
                font=("Consolas", 10, "bold"), bg=self.colors["accent"],
                fg=self.colors["bg"]).pack(pady=3)
    
    def _reset_buttons(self):
        self.is_running = False
        self.run_btn.state(['!disabled'])
        self.stop_btn.state(['disabled'])
    
    def stop_optimization(self):
        self.stop_requested = True
        self.status_label.config(text="⏹️ Optimization stopped")
    
    def clear_all(self):
        self.text_input.delete("1.0", tk.END)
        self.sensors = []
        self.hub = None
        self.draw_visualization()
        
        # Reset labels
        self.hub_label.config(text="( -- , -- )")
        self.total_dist_label.config(text="--")
        self.iter_label.config(text="--")
        for lbl in self.stats_labels.values():
            lbl.config(text="--")
        
        # Clear breakdown
        for widget in self.breakdown_frame.winfo_children():
            widget.destroy()
        
        self.progress["value"] = 0
        self.status_label.config(text="Cleared. Enter new sensor coordinates.")

# -------------------------------
# Launch Application
# -------------------------------
if __name__ == "__main__":
    SensorHubApp()