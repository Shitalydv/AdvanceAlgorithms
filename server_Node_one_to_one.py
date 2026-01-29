"""
Minimum Service Centers — DP Visualization & Interactive GUI
===================================================================
Problem: Place minimum service centers on a tree so every node is covered
Root idea: Dynamic programming on tree (place / don't place recurrence)

Features:
- Tree presets (linear, balanced, skewed, full) + random tree generator
- Interactive Tk GUI with canvas visualization and colored node states
- Step-by-step DP animation with per-node processing, logging and delays
- DP recurrence shown and intermediate DP values displayed on nodes
- Manual toggling of centers, run/stop controls, and result summary
- Exportable visual snapshots via canvas (useful for reports)
"""



import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading

# -------------------------------
# Tree Node & DP Calculation
# -------------------------------
class TreeNode:
    def __init__(self, val=0, left=None, right=None, name=None):
        self.val = val
        self.left = left
        self.right = right
        self.name = name  # Node label
        self.center = False  # service center
        self.covered = False  # covered by parent/child
        self.processing = False  # currently being processed
        self.dp_not_placed = 0  # DP value when not placed
        self.dp_placed = 0  # DP value when placed

def min_service_centers_dp(node, animate=None, delay=0.5, step_callback=None):
    """
    Returns (not_placed, placed) - min centers needed.
    not_placed: node is NOT a center (must be covered by children who are centers)
    placed: node IS a center
    """
    if not node:
        return 0, 0

    # Mark as processing
    if animate:
        node.processing = True
        animate()
        if step_callback:
            step_callback(f"Processing node {node.name}...", "processing")
        time.sleep(delay)

    # Recursively solve for children
    left_not, left_placed = min_service_centers_dp(node.left, animate, delay, step_callback)
    right_not, right_placed = min_service_centers_dp(node.right, animate, delay, step_callback)

    # DP transitions:
    # If we place a center here: cost = 1 + min cost of left subtree + min cost of right subtree
    place_here = 1 + min(left_not, left_placed) + min(right_not, right_placed)
    
    # If we don't place here: children must have centers to cover themselves
    dont_place = left_placed + right_placed

    # Store DP values
    node.dp_not_placed = dont_place
    node.dp_placed = place_here

    if animate:
        node.processing = False
        # Decide based on DP
        if place_here <= dont_place:
            node.center = True
            node.covered = True
            if step_callback:
                step_callback(
                    f"Node {node.name}: Place center here (cost={place_here}) ≤ Don't place (cost={dont_place})",
                    "center"
                )
        else:
            node.center = False
            node.covered = True
            if step_callback:
                step_callback(
                    f"Node {node.name}: Don't place (cost={dont_place}) < Place here (cost={place_here})",
                    "covered"
                )
        animate()
        time.sleep(delay)

    return dont_place, place_here

def count_centers(node):
    """Count total centers in tree"""
    if not node:
        return 0
    count = 1 if node.center else 0
    return count + count_centers(node.left) + count_centers(node.right)

def get_tree_depth(node):
    """Get maximum depth of tree"""
    if not node:
        return 0
    return 1 + max(get_tree_depth(node.left), get_tree_depth(node.right))

def get_node_count(node):
    """Count total nodes in tree"""
    if not node:
        return 0
    return 1 + get_node_count(node.left) + get_node_count(node.right)

