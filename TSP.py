"""
TSP — Simulated Annealing Visualizer with Interactive UI
===================================================================
Problem: Find near-optimal tours for the Traveling Salesman Problem using Simulated Annealing

Purpose: Educational GUI to demonstrate SA behavior and neighborhood operators

Features:
- Generate random or custom city layouts; configurable N, temperature, cooling schedule
- Neighborhood operators: swap, 2-opt, or-opt (configurable)
- Multiple cooling schedules (exponential, linear, logarithmic, quadratic)
- Real-time visualization of current best tour, convergence plots and distance breakdown
- Progress controls (run/stop), seed option for reproducibility, and convergence/export tools
- Detailed per-edge distance breakdown and summary statistics for report inclusion
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import string
import time

# -------------------------------
# TSP + SA Functions
# -------------------------------
def generate_cities(N, x_range=(0, 500), y_range=(0, 500), seed=None):
    if seed is not None:
        np.random.seed(seed)
    xs = np.random.uniform(*x_range, N)
    ys = np.random.uniform(*y_range, N)
    return np.column_stack((xs, ys))

def euclidean_distance(a, b):
    return np.linalg.norm(a - b)

def total_distance(tour, cities):
    dist = 0
    N = len(tour)
    for i in range(N):
        dist += euclidean_distance(cities[tour[i]], cities[tour[(i + 1) % N]])
    return dist

def get_distance_breakdown(tour, cities):
    """Returns detailed breakdown of distances between consecutive cities"""
    breakdown = []
    N = len(tour)
    total = 0
    for i in range(N):
        city1_idx = tour[i]
        city2_idx = tour[(i + 1) % N]
        dist = euclidean_distance(cities[city1_idx], cities[city2_idx])
        total += dist
        breakdown.append({
            'from': city1_idx,
            'to': city2_idx,
            'distance': dist,
            'cumulative': total
        })
    return breakdown, total

def swap(tour):
    new_tour = tour[:]
    a, b = random.sample(range(len(new_tour)), 2)
    new_tour[a], new_tour[b] = new_tour[b], new_tour[a]
    return new_tour

def two_opt(tour):
    new_tour = tour[:]
    a, b = sorted(random.sample(range(len(new_tour)), 2))
    new_tour[a:b + 1] = new_tour[a:b + 1][::-1]
    return new_tour

def or_opt(tour):
    """Or-opt: Move a sequence of 1-3 cities to another position"""
    new_tour = tour[:]
    n = len(new_tour)
    if n < 4:
        return swap(new_tour)
    
    seq_len = random.randint(1, min(3, n - 2))
    start = random.randint(0, n - seq_len)
    segment = new_tour[start:start + seq_len]
    del new_tour[start:start + seq_len]
    insert_pos = random.randint(0, len(new_tour))
    new_tour[insert_pos:insert_pos] = segment
    return new_tour

def simulated_annealing(cities, initial_temp=1000, cooling='exponential', alpha=0.995, beta=1.0,
                        max_iter=10000, neighborhood='2-opt', seed=None, update_callback=None,
                        stop_flag=None):
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    
    N = len(cities)
    current = list(np.random.permutation(N))
    current_cost = total_distance(current, cities)
    best = current[:]
    best_cost = current_cost
    T = initial_temp
    
    cost_history = [best_cost]
    temp_history = [T]
    
    neighborhood_func = {
        'swap': swap,
        '2-opt': two_opt,
        'or-opt': or_opt
    }.get(neighborhood, two_opt)

    for k in range(1, max_iter + 1):
        # Check stop flag
        if stop_flag and stop_flag():
            break
            
        neighbor = neighborhood_func(current)
        neighbor_cost = total_distance(neighbor, cities)
        delta = neighbor_cost - current_cost
        
        if delta < 0 or random.random() < np.exp(-delta / max(T, 1e-10)):
            current = neighbor
            current_cost = neighbor_cost
            if current_cost < best_cost:
                best = current[:]
                best_cost = current_cost

        # Update callback for GUI visualization
        update_freq = max(1, max_iter // 200)
        if update_callback and k % update_freq == 0:
            progress = k / max_iter
            update_callback(best, best_cost, T, k, progress, cost_history[-100:])
        
        # Record history
        if k % max(1, max_iter // 500) == 0:
            cost_history.append(best_cost)
            temp_history.append(T)
        
        # Cooling schedule
        if cooling == 'exponential':
            T = initial_temp * (alpha ** k)
        elif cooling == 'linear':
            T = max(0.001, initial_temp - beta * k)
        elif cooling == 'logarithmic':
            T = initial_temp / (1 + np.log(1 + k))
        elif cooling == 'quadratic':
            T = initial_temp / (1 + alpha * (k ** 2))

        if T < 1e-8:
            break

    return best, best_cost, cost_history

# -------------------------------
# Main Application Class
# -------------------------------
class TSPApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🗺️ TSP - Simulated Annealing Visualizer")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1e1e2e")
        
        self.cities = None
        self.best_tour = None
        self.is_running = False
        self.stop_requested = False
        self.custom_cities = []
        
        self._setup_styles()
        self._setup_ui()
        
    def _setup_styles(self):
        self.colors = {
            "bg": "#1e1e2e",
            "card": "#313244",
            "accent": "#89b4fa",
            "accent2": "#f38ba8",
            "text": "#cdd6f4",
            "success": "#a6e3a1",
            "warning": "#f9e2af",
            "surface": "#45475a"
        }

        style = ttk.Style()
        style.theme_use("clam")

        # Buttons
        style.configure("Run.TButton", font=("Arial", 12, "bold"),
                        foreground="white", background=self.colors["accent"], padding=10)
        style.configure("Stop.TButton", font=("Arial", 12, "bold"),
                        foreground="white", background=self.colors["accent2"], padding=10)
        style.configure("Secondary.TButton", font=("Arial", 10),
                        foreground="white", background=self.colors["surface"], padding=6)

        style.map("Run.TButton", background=[("active", "#7aa2f7")])
        style.map("Stop.TButton", background=[("active", "#f7768e")])

        # Progressbar - simple configuration
        style.configure("TProgressbar",
                        troughcolor=self.colors["card"],
                        background=self.colors["success"],
                        thickness=20)

    def _setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - Controls
        left_panel = tk.Frame(main_frame, bg=self.colors["card"], width=320)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        self._setup_controls(left_panel)
        
        # Middle panel - Visualization
        middle_panel = tk.Frame(main_frame, bg=self.colors["bg"])
        middle_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self._setup_visualization(middle_panel)
        
        # Right panel - Distance Calculation
        right_panel = tk.Frame(main_frame, bg=self.colors["card"], width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        
        self._setup_distance_panel(right_panel)

    def _setup_controls(self, parent):
        # Title
        tk.Label(parent, text="⚙️ Configuration", font=("Arial", 14, "bold"),
                 bg=self.colors["card"], fg=self.colors["accent"]).pack(pady=15)
        
        # Input fields
        fields_frame = tk.Frame(parent, bg=self.colors["card"])
        fields_frame.pack(fill=tk.X, padx=15)
        
        self.entries = {}
        fields = [
            ("Number of Cities:", "N", "10"),
            ("Initial Temperature:", "temp", "5000"),
            ("Max Iterations:", "iter", "20000"),
            ("Alpha (exp):", "alpha", "0.9995"),
            ("Beta (linear):", "beta", "0.1"),
        ]
        
        for i, (label, key, default) in enumerate(fields):
            tk.Label(fields_frame, text=label, font=("Arial", 9),
                     bg=self.colors["card"], fg=self.colors["text"],
                     anchor="w").grid(row=i, column=0, sticky="w", pady=4)
            entry = tk.Entry(fields_frame, font=("Arial", 10), width=10,
                            bg=self.colors["surface"], fg=self.colors["text"],
                            insertbackground="white", relief="flat")
            entry.insert(0, default)
            entry.grid(row=i, column=1, sticky="e", pady=4, padx=(5, 0))
            self.entries[key] = entry
        
        # Dropdowns
        dropdown_frame = tk.Frame(parent, bg=self.colors["card"])
        dropdown_frame.pack(fill=tk.X, padx=15, pady=8)
        
        tk.Label(dropdown_frame, text="Neighborhood:", font=("Arial", 9),
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w")
        self.neigh_var = tk.StringVar(value="2-opt")
        neigh_menu = ttk.OptionMenu(dropdown_frame, self.neigh_var, "2-opt", 
                                    "2-opt", "swap", "or-opt")
        neigh_menu.pack(fill=tk.X, pady=3)
        
        tk.Label(dropdown_frame, text="Cooling Schedule:", font=("Arial", 9),
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w")
        self.cool_var = tk.StringVar(value="exponential")
        cool_menu = ttk.OptionMenu(dropdown_frame, self.cool_var, "exponential",
                                   "exponential", "linear", "logarithmic", "quadratic")
        cool_menu.pack(fill=tk.X, pady=3)
        
        # Seed option
        seed_frame = tk.Frame(parent, bg=self.colors["card"])
        seed_frame.pack(fill=tk.X, padx=15, pady=5)
        
        self.use_seed = tk.BooleanVar(value=True)
        tk.Checkbutton(seed_frame, text="Use fixed seed",
                       variable=self.use_seed, bg=self.colors["card"],
                       fg=self.colors["text"], selectcolor=self.colors["surface"],
                       activebackground=self.colors["card"], font=("Arial", 9)).pack(anchor="w")
        
        # Buttons
        btn_frame = tk.Frame(parent, bg=self.colors["card"])
        btn_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.run_btn = ttk.Button(btn_frame, text="▶ Run SA", style="Run.TButton",
                                  command=self.run_sa)
        self.run_btn.pack(fill=tk.X, pady=3)
        
        self.stop_btn = ttk.Button(btn_frame, text="⬛ Stop", style="Stop.TButton",
                                   command=self.stop_sa, state="disabled")
        self.stop_btn.pack(fill=tk.X, pady=3)
        
        ttk.Button(btn_frame, text="🎲 Generate Cities", style="Secondary.TButton",
                   command=self.generate_preview).pack(fill=tk.X, pady=3)
        
        ttk.Button(btn_frame, text="🖱️ Custom Cities", style="Secondary.TButton",
                   command=self.toggle_custom_mode).pack(fill=tk.X, pady=3)
        
        ttk.Button(btn_frame, text="📊 Convergence", style="Secondary.TButton",
                   command=self.show_convergence).pack(fill=tk.X, pady=3)
        
        # Progress bar
        tk.Label(parent, text="Progress:", font=("Arial", 9),
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w", padx=15)
        self.progress = ttk.Progressbar(parent, length=280, mode='determinate')
        self.progress.pack(padx=15, pady=5, fill=tk.X)
        
        # Stats
        stats_frame = tk.Frame(parent, bg=self.colors["card"])
        stats_frame.pack(fill=tk.X, padx=15, pady=5)
        
        self.stats_labels = {}
        for stat in ["Distance:", "Temperature:", "Iteration:", "Improvement:"]:
            frame = tk.Frame(stats_frame, bg=self.colors["card"])
            frame.pack(fill=tk.X, pady=1)
            tk.Label(frame, text=stat, font=("Arial", 8),
                     bg=self.colors["card"], fg=self.colors["text"],
                     width=11, anchor="w").pack(side=tk.LEFT)
            lbl = tk.Label(frame, text="--", font=("Consolas", 9, "bold"),
                          bg=self.colors["card"], fg=self.colors["success"])
            lbl.pack(side=tk.RIGHT)
            self.stats_labels[stat] = lbl

    def _setup_visualization(self, parent):
        # Title
        tk.Label(parent, text="🗺️ Tour Visualization", font=("Arial", 14, "bold"),
                 bg=self.colors["bg"], fg=self.colors["accent"]).pack(pady=(0, 10))
        
        # Canvas for tour
        canvas_frame = tk.Frame(parent, bg=self.colors["card"], relief="flat")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tour_canvas = tk.Canvas(canvas_frame, bg="#1a1a2e", highlightthickness=0)
        self.tour_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bind for custom cities
        self.custom_mode = False
        self.tour_canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Status bar
        self.status_label = tk.Label(parent, text="Ready. Configure parameters and click Run.",
                                     font=("Arial", 10), bg=self.colors["bg"],
                                     fg=self.colors["text"])
        self.status_label.pack(pady=10)
        
        # Cost history for convergence plot
        self.cost_history = []
        self.initial_cost = 0

    def _setup_distance_panel(self, parent):
        """Setup the distance calculation display panel"""
        # Title
        tk.Label(parent, text="📏 Distance Calculation", font=("Arial", 14, "bold"),
                 bg=self.colors["card"], fg=self.colors["accent"]).pack(pady=15)
        
        # Formula display
        formula_frame = tk.Frame(parent, bg=self.colors["surface"], relief="flat")
        formula_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(formula_frame, text="Euclidean Distance Formula:", 
                 font=("Arial", 9, "bold"),
                 bg=self.colors["surface"], fg=self.colors["warning"]).pack(pady=5)
        tk.Label(formula_frame, text="d = √[(x₂-x₁)² + (y₂-y₁)²]", 
                 font=("Consolas", 11),
                 bg=self.colors["surface"], fg=self.colors["text"]).pack(pady=5)
        
        # Total distance display
        total_frame = tk.Frame(parent, bg=self.colors["card"])
        total_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(total_frame, text="Total Tour Distance:", font=("Arial", 10, "bold"),
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w")
        self.total_distance_label = tk.Label(total_frame, text="--", 
                                              font=("Consolas", 16, "bold"),
                                              bg=self.colors["card"], 
                                              fg=self.colors["success"])
        self.total_distance_label.pack(anchor="w", pady=5)
        
        # Scrollable breakdown list
        tk.Label(parent, text="Step-by-Step Breakdown:", font=("Arial", 10, "bold"),
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Create scrollable frame
        breakdown_container = tk.Frame(parent, bg=self.colors["card"])
        breakdown_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Canvas and scrollbar for scrolling
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
        self.breakdown_canvas.bind("<Configure>", self._on_canvas_resize)
        
        # Bind mouse wheel for scrolling
        self.breakdown_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Summary section
        summary_frame = tk.Frame(parent, bg=self.colors["surface"])
        summary_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(summary_frame, text="📊 Summary", font=("Arial", 10, "bold"),
                 bg=self.colors["surface"], fg=self.colors["warning"]).pack(anchor="w", pady=5, padx=5)
        
        self.summary_labels = {}
        for label_text in ["Shortest Edge:", "Longest Edge:", "Average Edge:"]:
            frame = tk.Frame(summary_frame, bg=self.colors["surface"])
            frame.pack(fill=tk.X, padx=5, pady=2)
            tk.Label(frame, text=label_text, font=("Arial", 9),
                     bg=self.colors["surface"], fg=self.colors["text"],
                     width=14, anchor="w").pack(side=tk.LEFT)
            lbl = tk.Label(frame, text="--", font=("Consolas", 9),
                          bg=self.colors["surface"], fg=self.colors["accent"])
            lbl.pack(side=tk.RIGHT, padx=5)
            self.summary_labels[label_text] = lbl

    def _on_breakdown_configure(self, event):
        self.breakdown_canvas.configure(scrollregion=self.breakdown_canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self.breakdown_canvas.itemconfig(self.breakdown_window, width=event.width)

    def _on_mousewheel(self, event):
        self.breakdown_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def update_distance_display(self, tour):
        """Update the distance calculation breakdown display"""
        if self.cities is None or tour is None or len(tour) < 2:
            return
        
        # Clear previous breakdown
        for widget in self.breakdown_frame.winfo_children():
            widget.destroy()
        
        letters = list(string.ascii_uppercase) + [f"{i}" for i in range(26, 100)]
        
        # Get breakdown
        breakdown, total = get_distance_breakdown(tour, self.cities)
        
        # Update total distance
        self.total_distance_label.config(text=f"{total:.2f} units")
        
        # Create breakdown entries
        distances = []
        for i, step in enumerate(breakdown):
            from_city = letters[step['from']]
            to_city = letters[step['to']]
            dist = step['distance']
            cumulative = step['cumulative']
            distances.append(dist)
            
            # Create row frame
            row = tk.Frame(self.breakdown_frame, bg=self.colors["surface"])
            row.pack(fill=tk.X, pady=1, padx=3)
            
            # Step number
            step_lbl = tk.Label(row, text=f"{i+1}.", font=("Consolas", 8),
                               bg=self.colors["surface"], fg=self.colors["text"],
                               width=3, anchor="e")
            step_lbl.pack(side=tk.LEFT)
            
            # Cities
            cities_lbl = tk.Label(row, text=f"{from_city}→{to_city}", 
                                  font=("Consolas", 9, "bold"),
                                  bg=self.colors["surface"], fg=self.colors["accent"],
                                  width=6, anchor="w")
            cities_lbl.pack(side=tk.LEFT, padx=3)
            
            # Distance
            dist_lbl = tk.Label(row, text=f"{dist:.2f}", font=("Consolas", 9),
                               bg=self.colors["surface"], fg=self.colors["success"],
                               width=8, anchor="e")
            dist_lbl.pack(side=tk.LEFT, padx=3)
            
            # Cumulative (running total)
            cum_lbl = tk.Label(row, text=f"Σ {cumulative:.2f}", font=("Consolas", 8),
                              bg=self.colors["surface"], fg=self.colors["warning"],
                              width=10, anchor="e")
            cum_lbl.pack(side=tk.RIGHT)
        
        # Add final row showing return to start
        final_row = tk.Frame(self.breakdown_frame, bg=self.colors["accent"])
        final_row.pack(fill=tk.X, pady=3, padx=3)
        tk.Label(final_row, text=f"TOTAL: {total:.2f} units", 
                 font=("Consolas", 10, "bold"),
                 bg=self.colors["accent"], fg=self.colors["bg"]).pack(pady=3)
        
        # Update summary statistics
        if distances:
            self.summary_labels["Shortest Edge:"].config(text=f"{min(distances):.2f}")
            self.summary_labels["Longest Edge:"].config(text=f"{max(distances):.2f}")
            self.summary_labels["Average Edge:"].config(text=f"{sum(distances)/len(distances):.2f}")
        
        # Reset scroll position
        self.breakdown_canvas.yview_moveto(0)

    def generate_preview(self):
        try:
            N = int(self.entries["N"].get())
            if N < 3:
                messagebox.showwarning("Warning", "Need at least 3 cities")
                return
            if N > 100:
                messagebox.showwarning("Warning", "Maximum 100 cities for visualization")
                return
                
            seed = 42 if self.use_seed.get() else None
            self.cities = generate_cities(N, x_range=(50, 550), y_range=(50, 550), seed=seed)
            self.custom_cities = []
            self.custom_mode = False
            self.draw_cities()
            
            # Show initial tour distance
            initial_tour = list(range(len(self.cities)))
            self.update_distance_display(initial_tour)
            
            self.status_label.config(text=f"Generated {N} random cities. Ready to run.")
        except ValueError:
            messagebox.showerror("Error", "Invalid number of cities")

    def toggle_custom_mode(self):
        self.custom_mode = not self.custom_mode
        if self.custom_mode:
            self.custom_cities = []
            self.cities = None
            self.tour_canvas.delete("all")
            self.status_label.config(text="🖱️ Click on canvas to add cities. Min 3 required.")
            self.tour_canvas.create_text(300, 300, text="Click to add cities",
                                        font=("Arial", 14), fill=self.colors["text"])
            # Clear distance display
            self.total_distance_label.config(text="--")
            for widget in self.breakdown_frame.winfo_children():
                widget.destroy()
        else:
            self.status_label.config(text="Custom mode disabled.")

    def on_canvas_click(self, event):
        if not self.custom_mode:
            return
        
        self.custom_cities.append([event.x, event.y])
        self.cities = np.array(self.custom_cities)
        self.draw_cities()
        
        # Update distance display for custom cities
        if len(self.custom_cities) >= 2:
            initial_tour = list(range(len(self.cities)))
            self.update_distance_display(initial_tour)
        
        self.status_label.config(text=f"Added city #{len(self.custom_cities)}. "
                                 f"({len(self.custom_cities)} total)")

    def draw_cities(self, tour=None):
        self.tour_canvas.delete("all")
        if self.cities is None or len(self.cities) == 0:
            return
        
        letters = list(string.ascii_uppercase) + [f"{i}" for i in range(26, 100)]
        
        # Draw tour path if provided
        if tour is not None and len(tour) > 1:
            for i in range(len(tour)):
                c1 = self.cities[tour[i]]
                c2 = self.cities[tour[(i + 1) % len(tour)]]
                
                # Draw edge with distance label
                mid_x = (c1[0] + c2[0]) / 2
                mid_y = (c1[1] + c2[1]) / 2
                dist = euclidean_distance(c1, c2)
                
                self.tour_canvas.create_line(c1[0], c1[1], c2[0], c2[1],
                                            fill=self.colors["accent"], width=2)
                
                # Show distance on edge (only for small tours to avoid clutter)
                if len(tour) <= 15:
                    self.tour_canvas.create_text(mid_x, mid_y, text=f"{dist:.1f}",
                                                font=("Arial", 7), fill=self.colors["warning"])
        
        # Draw cities
        for i, (x, y) in enumerate(self.cities):
            color = self.colors["accent2"] if i == 0 else self.colors["success"]
            self.tour_canvas.create_oval(x - 8, y - 8, x + 8, y + 8, 
                                         fill=color, outline="white", width=2)
            self.tour_canvas.create_text(x, y - 18, text=letters[i],
                                        font=("Arial", 9, "bold"), fill=self.colors["text"])

    def run_sa(self):
        if self.is_running:
            return
            
        # Validate inputs
        try:
            N = int(self.entries["N"].get())
            initial_temp = float(self.entries["temp"].get())
            max_iter = int(self.entries["iter"].get())
            alpha = float(self.entries["alpha"].get())
            beta = float(self.entries["beta"].get())
            
            if N < 3:
                messagebox.showwarning("Warning", "Need at least 3 cities")
                return
            if initial_temp <= 0:
                messagebox.showwarning("Warning", "Temperature must be positive")
                return
            if not (0 < alpha < 1):
                messagebox.showwarning("Warning", "Alpha must be between 0 and 1")
                return
                
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
            return
        
        # Generate cities if not custom
        if self.cities is None or len(self.cities) != N:
            if self.custom_mode and len(self.custom_cities) >= 3:
                self.cities = np.array(self.custom_cities)
            else:
                seed = 42 if self.use_seed.get() else None
                self.cities = generate_cities(N, x_range=(50, 550), y_range=(50, 550), seed=seed)
        
        self.is_running = True
        self.stop_requested = False
        self.cost_history = []
        self.progress["value"] = 0
        
        self.run_btn.state(['disabled'])
        self.stop_btn.state(['!disabled'])
        
        def update_callback(tour, cost, temp, iteration, progress, history):
            self.root.after(0, lambda: self._update_display(tour, cost, temp, iteration, progress, history))
        
        def task():
            try:
                seed = 42 if self.use_seed.get() else None
                
                # Calculate initial distance
                initial_tour = list(range(len(self.cities)))
                self.initial_cost = total_distance(initial_tour, self.cities)
                
                best_tour, best_cost, history = simulated_annealing(
                    self.cities,
                    initial_temp=initial_temp,
                    cooling=self.cool_var.get(),
                    alpha=alpha,
                    beta=beta,
                    max_iter=max_iter,
                    neighborhood=self.neigh_var.get(),
                    seed=seed,
                    update_callback=update_callback,
                    stop_flag=lambda: self.stop_requested
                )
                
                self.best_tour = best_tour
                self.cost_history = history
                
                self.root.after(0, lambda: self._on_complete(best_tour, best_cost))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, self._reset_buttons)
        
        threading.Thread(target=task, daemon=True).start()

    def _update_display(self, tour, cost, temp, iteration, progress, history):
        self.draw_cities(tour)
        self.progress["value"] = progress * 100
        
        self.stats_labels["Distance:"].config(text=f"{cost:.2f}")
        self.stats_labels["Temperature:"].config(text=f"{temp:.4f}")
        self.stats_labels["Iteration:"].config(text=f"{iteration}")
        
        if self.initial_cost > 0:
            improvement = ((self.initial_cost - cost) / self.initial_cost) * 100
            self.stats_labels["Improvement:"].config(text=f"{improvement:.1f}%")
        
        self.status_label.config(text=f"Running... Best distance: {cost:.2f}")
        
        # Update distance breakdown (less frequently to avoid lag)
        if iteration % 1000 == 0 or progress >= 0.99:
            self.update_distance_display(tour)

    def _on_complete(self, tour, cost):
        self.draw_cities(tour)
        self.progress["value"] = 100
        
        # Update distance display with final tour
        self.update_distance_display(tour)
        
        letters = list(string.ascii_uppercase) + [f"{i}" for i in range(26, 100)]
        tour_str = " → ".join([letters[i] for i in tour[:10]])
        if len(tour) > 10:
            tour_str += f" ... ({len(tour)} cities)"
        
        self.status_label.config(text=f"✅ Complete! Best: {cost:.2f} | Tour: {tour_str}")
        
        if self.initial_cost > 0:
            improvement = ((self.initial_cost - cost) / self.initial_cost) * 100
            self.stats_labels["Improvement:"].config(text=f"{improvement:.1f}%")

    def _reset_buttons(self):
        self.is_running = False
        self.run_btn.state(['!disabled'])
        self.stop_btn.state(['disabled'])

    def stop_sa(self):
        self.stop_requested = True
        self.status_label.config(text="⏹️ Stopping...")

    def show_convergence(self):
        if not self.cost_history:
            messagebox.showinfo("Info", "Run the algorithm first to see convergence")
            return
        
        plt.figure(figsize=(10, 6))
        plt.subplot(1, 1, 1)
        plt.plot(self.cost_history, color='#89b4fa', linewidth=2)
        plt.xlabel('Iterations (sampled)')
        plt.ylabel('Best Distance')
        plt.title('SA Convergence - Distance over Time')
        plt.grid(True, alpha=0.3)
        
        # Add improvement annotation
        if len(self.cost_history) > 1:
            initial = self.cost_history[0]
            final = self.cost_history[-1]
            improvement = ((initial - final) / initial) * 100
            plt.annotate(f'Improvement: {improvement:.1f}%', 
                        xy=(len(self.cost_history) - 1, final),
                        xytext=(len(self.cost_history) * 0.7, (initial + final) / 2),
                        arrowprops=dict(arrowstyle='->', color='red'),
                        fontsize=12, color='green')
        
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = TSPApp(root)
    root.mainloop()