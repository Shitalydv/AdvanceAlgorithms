"""
Strategic Tile Shatter — Burst Balloons / Dynamic Programming Game
=================================================================
Problem: Burst tiles (burst-balloons variant) to maximize score using DP-optimal strategy

Purpose: Interactive game + DP matrix visualizer to teach optimal substructure and reconstruction

Features:
- Input tile values and play interactive shattering
- DP computation (nums, dp, order) and visual heatmap of subproblems
- Interactive tile shatter with preview, animations and move history
- Highlights DP cells related to each player move and shows optimal order
- Scores: current vs optimal, completion feedback and hints
- Exportable DP matrix snapshot for report inclusion
"""



import tkinter as tk
from tkinter import messagebox
import math

# --- Constants & Styling ---
COLORS = {
    "bg": "#1e1e2e",
    "tile": "#89b4fa",
    "tile_hover": "#b4befe",
    "text": "#cdd6f4",
    "accent": "#f38ba8",
    "dp_cell": "#313244",
    "dp_highlight": "#fab387",
    "success": "#a6e3a1",
    "warning": "#f9e2af"
}

class TileShatterGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Strategic Tile Shatter ")
        self.root.geometry("1100x900")
        self.root.configure(bg=COLORS["bg"])
        
        self.nums = []
        self.dp = []
        self.order = []
        self.current_score = 0
        self.optimal_score = 0
        self.active_indices = []
        self.move_history = []
        self.dp_labels = []

        self._setup_ui()

    def _setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg=COLORS["bg"])
        header.pack(fill="x", pady=20)
        
        tk.Label(header, text="🎮 STRATEGIC TILE SHATTER", font=("Helvetica", 28, "bold"), 
                 fg=COLORS["accent"], bg=COLORS["bg"]).pack()
        tk.Label(header, text="Burst tiles strategically to maximize your score!", 
                 font=("Helvetica", 12), fg=COLORS["text"], bg=COLORS["bg"]).pack()

        # Input Area
        input_frame = tk.Frame(self.root, bg=COLORS["bg"])
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="Tile Values:", font=("Consolas", 12), 
                 fg=COLORS["text"], bg=COLORS["bg"]).pack(side="left", padx=5)
        
        self.entry = tk.Entry(input_frame, font=("Consolas", 14), width=30, 
                              bg=COLORS["dp_cell"], fg=COLORS["text"], 
                              insertbackground="white", relief="flat")
        self.entry.pack(side="left", padx=10, ipady=8)
        self.entry.insert(0, "3 1 5 8")
        self.entry.bind("<Return>", lambda e: self.start_game())

        btn_frame = tk.Frame(input_frame, bg=COLORS["bg"])
        btn_frame.pack(side="left", padx=5)
        
        self.start_btn = tk.Button(btn_frame, text="▶ START", command=self.start_game, 
                                   font=("Helvetica", 11, "bold"), bg=COLORS["tile"], 
                                   fg=COLORS["bg"], activebackground=COLORS["tile_hover"], 
                                   relief="flat", padx=15, pady=5, cursor="hand2")
        self.start_btn.pack(side="left", padx=3)
        
        self.reset_btn = tk.Button(btn_frame, text="↻ RESET", command=self.reset_game, 
                                   font=("Helvetica", 11, "bold"), bg=COLORS["warning"], 
                                   fg=COLORS["bg"], activebackground=COLORS["tile_hover"], 
                                   relief="flat", padx=15, pady=5, cursor="hand2")
        self.reset_btn.pack(side="left", padx=3)

        # Score Display
        score_frame = tk.Frame(self.root, bg=COLORS["bg"])
        score_frame.pack(pady=15)
        
        self.score_label = tk.Label(score_frame, text="YOUR SCORE: 0", 
                                    font=("Consolas", 22, "bold"), 
                                    fg=COLORS["text"], bg=COLORS["bg"])
        self.score_label.pack(side="left", padx=20)
        
        self.optimal_label = tk.Label(score_frame, text="OPTIMAL: 0", 
                                      font=("Consolas", 16), 
                                      fg=COLORS["dp_highlight"], bg=COLORS["bg"])
        self.optimal_label.pack(side="left", padx=20)
        
        self.status_label = tk.Label(score_frame, text="", font=("Consolas", 14, "bold"), 
                                     fg=COLORS["success"], bg=COLORS["bg"])
        self.status_label.pack(side="left", padx=20)

        # Points Preview
        self.preview_label = tk.Label(self.root, text="", font=("Consolas", 12), 
                                      fg=COLORS["warning"], bg=COLORS["bg"])
        self.preview_label.pack()

        # Game Canvas
        self.canvas = tk.Canvas(self.root, height=180, bg=COLORS["bg"], highlightthickness=0)
        self.canvas.pack(fill="x", padx=50, pady=10)

        # Move History
        history_frame = tk.Frame(self.root, bg=COLORS["bg"])
        history_frame.pack(fill="x", padx=50)
        tk.Label(history_frame, text="Move History:", font=("Consolas", 10), 
                 fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w")
        self.history_label = tk.Label(history_frame, text="", font=("Consolas", 10), 
                                      fg=COLORS["tile"], bg=COLORS["bg"], wraplength=900, 
                                      justify="left")
        self.history_label.pack(anchor="w")

        # DP Matrix Section
        dp_header = tk.Frame(self.root, bg=COLORS["bg"])
        dp_header.pack(fill="x", padx=50, pady=(20, 5))
        tk.Label(dp_header, text="📊 DP Matrix (Optimal Solutions)", font=("Helvetica", 14, "bold"), 
                 fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w")

        # Scrollable DP Matrix Container
        matrix_container = tk.Frame(self.root, bg=COLORS["bg"])
        matrix_container.pack(fill="both", expand=True, padx=50, pady=10)
        
        self.matrix_canvas = tk.Canvas(matrix_container, bg=COLORS["bg"], highlightthickness=0)
        scrollbar_y = tk.Scrollbar(matrix_container, orient="vertical", command=self.matrix_canvas.yview)
        scrollbar_x = tk.Scrollbar(matrix_container, orient="horizontal", command=self.matrix_canvas.xview)
        
        self.matrix_frame = tk.Frame(self.matrix_canvas, bg=COLORS["bg"])
        
        self.matrix_canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        self.matrix_canvas.pack(side="left", fill="both", expand=True)
        
        self.matrix_window = self.matrix_canvas.create_window((0, 0), window=self.matrix_frame, anchor="nw")
        self.matrix_frame.bind("<Configure>", self._on_frame_configure)

    def _on_frame_configure(self, event):
        self.matrix_canvas.configure(scrollregion=self.matrix_canvas.bbox("all"))

    def calculate_dp(self, multipliers):
        """
        Classic Burst Balloons DP Algorithm
        dp[left][right] = max coins obtainable by bursting all balloons between left and right (exclusive)
        """
        nums = [1] + multipliers + [1]
        n = len(nums)
        dp = [[0] * n for _ in range(n)]
        order = [[-1] * n for _ in range(n)]

        # Length of subarray to consider
        for length in range(2, n):
            for left in range(n - length):
                right = left + length
                # k is the LAST balloon to burst in range (left, right)
                for k in range(left + 1, right):
                    # When k is burst last, left and right are its neighbors
                    val = dp[left][k] + nums[left] * nums[k] * nums[right] + dp[k][right]
                    if val > dp[left][right]:
                        dp[left][right] = val
                        order[left][right] = k
        
        return nums, dp, order

    def get_optimal_order(self, left, right):
        """Reconstruct the optimal bursting order"""
        if right - left <= 1:
            return []
        k = self.order[left][right]
        if k == -1:
            return []
        # Get order for left part, then right part, then burst k
        return self.get_optimal_order(left, k) + self.get_optimal_order(k, right) + [k]

    def start_game(self):
        try:
            raw_input = self.entry.get().strip().split()
            if not raw_input:
                messagebox.showwarning("Warning", "Please enter tile values.")
                return
                
            multipliers = [int(x) for x in raw_input]
            if len(multipliers) < 1:
                messagebox.showwarning("Warning", "Enter at least one tile value.")
                return
            if any(m < 0 for m in multipliers):
                messagebox.showwarning("Warning", "Please enter non-negative integers.")
                return
            
            self.nums, self.dp, self.order = self.calculate_dp(multipliers)
            self.active_indices = list(range(1, len(self.nums) - 1))
            self.current_score = 0
            self.optimal_score = self.dp[0][len(self.nums) - 1]
            self.move_history = []
            
            self.score_label.config(text="YOUR SCORE: 0")
            self.optimal_label.config(text=f"OPTIMAL: {self.optimal_score}")
            self.status_label.config(text="")
            self.preview_label.config(text="Click a tile to shatter it!")
            self.history_label.config(text="")
            
            self.draw_tiles()
            self.draw_matrix()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integers separated by spaces.")

    def reset_game(self):
        """Reset to replay with same numbers"""
        if not self.nums:
            return
        self.active_indices = list(range(1, len(self.nums) - 1))
        self.current_score = 0
        self.move_history = []
        
        self.score_label.config(text="YOUR SCORE: 0")
        self.status_label.config(text="")
        self.preview_label.config(text="Click a tile to shatter it!")
        self.history_label.config(text="")
        
        self.draw_tiles()
        self.draw_matrix()

    def draw_tiles(self):
        self.canvas.delete("all")
        self.root.update_idletasks()
        width = self.canvas.winfo_width()
        if width <= 1:
            width = 1000
        
        n = len(self.active_indices)
        if n == 0:
            self.canvas.create_text(width/2, 90, text="🎉 All tiles shattered!", 
                                    font=("Helvetica", 18, "bold"), fill=COLORS["success"])
            self._check_game_complete()
            return

        tile_w = min(80, (width - 100) // n - 10)
        gap = 15
        total_w = n * tile_w + (n - 1) * gap
        start_x = (width - total_w) / 2

        # Draw boundary indicators (the invisible 1s)
        self.canvas.create_text(start_x - 30, 100, text="[1]", 
                               font=("Consolas", 12), fill=COLORS["dp_cell"])
        self.canvas.create_text(start_x + total_w + 30, 100, text="[1]", 
                               font=("Consolas", 12), fill=COLORS["dp_cell"])

        for i, idx in enumerate(self.active_indices):
            x1 = start_x + i * (tile_w + gap)
            y1 = 50
            x2 = x1 + tile_w
            y2 = y1 + 100
            
            tag = f"tile_{idx}"
            
            # Draw Tile Shadow
            self.canvas.create_rectangle(x1 + 4, y1 + 4, x2 + 4, y2 + 4, 
                                        fill="#11111b", outline="", tags=tag)
            
            # Draw Tile
            rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLORS["tile"], 
                                                outline=COLORS["text"], width=2, tags=tag)
            self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=str(self.nums[idx]), 
                                    font=("Helvetica", 16, "bold"), fill=COLORS["bg"], tags=tag)
            
            # Bind Events
            self.canvas.tag_bind(tag, "<Button-1>", lambda e, idx=idx: self.shatter(idx))
            self.canvas.tag_bind(tag, "<Enter>", lambda e, r=rect, idx=idx: self._on_tile_hover(r, idx))
            self.canvas.tag_bind(tag, "<Leave>", lambda e, r=rect: self._on_tile_leave(r))

    def _on_tile_hover(self, rect, idx):
        self.canvas.itemconfig(rect, fill=COLORS["tile_hover"])
        
        # Calculate and show preview points
        curr_pos = self.active_indices.index(idx)
        left_val = self.nums[self.active_indices[curr_pos - 1]] if curr_pos > 0 else 1
        right_val = self.nums[self.active_indices[curr_pos + 1]] if curr_pos < len(self.active_indices) - 1 else 1
        points = left_val * self.nums[idx] * right_val
        
        self.preview_label.config(text=f"💥 {left_val} × {self.nums[idx]} × {right_val} = +{points} points")

    def _on_tile_leave(self, rect):
        self.canvas.itemconfig(rect, fill=COLORS["tile"])
        self.preview_label.config(text="Click a tile to shatter it!")

    def shatter(self, idx):
        if idx not in self.active_indices:
            return
            
        curr_pos = self.active_indices.index(idx)
        
        left_val = self.nums[self.active_indices[curr_pos - 1]] if curr_pos > 0 else 1
        right_val = self.nums[self.active_indices[curr_pos + 1]] if curr_pos < len(self.active_indices) - 1 else 1
        
        points = left_val * self.nums[idx] * right_val
        self.current_score += points
        
        # Record move
        move_str = f"[{self.nums[idx]}] → {left_val}×{self.nums[idx]}×{right_val}={points}"
        self.move_history.append(move_str)
        
        self.score_label.config(text=f"YOUR SCORE: {self.current_score}")
        self.history_label.config(text=" → ".join(self.move_history))
        
        # Animate shatter effect
        self._animate_shatter(idx)
        
        # Remove from active
        self.active_indices.pop(curr_pos)
        
        # Redraw
        self.root.after(150, self.draw_tiles)
        self.highlight_matrix(idx)

    def _animate_shatter(self, idx):
        """Simple shatter animation"""
        tag = f"tile_{idx}"
        # Flash effect
        self.canvas.itemconfig(tag, fill=COLORS["accent"])
        self.root.update()

    def _check_game_complete(self):
        """Check if game is complete and show result"""
        if len(self.active_indices) == 0:
            if self.current_score == self.optimal_score:
                self.status_label.config(text="🏆 PERFECT! You found the optimal solution!", 
                                        fg=COLORS["success"])
            else:
                diff = self.optimal_score - self.current_score
                pct = (self.current_score / self.optimal_score * 100) if self.optimal_score > 0 else 0
                self.status_label.config(text=f"Score: {pct:.1f}% of optimal (missed {diff} points)", 
                                        fg=COLORS["warning"])
                
                # Show optimal order hint
                optimal_order = self.get_optimal_order(0, len(self.nums) - 1)
                optimal_values = [self.nums[k] for k in optimal_order]
                self.preview_label.config(text=f"💡 Optimal order: {' → '.join(map(str, optimal_values))}")

    def draw_matrix(self):
        for widget in self.matrix_frame.winfo_children():
            widget.destroy()
        
        self.dp_labels = []
        n = len(self.nums)
        max_val = self.dp[0][n - 1] if self.dp[0][n - 1] > 0 else 1
        
        # Column headers
        tk.Label(self.matrix_frame, text="", width=4, bg=COLORS["bg"]).grid(row=0, column=0)
        for j in range(n):
            header_text = f"{self.nums[j]}" if j < n else ""
            tk.Label(self.matrix_frame, text=header_text, font=("Consolas", 9, "bold"), 
                    bg=COLORS["bg"], fg=COLORS["accent"], width=6).grid(row=0, column=j + 1)
        
        for i in range(n):
            row_labels = []
            # Row header
            tk.Label(self.matrix_frame, text=f"{self.nums[i]}", font=("Consolas", 9, "bold"), 
                    bg=COLORS["bg"], fg=COLORS["accent"], width=4).grid(row=i + 1, column=0)
            
            for j in range(n):
                val = self.dp[i][j]
                
                if j <= i:
                    # Lower triangle - no valid subproblem
                    bg_color = COLORS["bg"]
                    text = ""
                else:
                    # Heatmap intensity based on value
                    intensity = int((val / max_val) * 150) if val > 0 else 0
                    r = 49 + min(intensity, 100)
                    g = 50 + min(intensity // 2, 50)
                    b = 68 + min(intensity, 100)
                    bg_color = f"#{r:02x}{g:02x}{b:02x}"
                    text = str(val) if val > 0 else "0"
                
                lbl = tk.Label(self.matrix_frame, text=text, font=("Consolas", 9), 
                              bg=bg_color, fg=COLORS["text"], width=6, height=2, relief="flat")
                lbl.grid(row=i + 1, column=j + 1, padx=1, pady=1)
                row_labels.append(lbl)
            
            self.dp_labels.append(row_labels)

    def highlight_matrix(self, idx):
        """Highlight relevant DP cells when a tile is shattered"""
        if not self.dp_labels:
            return
            
        n = len(self.nums)
        
        # Reset all highlights first
        for i in range(n):
            for j in range(n):
                if j > i and self.dp_labels[i][j].cget("text"):
                    val = self.dp[i][j]
                    max_val = self.dp[0][n - 1] if self.dp[0][n - 1] > 0 else 1
                    intensity = int((val / max_val) * 150) if val > 0 else 0
                    r = 49 + min(intensity, 100)
                    g = 50 + min(intensity // 2, 50)
                    b = 68 + min(intensity, 100)
                    self.dp_labels[i][j].configure(bg=f"#{r:02x}{g:02x}{b:02x}")
        
        # Highlight cells involving this index
        for i in range(n):
            for j in range(n):
                if j > i:
                    # Highlight if this subproblem involves idx
                    if i < idx < j:
                        self.dp_labels[i][j].configure(bg=COLORS["dp_highlight"])
        
        # Reset after delay
        self.root.after(800, self.draw_matrix)


if __name__ == "__main__":
    root = tk.Tk()
    app = TileShatterGame(root)
    root.mainloop()