# -------------------------------
# GUI Class
# -------------------------------
class TreeGUI:
    def __init__(self):
        self.root_node = None
        self.node_coords = {}
        self.node_radius = 25
        self.is_running = False
        self.stop_requested = False
        
        self._setup_colors()
        self._setup_window()
        self._setup_ui()
        self._create_default_tree()
        
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
            "center": "#a6e3a1",      # Green for service centers
            "covered": "#f9e2af",      # Yellow for covered nodes
            "uncovered": "#89b4fa",    # Blue for uncovered
            "processing": "#f38ba8",   # Pink for currently processing
            "canvas_bg": "#1a1a2e"
        }

    def _setup_window(self):
        self.root = tk.Tk()
        self.root.title("🖧 Minimum Service Centers - DP Visualization")
        self.root.geometry("1200x800")
        self.root.configure(bg=self.colors["bg"])
        
        # Style
        style = ttk.Style()
        style.theme_use("clam")
        
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
        
        # Left panel - Controls
        left_panel = tk.Frame(main_frame, bg=self.colors["card"], width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_panel.pack_propagate(False)
        
        self._setup_controls(left_panel)
        
        # Middle panel - Tree visualization
        middle_panel = tk.Frame(main_frame, bg=self.colors["bg"])
        middle_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        self._setup_visualization(middle_panel)
        
        # Right panel - Algorithm steps
        right_panel = tk.Frame(main_frame, bg=self.colors["card"], width=320)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        
        self._setup_steps_panel(right_panel)

    def _setup_controls(self, parent):
        # Title
        tk.Label(parent, text="⚙️ Configuration", font=("Arial", 14, "bold"),
                 bg=self.colors["card"], fg=self.colors["accent"]).pack(pady=15)
        
        # Tree presets
        preset_frame = tk.Frame(parent, bg=self.colors["card"])
        preset_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(preset_frame, text="Tree Preset:", font=("Arial", 10),
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w")
        
        self.preset_var = tk.StringVar(value="Linear Chain")
        presets = ["Linear Chain", "Balanced Binary", "Left Skewed", "Full Binary", "Custom (Click)"]
        preset_menu = ttk.OptionMenu(preset_frame, self.preset_var, "Linear Chain", *presets,
                                     command=self._on_preset_change)
        preset_menu.pack(fill=tk.X, pady=5)
        
        # Animation speed
        speed_frame = tk.Frame(parent, bg=self.colors["card"])
        speed_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(speed_frame, text="Animation Speed:", font=("Arial", 10),
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w")
        
        self.speed_var = tk.DoubleVar(value=0.5)
        speed_scale = ttk.Scale(speed_frame, from_=0.1, to=2.0, variable=self.speed_var,
                                orient="horizontal")
        speed_scale.pack(fill=tk.X, pady=5)
        
        self.speed_label = tk.Label(speed_frame, text="0.5s delay", font=("Arial", 9),
                                    bg=self.colors["card"], fg=self.colors["text"])
        self.speed_label.pack()
        self.speed_var.trace("w", self._update_speed_label)
        
        # Buttons
        btn_frame = tk.Frame(parent, bg=self.colors["card"])
        btn_frame.pack(fill=tk.X, padx=15, pady=15)
        
        self.run_btn = ttk.Button(btn_frame, text="▶ Run DP Animation", 
                                  style="Run.TButton", command=self.run_animation)
        self.run_btn.pack(fill=tk.X, pady=3)
        
        self.stop_btn = ttk.Button(btn_frame, text="⬛ Stop", 
                                   style="Stop.TButton", command=self.stop_animation,
                                   state="disabled")
        self.stop_btn.pack(fill=tk.X, pady=3)
        
        ttk.Button(btn_frame, text="🔄 Reset Tree", style="Secondary.TButton",
                   command=self.reset_tree).pack(fill=tk.X, pady=3)
        
        ttk.Button(btn_frame, text="🎲 Random Tree", style="Secondary.TButton",
                   command=self.generate_random_tree).pack(fill=tk.X, pady=3)
        
        # Legend
        legend_frame = tk.Frame(parent, bg=self.colors["surface"])
        legend_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(legend_frame, text="📋 Legend", font=("Arial", 10, "bold"),
                 bg=self.colors["surface"], fg=self.colors["warning"]).pack(pady=5)
        
        legends = [
            ("🟢 Service Center", self.colors["center"]),
            ("🟡 Covered by Center", self.colors["covered"]),
            ("🔵 Uncovered Node", self.colors["uncovered"]),
            ("🔴 Processing", self.colors["processing"])
        ]
        
        for text, color in legends:
            row = tk.Frame(legend_frame, bg=self.colors["surface"])
            row.pack(fill=tk.X, padx=10, pady=2)
            tk.Canvas(row, width=15, height=15, bg=color, highlightthickness=1,
                     highlightbackground="white").pack(side=tk.LEFT, padx=5)
            tk.Label(row, text=text, font=("Arial", 9),
                    bg=self.colors["surface"], fg=self.colors["text"]).pack(side=tk.LEFT)
        
        # Stats
        stats_frame = tk.Frame(parent, bg=self.colors["card"])
        stats_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(stats_frame, text="📊 Statistics", font=("Arial", 10, "bold"),
                 bg=self.colors["card"], fg=self.colors["accent"]).pack(anchor="w", pady=5)
        
        self.stats_labels = {}
        for stat in ["Total Nodes:", "Tree Depth:", "Centers Used:", "Result:"]:
            frame = tk.Frame(stats_frame, bg=self.colors["card"])
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=stat, font=("Arial", 9),
                     bg=self.colors["card"], fg=self.colors["text"],
                     width=12, anchor="w").pack(side=tk.LEFT)
            lbl = tk.Label(frame, text="--", font=("Consolas", 10, "bold"),
                          bg=self.colors["card"], fg=self.colors["success"])
            lbl.pack(side=tk.RIGHT)
            self.stats_labels[stat] = lbl

    def _setup_visualization(self, parent):
        # Title
        tk.Label(parent, text="🌳 Tree Visualization", font=("Arial", 14, "bold"),
                 bg=self.colors["bg"], fg=self.colors["accent"]).pack(pady=(0, 10))
        
        # Canvas
        canvas_frame = tk.Frame(parent, bg=self.colors["card"])
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.colors["canvas_bg"], 
                                highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status
        self.status_label = tk.Label(parent, text="Click nodes to toggle centers manually, or run DP animation.",
                                     font=("Arial", 10), bg=self.colors["bg"],
                                     fg=self.colors["text"])
        self.status_label.pack(pady=10)

    def _setup_steps_panel(self, parent):
        # Title
        tk.Label(parent, text="📝 Algorithm Steps", font=("Arial", 14, "bold"),
                 bg=self.colors["card"], fg=self.colors["accent"]).pack(pady=15)
        
        # Algorithm explanation
        algo_frame = tk.Frame(parent, bg=self.colors["surface"])
        algo_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(algo_frame, text="DP Recurrence:", font=("Arial", 9, "bold"),
                 bg=self.colors["surface"], fg=self.colors["warning"]).pack(pady=5, anchor="w", padx=5)
        
        formulas = [
            "place[n] = 1 + min(L) + min(R)",
            "don't[n] = place[L] + place[R]",
            "Answer = min(place, don't)"
        ]
        for f in formulas:
            tk.Label(algo_frame, text=f, font=("Consolas", 9),
                     bg=self.colors["surface"], fg=self.colors["text"]).pack(anchor="w", padx=10)
        
        tk.Label(algo_frame, text="", bg=self.colors["surface"]).pack(pady=2)
        
        # Steps log
        tk.Label(parent, text="Execution Log:", font=("Arial", 10, "bold"),
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Scrollable text for steps
        log_container = tk.Frame(parent, bg=self.colors["card"])
        log_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        self.log_text = tk.Text(log_container, bg=self.colors["surface"], 
                                fg=self.colors["text"], font=("Consolas", 9),
                                wrap=tk.WORD, relief="flat", height=20)
        scrollbar = ttk.Scrollbar(log_container, orient="vertical", 
                                  command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure tags for colored text
        self.log_text.tag_configure("processing", foreground=self.colors["processing"])
        self.log_text.tag_configure("center", foreground=self.colors["center"])
        self.log_text.tag_configure("covered", foreground=self.colors["covered"])
        self.log_text.tag_configure("info", foreground=self.colors["accent"])
        self.log_text.tag_configure("result", foreground=self.colors["success"], 
                                    font=("Consolas", 10, "bold"))

    def _update_speed_label(self, *args):
        self.speed_label.config(text=f"{self.speed_var.get():.1f}s delay")

    def _on_preset_change(self, selection):
        if selection == "Linear Chain":
            self._create_linear_tree()
        elif selection == "Balanced Binary":
            self._create_balanced_tree()
        elif selection == "Left Skewed":
            self._create_left_skewed_tree()
        elif selection == "Full Binary":
            self._create_full_binary_tree()
        elif selection == "Custom (Click)":
            self.status_label.config(text="Click on canvas to build custom tree (not implemented yet)")
        self.draw_tree()
        self._update_stats()

    def _create_default_tree(self):
        self._create_linear_tree()
        self.draw_tree()
        self._update_stats()

    def _create_linear_tree(self):
        """Linear chain: 0 -> 0 -> 0 -> 0 -> 0"""
        self.root_node = TreeNode(0, name="A")
        self.root_node.left = TreeNode(0, name="B")
        self.root_node.left.left = TreeNode(0, name="C")
        self.root_node.left.left.left = TreeNode(0, name="D")
        self.root_node.left.left.left.right = TreeNode(0, name="E")

    def _create_balanced_tree(self):
        """Balanced binary tree with 7 nodes"""
        self.root_node = TreeNode(0, name="A")
        self.root_node.left = TreeNode(0, name="B")
        self.root_node.right = TreeNode(0, name="C")
        self.root_node.left.left = TreeNode(0, name="D")
        self.root_node.left.right = TreeNode(0, name="E")
        self.root_node.right.left = TreeNode(0, name="F")
        self.root_node.right.right = TreeNode(0, name="G")

    def _create_left_skewed_tree(self):
        """Left-skewed tree"""
        self.root_node = TreeNode(0, name="A")
        current = self.root_node
        for i, name in enumerate(["B", "C", "D", "E"]):
            current.left = TreeNode(0, name=name)
            current = current.left

    def _create_full_binary_tree(self):
        """Full binary tree with 15 nodes"""
        self.root_node = TreeNode(0, name="A")
        self.root_node.left = TreeNode(0, name="B")
        self.root_node.right = TreeNode(0, name="C")
        self.root_node.left.left = TreeNode(0, name="D")
        self.root_node.left.right = TreeNode(0, name="E")
        self.root_node.right.left = TreeNode(0, name="F")
        self.root_node.right.right = TreeNode(0, name="G")
        self.root_node.left.left.left = TreeNode(0, name="H")
        self.root_node.left.left.right = TreeNode(0, name="I")
        self.root_node.left.right.left = TreeNode(0, name="J")
        self.root_node.left.right.right = TreeNode(0, name="K")
        self.root_node.right.left.left = TreeNode(0, name="L")
        self.root_node.right.left.right = TreeNode(0, name="M")
        self.root_node.right.right.left = TreeNode(0, name="N")
        self.root_node.right.right.right = TreeNode(0, name="O")

    def generate_random_tree(self):
        """Generate a random tree structure"""
        import random
        
        depth = random.randint(3, 5)
        names = iter("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        
        def build_random(d):
            if d == 0 or random.random() < 0.3:
                return None
            try:
                name = next(names)
            except StopIteration:
                return None
            node = TreeNode(0, name=name)
            if d > 1:
                if random.random() > 0.3:
                    node.left = build_random(d - 1)
                if random.random() > 0.3:
                    node.right = build_random(d - 1)
            return node
        
        self.root_node = build_random(depth)
        if not self.root_node:
            self.root_node = TreeNode(0, name="A")
        
        self.reset_tree()
        self._update_stats()

    def draw_tree(self):
        self.canvas.delete("all")
        if not self.root_node:
            return
        
        self.node_coords = {}
        self.canvas.update()
        width = self.canvas.winfo_width() or 800
        height = self.canvas.winfo_height() or 500
        
        self._draw_node(self.root_node, width // 2, 50, width // 4)

    def _draw_node(self, node, x, y, x_offset):
        if not node:
            return
        
        # Draw children lines first (so they're behind nodes)
        if node.left:
            child_x = x - x_offset
            child_y = y + 80
            self.canvas.create_line(x, y, child_x, child_y, 
                                   fill=self.colors["text"], width=2)
            self._draw_node(node.left, child_x, child_y, max(x_offset // 2, 30))
        
        if node.right:
            child_x = x + x_offset
            child_y = y + 80
            self.canvas.create_line(x, y, child_x, child_y,
                                   fill=self.colors["text"], width=2)
            self._draw_node(node.right, child_x, child_y, max(x_offset // 2, 30))
        
        # Determine node color
        if node.processing:
            color = self.colors["processing"]
        elif node.center:
            color = self.colors["center"]
        elif node.covered:
            color = self.colors["covered"]
        else:
            color = self.colors["uncovered"]
        
        # Draw node circle
        r = self.node_radius
        circle = self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                         fill=color, outline="white", width=2)
        
        # Draw node label
        label = "★" if node.center else node.name
        text_color = self.colors["bg"] if node.center else self.colors["text"]
        self.canvas.create_text(x, y, text=label, font=("Arial", 12, "bold"),
                               fill=text_color)
        
        # Draw DP values if calculated
        if node.dp_placed > 0 or node.dp_not_placed > 0:
            dp_text = f"P:{node.dp_placed} N:{node.dp_not_placed}"
            self.canvas.create_text(x, y + r + 12, text=dp_text,
                                   font=("Arial", 8), fill=self.colors["warning"])
        
        # Store for click handling
        self.node_coords[circle] = node
        self.canvas.tag_bind(circle, "<Button-1>", self.toggle_center)

    def toggle_center(self, event):
        if self.is_running:
            return
        clicked = self.canvas.find_closest(event.x, event.y)[0]
        node = self.node_coords.get(clicked)
        if node:
            node.center = not node.center
            node.covered = node.center
            self.draw_tree()
            self._update_stats()

    def run_animation(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.stop_requested = False
        self.run_btn.state(['disabled'])
        self.stop_btn.state(['!disabled'])
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, "Starting DP algorithm...\n\n", "info")
        
        def animate():
            self.root.after(0, self.draw_tree)
        
        def step_callback(message, tag):
            def update():
                self.log_text.insert(tk.END, message + "\n", tag)
                self.log_text.see(tk.END)
            self.root.after(0, update)
        
        def task():
            try:
                self.reset_tree()
                time.sleep(0.3)
                
                delay = self.speed_var.get()
                dont_place, place_here = min_service_centers_dp(
                    self.root_node, animate, delay, step_callback
                )
                
                if not self.stop_requested:
                    result = min(dont_place, place_here)
                    self.root.after(0, lambda: self._on_complete(result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, self._reset_buttons)
        
        threading.Thread(target=task, daemon=True).start()

    def _on_complete(self, result):
        self.log_text.insert(tk.END, f"\n{'='*30}\n", "info")
        self.log_text.insert(tk.END, f"✅ RESULT: {result} service centers needed\n", "result")
        self.log_text.see(tk.END)
        
        self.stats_labels["Result:"].config(text=f"{result} centers")
        self.stats_labels["Centers Used:"].config(text=str(count_centers(self.root_node)))
        
        self.status_label.config(text=f"✅ Complete! Minimum {result} service centers required.")

    def _reset_buttons(self):
        self.is_running = False
        self.run_btn.state(['!disabled'])
        self.stop_btn.state(['disabled'])

    def stop_animation(self):
        self.stop_requested = True
        self.status_label.config(text="⏹️ Animation stopped.")

    def reset_tree(self):
        def reset(node):
            if node:
                node.center = False
                node.covered = False
                node.processing = False
                node.dp_placed = 0
                node.dp_not_placed = 0
                reset(node.left)
                reset(node.right)
        
        reset(self.root_node)
        self.draw_tree()
        self._update_stats()
        self.log_text.delete(1.0, tk.END)
        self.status_label.config(text="Tree reset. Ready to run.")

    def _update_stats(self):
        if self.root_node:
            self.stats_labels["Total Nodes:"].config(text=str(get_node_count(self.root_node)))
            self.stats_labels["Tree Depth:"].config(text=str(get_tree_depth(self.root_node)))
            self.stats_labels["Centers Used:"].config(text=str(count_centers(self.root_node)))
        else:
            for lbl in self.stats_labels.values():
                lbl.config(text="--")

# -------------------------------
# Launch Application
# -------------------------------
if __name__ == "__main__":
    TreeGUI()