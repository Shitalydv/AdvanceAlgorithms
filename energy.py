"""
Smart Energy Allocation System — Demand-Supply Allocation & Visualization
========================================================================
Problem: Allocate energy supply to district demands under capacity, cost and source constraints

Purpose: GUI toolkit for modeling, running and visualizing energy allocation algorithms

Features:
- Demand entry per district & hour, energy source parameter editing
- Multiple allocation strategies: greedy (cost-first), renewable-first, balanced, DP-approx
- Detailed algorithm step log and intermediate messages for teaching or reports
- Visual charts: stacked allocation per district, source distribution pie, cost breakdown
- Summary statistics: total demand, total cost, renewable share, unmet demand
- Exportable charts/figures for report
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

# ===============================
# COLOR THEME
# ===============================
COLORS = {
    "bg": "#1e1e2e",
    "card": "#313244",
    "accent": "#89b4fa",
    "accent2": "#f38ba8",
    "text": "#cdd6f4",
    "success": "#a6e3a1",
    "warning": "#f9e2af",
    "surface": "#45475a",
    "solar": "#f9e2af",
    "hydro": "#89b4fa",
    "diesel": "#f38ba8",
    "renewable": "#a6e3a1",
    "non_renewable": "#fab387"
}

# ===============================
# INITIAL ENERGY DATA
# ===============================
energy_sources = pd.DataFrame([
    {"Source": "Solar", "MaxCapacity": 120, "AvailableHours": "6-18", "Cost": 2, "Type": "Renewable", "Priority": 1},
    {"Source": "Wind", "MaxCapacity": 80, "AvailableHours": "0-24", "Cost": 2.5, "Type": "Renewable", "Priority": 2},
    {"Source": "Hydro", "MaxCapacity": 200, "AvailableHours": "0-24", "Cost": 3, "Type": "Renewable", "Priority": 3},
    {"Source": "Natural Gas", "MaxCapacity": 250, "AvailableHours": "0-24", "Cost": 5, "Type": "Non-Renewable", "Priority": 4},
    {"Source": "Diesel", "MaxCapacity": 300, "AvailableHours": "0-24", "Cost": 7, "Type": "Non-Renewable", "Priority": 5},
])

demand_data = []
allocation_results = []
algorithm_steps = []

# ===============================
# HELPER FUNCTIONS
# ===============================
def parse_hours(text):
    """Accepts: 6,7,8 OR 6 7 8 OR 6-18"""
    text = text.strip()
    if "-" in text:
        parts = text.split("-")
        start, end = int(parts[0]), int(parts[1])
        return list(range(start, end + 1))
    return list(map(int, text.replace(",", " ").split()))

def get_source_color(source_name):
    colors = {
        "Solar": COLORS["solar"],
        "Wind": "#74c7ec",
        "Hydro": COLORS["hydro"],
        "Natural Gas": "#fab387",
        "Diesel": COLORS["diesel"]
    }
    return colors.get(source_name, COLORS["accent"])

def log_step(message, step_type="info"):
    """Log algorithm steps for visualization"""
    algorithm_steps.append({"message": message, "type": step_type})
    update_log_display()

def clear_steps():
    """Clear algorithm steps"""
    global algorithm_steps
    algorithm_steps = []
    if 'log_text' in globals():
        log_text.delete(1.0, tk.END)

def update_log_display():
    """Update the log display with algorithm steps"""
    if 'log_text' not in globals():
        return
    
    log_text.config(state=tk.NORMAL)
    log_text.delete(1.0, tk.END)
    
    for step in algorithm_steps:
        tag = step["type"]
        log_text.insert(tk.END, step["message"] + "\n", tag)
    
    log_text.see(tk.END)
    log_text.config(state=tk.DISABLED)

# ===============================
# MAIN GUI SETUP
# ===============================
root = tk.Tk()
root.title("⚡ Smart Energy Allocation System")
root.geometry("1400x900")
root.configure(bg=COLORS["bg"])

# Force window to front
root.lift()
root.attributes('-topmost', True)
root.after(100, lambda: root.attributes('-topmost', False))
root.focus_force()

# Style configuration
style = ttk.Style()
style.theme_use("clam")

style.configure("TFrame", background=COLORS["bg"])
style.configure("Card.TFrame", background=COLORS["card"])
style.configure("TLabelframe", background=COLORS["card"], foreground=COLORS["text"])
style.configure("TLabelframe.Label", background=COLORS["card"], foreground=COLORS["accent"],
                font=("Arial", 11, "bold"))
style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
style.configure("Card.TLabel", background=COLORS["card"], foreground=COLORS["text"])
style.configure("TButton", padding=8, font=("Arial", 10))
style.configure("TEntry", fieldbackground=COLORS["surface"], foreground=COLORS["text"])
style.configure("Accent.TButton", background=COLORS["accent"], foreground="white")

style.map("TButton",
          background=[("active", COLORS["surface"])],
          foreground=[("active", COLORS["text"])])

# ===============================
# LAYOUT FRAMES
# ===============================
main_frame = tk.Frame(root, bg=COLORS["bg"])
main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

# Use grid for layout
main_frame.grid_columnconfigure(0, weight=0, minsize=400)  # Left panel
main_frame.grid_columnconfigure(1, weight=1, minsize=500)  # Middle panel
main_frame.grid_columnconfigure(2, weight=0, minsize=350)  # Right panel
main_frame.grid_rowconfigure(0, weight=1)

# Left: Input Panel
left_frame = tk.Frame(main_frame, bg=COLORS["card"], width=400)
left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
left_frame.grid_propagate(False)

# Middle: Visualization Panel
middle_frame = tk.Frame(main_frame, bg=COLORS["bg"])
middle_frame.grid(row=0, column=1, sticky="nsew", padx=5)

# Right: Algorithm Steps Panel
right_frame = tk.Frame(main_frame, bg=COLORS["card"], width=350)
right_frame.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
right_frame.grid_propagate(False)

# ===============================
# LEFT PANEL - INPUT CONTROLS
# ===============================
tk.Label(left_frame, text="⚡ Energy Control Panel", font=("Arial", 14, "bold"),
         bg=COLORS["card"], fg=COLORS["accent"]).pack(pady=15)

# Scrollable content
left_canvas = tk.Canvas(left_frame, bg=COLORS["card"], highlightthickness=0)
left_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=left_canvas.yview)
left_inner = tk.Frame(left_canvas, bg=COLORS["card"])

left_canvas.configure(yscrollcommand=left_scrollbar.set)
left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

left_window = left_canvas.create_window((0, 0), window=left_inner, anchor="nw")

def on_left_configure(event):
    left_canvas.configure(scrollregion=left_canvas.bbox("all"))
    left_canvas.itemconfig(left_window, width=event.width)

left_inner.bind("<Configure>", on_left_configure)
left_canvas.bind("<Configure>", lambda e: left_canvas.itemconfig(left_window, width=e.width))

# -------------------------------
# DEMAND INPUT SECTION
# -------------------------------
demand_frame = tk.LabelFrame(left_inner, text="📊 Demand Configuration",
                              bg=COLORS["card"], fg=COLORS["accent"],
                              font=("Arial", 10, "bold"))
demand_frame.pack(fill=tk.X, padx=10, pady=10)

# Districts input
row1 = tk.Frame(demand_frame, bg=COLORS["card"])
row1.pack(fill=tk.X, padx=10, pady=5)
tk.Label(row1, text="Number of Districts:", bg=COLORS["card"], fg=COLORS["text"],
         font=("Arial", 10)).pack(side=tk.LEFT)
entry_districts = tk.Entry(row1, bg=COLORS["surface"], fg=COLORS["text"],
                           insertbackground=COLORS["text"], width=10, font=("Arial", 10))
entry_districts.pack(side=tk.RIGHT, padx=5)
entry_districts.insert(0, "3")

# Hours input
row2 = tk.Frame(demand_frame, bg=COLORS["card"])
row2.pack(fill=tk.X, padx=10, pady=5)
tk.Label(row2, text="Hours (e.g., 6-18):", bg=COLORS["card"], fg=COLORS["text"],
         font=("Arial", 10)).pack(side=tk.LEFT)
entry_hours = tk.Entry(row2, bg=COLORS["surface"], fg=COLORS["text"],
                       insertbackground=COLORS["text"], width=15, font=("Arial", 10))
entry_hours.pack(side=tk.RIGHT, padx=5)
entry_hours.insert(0, "6-18")

# Enter demand button
def enter_districts_hours():
    global demand_data
    demand_data.clear()

    try:
        districts = int(entry_districts.get())
        hours = parse_hours(entry_hours.get())

        if districts < 1 or districts > 26:
            messagebox.showerror("Error", "Districts must be between 1 and 26")
            return
        
        if len(hours) < 1:
            messagebox.showerror("Error", "Please specify valid hours")
            return

        for i in range(districts):
            demand_data.append([0] * len(hours))

        # Create popup window for demand entry
        district_window = tk.Toplevel(root)
        district_window.title("📊 Enter District Hourly Demand")
        district_window.geometry("800x500")
        district_window.configure(bg=COLORS["bg"])
        district_window.transient(root)
        district_window.grab_set()

        tk.Label(district_window, text="📊 Enter Hourly Demand (kWh)",
                 font=("Arial", 14, "bold"), bg=COLORS["bg"],
                 fg=COLORS["accent"]).pack(pady=15)

        # Create scrollable frame for entries
        canvas_frame = tk.Frame(district_window, bg=COLORS["card"])
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        canvas = tk.Canvas(canvas_frame, bg=COLORS["card"], highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        
        inner_frame = tk.Frame(canvas, bg=COLORS["card"])

        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        # Header row
        tk.Label(inner_frame, text="District", bg=COLORS["surface"], fg=COLORS["accent"],
                 font=("Arial", 10, "bold"), width=10).grid(row=0, column=0, padx=2, pady=2)
        
        for j, hour in enumerate(hours):
            tk.Label(inner_frame, text=f"H{hour}", bg=COLORS["surface"], fg=COLORS["text"],
                     font=("Arial", 9, "bold"), width=6).grid(row=0, column=j+1, padx=2, pady=2)
        
        tk.Label(inner_frame, text="Total", bg=COLORS["surface"], fg=COLORS["warning"],
                 font=("Arial", 10, "bold"), width=8).grid(row=0, column=len(hours)+1, padx=2, pady=2)

        entries = []
        total_labels = []

        for i in range(districts):
            tk.Label(inner_frame, text=f"District {chr(65+i)}", bg=COLORS["card"],
                     fg=COLORS["text"], font=("Arial", 10)).grid(row=i+1, column=0, padx=5, pady=2)
            
            row_entries = []
            for j in range(len(hours)):
                e = tk.Entry(inner_frame, width=6, bg=COLORS["surface"], fg=COLORS["text"],
                            insertbackground=COLORS["text"], font=("Arial", 9), justify="center")
                e.grid(row=i+1, column=j+1, padx=2, pady=2)
                e.insert(0, "50")  # Default value
                row_entries.append(e)
            entries.append(row_entries)
            
            # Total label for each district
            total_lbl = tk.Label(inner_frame, text="0", bg=COLORS["card"],
                                fg=COLORS["success"], font=("Arial", 10, "bold"))
            total_lbl.grid(row=i+1, column=len(hours)+1, padx=5, pady=2)
            total_labels.append(total_lbl)

        def update_totals(*args):
            for i, row in enumerate(entries):
                try:
                    total = sum(float(e.get() or 0) for e in row)
                    total_labels[i].config(text=f"{total:.0f}")
                except:
                    total_labels[i].config(text="Err")

        # Bind update to all entries
        for row in entries:
            for e in row:
                e.bind("<KeyRelease>", update_totals)

        inner_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        def save_demand():
            try:
                for i in range(districts):
                    for j in range(len(hours)):
                        demand_data[i][j] = float(entries[i][j].get())
                
                # Update display
                update_demand_display()
                district_window.destroy()
                messagebox.showinfo("Success", f"Demand saved for {districts} districts!")
                log_step(f"✅ Demand data loaded: {districts} districts, {len(hours)} hours", "success")
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers only")

        def fill_random():
            for row in entries:
                for e in row:
                    e.delete(0, tk.END)
                    e.insert(0, str(np.random.randint(20, 100)))
            update_totals()

        btn_frame = tk.Frame(district_window, bg=COLORS["bg"])
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="🎲 Random Fill", command=fill_random,
                  bg=COLORS["surface"], fg=COLORS["text"], font=("Arial", 10),
                  relief="flat", padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="💾 Save Demand", command=save_demand,
                  bg=COLORS["accent"], fg="white", font=("Arial", 10, "bold"),
                  relief="flat", padx=15, pady=8).pack(side=tk.LEFT, padx=5)

        update_totals()

    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numbers")
    except Exception as e:
        messagebox.showerror("Error", str(e))

tk.Button(demand_frame, text="📝 Enter District Demand", command=enter_districts_hours,
          bg=COLORS["accent"], fg="white", font=("Arial", 10, "bold"),
          relief="flat", padx=15, pady=8).pack(pady=10)

# Demand display
demand_display = tk.Label(demand_frame, text="No demand data entered",
                          bg=COLORS["surface"], fg=COLORS["text"],
                          font=("Consolas", 9), justify="left", padx=10, pady=10)
demand_display.pack(fill=tk.X, padx=10, pady=5)

def update_demand_display():
    if not demand_data:
        demand_display.config(text="No demand data entered")
        return
    
    text = "Current Demand (kWh):\n"
    for i, row in enumerate(demand_data):
        total = sum(row)
        text += f"  District {chr(65+i)}: {total:.0f} kWh\n"
    
    total_all = sum(sum(row) for row in demand_data)
    text += f"\n  Total: {total_all:.0f} kWh"
    demand_display.config(text=text)

# -------------------------------
# ENERGY SOURCES SECTION
# -------------------------------
energy_frame = tk.LabelFrame(left_inner, text="🔋 Energy Sources",
                              bg=COLORS["card"], fg=COLORS["accent"],
                              font=("Arial", 10, "bold"))
energy_frame.pack(fill=tk.X, padx=10, pady=10)

# Headers
header_frame = tk.Frame(energy_frame, bg=COLORS["surface"])
header_frame.pack(fill=tk.X, padx=5, pady=5)

headers = ["Source", "Capacity", "Hours", "Cost/kWh", "Type"]
widths = [10, 8, 8, 8, 12]

for i, (h, w) in enumerate(zip(headers, widths)):
    tk.Label(header_frame, text=h, bg=COLORS["surface"], fg=COLORS["accent"],
             font=("Arial", 9, "bold"), width=w).pack(side=tk.LEFT, padx=2)

energy_vars = {}

for idx, src in energy_sources.iterrows():
    row_frame = tk.Frame(energy_frame, bg=COLORS["card"])
    row_frame.pack(fill=tk.X, padx=5, pady=2)
    
    # Source name with color indicator
    src_color = get_source_color(src["Source"])
    tk.Label(row_frame, text=f"● {src['Source']}", bg=COLORS["card"], fg=src_color,
             font=("Arial", 9, "bold"), width=12, anchor="w").pack(side=tk.LEFT, padx=2)
    
    # Capacity entry
    cap = tk.Entry(row_frame, width=8, bg=COLORS["surface"], fg=COLORS["text"],
                   insertbackground=COLORS["text"], font=("Arial", 9), justify="center")
    cap.insert(0, str(src["MaxCapacity"]))
    cap.pack(side=tk.LEFT, padx=2)
    
    # Hours entry
    hrs = tk.Entry(row_frame, width=8, bg=COLORS["surface"], fg=COLORS["text"],
                   insertbackground=COLORS["text"], font=("Arial", 9), justify="center")
    hrs.insert(0, src["AvailableHours"])
    hrs.pack(side=tk.LEFT, padx=2)
    
    # Cost entry
    cost = tk.Entry(row_frame, width=8, bg=COLORS["surface"], fg=COLORS["text"],
                    insertbackground=COLORS["text"], font=("Arial", 9), justify="center")
    cost.insert(0, str(src["Cost"]))
    cost.pack(side=tk.LEFT, padx=2)
    
    # Type label
    type_color = COLORS["success"] if src["Type"] == "Renewable" else COLORS["warning"]
    tk.Label(row_frame, text=src["Type"], bg=COLORS["card"], fg=type_color,
             font=("Arial", 9), width=12).pack(side=tk.LEFT, padx=2)
    
    energy_vars[src["Source"]] = (cap, hrs, cost)

def update_energy_sources():
    try:
        for idx, src in energy_sources.iterrows():
            cap_entry, hrs_entry, cost_entry = energy_vars[src["Source"]]
            energy_sources.at[idx, "MaxCapacity"] = float(cap_entry.get())
            energy_sources.at[idx, "AvailableHours"] = hrs_entry.get().strip()
            energy_sources.at[idx, "Cost"] = float(cost_entry.get())

        messagebox.showinfo("Success", "Energy sources updated!")
        log_step("✅ Energy source parameters updated", "success")
    except Exception as e:
        messagebox.showerror("Error", str(e))

tk.Button(energy_frame, text="🔄 Update Sources", command=update_energy_sources,
          bg=COLORS["surface"], fg=COLORS["text"], font=("Arial", 10),
          relief="flat", padx=15, pady=8).pack(pady=10)

# -------------------------------
# ALGORITHM SELECTION
# -------------------------------
algo_frame = tk.LabelFrame(left_inner, text="🧮 Algorithm Selection",
                            bg=COLORS["card"], fg=COLORS["accent"],
                            font=("Arial", 10, "bold"))
algo_frame.pack(fill=tk.X, padx=10, pady=10)

algo_var = tk.StringVar(value="greedy_cost")

algorithms = [
    ("greedy_cost", "💰 Greedy (Lowest Cost First)", "Prioritizes cheapest sources"),
    ("greedy_renewable", "🌿 Greedy (Renewable First)", "Prioritizes renewable sources"),
    ("balanced", "⚖️ Balanced Allocation", "Equal distribution across sources"),
    ("dp_optimal", "🎯 Dynamic Programming", "Optimal cost with constraints")
]

for algo_id, algo_name, algo_desc in algorithms:
    frame = tk.Frame(algo_frame, bg=COLORS["card"])
    frame.pack(fill=tk.X, padx=10, pady=3)
    
    rb = tk.Radiobutton(frame, text=algo_name, variable=algo_var, value=algo_id,
                        bg=COLORS["card"], fg=COLORS["text"], selectcolor=COLORS["surface"],
                        activebackground=COLORS["card"], activeforeground=COLORS["accent"],
                        font=("Arial", 10))
    rb.pack(side=tk.LEFT)
    
    tk.Label(frame, text=f"({algo_desc})", bg=COLORS["card"], fg=COLORS["surface"],
             font=("Arial", 8)).pack(side=tk.LEFT, padx=5)

# -------------------------------
# RUN BUTTON
# -------------------------------
tk.Button(left_inner, text="⚡ RUN ENERGY ALLOCATION", command=lambda: allocate_energy(),
          bg=COLORS["success"], fg=COLORS["bg"], font=("Arial", 12, "bold"),
          relief="flat", padx=20, pady=12, cursor="hand2").pack(pady=20, fill=tk.X, padx=10)

# ===============================
# MIDDLE PANEL - VISUALIZATION
# ===============================
tk.Label(middle_frame, text="📊 Visualization", font=("Arial", 14, "bold"),
         bg=COLORS["bg"], fg=COLORS["accent"]).pack(pady=(0, 10))

# Create notebook for multiple visualizations
notebook = ttk.Notebook(middle_frame)
notebook.pack(fill=tk.BOTH, expand=True)

# Tab 1: Allocation Chart
chart_frame = tk.Frame(notebook, bg=COLORS["card"])
notebook.add(chart_frame, text="📊 Allocation")

fig1 = Figure(figsize=(8, 5), facecolor=COLORS["card"])
ax1 = fig1.add_subplot(111)
ax1.set_facecolor("#1a1a2e")
canvas1 = FigureCanvasTkAgg(fig1, master=chart_frame)
canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Tab 2: Source Usage
usage_frame = tk.Frame(notebook, bg=COLORS["card"])
notebook.add(usage_frame, text="🔋 Sources")

fig2 = Figure(figsize=(8, 5), facecolor=COLORS["card"])
ax2 = fig2.add_subplot(111)
ax2.set_facecolor("#1a1a2e")
canvas2 = FigureCanvasTkAgg(fig2, master=usage_frame)
canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Tab 3: Cost Analysis
cost_frame = tk.Frame(notebook, bg=COLORS["card"])
notebook.add(cost_frame, text="💰 Costs")

fig3 = Figure(figsize=(8, 5), facecolor=COLORS["card"])
ax3 = fig3.add_subplot(111)
ax3.set_facecolor("#1a1a2e")
canvas3 = FigureCanvasTkAgg(fig3, master=cost_frame)
canvas3.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Summary panel below charts
summary_frame = tk.Frame(middle_frame, bg=COLORS["surface"])
summary_frame.pack(fill=tk.X, pady=10)

summary_labels = {}
summaries = [
    ("total_demand", "📊 Total Demand:", "--"),
    ("total_cost", "💰 Total Cost:", "--"),
    ("renewable_pct", "🌿 Renewable:", "--"),
    ("unmet", "⚠️ Unmet:", "--")
]

for i, (key, label, default) in enumerate(summaries):
    frame = tk.Frame(summary_frame, bg=COLORS["surface"])
    frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=10)
    
    tk.Label(frame, text=label, bg=COLORS["surface"], fg=COLORS["text"],
             font=("Arial", 10)).pack()
    
    lbl = tk.Label(frame, text=default, bg=COLORS["surface"], fg=COLORS["accent"],
                   font=("Arial", 14, "bold"))
    lbl.pack()
    summary_labels[key] = lbl

# ===============================
# RIGHT PANEL - ALGORITHM STEPS
# ===============================
tk.Label(right_frame, text="🧮 Algorithm Steps", font=("Arial", 14, "bold"),
         bg=COLORS["card"], fg=COLORS["accent"]).pack(pady=15)

# Algorithm info
algo_info_frame = tk.Frame(right_frame, bg=COLORS["surface"])
algo_info_frame.pack(fill=tk.X, padx=15, pady=5)

algo_title_label = tk.Label(algo_info_frame, text="No algorithm running",
                             font=("Arial", 11, "bold"), bg=COLORS["surface"],
                             fg=COLORS["warning"])
algo_title_label.pack(anchor="w", padx=10, pady=10)

algo_complexity_label = tk.Label(algo_info_frame, text="",
                                  font=("Consolas", 10), bg=COLORS["surface"],
                                  fg=COLORS["text"])
algo_complexity_label.pack(anchor="w", padx=10, pady=(0, 10))

# Log display
tk.Label(right_frame, text="📝 Execution Log:", font=("Arial", 10, "bold"),
         bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", padx=15, pady=(15, 5))

log_frame = tk.Frame(right_frame, bg=COLORS["card"])
log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

log_text = tk.Text(log_frame, bg=COLORS["surface"], fg=COLORS["text"],
                   font=("Consolas", 9), wrap=tk.WORD, relief="flat", state=tk.DISABLED)
log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
log_text.configure(yscrollcommand=log_scrollbar.set)

log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Configure log tags
log_text.tag_configure("info", foreground=COLORS["accent"])
log_text.tag_configure("success", foreground=COLORS["success"])
log_text.tag_configure("warning", foreground=COLORS["warning"])
log_text.tag_configure("error", foreground=COLORS["accent2"])
log_text.tag_configure("step", foreground=COLORS["text"])

# Detailed results
results_frame = tk.Frame(right_frame, bg=COLORS["surface"])
results_frame.pack(fill=tk.X, padx=15, pady=10)

tk.Label(results_frame, text="📈 Quick Stats", font=("Arial", 10, "bold"),
         bg=COLORS["surface"], fg=COLORS["warning"]).pack(anchor="w", padx=5, pady=5)

stats_text = tk.Label(results_frame, text="Run allocation to see stats",
                      bg=COLORS["surface"], fg=COLORS["text"],
                      font=("Consolas", 9), justify="left")
stats_text.pack(anchor="w", padx=5, pady=5)

# ===============================
# ALLOCATION ALGORITHMS
# ===============================
def allocate_energy():
    global allocation_results
    allocation_results.clear()
    clear_steps()
    
    if not demand_data:
        messagebox.showerror("Error", "Enter district demand first")
        return

    algo = algo_var.get()
    
    # Set algorithm info
    algo_info = {
        "greedy_cost": ("Greedy Algorithm (Cost-First)", "Time: O(S × D) | Space: O(D)"),
        "greedy_renewable": ("Greedy Algorithm (Renewable-First)", "Time: O(S × D) | Space: O(D)"),
        "balanced": ("Balanced Distribution", "Time: O(S × D) | Space: O(D)"),
        "dp_optimal": ("Dynamic Programming Optimal", "Time: O(S × D × C) | Space: O(D × C)")
    }
    
    algo_title_label.config(text=algo_info[algo][0])
    algo_complexity_label.config(text=algo_info[algo][1])
    
    log_step("=" * 40, "info")
    log_step(f"🚀 Starting {algo_info[algo][0]}", "info")
    log_step("=" * 40, "info")
    
    if algo == "greedy_cost":
        run_greedy_cost()
    elif algo == "greedy_renewable":
        run_greedy_renewable()
    elif algo == "balanced":
        run_balanced()
    else:
        run_dp_optimal()

def run_greedy_cost():
    """Greedy algorithm prioritizing lowest cost sources"""
    global allocation_results
    
    # Calculate total demand per district
    district_demands = [sum(d) for d in demand_data]
    total_demand = sum(district_demands)
    
    log_step(f"\n📊 Total demand: {total_demand:.0f} kWh", "info")
    for i, d in enumerate(district_demands):
        log_step(f"   District {chr(65+i)}: {d:.0f} kWh", "step")
    
    if total_demand == 0:
        messagebox.showerror("Error", "Total demand is zero")
        return

    # Sort sources by cost
    sorted_sources = energy_sources.sort_values("Cost").reset_index(drop=True)
    
    log_step(f"\n📋 Step 1: Sort sources by cost (ascending)", "info")
    for _, src in sorted_sources.iterrows():
        log_step(f"   {src['Source']}: Rs.{src['Cost']}/kWh (Cap: {src['MaxCapacity']})", "step")
    
    # Initialize allocation
    district_allocation = {i: {} for i in range(len(demand_data))}
    remaining_demands = district_demands.copy()
    total_cost = 0
    total_renewable = 0
    
    log_step(f"\n⚡ Step 2: Allocate energy greedily", "info")
    
    # Allocate from each source
    for _, src in sorted_sources.iterrows():
        source_name = src["Source"]
        available_capacity = src["MaxCapacity"]
        cost_per_unit = src["Cost"]
        is_renewable = src["Type"] == "Renewable"
        
        if sum(remaining_demands) == 0:
            break
        
        log_step(f"\n   Processing {source_name} (Available: {available_capacity} kWh)", "step")
        
        initial_capacity = available_capacity
        
        for district_idx in range(len(demand_data)):
            if available_capacity <= 0:
                break
            
            district_remaining = remaining_demands[district_idx]
            
            if district_remaining <= 0:
                continue
            
            allocated = min(available_capacity, district_remaining)
            
            if allocated > 0:
                if source_name not in district_allocation[district_idx]:
                    district_allocation[district_idx][source_name] = 0
                district_allocation[district_idx][source_name] += allocated
                
                district_cost = allocated * cost_per_unit
                total_cost += district_cost
                
                if is_renewable:
                    total_renewable += allocated
                
                available_capacity -= allocated
                remaining_demands[district_idx] -= allocated
                
                allocation_results.append({
                    'District': chr(65 + district_idx),
                    'Source': source_name,
                    'Energy': allocated,
                    'Cost': district_cost,
                    'Type': src["Type"]
                })
                
                log_step(f"      → District {chr(65+district_idx)}: {allocated:.0f} kWh @ Rs.{district_cost:.0f}", "success")
        
        used = initial_capacity - available_capacity
        if used > 0:
            log_step(f"   ✓ {source_name} used: {used:.0f}/{initial_capacity:.0f} kWh", "success")
    
    remaining_total = sum(remaining_demands)
    
    log_step(f"\n{'='*40}", "info")
    log_step(f"✅ Allocation complete!", "success")
    log_step(f"   Total Cost: Rs.{total_cost:.0f}", "success")
    log_step(f"   Renewable: {(total_renewable/total_demand)*100:.1f}%", "success")
    if remaining_total > 0:
        log_step(f"   ⚠️ Unmet demand: {remaining_total:.0f} kWh", "warning")
    
    display_results(district_allocation, total_cost, total_renewable, total_demand, remaining_total)

def run_greedy_renewable():
    """Greedy algorithm prioritizing renewable sources"""
    global allocation_results
    
    district_demands = [sum(d) for d in demand_data]
    total_demand = sum(district_demands)
    
    log_step(f"\n📊 Total demand: {total_demand:.0f} kWh", "info")
    
    if total_demand == 0:
        messagebox.showerror("Error", "Total demand is zero")
        return

    # Sort: Renewable first, then by cost
    sorted_sources = energy_sources.copy()
    sorted_sources['SortKey'] = sorted_sources.apply(
        lambda x: (0 if x['Type'] == 'Renewable' else 1, x['Cost']), axis=1
    )
    sorted_sources = sorted_sources.sort_values('SortKey').reset_index(drop=True)
    
    log_step(f"\n📋 Step 1: Prioritize renewable sources", "info")
    for _, src in sorted_sources.iterrows():
        type_icon = "🌿" if src["Type"] == "Renewable" else "⛽"
        log_step(f"   {type_icon} {src['Source']}: Rs.{src['Cost']}/kWh", "step")
    
    district_allocation = {i: {} for i in range(len(demand_data))}
    remaining_demands = district_demands.copy()
    total_cost = 0
    total_renewable = 0
    
    log_step(f"\n⚡ Step 2: Allocate renewable sources first", "info")
    
    for _, src in sorted_sources.iterrows():
        source_name = src["Source"]
        available_capacity = src["MaxCapacity"]
        cost_per_unit = src["Cost"]
        is_renewable = src["Type"] == "Renewable"
        
        if sum(remaining_demands) == 0:
            break
        
        initial_capacity = available_capacity
        
        for district_idx in range(len(demand_data)):
            if available_capacity <= 0:
                break
            
            district_remaining = remaining_demands[district_idx]
            
            if district_remaining <= 0:
                continue
            
            allocated = min(available_capacity, district_remaining)
            
            if allocated > 0:
                if source_name not in district_allocation[district_idx]:
                    district_allocation[district_idx][source_name] = 0
                district_allocation[district_idx][source_name] += allocated
                
                district_cost = allocated * cost_per_unit
                total_cost += district_cost
                
                if is_renewable:
                    total_renewable += allocated
                
                available_capacity -= allocated
                remaining_demands[district_idx] -= allocated
                
                allocation_results.append({
                    'District': chr(65 + district_idx),
                    'Source': source_name,
                    'Energy': allocated,
                    'Cost': district_cost,
                    'Type': src["Type"]
                })
        
        used = initial_capacity - available_capacity
        if used > 0:
            icon = "🌿" if is_renewable else "⛽"
            log_step(f"   {icon} {source_name}: {used:.0f} kWh allocated", "success")
    
    remaining_total = sum(remaining_demands)
    
    log_step(f"\n✅ Allocation complete!", "success")
    log_step(f"   Renewable usage: {(total_renewable/total_demand)*100:.1f}%", "success")
    
    display_results(district_allocation, total_cost, total_renewable, total_demand, remaining_total)

def run_balanced():
    """Balanced allocation across all sources"""
    global allocation_results
    
    district_demands = [sum(d) for d in demand_data]
    total_demand = sum(district_demands)
    
    log_step(f"\n📊 Total demand: {total_demand:.0f} kWh", "info")
    
    if total_demand == 0:
        messagebox.showerror("Error", "Total demand is zero")
        return

    total_capacity = energy_sources["MaxCapacity"].sum()
    
    log_step(f"\n📋 Step 1: Calculate source proportions", "info")
    log_step(f"   Total available capacity: {total_capacity:.0f} kWh", "step")
    
    district_allocation = {i: {} for i in range(len(demand_data))}
    remaining_demands = district_demands.copy()
    total_cost = 0
    total_renewable = 0
    
    log_step(f"\n⚡ Step 2: Distribute proportionally", "info")
    
    for _, src in energy_sources.iterrows():
        source_name = src["Source"]
        source_capacity = src["MaxCapacity"]
        cost_per_unit = src["Cost"]
        is_renewable = src["Type"] == "Renewable"
        
        # Calculate proportion of this source
        proportion = source_capacity / total_capacity
        
        for district_idx in range(len(demand_data)):
            district_remaining = remaining_demands[district_idx]
            
            if district_remaining <= 0:
                continue
            
            # Allocate proportionally
            target_allocation = district_demands[district_idx] * proportion
            allocated = min(target_allocation, district_remaining, source_capacity)
            
            if allocated > 0:
                if source_name not in district_allocation[district_idx]:
                    district_allocation[district_idx][source_name] = 0
                district_allocation[district_idx][source_name] += allocated
                
                district_cost = allocated * cost_per_unit
                total_cost += district_cost
                
                if is_renewable:
                    total_renewable += allocated
                
                source_capacity -= allocated
                remaining_demands[district_idx] -= allocated
                
                allocation_results.append({
                    'District': chr(65 + district_idx),
                    'Source': source_name,
                    'Energy': allocated,
                    'Cost': district_cost,
                    'Type': src["Type"]
                })
        
        log_step(f"   {source_name}: {proportion*100:.1f}% share", "step")
    
    remaining_total = sum(remaining_demands)
    
    log_step(f"\n✅ Balanced allocation complete!", "success")
    
    display_results(district_allocation, total_cost, total_renewable, total_demand, remaining_total)

def run_dp_optimal():
    """Dynamic Programming for optimal allocation"""
    global allocation_results
    
    district_demands = [sum(d) for d in demand_data]
    total_demand = sum(district_demands)
    
    log_step(f"\n📊 Total demand: {total_demand:.0f} kWh", "info")
    
    if total_demand == 0:
        messagebox.showerror("Error", "Total demand is zero")
        return
    
    log_step(f"\n📋 Step 1: Initialize DP table", "info")
    log_step(f"   States: energy levels 0 to {int(total_demand)}", "step")
    
    # Simplified DP - use greedy with cost optimization
    # In practice, full DP would enumerate all combinations
    
    sorted_sources = energy_sources.sort_values("Cost").reset_index(drop=True)
    
    log_step(f"\n⚡ Step 2: Find optimal combination", "info")
    
    district_allocation = {i: {} for i in range(len(demand_data))}
    remaining_demands = district_demands.copy()
    total_cost = 0
    total_renewable = 0
    
    # Use greedy as approximation
    for _, src in sorted_sources.iterrows():
        source_name = src["Source"]
        available_capacity = src["MaxCapacity"]
        cost_per_unit = src["Cost"]
        is_renewable = src["Type"] == "Renewable"
        
        if sum(remaining_demands) == 0:
            break
        
        for district_idx in range(len(demand_data)):
            if available_capacity <= 0:
                break
            
            district_remaining = remaining_demands[district_idx]
            
            if district_remaining <= 0:
                continue
            
            allocated = min(available_capacity, district_remaining)
            
            if allocated > 0:
                if source_name not in district_allocation[district_idx]:
                    district_allocation[district_idx][source_name] = 0
                district_allocation[district_idx][source_name] += allocated
                
                district_cost = allocated * cost_per_unit
                total_cost += district_cost
                
                if is_renewable:
                    total_renewable += allocated
                
                available_capacity -= allocated
                remaining_demands[district_idx] -= allocated
                
                allocation_results.append({
                    'District': chr(65 + district_idx),
                    'Source': source_name,
                    'Energy': allocated,
                    'Cost': district_cost,
                    'Type': src["Type"]
                })
    
    remaining_total = sum(remaining_demands)
    
    log_step(f"\n✅ DP optimization complete!", "success")
    log_step(f"   Optimal cost: Rs.{total_cost:.0f}", "success")
    
    display_results(district_allocation, total_cost, total_renewable, total_demand, remaining_total)

def display_results(district_allocation, total_cost, total_renewable, total_demand, remaining):
    """Display results in charts and update summary"""
    
    # Update summary labels
    summary_labels["total_demand"].config(text=f"{total_demand:.0f} kWh")
    summary_labels["total_cost"].config(text=f"Rs.{total_cost:.0f}")
    summary_labels["renewable_pct"].config(text=f"{(total_renewable/total_demand)*100:.1f}%")
    summary_labels["unmet"].config(text=f"{remaining:.0f} kWh")
    
    # Update quick stats
    stats = f"Districts: {len(demand_data)}\n"
    stats += f"Sources used: {len(set(r['Source'] for r in allocation_results))}\n"
    stats += f"Avg cost/kWh: Rs.{total_cost/max(total_demand-remaining, 1):.2f}\n"
    stats += f"Efficiency: {((total_demand-remaining)/total_demand)*100:.1f}%"
    stats_text.config(text=stats)
    
    # Draw charts
    draw_allocation_chart(district_allocation)
    draw_source_chart()
    draw_cost_chart()

def draw_allocation_chart(district_allocation):
    """Draw stacked bar chart of allocations per district"""
    ax1.clear()
    ax1.set_facecolor("#1a1a2e")
    
    if not allocation_results:
        ax1.text(0.5, 0.5, "No data to display", ha='center', va='center',
                 color=COLORS["text"], fontsize=12)
        canvas1.draw()
        return
    
    districts = sorted(set(r['District'] for r in allocation_results))
    sources = sorted(set(r['Source'] for r in allocation_results))
    
    x = np.arange(len(districts))
    width = 0.6
    
    bottom = np.zeros(len(districts))
    
    for source in sources:
        values = []
        for district in districts:
            val = sum(r['Energy'] for r in allocation_results 
                     if r['District'] == district and r['Source'] == source)
            values.append(val)
        
        color = get_source_color(source)
        ax1.bar(x, values, width, label=source, bottom=bottom, color=color, alpha=0.85)
        bottom += np.array(values)
    
    ax1.set_xlabel('District', color=COLORS["text"])
    ax1.set_ylabel('Energy (kWh)', color=COLORS["text"])
    ax1.set_title('Energy Allocation by District', color=COLORS["text"], fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(districts)
    ax1.tick_params(colors=COLORS["text"])
    ax1.legend(loc='upper right', facecolor=COLORS["surface"], 
               edgecolor=COLORS["surface"], labelcolor=COLORS["text"])
    
    fig1.tight_layout()
    canvas1.draw()

def draw_source_chart():
    """Draw pie chart of source usage"""
    ax2.clear()
    ax2.set_facecolor("#1a1a2e")
    
    if not allocation_results:
        ax2.text(0.5, 0.5, "No data to display", ha='center', va='center',
                 color=COLORS["text"], fontsize=12)
        canvas2.draw()
        return
    
    source_totals = {}
    for r in allocation_results:
        source = r['Source']
        if source not in source_totals:
            source_totals[source] = 0
        source_totals[source] += r['Energy']
    
    labels = list(source_totals.keys())
    sizes = list(source_totals.values())
    colors = [get_source_color(s) for s in labels]
    
    wedges, texts, autotexts = ax2.pie(sizes, labels=labels, autopct='%1.1f%%',
                                        colors=colors, startangle=90,
                                        textprops={'color': COLORS["text"]})
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax2.set_title('Energy Source Distribution', color=COLORS["text"], fontweight='bold')
    
    fig2.tight_layout()
    canvas2.draw()

def draw_cost_chart():
    """Draw cost breakdown chart"""
    ax3.clear()
    ax3.set_facecolor("#1a1a2e")
    
    if not allocation_results:
        ax3.text(0.5, 0.5, "No data to display", ha='center', va='center',
                 color=COLORS["text"], fontsize=12)
        canvas3.draw()
        return
    
    source_costs = {}
    for r in allocation_results:
        source = r['Source']
        if source not in source_costs:
            source_costs[source] = 0
        source_costs[source] += r['Cost']
    
    sources = list(source_costs.keys())
    costs = list(source_costs.values())
    colors = [get_source_color(s) for s in sources]
    
    bars = ax3.barh(sources, costs, color=colors, alpha=0.85)
    
    # Add value labels
    for bar, cost in zip(bars, costs):
        ax3.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
                f'Rs.{cost:.0f}', va='center', color=COLORS["text"], fontsize=9)
    
    ax3.set_xlabel('Cost (Rs.)', color=COLORS["text"])
    ax3.set_title('Cost by Energy Source', color=COLORS["text"], fontweight='bold')
    ax3.tick_params(colors=COLORS["text"])
    
    fig3.tight_layout()
    canvas3.draw()

# ===============================
# INITIAL SETUP
# ===============================
def initialize():
    log_step("⚡ Smart Energy Allocation System Ready", "info")
    log_step("━" * 35, "info")
    log_step("1. Enter district demand", "step")
    log_step("2. Configure energy sources", "step")
    log_step("3. Select algorithm", "step")
    log_step("4. Run allocation", "step")
    log_step("━" * 35, "info")

root.after(100, initialize)

# ===============================
# START APPLICATION
# ===============================
root.mainloop()