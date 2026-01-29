"""
Emergency Network Management System — Graph Algorithms & Visualization
=====================================================================
Problem: Analyze and visualize network graphs for MST, k-shortest paths,
         failure impact, tree traversals and frequency assignment

Purpose: Multi-tab GUI for interactive graph analysis, algorithm demos and animations

Features:
- Animated Kruskal's MST construction with logging
- Yen's / Dijkstra-based K-shortest path finder with animation
- Command-hierarchy tree traversals and optimization (visual tree builder)
- Failure simulation (node/edge) with connectivity and path-impact analysis
- Greedy graph coloring (frequency assignment) with animated assignment
- Editing tools: add/remove nodes & edges, mark vulnerable roads, reset
- Rich theme, charts, adjacency matrix and execution log for reports
"""



import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import time
import threading
from collections import deque
import heapq

# --------------------------------
# Graph Initialization
# --------------------------------
G = nx.Graph()
G.add_weighted_edges_from([
    ("A", "B", 4), ("A", "C", 3), ("B", "C", 2),
    ("B", "D", 5), ("C", "D", 7), ("C", "E", 8),
    ("D", "E", 6), ("D", "F", 3), ("E", "F", 4),
    ("A", "G", 6), ("G", "H", 2), ("H", "F", 5)
])

original_graph = G.copy()
pos = nx.spring_layout(G, seed=42, k=2)

vulnerable_roads = set()
failed_nodes = set()
animation_speed = 0.5

# Command hierarchy tree
class CommandNode:
    def __init__(self, name, level=0):
        self.name = name
        self.level = level
        self.left = None
        self.right = None

# Build command hierarchy
hq = CommandNode("HQ", 0)
hq.left = CommandNode("Regional-A", 1)
hq.right = CommandNode("Regional-B", 1)
hq.left.left = CommandNode("Local-A1", 2)
hq.left.right = CommandNode("Local-A2", 2)
hq.right.left = CommandNode("Local-B1", 2)
hq.right.right = CommandNode("Local-B2", 2)

# --------------------------------
# Enhanced Color Theme (Catppuccin Mocha)
# --------------------------------
COLORS = {
    "bg": "#1e1e2e",
    "card": "#313244",
    "accent": "#89b4fa",
    "accent2": "#f38ba8",
    "text": "#cdd6f4",
    "subtext": "#a6adc8",
    "success": "#a6e3a1",
    "warning": "#f9e2af",
    "error": "#f38ba8",
    "surface": "#45475a",
    "surface2": "#585b70",
    "overlay": "#6c7086",
    "lavender": "#b4befe",
    "sapphire": "#74c7ec",
    "teal": "#94e2d5",
    "peach": "#fab387",
    "maroon": "#eba0ac",
    "node_default": "#89b4fa",
    "node_failed": "#f38ba8",
    "node_highlight": "#a6e3a1",
    "node_visited": "#cba6f7",
    "node_current": "#f9e2af",
    "edge_default": "#6c7086",
    "edge_vulnerable": "#fab387",
    "edge_highlight": "#a6e3a1",
    "edge_path": "#f5c2e7",
    "mst_edge": "#a6e3a1"
}

# --------------------------------
# Main Window Setup
# --------------------------------
root = tk.Tk()
root.title("🚨 Emergency Network Management System v2.0")
root.geometry("1600x950")
root.configure(bg=COLORS["bg"])
root.minsize(1400, 800)

# Window management
root.lift()
root.attributes('-topmost', True)
root.after(100, lambda: root.attributes('-topmost', False))
root.focus_force()

# Enhanced styles
style = ttk.Style()
style.theme_use("clam")

style.configure("TFrame", background=COLORS["bg"])
style.configure("Card.TFrame", background=COLORS["card"])
style.configure("TLabelframe", background=COLORS["card"], foreground=COLORS["text"])
style.configure("TLabelframe.Label", background=COLORS["card"], foreground=COLORS["accent"],
                font=("Segoe UI", 11, "bold"))
style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
style.configure("TButton", padding=10, font=("Segoe UI", 10))
style.configure("TCombobox", fieldbackground=COLORS["surface"], background=COLORS["surface"],
                foreground=COLORS["text"])
style.configure("TEntry", fieldbackground=COLORS["surface"])
style.configure("TScale", background=COLORS["card"], troughcolor=COLORS["surface"])
style.configure("TNotebook", background=COLORS["bg"])
style.configure("TNotebook.Tab", background=COLORS["surface"], foreground=COLORS["text"],
                padding=[15, 8], font=("Segoe UI", 10))
style.map("TNotebook.Tab",
          background=[("selected", COLORS["card"])],
          foreground=[("selected", COLORS["accent"])])
style.map("TButton",
          background=[("active", COLORS["surface2"])],
          foreground=[("active", COLORS["text"])])
style.map("TCombobox",
          fieldbackground=[("readonly", COLORS["surface"])],
          selectbackground=[("readonly", COLORS["accent"])])

# --------------------------------
# Layout with Notebook Tabs
# --------------------------------
main_frame = tk.Frame(root, bg=COLORS["bg"])
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Header
header_frame = tk.Frame(main_frame, bg=COLORS["bg"])
header_frame.pack(fill=tk.X, pady=(0, 10))

tk.Label(header_frame, text="🚨 Emergency Network Management System",
         font=("Segoe UI", 20, "bold"), bg=COLORS["bg"],
         fg=COLORS["accent"]).pack(side=tk.LEFT)

# Animation speed control
speed_frame = tk.Frame(header_frame, bg=COLORS["bg"])
speed_frame.pack(side=tk.RIGHT, padx=20)

tk.Label(speed_frame, text="Animation Speed:", font=("Segoe UI", 10),
         bg=COLORS["bg"], fg=COLORS["subtext"]).pack(side=tk.LEFT, padx=5)

speed_var = tk.DoubleVar(value=0.5)
speed_scale = ttk.Scale(speed_frame, from_=0.1, to=2.0, variable=speed_var,
                        orient=tk.HORIZONTAL, length=120)
speed_scale.pack(side=tk.LEFT)

def update_speed(val):
    global animation_speed
    animation_speed = float(val)

speed_scale.configure(command=update_speed)

# Content area
content_frame = tk.Frame(main_frame, bg=COLORS["bg"])
content_frame.pack(fill=tk.BOTH, expand=True)

content_frame.grid_columnconfigure(0, weight=0, minsize=320)
content_frame.grid_columnconfigure(1, weight=1, minsize=600)
content_frame.grid_columnconfigure(2, weight=0, minsize=380)
content_frame.grid_rowconfigure(0, weight=1)

# --------------------------------
# Left Panel - Control Center
# --------------------------------
left_panel = tk.Frame(content_frame, bg=COLORS["card"], width=320)
left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
left_panel.grid_propagate(False)

# Panel header with icon
panel_header = tk.Frame(left_panel, bg=COLORS["surface"])
panel_header.pack(fill=tk.X)

tk.Label(panel_header, text="🎛️ Control Center", font=("Segoe UI", 14, "bold"),
         bg=COLORS["surface"], fg=COLORS["accent"], pady=12).pack()

# Scrollable control area
control_canvas = tk.Canvas(left_panel, bg=COLORS["card"], highlightthickness=0)
control_scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=control_canvas.yview)
control_inner = tk.Frame(control_canvas, bg=COLORS["card"])

control_canvas.configure(yscrollcommand=control_scrollbar.set)
control_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
control_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

control_window = control_canvas.create_window((0, 0), window=control_inner, anchor="nw")

def on_control_configure(event):
    control_canvas.configure(scrollregion=control_canvas.bbox("all"))

def on_canvas_configure(event):
    control_canvas.itemconfig(control_window, width=event.width)

control_inner.bind("<Configure>", on_control_configure)
control_canvas.bind("<Configure>", on_canvas_configure)

# Mouse wheel scrolling
def on_mousewheel(event):
    control_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

control_canvas.bind_all("<MouseWheel>", on_mousewheel)

# --------------------------------
# Middle Panel - Visualization
# --------------------------------
middle_panel = tk.Frame(content_frame, bg=COLORS["bg"])
middle_panel.grid(row=0, column=1, sticky="nsew", padx=8)

# Notebook for multiple views
viz_notebook = ttk.Notebook(middle_panel)
viz_notebook.pack(fill=tk.BOTH, expand=True)

# Tab 1: Main Graph
graph_tab = tk.Frame(viz_notebook, bg=COLORS["card"])
viz_notebook.add(graph_tab, text="🗺️ Network Graph")

fig = Figure(figsize=(10, 7), facecolor=COLORS["card"])
ax = fig.add_subplot(111)
ax.set_facecolor("#1a1a2e")
canvas = FigureCanvasTkAgg(fig, master=graph_tab)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Tab 2: Statistics
stats_tab = tk.Frame(viz_notebook, bg=COLORS["card"])
viz_notebook.add(stats_tab, text="📊 Statistics")

fig_stats = Figure(figsize=(10, 7), facecolor=COLORS["card"])
canvas_stats = FigureCanvasTkAgg(fig_stats, master=stats_tab)
canvas_stats.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Tab 3: Adjacency Matrix
matrix_tab = tk.Frame(viz_notebook, bg=COLORS["card"])
viz_notebook.add(matrix_tab, text="🔢 Matrix View")

fig_matrix = Figure(figsize=(10, 7), facecolor=COLORS["card"])
canvas_matrix = FigureCanvasTkAgg(fig_matrix, master=matrix_tab)
canvas_matrix.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Status bar
status_frame = tk.Frame(middle_panel, bg=COLORS["surface"])
status_frame.pack(fill=tk.X, pady=(8, 0))

status_icon = tk.Label(status_frame, text="✅", font=("Segoe UI", 12),
                       bg=COLORS["surface"], fg=COLORS["success"])
status_icon.pack(side=tk.LEFT, padx=10, pady=8)

status_label = tk.Label(status_frame, text="Ready - Select an operation from the control panel",
                        font=("Segoe UI", 10), bg=COLORS["surface"], fg=COLORS["text"])
status_label.pack(side=tk.LEFT, pady=8)

progress_var = tk.DoubleVar(value=0)
progress_bar = ttk.Progressbar(status_frame, variable=progress_var, maximum=100, length=150)
progress_bar.pack(side=tk.RIGHT, padx=10, pady=8)

# --------------------------------
# Right Panel - Algorithm Details
# --------------------------------
right_panel = tk.Frame(content_frame, bg=COLORS["card"], width=380)
right_panel.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
right_panel.grid_propagate(False)

# Panel header
right_header = tk.Frame(right_panel, bg=COLORS["surface"])
right_header.pack(fill=tk.X)

tk.Label(right_header, text="📊 Algorithm Details", font=("Segoe UI", 14, "bold"),
         bg=COLORS["surface"], fg=COLORS["accent"], pady=12).pack()

# Algorithm info card
algo_card = tk.Frame(right_panel, bg=COLORS["surface2"])
algo_card.pack(fill=tk.X, padx=12, pady=12)

algo_name_label = tk.Label(algo_card, text="No algorithm running",
                            font=("Segoe UI", 12, "bold"), bg=COLORS["surface2"],
                            fg=COLORS["warning"])
algo_name_label.pack(anchor="w", padx=12, pady=(12, 4))

algo_complexity_label = tk.Label(algo_card, text="",
                                  font=("Consolas", 10), bg=COLORS["surface2"],
                                  fg=COLORS["subtext"])
algo_complexity_label.pack(anchor="w", padx=12, pady=(0, 4))

algo_desc_label = tk.Label(algo_card, text="",
                            font=("Segoe UI", 9), bg=COLORS["surface2"],
                            fg=COLORS["text"], wraplength=340, justify="left")
algo_desc_label.pack(anchor="w", padx=12, pady=(0, 12))

# Execution log
log_header = tk.Frame(right_panel, bg=COLORS["card"])
log_header.pack(fill=tk.X, padx=12, pady=(8, 4))

tk.Label(log_header, text="📝 Execution Log", font=("Segoe UI", 11, "bold"),
         bg=COLORS["card"], fg=COLORS["text"]).pack(side=tk.LEFT)

clear_log_btn = tk.Button(log_header, text="Clear", font=("Segoe UI", 8),
                          bg=COLORS["surface"], fg=COLORS["subtext"],
                          relief="flat", padx=8, pady=2,
                          command=lambda: clear_log())
clear_log_btn.pack(side=tk.RIGHT)

log_frame = tk.Frame(right_panel, bg=COLORS["card"])
log_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

log_text = tk.Text(log_frame, bg=COLORS["surface"], fg=COLORS["text"],
                   font=("Consolas", 9), wrap=tk.WORD, relief="flat",
                   insertbackground=COLORS["text"], selectbackground=COLORS["accent"])
log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
log_text.configure(yscrollcommand=log_scrollbar.set)

log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Configure log tags with icons
log_text.tag_configure("title", foreground=COLORS["lavender"], font=("Consolas", 10, "bold"))
log_text.tag_configure("info", foreground=COLORS["accent"])
log_text.tag_configure("success", foreground=COLORS["success"])
log_text.tag_configure("warning", foreground=COLORS["warning"])
log_text.tag_configure("error", foreground=COLORS["error"])
log_text.tag_configure("step", foreground=COLORS["text"])
log_text.tag_configure("highlight", foreground=COLORS["peach"], font=("Consolas", 9, "bold"))

# Results summary card
results_card = tk.Frame(right_panel, bg=COLORS["surface2"])
results_card.pack(fill=tk.X, padx=12, pady=12)

tk.Label(results_card, text="📈 Results Summary", font=("Segoe UI", 11, "bold"),
         bg=COLORS["surface2"], fg=COLORS["warning"]).pack(anchor="w", padx=12, pady=(12, 8))

results_grid = tk.Frame(results_card, bg=COLORS["surface2"])
results_grid.pack(fill=tk.X, padx=12, pady=(0, 12))

results_labels = {}
result_items = [
    ("nodes", "Nodes", "📍"),
    ("edges", "Edges", "🔗"),
    ("weight", "Total Weight", "⚖️"),
    ("result", "Result", "🎯")
]

for i, (key, label, icon) in enumerate(result_items):
    row = tk.Frame(results_grid, bg=COLORS["surface2"])
    row.pack(fill=tk.X, pady=2)
    
    tk.Label(row, text=f"{icon} {label}:", font=("Segoe UI", 9),
             bg=COLORS["surface2"], fg=COLORS["subtext"], width=14, anchor="w").pack(side=tk.LEFT)
    
    lbl = tk.Label(row, text="--", font=("Consolas", 10, "bold"),
                   bg=COLORS["surface2"], fg=COLORS["accent"])
    lbl.pack(side=tk.RIGHT, padx=5)
    results_labels[key] = lbl

# --------------------------------
# Helper Functions
# --------------------------------
def log_message(message, tag="step"):
    log_text.config(state=tk.NORMAL)
    timestamp = time.strftime("%H:%M:%S")
    
    icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", 
             "step": "→", "title": "═", "highlight": "★"}
    
    icon = icons.get(tag, "→")
    log_text.insert(tk.END, f"[{timestamp}] {icon} {message}\n", tag)
    log_text.see(tk.END)
    log_text.config(state=tk.DISABLED)
    root.update_idletasks()

def clear_log():
    log_text.config(state=tk.NORMAL)
    log_text.delete(1.0, tk.END)
    log_text.config(state=tk.DISABLED)

def update_algo_info(name, complexity, description=""):
    algo_name_label.config(text=name)
    algo_complexity_label.config(text=complexity)
    algo_desc_label.config(text=description)
    root.update_idletasks()

def update_results(nodes=None, edges=None, weight=None, result=None):
    if nodes is not None:
        results_labels["nodes"].config(text=str(nodes))
    if edges is not None:
        results_labels["edges"].config(text=str(edges))
    if weight is not None:
        results_labels["weight"].config(text=f"{weight:.2f}" if isinstance(weight, float) else str(weight))
    if result is not None:
        results_labels["result"].config(text=str(result))
    root.update_idletasks()

def update_status(message, status_type="info"):
    icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "processing": "⏳"}
    colors = {"info": COLORS["accent"], "success": COLORS["success"], 
              "warning": COLORS["warning"], "error": COLORS["error"],
              "processing": COLORS["peach"]}
    
    status_icon.config(text=icons.get(status_type, "ℹ️"), fg=colors.get(status_type, COLORS["accent"]))
    status_label.config(text=message)
    root.update_idletasks()

def update_progress(value):
    progress_var.set(value)
    root.update_idletasks()

# --------------------------------
# Enhanced Graph Drawing
# --------------------------------
def draw_graph(highlight_edges=None, node_colors=None, title="Network Graph",
               edge_labels_custom=None, visited_nodes=None, current_node=None,
               path_edges=None):
    ax.clear()
    ax.set_facecolor("#1a1a2e")
    ax.set_title(title, fontsize=14, fontweight='bold', color=COLORS["text"], pad=15)
    
    if len(G.nodes()) == 0:
        ax.text(0.5, 0.5, "🕸️ No nodes in graph\nAdd nodes to get started!",
                ha='center', va='center', fontsize=14, color=COLORS["subtext"],
                transform=ax.transAxes)
        canvas.draw()
        return
    
    # Update positions
    global pos
    for node in G.nodes():
        if node not in pos:
            pos[node] = (np.random.rand() * 2 - 1, np.random.rand() * 2 - 1)
    pos = {k: v for k, v in pos.items() if k in G.nodes()}
    
    # Calculate node colors
    if node_colors is None:
        node_colors = []
        for node in G.nodes():
            if current_node and node == current_node:
                node_colors.append(COLORS["node_current"])
            elif visited_nodes and node in visited_nodes:
                node_colors.append(COLORS["node_visited"])
            elif node in failed_nodes:
                node_colors.append(COLORS["node_failed"])
            else:
                node_colors.append(COLORS["node_default"])
    
    # Draw regular edges
    regular_edges = [e for e in G.edges() if 
                     (highlight_edges is None or (e not in highlight_edges and (e[1], e[0]) not in highlight_edges)) and
                     (path_edges is None or (e not in path_edges and (e[1], e[0]) not in path_edges))]
    
    edge_colors = []
    edge_widths = []
    edge_styles = []
    
    for edge in regular_edges:
        if edge in vulnerable_roads or (edge[1], edge[0]) in vulnerable_roads:
            edge_colors.append(COLORS["edge_vulnerable"])
            edge_widths.append(2.5)
        else:
            edge_colors.append(COLORS["edge_default"])
            edge_widths.append(1.5)
    
    if regular_edges:
        nx.draw_networkx_edges(G, pos, ax=ax, edgelist=regular_edges,
                               edge_color=edge_colors, width=edge_widths, alpha=0.6)
    
    # Draw path edges
    if path_edges:
        nx.draw_networkx_edges(G, pos, ax=ax, edgelist=path_edges,
                               edge_color=COLORS["edge_path"], width=4, alpha=0.9,
                               style='dashed')
    
    # Draw highlighted edges (MST, etc.)
    if highlight_edges:
        nx.draw_networkx_edges(G, pos, ax=ax, edgelist=highlight_edges,
                               edge_color=COLORS["mst_edge"], width=5, alpha=1.0)
    
    # Draw nodes with glow effect
    # Outer glow
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=1600, alpha=0.3)
    # Main node
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=1200, alpha=0.95, edgecolors='white', linewidths=2)
    
    # Node labels
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=12, font_weight="bold",
                            font_color="white")
    
    # Edge labels
    if edge_labels_custom:
        nx.draw_networkx_edge_labels(G, pos, edge_labels_custom, ax=ax,
                                     font_size=9, font_color=COLORS["warning"],
                                     bbox=dict(boxstyle="round,pad=0.3", facecolor=COLORS["surface"],
                                              edgecolor="none", alpha=0.8))
    else:
        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels, ax=ax,
                                     font_size=9, font_color=COLORS["text"],
                                     bbox=dict(boxstyle="round,pad=0.2", facecolor=COLORS["surface"],
                                              edgecolor="none", alpha=0.7))
    
    # Add legend
    legend_elements = []
    if failed_nodes:
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w',
                                          markerfacecolor=COLORS["node_failed"],
                                          markersize=10, label='Failed Node'))
    if vulnerable_roads:
        legend_elements.append(plt.Line2D([0], [0], color=COLORS["edge_vulnerable"],
                                          linewidth=3, label='Vulnerable Road'))
    if highlight_edges:
        legend_elements.append(plt.Line2D([0], [0], color=COLORS["mst_edge"],
                                          linewidth=3, label='MST/Selected'))
    
    if legend_elements:
        ax.legend(handles=legend_elements, loc='upper left', facecolor=COLORS["surface"],
                  edgecolor=COLORS["surface"], labelcolor=COLORS["text"], fontsize=9)
    
    ax.axis('off')
    fig.tight_layout()
    canvas.draw()
    
    # Update stats
    total_weight = sum(data['weight'] for u, v, data in G.edges(data=True)) if G.number_of_edges() > 0 else 0
    update_results(nodes=G.number_of_nodes(), edges=G.number_of_edges(), weight=total_weight)

def draw_statistics():
    """Draw network statistics charts"""
    fig_stats.clear()
    
    if len(G.nodes()) == 0:
        ax_s = fig_stats.add_subplot(111)
        ax_s.set_facecolor("#1a1a2e")
        ax_s.text(0.5, 0.5, "No data available", ha='center', va='center',
                  fontsize=14, color=COLORS["subtext"])
        canvas_stats.draw()
        return
    
    # Create 2x2 subplot grid
    gs = fig_stats.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # 1. Degree distribution
    ax1 = fig_stats.add_subplot(gs[0, 0])
    ax1.set_facecolor("#1a1a2e")
    degrees = [G.degree(n) for n in G.nodes()]
    ax1.bar(list(G.nodes()), degrees, color=COLORS["accent"], alpha=0.8)
    ax1.set_title("Node Degrees", color=COLORS["text"], fontsize=11, fontweight='bold')
    ax1.set_ylabel("Degree", color=COLORS["text"], fontsize=9)
    ax1.tick_params(colors=COLORS["text"], labelsize=8)
    ax1.set_xticklabels(list(G.nodes()), rotation=45)
    
    # 2. Edge weight distribution
    ax2 = fig_stats.add_subplot(gs[0, 1])
    ax2.set_facecolor("#1a1a2e")
    weights = [data['weight'] for u, v, data in G.edges(data=True)]
    ax2.hist(weights, bins=10, color=COLORS["teal"], alpha=0.8, edgecolor=COLORS["surface"])
    ax2.set_title("Edge Weight Distribution", color=COLORS["text"], fontsize=11, fontweight='bold')
    ax2.set_xlabel("Weight", color=COLORS["text"], fontsize=9)
    ax2.set_ylabel("Frequency", color=COLORS["text"], fontsize=9)
    ax2.tick_params(colors=COLORS["text"], labelsize=8)
    
    # 3. Centrality measures
    ax3 = fig_stats.add_subplot(gs[1, 0])
    ax3.set_facecolor("#1a1a2e")
    
    betweenness = nx.betweenness_centrality(G)
    nodes = list(betweenness.keys())
    values = list(betweenness.values())
    
    bars = ax3.barh(nodes, values, color=COLORS["peach"], alpha=0.8)
    ax3.set_title("Betweenness Centrality", color=COLORS["text"], fontsize=11, fontweight='bold')
    ax3.set_xlabel("Centrality", color=COLORS["text"], fontsize=9)
    ax3.tick_params(colors=COLORS["text"], labelsize=8)
    
    # 4. Network summary
    ax4 = fig_stats.add_subplot(gs[1, 1])
    ax4.set_facecolor("#1a1a2e")
    ax4.axis('off')
    
    # Calculate metrics
    avg_degree = sum(dict(G.degree()).values()) / len(G.nodes())
    density = nx.density(G)
    try:
        avg_clustering = nx.average_clustering(G)
    except:
        avg_clustering = 0
    
    is_connected = "Yes ✅" if nx.is_connected(G) else "No ❌"
    
    summary_text = f"""
    📊 Network Summary
    ─────────────────────
    Nodes: {G.number_of_nodes()}
    Edges: {G.number_of_edges()}
    Average Degree: {avg_degree:.2f}
    Density: {density:.4f}
    Clustering: {avg_clustering:.4f}
    Connected: {is_connected}
    Vulnerable Roads: {len(vulnerable_roads)}
    Failed Nodes: {len(failed_nodes)}
    """
    
    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, fontsize=10,
             color=COLORS["text"], verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=0.5", facecolor=COLORS["surface"], edgecolor="none"))
    
    canvas_stats.draw()

def draw_adjacency_matrix():
    """Draw adjacency matrix heatmap"""
    fig_matrix.clear()
    
    if len(G.nodes()) == 0:
        ax_m = fig_matrix.add_subplot(111)
        ax_m.set_facecolor("#1a1a2e")
        ax_m.text(0.5, 0.5, "No data available", ha='center', va='center',
                  fontsize=14, color=COLORS["subtext"])
        canvas_matrix.draw()
        return
    
    ax_m = fig_matrix.add_subplot(111)
    ax_m.set_facecolor("#1a1a2e")
    
    nodes = sorted(G.nodes())
    n = len(nodes)
    matrix = np.zeros((n, n))
    
    for i, u in enumerate(nodes):
        for j, v in enumerate(nodes):
            if G.has_edge(u, v):
                matrix[i][j] = G[u][v]['weight']
    
    im = ax_m.imshow(matrix, cmap='Blues', aspect='auto')
    
    ax_m.set_xticks(range(n))
    ax_m.set_yticks(range(n))
    ax_m.set_xticklabels(nodes, color=COLORS["text"], fontsize=10)
    ax_m.set_yticklabels(nodes, color=COLORS["text"], fontsize=10)
    
    ax_m.set_title("Weighted Adjacency Matrix", color=COLORS["text"], 
                   fontsize=14, fontweight='bold', pad=15)
    
    # Add color bar
    cbar = fig_matrix.colorbar(im, ax=ax_m, shrink=0.8)
    cbar.ax.yaxis.set_tick_params(color=COLORS["text"])
    cbar.ax.set_ylabel('Edge Weight', color=COLORS["text"], fontsize=10)
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=COLORS["text"])
    
    # Add values to cells
    for i in range(n):
        for j in range(n):
            if matrix[i][j] > 0:
                text_color = 'white' if matrix[i][j] > matrix.max()/2 else COLORS["text"]
                ax_m.text(j, i, f'{int(matrix[i][j])}', ha='center', va='center',
                         color=text_color, fontsize=9, fontweight='bold')
    
    fig_matrix.tight_layout()
    canvas_matrix.draw()

# --------------------------------
# Q1: Animated MST Visualization
# --------------------------------
def show_mst_animated():
    if len(G.nodes()) == 0:
        messagebox.showwarning("Warning", "Graph is empty!")
        return
    
    if not nx.is_connected(G):
        messagebox.showwarning("Warning", "Graph is not connected! MST requires a connected graph.")
        return
    
    def run_animation():
        clear_log()
        update_algo_info(
            "Kruskal's MST Algorithm",
            "Time: O(E log E) | Space: O(V)",
            "Finds minimum cost spanning tree using greedy edge selection with Union-Find."
        )
        update_status("Computing MST...", "processing")
        
        log_message("═══ MINIMUM SPANNING TREE (Kruskal's) ═══", "title")
        log_message("Finding minimum cost network connections\n", "info")
        
        # Get sorted edges
        edges = [(u, v, data['weight']) for u, v, data in G.edges(data=True)]
        edges.sort(key=lambda x: x[2])
        
        log_message("Step 1: Sort all edges by weight", "info")
        for i, (u, v, w) in enumerate(edges):
            log_message(f"  {i+1}. {u}↔{v}: weight={w}", "step")
        
        log_message("\nStep 2: Build MST (Union-Find)", "info")
        
        # Kruskal's with animation
        parent = {node: node for node in G.nodes()}
        rank = {node: 0 for node in G.nodes()}
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px == py:
                return False
            if rank[px] < rank[py]:
                px, py = py, px
            parent[py] = px
            if rank[px] == rank[py]:
                rank[px] += 1
            return True
        
        mst_edges = []
        total_weight = 0
        
        for i, (u, v, w) in enumerate(edges):
            update_progress((i + 1) / len(edges) * 100)
            
            if union(u, v):
                mst_edges.append((u, v))
                total_weight += w
                log_message(f"  ✓ Added {u}↔{v} (weight={w}) - Trees merged!", "success")
                
                # Animate
                draw_graph(highlight_edges=mst_edges,
                          title=f"Building MST: {len(mst_edges)}/{len(G.nodes())-1} edges")
                time.sleep(animation_speed)
            else:
                log_message(f"  ✗ Skipped {u}↔{v} - Would create cycle", "warning")
            
            if len(mst_edges) == len(G.nodes()) - 1:
                break
        
        # Final result
        draw_graph(highlight_edges=mst_edges,
                   title=f"✅ Minimum Spanning Tree (Total Weight: {total_weight})")
        
        log_message(f"\n{'═'*40}", "title")
        log_message(f"MST Complete!", "success")
        log_message(f"  Total Weight: {total_weight}", "highlight")
        log_message(f"  Edges Used: {len(mst_edges)}", "info")
        log_message(f"  Cost Savings: {sum(e[2] for e in edges) - total_weight}", "success")
        
        update_results(result=f"MST: {total_weight}")
        update_status(f"MST computed - Total weight: {total_weight}", "success")
        update_progress(100)
        
        # Update other views
        draw_statistics()
        draw_adjacency_matrix()
    
    threading.Thread(target=run_animation, daemon=True).start()

# --------------------------------
# Q2: K-Shortest Paths with Animation
# --------------------------------
def find_reliable_paths():
    if len(G.nodes()) < 2:
        messagebox.showwarning("Warning", "Need at least 2 nodes!")
        return
    
    path_window = tk.Toplevel(root)
    path_window.title("🛤️ Reliable Path Finder")
    path_window.geometry("650x700")
    path_window.configure(bg=COLORS["bg"])
    path_window.transient(root)
    path_window.grab_set()
    
    # Header
    header = tk.Frame(path_window, bg=COLORS["surface"])
    header.pack(fill=tk.X)
    tk.Label(header, text="🛤️ K-Shortest Reliable Paths", font=("Segoe UI", 16, "bold"),
             bg=COLORS["surface"], fg=COLORS["accent"], pady=15).pack()
    
    # Input section
    input_frame = tk.Frame(path_window, bg=COLORS["card"])
    input_frame.pack(fill=tk.X, padx=20, pady=15)
    
    nodes_list = sorted(G.nodes())
    
    # Source
    row1 = tk.Frame(input_frame, bg=COLORS["card"])
    row1.pack(fill=tk.X, padx=15, pady=8)
    tk.Label(row1, text="📍 Source:", font=("Segoe UI", 11), bg=COLORS["card"],
             fg=COLORS["text"], width=12, anchor="w").pack(side=tk.LEFT)
    source_var = tk.StringVar(value=nodes_list[0])
    source_combo = ttk.Combobox(row1, textvariable=source_var, values=nodes_list,
                                 state="readonly", width=20, font=("Segoe UI", 10))
    source_combo.pack(side=tk.LEFT, padx=10)
    
    # Destination
    row2 = tk.Frame(input_frame, bg=COLORS["card"])
    row2.pack(fill=tk.X, padx=15, pady=8)
    tk.Label(row2, text="🎯 Destination:", font=("Segoe UI", 11), bg=COLORS["card"],
             fg=COLORS["text"], width=12, anchor="w").pack(side=tk.LEFT)
    dest_var = tk.StringVar(value=nodes_list[-1] if len(nodes_list) > 1 else nodes_list[0])
    dest_combo = ttk.Combobox(row2, textvariable=dest_var, values=nodes_list,
                               state="readonly", width=20, font=("Segoe UI", 10))
    dest_combo.pack(side=tk.LEFT, padx=10)
    
    # K value
    row3 = tk.Frame(input_frame, bg=COLORS["card"])
    row3.pack(fill=tk.X, padx=15, pady=8)
    tk.Label(row3, text="🔢 K Paths:", font=("Segoe UI", 11), bg=COLORS["card"],
             fg=COLORS["text"], width=12, anchor="w").pack(side=tk.LEFT)
    k_var = tk.StringVar(value="3")
    k_spinbox = ttk.Spinbox(row3, from_=1, to=10, textvariable=k_var, width=8,
                            font=("Segoe UI", 10))
    k_spinbox.pack(side=tk.LEFT, padx=10)
    
    # Options
    options_frame = tk.Frame(input_frame, bg=COLORS["card"])
    options_frame.pack(fill=tk.X, padx=15, pady=10)
    
    avoid_var = tk.BooleanVar(value=True)
    avoid_check = tk.Checkbutton(options_frame, text="⚠️ Avoid vulnerable roads",
                                  variable=avoid_var, bg=COLORS["card"], fg=COLORS["text"],
                                  selectcolor=COLORS["surface"], font=("Segoe UI", 10),
                                  activebackground=COLORS["card"])
    avoid_check.pack(side=tk.LEFT)
    
    animate_var = tk.BooleanVar(value=True)
    animate_check = tk.Checkbutton(options_frame, text="🎬 Animate search",
                                    variable=animate_var, bg=COLORS["card"], fg=COLORS["text"],
                                    selectcolor=COLORS["surface"], font=("Segoe UI", 10),
                                    activebackground=COLORS["card"])
    animate_check.pack(side=tk.LEFT, padx=20)
    
    # Results section
    tk.Label(path_window, text="📋 Found Paths:", font=("Segoe UI", 11, "bold"),
             bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", padx=20, pady=(15, 5))
    
    result_frame = tk.Frame(path_window, bg=COLORS["surface"])
    result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
    
    result_text = tk.Text(result_frame, bg=COLORS["surface"], fg=COLORS["text"],
                          font=("Consolas", 10), wrap=tk.WORD, relief="flat")
    result_scroll = ttk.Scrollbar(result_frame, orient="vertical", command=result_text.yview)
    result_text.configure(yscrollcommand=result_scroll.set)
    
    result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
    
    result_text.tag_configure("header", foreground=COLORS["lavender"], font=("Consolas", 11, "bold"))
    result_text.tag_configure("path", foreground=COLORS["success"])
    result_text.tag_configure("info", foreground=COLORS["warning"])
    result_text.tag_configure("error", foreground=COLORS["error"])
    result_text.tag_configure("best", foreground=COLORS["teal"], font=("Consolas", 10, "bold"))
    
    def compute_paths():
        def run_search():
            clear_log()
            update_algo_info(
                "Yen's K-Shortest Paths",
                "Time: O(KV(E + V log V))",
                "Finds K shortest loopless paths using Dijkstra's algorithm iteratively."
            )
            
            try:
                source = source_var.get()
                dest = dest_var.get()
                k = int(k_var.get())
                
                if source == dest:
                    messagebox.showerror("Error", "Source and destination must be different")
                    return
                
                log_message("═══ K-SHORTEST PATHS (Yen's Algorithm) ═══", "title")
                log_message(f"Finding {k} paths: {source} → {dest}\n", "info")
                
                update_status(f"Finding {k} paths from {source} to {dest}...", "processing")
                
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"🔍 Searching for {k} shortest paths: {source} → {dest}\n\n", "header")
                
                # Create working graph
                G_work = G.copy()
                avoided = []
                
                if avoid_var.get() and vulnerable_roads:
                    for edge in vulnerable_roads:
                        if G_work.has_edge(edge[0], edge[1]):
                            G_work.remove_edge(edge[0], edge[1])
                            avoided.append(f"{edge[0]}↔{edge[1]}")
                    
                    if avoided:
                        result_text.insert(tk.END, f"⚠️ Avoiding vulnerable: {', '.join(avoided)}\n\n", "info")
                        log_message(f"Avoiding {len(avoided)} vulnerable roads", "warning")
                
                # Find paths
                try:
                    paths = list(nx.shortest_simple_paths(G_work, source, dest, weight='weight'))[:k]
                except nx.NetworkXNoPath:
                    result_text.insert(tk.END, "❌ No path exists between these nodes!\n", "error")
                    log_message("No path found!", "error")
                    update_status("No path found", "error")
                    return
                
                if not paths:
                    result_text.insert(tk.END, "❌ No paths found!\n", "error")
                    return
                
                result_text.insert(tk.END, f"✅ Found {len(paths)} path(s):\n\n", "header")
                
                for i, path in enumerate(paths, 1):
                    length = sum(G[path[j]][path[j+1]]['weight'] for j in range(len(path)-1))
                    path_str = " → ".join(path)
                    
                    tag = "best" if i == 1 else "path"
                    prefix = "🥇 BEST" if i == 1 else f"#{i}"
                    
                    result_text.insert(tk.END, f"{prefix}: {path_str}\n", tag)
                    result_text.insert(tk.END, f"   📏 Distance: {length}\n", "info")
                    
                    edges_str = " + ".join([f"{path[j]}→{path[j+1]}({G[path[j]][path[j+1]]['weight']})" 
                                           for j in range(len(path)-1)])
                    result_text.insert(tk.END, f"   🔗 Edges: {edges_str}\n\n")
                    
                    log_message(f"Path {i}: {path_str} (length={length})", "success")
                    
                    if animate_var.get():
                        path_edges = [(path[j], path[j+1]) for j in range(len(path)-1)]
                        draw_graph(path_edges=path_edges if i > 1 else None,
                                   highlight_edges=path_edges if i == 1 else None,
                                   title=f"Path {i}: {path_str}")
                        time.sleep(animation_speed * 0.7)
                
                # Show best path
                best_path = paths[0]
                best_edges = [(best_path[j], best_path[j+1]) for j in range(len(best_path)-1)]
                draw_graph(highlight_edges=best_edges,
                           title=f"Best Path: {' → '.join(best_path)}")
                
                update_results(result=f"{len(paths)} paths")
                update_status(f"Found {len(paths)} paths from {source} to {dest}", "success")
                
            except Exception as e:
                log_message(f"Error: {str(e)}", "error")
                result_text.insert(tk.END, f"❌ Error: {str(e)}\n", "error")
                update_status(f"Error: {str(e)}", "error")
        
        threading.Thread(target=run_search, daemon=True).start()
    
    # Buttons
    btn_frame = tk.Frame(path_window, bg=COLORS["bg"])
    btn_frame.pack(pady=15)
    
    tk.Button(btn_frame, text="🔍 Find Paths", command=compute_paths,
              bg=COLORS["accent"], fg="white", font=("Segoe UI", 11, "bold"),
              relief="flat", padx=25, pady=10, cursor="hand2").pack(side=tk.LEFT, padx=8)
    
    tk.Button(btn_frame, text="Close", command=path_window.destroy,
              bg=COLORS["surface"], fg=COLORS["text"], font=("Segoe UI", 10),
              relief="flat", padx=20, pady=10).pack(side=tk.LEFT, padx=8)

# --------------------------------
# Q3: Command Hierarchy with Tree Traversals
# --------------------------------
def show_command_tree():
    tree_window = tk.Toplevel(root)
    tree_window.title("🌳 Command Hierarchy Optimizer")
    tree_window.geometry("1000x750")
    tree_window.configure(bg=COLORS["bg"])
    tree_window.transient(root)
    tree_window.grab_set()
    
    # Header
    header = tk.Frame(tree_window, bg=COLORS["surface"])
    header.pack(fill=tk.X)
    tk.Label(header, text="🌳 Command Hierarchy Optimization", font=("Segoe UI", 16, "bold"),
             bg=COLORS["surface"], fg=COLORS["accent"], pady=15).pack()
    
    # Main content
    content = tk.Frame(tree_window, bg=COLORS["bg"])
    content.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
    
    content.grid_columnconfigure(0, weight=2)
    content.grid_columnconfigure(1, weight=1)
    content.grid_rowconfigure(0, weight=1)
    
    # Tree visualization
    tree_viz = tk.Frame(content, bg=COLORS["card"])
    tree_viz.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    
    fig_tree = Figure(figsize=(8, 6), facecolor=COLORS["card"])
    ax_tree = fig_tree.add_subplot(111)
    ax_tree.set_facecolor("#1a1a2e")
    canvas_tree = FigureCanvasTkAgg(fig_tree, master=tree_viz)
    canvas_tree.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Control panel
    control_panel = tk.Frame(content, bg=COLORS["card"])
    control_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
    
    tk.Label(control_panel, text="🎛️ Controls", font=("Segoe UI", 12, "bold"),
             bg=COLORS["card"], fg=COLORS["accent"]).pack(pady=15)
    
    # Info display
    info_frame = tk.Frame(control_panel, bg=COLORS["surface"])
    info_frame.pack(fill=tk.X, padx=10, pady=5)
    
    tree_info_label = tk.Label(info_frame, text="", font=("Consolas", 9),
                                bg=COLORS["surface"], fg=COLORS["text"],
                                justify="left", padx=10, pady=10)
    tree_info_label.pack(fill=tk.X)
    
    # Traversal output
    tk.Label(control_panel, text="📝 Traversal Output:", font=("Segoe UI", 10, "bold"),
             bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", padx=10, pady=(15, 5))
    
    traversal_frame = tk.Frame(control_panel, bg=COLORS["card"])
    traversal_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    traversal_text = tk.Text(traversal_frame, bg=COLORS["surface"], fg=COLORS["text"],
                             font=("Consolas", 9), wrap=tk.WORD, height=12)
    traversal_scroll = ttk.Scrollbar(traversal_frame, orient="vertical", command=traversal_text.yview)
    traversal_text.configure(yscrollcommand=traversal_scroll.set)
    
    traversal_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    traversal_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    traversal_text.tag_configure("title", foreground=COLORS["lavender"], font=("Consolas", 10, "bold"))
    traversal_text.tag_configure("node", foreground=COLORS["success"])
    traversal_text.tag_configure("info", foreground=COLORS["warning"])
    
    current_root = [hq]  # Use list for mutable reference
    
    def draw_tree(root_node, highlight_nodes=None, title="Command Hierarchy"):
        ax_tree.clear()
        ax_tree.set_facecolor("#1a1a2e")
        ax_tree.set_title(title, fontsize=12, fontweight='bold', color=COLORS["text"], pad=10)
        
        T = nx.DiGraph()
        levels = {}
        
        def add_edges(node, level=0):
            if node:
                levels[node.name] = level
                if node.left:
                    T.add_edge(node.name, node.left.name)
                    add_edges(node.left, level + 1)
                if node.right:
                    T.add_edge(node.name, node.right.name)
                    add_edges(node.right, level + 1)
        
        add_edges(root_node)
        
        if T.number_of_nodes() == 0:
            ax_tree.text(0.5, 0.5, "Empty tree", ha='center', va='center',
                        color=COLORS["subtext"], fontsize=14)
            canvas_tree.draw()
            return
        
        # Hierarchical layout
        tree_pos = {}
        level_counts = {}
        level_indices = {}
        
        for node, level in levels.items():
            if level not in level_counts:
                level_counts[level] = 0
                level_indices[level] = 0
            level_counts[level] += 1
        
        for node, level in sorted(levels.items(), key=lambda x: (x[1], x[0])):
            width = level_counts[level]
            idx = level_indices[level]
            x = (idx - width/2 + 0.5) * (3 / max(width, 1))
            y = -level * 1.5
            tree_pos[node] = (x, y)
            level_indices[level] += 1
        
        # Node colors
        max_level = max(levels.values()) if levels else 1
        node_colors = []
        for n in T.nodes():
            if highlight_nodes and n in highlight_nodes:
                node_colors.append(COLORS["node_current"])
            else:
                # Gradient by level
                level_ratio = levels.get(n, 0) / max(max_level, 1)
                node_colors.append(plt.cm.viridis(0.3 + level_ratio * 0.5))
        
        # Draw
        nx.draw_networkx_edges(T, tree_pos, ax=ax_tree, edge_color=COLORS["text"],
                               arrows=True, arrowsize=20, alpha=0.7, width=2)
        
        nx.draw_networkx_nodes(T, tree_pos, ax=ax_tree, node_color=node_colors,
                               node_size=3000, alpha=0.9, edgecolors='white', linewidths=2)
        
        nx.draw_networkx_labels(T, tree_pos, ax=ax_tree, font_size=8,
                                font_weight='bold', font_color='white')
        
        ax_tree.axis('off')
        fig_tree.tight_layout()
        canvas_tree.draw()
        
        # Update info
        def max_depth(node):
            if node is None:
                return 0
            return 1 + max(max_depth(node.left), max_depth(node.right))
        
        def count_nodes(node):
            if node is None:
                return 0
            return 1 + count_nodes(node.left) + count_nodes(node.right)
        
        depth = max_depth(root_node)
        nodes = count_nodes(root_node)
        optimal = int(np.ceil(np.log2(nodes + 1)))
        
        info = f"📊 Tree Statistics\n"
        info += f"─────────────────\n"
        info += f"Nodes: {nodes}\n"
        info += f"Max Depth: {depth}\n"
        info += f"Optimal Depth: {optimal}\n"
        info += f"Balance: {'✅ Good' if depth <= optimal + 1 else '⚠️ Unbalanced'}"
        
        tree_info_label.config(text=info)
    
    def run_traversal(traversal_type):
        traversal_text.delete(1.0, tk.END)
        traversal_text.insert(tk.END, f"═══ {traversal_type.upper()} TRAVERSAL ═══\n\n", "title")
        
        visited = []
        
        def inorder(node):
            if node:
                inorder(node.left)
                visited.append(node.name)
                traversal_text.insert(tk.END, f"  → {node.name}\n", "node")
                traversal_text.see(tk.END)
                draw_tree(current_root[0], highlight_nodes=set(visited),
                         title=f"{traversal_type}: Visiting {node.name}")
                root.update()
                time.sleep(animation_speed * 0.3)
                inorder(node.right)
        
        def preorder(node):
            if node:
                visited.append(node.name)
                traversal_text.insert(tk.END, f"  → {node.name}\n", "node")
                traversal_text.see(tk.END)
                draw_tree(current_root[0], highlight_nodes=set(visited),
                         title=f"{traversal_type}: Visiting {node.name}")
                root.update()
                time.sleep(animation_speed * 0.3)
                preorder(node.left)
                preorder(node.right)
        
        def postorder(node):
            if node:
                postorder(node.left)
                postorder(node.right)
                visited.append(node.name)
                traversal_text.insert(tk.END, f"  → {node.name}\n", "node")
                traversal_text.see(tk.END)
                draw_tree(current_root[0], highlight_nodes=set(visited),
                         title=f"{traversal_type}: Visiting {node.name}")
                root.update()
                time.sleep(animation_speed * 0.3)
        
        def levelorder(node):
            if not node:
                return
            queue = deque([node])
            while queue:
                curr = queue.popleft()
                visited.append(curr.name)
                traversal_text.insert(tk.END, f"  → {curr.name}\n", "node")
                traversal_text.see(tk.END)
                draw_tree(current_root[0], highlight_nodes=set(visited),
                         title=f"{traversal_type}: Visiting {curr.name}")
                root.update()
                time.sleep(animation_speed * 0.3)
                if curr.left:
                    queue.append(curr.left)
                if curr.right:
                    queue.append(curr.right)
        
        def run():
            if traversal_type == "In-Order":
                inorder(current_root[0])
            elif traversal_type == "Pre-Order":
                preorder(current_root[0])
            elif traversal_type == "Post-Order":
                postorder(current_root[0])
            elif traversal_type == "Level-Order":
                levelorder(current_root[0])
            
            traversal_text.insert(tk.END, f"\n✅ Traversal complete!\n", "info")
            traversal_text.insert(tk.END, f"Order: {' → '.join(visited)}\n", "node")
            draw_tree(current_root[0], title="Traversal Complete")
        
        threading.Thread(target=run, daemon=True).start()
    
    def optimize_tree():
        traversal_text.delete(1.0, tk.END)
        traversal_text.insert(tk.END, "═══ TREE OPTIMIZATION ═══\n\n", "title")
        traversal_text.insert(tk.END, "Using Divide & Conquer to balance...\n\n", "info")
        
        # Collect nodes
        nodes = []
        def collect(node):
            if node:
                nodes.append(node.name)
                collect(node.left)
                collect(node.right)
        collect(current_root[0])
        
        traversal_text.insert(tk.END, f"Nodes collected: {nodes}\n", "node")
        traversal_text.insert(tk.END, f"Sorting nodes...\n\n", "info")
        
        sorted_nodes = sorted(nodes)
        
        def build_balanced(names, level=0):
            if not names:
                return None
            mid = len(names) // 2
            node = CommandNode(names[mid], level)
            node.left = build_balanced(names[:mid], level + 1)
            node.right = build_balanced(names[mid+1:], level + 1)
            return node
        
        current_root[0] = build_balanced(sorted_nodes)
        draw_tree(current_root[0], title="✅ Optimized Balanced Tree")
        
        traversal_text.insert(tk.END, "✅ Tree optimized!\n\n", "info")
        traversal_text.insert(tk.END, f"New structure is balanced with\n", "node")
        traversal_text.insert(tk.END, f"optimal O(log n) search time.\n", "node")
    
    # Buttons
    btn_frame = tk.Frame(control_panel, bg=COLORS["card"])
    btn_frame.pack(fill=tk.X, padx=10, pady=15)
    
    tk.Label(btn_frame, text="🔄 Traversals:", font=("Segoe UI", 10, "bold"),
             bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 8))
    
    traversals = ["In-Order", "Pre-Order", "Post-Order", "Level-Order"]
    for trav in traversals:
        tk.Button(btn_frame, text=f"▶️ {trav}", 
                  command=lambda t=trav: run_traversal(t),
                  bg=COLORS["surface"], fg=COLORS["text"], font=("Segoe UI", 9),
                  relief="flat", padx=10, pady=5, cursor="hand2",
                  width=15).pack(pady=2)
    
    tk.Label(btn_frame, text="", bg=COLORS["card"]).pack(pady=5)
    
    tk.Button(btn_frame, text="⚡ Optimize Tree", command=optimize_tree,
              bg=COLORS["accent"], fg="white", font=("Segoe UI", 10, "bold"),
              relief="flat", padx=15, pady=8, cursor="hand2",
              width=15).pack(pady=5)
    
    tk.Button(btn_frame, text="🔄 Reset Original", 
              command=lambda: [current_root.__setitem__(0, hq), draw_tree(hq)],
              bg=COLORS["surface"], fg=COLORS["text"], font=("Segoe UI", 9),
              relief="flat", padx=10, pady=5, width=15).pack(pady=2)
    
    # Initial draw
    draw_tree(hq)

# --------------------------------
# Q4: Advanced Failure Simulation
# --------------------------------
def simulate_failure():
    if len(G.nodes()) == 0:
        messagebox.showwarning("Warning", "Graph is empty!")
        return
    
    fail_window = tk.Toplevel(root)
    fail_window.title("💥 Network Failure Simulation")
    fail_window.geometry("700x800")
    fail_window.configure(bg=COLORS["bg"])
    fail_window.transient(root)
    fail_window.grab_set()
    
    # Header
    header = tk.Frame(fail_window, bg=COLORS["surface"])
    header.pack(fill=tk.X)
    tk.Label(header, text="💥 Network Failure Simulation", font=("Segoe UI", 16, "bold"),
             bg=COLORS["surface"], fg=COLORS["accent"], pady=15).pack()
    
    # Selection
    select_frame = tk.Frame(fail_window, bg=COLORS["card"])
    select_frame.pack(fill=tk.X, padx=20, pady=15)
    
    tk.Label(select_frame, text="Select failure type:", font=("Segoe UI", 11, "bold"),
             bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", padx=15, pady=(15, 10))
    
    fail_type = tk.StringVar(value="node")
    
    type_frame = tk.Frame(select_frame, bg=COLORS["card"])
    type_frame.pack(fill=tk.X, padx=15, pady=5)
    
    tk.Radiobutton(type_frame, text="🔴 Node Failure", variable=fail_type, value="node",
                   bg=COLORS["card"], fg=COLORS["text"], selectcolor=COLORS["surface"],
                   font=("Segoe UI", 10), activebackground=COLORS["card"]).pack(side=tk.LEFT, padx=10)
    
    tk.Radiobutton(type_frame, text="🔗 Edge Failure", variable=fail_type, value="edge",
                   bg=COLORS["card"], fg=COLORS["text"], selectcolor=COLORS["surface"],
                   font=("Segoe UI", 10), activebackground=COLORS["card"]).pack(side=tk.LEFT, padx=10)
    
    # Node selection
    node_frame = tk.Frame(select_frame, bg=COLORS["card"])
    node_frame.pack(fill=tk.X, padx=15, pady=10)
    
    tk.Label(node_frame, text="Target Node:", font=("Segoe UI", 10),
             bg=COLORS["card"], fg=COLORS["text"]).pack(side=tk.LEFT)
    
    node_var = tk.StringVar(value=list(G.nodes())[0] if G.nodes() else "")
    node_combo = ttk.Combobox(node_frame, textvariable=node_var,
                               values=list(G.nodes()), state="readonly", width=15)
    node_combo.pack(side=tk.LEFT, padx=10)
    
    # Edge selection
    edge_frame = tk.Frame(select_frame, bg=COLORS["card"])
    edge_frame.pack(fill=tk.X, padx=15, pady=10)
    
    tk.Label(edge_frame, text="Target Edge:", font=("Segoe UI", 10),
             bg=COLORS["card"], fg=COLORS["text"]).pack(side=tk.LEFT)
    
    edges_list = [f"{u}-{v}" for u, v in G.edges()]
    edge_var = tk.StringVar(value=edges_list[0] if edges_list else "")
    edge_combo = ttk.Combobox(edge_frame, textvariable=edge_var,
                               values=edges_list, state="readonly", width=15)
    edge_combo.pack(side=tk.LEFT, padx=10)
    
    # Results
    tk.Label(fail_window, text="📊 Impact Analysis:", font=("Segoe UI", 11, "bold"),
             bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", padx=20, pady=(15, 5))
    
    result_frame = tk.Frame(fail_window, bg=COLORS["surface"])
    result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
    
    result_text = tk.Text(result_frame, bg=COLORS["surface"], fg=COLORS["text"],
                          font=("Consolas", 10), wrap=tk.WORD)
    result_scroll = ttk.Scrollbar(result_frame, orient="vertical", command=result_text.yview)
    result_text.configure(yscrollcommand=result_scroll.set)
    
    result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
    
    result_text.tag_configure("header", foreground=COLORS["lavender"], font=("Consolas", 11, "bold"))
    result_text.tag_configure("danger", foreground=COLORS["error"])
    result_text.tag_configure("warning", foreground=COLORS["warning"])
    result_text.tag_configure("success", foreground=COLORS["success"])
    result_text.tag_configure("info", foreground=COLORS["accent"])
    
    def run_simulation():
        clear_log()
        update_algo_info(
            "Failure Impact Analysis",
            "Time: O(V²) for all-pairs paths",
            "Analyzes network connectivity and path changes after component failure."
        )
        
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "═══════ FAILURE SIMULATION REPORT ═══════\n\n", "header")
        
        ftype = fail_type.get()
        
        if ftype == "node":
            node = node_var.get()
            if not node or node not in G.nodes():
                messagebox.showerror("Error", "Please select a valid node")
                return
            
            log_message("═══ NODE FAILURE SIMULATION ═══", "title")
            log_message(f"Simulating failure of node: {node}\n", "warning")
            
            result_text.insert(tk.END, f"🔴 FAILED NODE: {node}\n", "danger")
            
            # Get metrics before
            neighbors = list(G.neighbors(node))
            affected_edges = G.degree(node)
            
            result_text.insert(tk.END, f"   Connections: {affected_edges}\n")
            result_text.insert(tk.END, f"   Neighbors: {', '.join(neighbors)}\n\n")
            
            # Store path info
            old_paths = {}
            for s in G.nodes():
                for t in G.nodes():
                    if s != t and s != node and t != node:
                        try:
                            old_paths[(s,t)] = nx.shortest_path_length(G, s, t, weight='weight')
                        except:
                            old_paths[(s,t)] = float('inf')
            
            # Remove node
            failed_nodes.add(node)
            G.remove_node(node)
            if node in pos:
                del pos[node]
            
            # Analyze impact
            disconnected = []
            increased = []
            
            for (s,t), old_len in old_paths.items():
                if s in G.nodes() and t in G.nodes():
                    try:
                        new_len = nx.shortest_path_length(G, s, t, weight='weight')
                        if new_len > old_len:
                            increased.append((s, t, new_len - old_len))
                    except:
                        disconnected.append((s, t))
            
            # Display results
            result_text.insert(tk.END, "─────── IMPACT ANALYSIS ───────\n\n")
            
            if disconnected:
                result_text.insert(tk.END, f"❌ DISCONNECTED PAIRS: {len(disconnected)}\n", "danger")
                for s, t in disconnected[:5]:
                    result_text.insert(tk.END, f"   • {s} ↔ {t}\n")
                if len(disconnected) > 5:
                    result_text.insert(tk.END, f"   ... and {len(disconnected)-5} more\n")
                result_text.insert(tk.END, "\n")
            
            if increased:
                increased.sort(key=lambda x: x[2], reverse=True)
                result_text.insert(tk.END, f"📈 PATH INCREASES: {len(increased)}\n", "warning")
                for s, t, inc in increased[:5]:
                    result_text.insert(tk.END, f"   • {s} → {t}: +{inc:.1f}\n")
                result_text.insert(tk.END, "\n")
            
            # Connectivity check
            if G.number_of_nodes() > 0:
                if nx.is_connected(G):
                    result_text.insert(tk.END, "✅ Network remains CONNECTED\n\n", "success")
                else:
                    components = list(nx.connected_components(G))
                    result_text.insert(tk.END, f"⚠️ Network FRAGMENTED into {len(components)} parts:\n", "danger")
                    for i, comp in enumerate(components, 1):
                        result_text.insert(tk.END, f"   Component {i}: {', '.join(sorted(comp))}\n")
            
            # Update combo
            node_combo.config(values=list(G.nodes()))
            if G.nodes():
                node_var.set(list(G.nodes())[0])
            
            edge_combo.config(values=[f"{u}-{v}" for u, v in G.edges()])
            
        else:
            edge_str = edge_var.get()
            if not edge_str:
                messagebox.showerror("Error", "Please select an edge")
                return
            
            u, v = edge_str.split("-")
            
            if not G.has_edge(u, v):
                messagebox.showerror("Error", "Edge doesn't exist")
                return
            
            log_message("═══ EDGE FAILURE SIMULATION ═══", "title")
            log_message(f"Simulating failure of edge: {u}↔{v}\n", "warning")
            
            weight = G[u][v]['weight']
            result_text.insert(tk.END, f"🔗 FAILED EDGE: {u} ↔ {v}\n", "danger")
            result_text.insert(tk.END, f"   Weight: {weight}\n\n")
            
            # Remove edge
            G.remove_edge(u, v)
            vulnerable_roads.add((u, v))
            
            # Check connectivity
            result_text.insert(tk.END, "─────── IMPACT ANALYSIS ───────\n\n")
            
            if nx.is_connected(G):
                try:
                    new_path = nx.shortest_path(G, u, v, weight='weight')
                    new_len = nx.shortest_path_length(G, u, v, weight='weight')
                    result_text.insert(tk.END, f"✅ Alternative path exists:\n", "success")
                    result_text.insert(tk.END, f"   Path: {' → '.join(new_path)}\n")
                    result_text.insert(tk.END, f"   New distance: {new_len} (was {weight})\n")
                    result_text.insert(tk.END, f"   Increase: +{new_len - weight}\n\n")
                except:
                    result_text.insert(tk.END, f"⚠️ No alternative path between {u} and {v}\n\n", "warning")
            else:
                result_text.insert(tk.END, f"❌ Network DISCONNECTED!\n", "danger")
                components = list(nx.connected_components(G))
                for i, comp in enumerate(components, 1):
                    result_text.insert(tk.END, f"   Component {i}: {', '.join(sorted(comp))}\n")
            
            edge_combo.config(values=[f"{u}-{v}" for u, v in G.edges()])
        
        # Update visualization
        draw_graph(title=f"Network After Failure")
        draw_statistics()
        draw_adjacency_matrix()
        
        update_status("Failure simulation complete", "warning")
    
    # Buttons
    btn_frame = tk.Frame(fail_window, bg=COLORS["bg"])
    btn_frame.pack(pady=15)
    
    tk.Button(btn_frame, text="💥 Simulate Failure", command=run_simulation,
              bg=COLORS["error"], fg="white", font=("Segoe UI", 11, "bold"),
              relief="flat", padx=20, pady=10, cursor="hand2").pack(side=tk.LEFT, padx=8)
    
    tk.Button(btn_frame, text="🔄 Reset Network", 
              command=lambda: [reset_graph(), fail_window.destroy()],
              bg=COLORS["surface"], fg=COLORS["text"], font=("Segoe UI", 10),
              relief="flat", padx=15, pady=10).pack(side=tk.LEFT, padx=8)

# --------------------------------
# Bonus: Graph Coloring with Animation
# --------------------------------
def color_graph_animated():
    if len(G.nodes()) == 0:
        messagebox.showwarning("Warning", "Graph is empty!")
        return
    
    def run_coloring():
        clear_log()
        update_algo_info(
            "Greedy Graph Coloring",
            "Time: O(V + E) | Largest First",
            "Assigns colors to nodes such that no adjacent nodes share the same color."
        )
        update_status("Coloring graph...", "processing")
        
        log_message("═══ GRAPH COLORING (Frequency Assignment) ═══", "title")
        log_message("Using Greedy Algorithm with Largest-First ordering\n", "info")
        
        # Sort nodes by degree
        nodes_by_degree = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True)
        
        log_message("Step 1: Order nodes by degree (descending)", "info")
        for i, node in enumerate(nodes_by_degree):
            log_message(f"  {i+1}. {node}: degree={G.degree(node)}", "step")
        
        log_message("\nStep 2: Assign colors greedily", "info")
        
        coloring = {}
        
        for i, node in enumerate(nodes_by_degree):
            update_progress((i + 1) / len(nodes_by_degree) * 100)
            
            # Find neighbors' colors
            neighbor_colors = {coloring[n] for n in G.neighbors(node) if n in coloring}
            
            # Find smallest available color
            color = 0
            while color in neighbor_colors:
                color += 1
            
            coloring[node] = color
            log_message(f"  {node}: assigned color {color + 1} (neighbors use: {neighbor_colors if neighbor_colors else 'none'})", "success")
            
            # Animate
            try:
                cmap = plt.colormaps.get_cmap('Set3')
            except:
                cmap = plt.cm.get_cmap('Set3')
            
            max_color = max(coloring.values()) + 1
            node_colors = []
            for n in G.nodes():
                if n in coloring:
                    node_colors.append(cmap(coloring[n] / max(max_color, 1)))
                else:
                    node_colors.append(COLORS["surface"])
            
            draw_graph(node_colors=node_colors, title=f"Coloring: {len(coloring)}/{len(G.nodes())} nodes")
            time.sleep(animation_speed * 0.3)
        
        num_colors = max(coloring.values()) + 1
        
        log_message(f"\n{'═'*40}", "title")
        log_message(f"Coloring Complete!", "success")
        log_message(f"  Chromatic number: {num_colors}", "highlight")
        log_message(f"  All adjacent nodes have different colors ✓", "success")
        
        update_results(result=f"{num_colors} colors")
        update_status(f"Graph colored with {num_colors} colors/frequencies", "success")
        update_progress(100)
        
        # Show final coloring
        info = f"🎨 Frequency Assignment Complete\n\n"
        info += f"Frequencies needed: {num_colors}\n\n"
        info += "Assignments:\n"
        for node in sorted(coloring.keys()):
            info += f"  {node}: Frequency {coloring[node] + 1}\n"
        
        messagebox.showinfo("Graph Coloring", info)
    
    threading.Thread(target=run_coloring, daemon=True).start()

# --------------------------------
# Graph Editing Functions
# --------------------------------
def add_node():
    name = simpledialog.askstring("Add Node", "Enter node name:", parent=root)
    if name:
        name = name.strip().upper()
        if not name:
            messagebox.showwarning("Warning", "Node name cannot be empty")
            return
        if name in G.nodes():
            messagebox.showwarning("Warning", "Node already exists")
            return
        G.add_node(name)
        pos[name] = (np.random.rand() * 2 - 1, np.random.rand() * 2 - 1)
        draw_graph(title=f"Added Node: {name}")
        draw_statistics()
        draw_adjacency_matrix()
        log_message(f"Added node: {name}", "success")
        update_status(f"Added node: {name}", "success")

def add_edge():
    if len(G.nodes()) < 2:
        messagebox.showwarning("Warning", "Need at least 2 nodes")
        return
    
    edge_window = tk.Toplevel(root)
    edge_window.title("➕ Add Edge")
    edge_window.geometry("400x350")
    edge_window.configure(bg=COLORS["bg"])
    edge_window.transient(root)
    edge_window.grab_set()
    
    tk.Label(edge_window, text="➕ Add New Edge", font=("Segoe UI", 14, "bold"),
             bg=COLORS["bg"], fg=COLORS["accent"]).pack(pady=20)
    
    frame = tk.Frame(edge_window, bg=COLORS["card"])
    frame.pack(fill=tk.X, padx=25, pady=10)
    
    nodes_list = sorted(G.nodes())
    
    # Source
    row1 = tk.Frame(frame, bg=COLORS["card"])
    row1.pack(fill=tk.X, padx=15, pady=10)
    tk.Label(row1, text="From:", font=("Segoe UI", 11), bg=COLORS["card"],
             fg=COLORS["text"], width=10, anchor="w").pack(side=tk.LEFT)
    source_var = tk.StringVar()
    ttk.Combobox(row1, textvariable=source_var, values=nodes_list,
                 state="readonly", width=15).pack(side=tk.LEFT, padx=10)
    
    # Destination
    row2 = tk.Frame(frame, bg=COLORS["card"])
    row2.pack(fill=tk.X, padx=15, pady=10)
    tk.Label(row2, text="To:", font=("Segoe UI", 11), bg=COLORS["card"],
             fg=COLORS["text"], width=10, anchor="w").pack(side=tk.LEFT)
    dest_var = tk.StringVar()
    ttk.Combobox(row2, textvariable=dest_var, values=nodes_list,
                 state="readonly", width=15).pack(side=tk.LEFT, padx=10)
    
    # Weight
    row3 = tk.Frame(frame, bg=COLORS["card"])
    row3.pack(fill=tk.X, padx=15, pady=10)
    tk.Label(row3, text="Weight:", font=("Segoe UI", 11), bg=COLORS["card"],
             fg=COLORS["text"], width=10, anchor="w").pack(side=tk.LEFT)
    weight_var = tk.StringVar(value="1")
    ttk.Entry(row3, textvariable=weight_var, width=10).pack(side=tk.LEFT, padx=10)
    
    def add():
        try:
            s, d = source_var.get(), dest_var.get()
            if not s or not d:
                messagebox.showerror("Error", "Please select both nodes")
                return
            w = float(weight_var.get())
            if w <= 0:
                messagebox.showerror("Error", "Weight must be positive")
                return
            if s == d:
                messagebox.showerror("Error", "Cannot add self-loop")
                return
            G.add_edge(s, d, weight=w)
            draw_graph(title=f"Added Edge: {s}↔{d}")
            draw_statistics()
            draw_adjacency_matrix()
            log_message(f"Added edge: {s}↔{d} (weight={w})", "success")
            update_status(f"Added edge: {s}↔{d}", "success")
            edge_window.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid weight")
    
    tk.Button(edge_window, text="Add Edge", command=add,
              bg=COLORS["accent"], fg="white", font=("Segoe UI", 11, "bold"),
              relief="flat", padx=25, pady=10).pack(pady=20)

def mark_vulnerable():
    if G.number_of_edges() == 0:
        messagebox.showwarning("Warning", "No edges to mark")
        return
    
    vuln_window = tk.Toplevel(root)
    vuln_window.title("⚠️ Mark Vulnerable Road")
    vuln_window.geometry("400x300")
    vuln_window.configure(bg=COLORS["bg"])
    vuln_window.transient(root)
    vuln_window.grab_set()
    
    tk.Label(vuln_window, text="⚠️ Mark Vulnerable Road", font=("Segoe UI", 14, "bold"),
             bg=COLORS["bg"], fg=COLORS["accent"]).pack(pady=20)
    
    frame = tk.Frame(vuln_window, bg=COLORS["card"])
    frame.pack(fill=tk.X, padx=25, pady=10)
    
    edges_list = [f"{u}↔{v}" for u, v in G.edges()]
    
    tk.Label(frame, text="Select Edge:", font=("Segoe UI", 11),
             bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", padx=15, pady=(15, 5))
    
    edge_var = tk.StringVar(value=edges_list[0] if edges_list else "")
    edge_combo = ttk.Combobox(frame, textvariable=edge_var, values=edges_list,
                               state="readonly", width=20)
    edge_combo.pack(padx=15, pady=10)
    
    def mark():
        edge_str = edge_var.get()
        if not edge_str:
            return
        u, v = edge_str.split("↔")
        if G.has_edge(u, v):
            vulnerable_roads.add((u, v))
            draw_graph(title="Road Marked as Vulnerable")
            log_message(f"Marked vulnerable: {u}↔{v}", "warning")
            update_status(f"Marked {u}↔{v} as vulnerable", "warning")
            vuln_window.destroy()
    
    tk.Button(vuln_window, text="Mark Vulnerable", command=mark,
              bg=COLORS["warning"], fg=COLORS["bg"], font=("Segoe UI", 11, "bold"),
              relief="flat", padx=20, pady=10).pack(pady=20)

def reset_graph():
    global G, pos
    G = original_graph.copy()
    pos = nx.spring_layout(G, seed=42, k=2)
    vulnerable_roads.clear()
    failed_nodes.clear()
    draw_graph(title="Network Graph (Reset)")
    draw_statistics()
    draw_adjacency_matrix()
    clear_log()
    log_message("Graph reset to original state", "success")
    update_status("Graph reset to original state", "success")
    update_results(result="--")
    update_progress(0)

# --------------------------------
# Control Panel Buttons
# --------------------------------
def create_section(parent, title, icon):
    frame = tk.LabelFrame(parent, text=f"{icon} {title}",
                          bg=COLORS["card"], fg=COLORS["accent"],
                          font=("Segoe UI", 10, "bold"))
    frame.pack(fill=tk.X, padx=10, pady=6)
    return frame

def create_button(parent, text, command, style="normal"):
    colors = {
        "normal": (COLORS["surface"], COLORS["text"]),
        "accent": (COLORS["accent"], "white"),
        "danger": (COLORS["error"], "white"),
        "warning": (COLORS["warning"], COLORS["bg"]),
        "success": (COLORS["success"], COLORS["bg"])
    }
    bg, fg = colors.get(style, colors["normal"])
    
    btn = tk.Button(parent, text=text, command=command,
                    bg=bg, fg=fg, font=("Segoe UI", 10),
                    relief="flat", padx=12, pady=8, cursor="hand2",
                    activebackground=COLORS["surface2"])
    btn.pack(fill=tk.X, padx=8, pady=4)
    return btn

# Q1: MST
q1_frame = create_section(control_inner, "Q1: MST Visualization", "🌲")
create_button(q1_frame, "🌲 Animated MST (Kruskal's)", show_mst_animated, "accent")

# Q2: Paths
q2_frame = create_section(control_inner, "Q2: Reliable Paths", "🛤️")
create_button(q2_frame, "🛤️ Find K-Shortest Paths", find_reliable_paths, "accent")

# Q3: Hierarchy
q3_frame = create_section(control_inner, "Q3: Command Hierarchy", "🌳")
create_button(q3_frame, "🌳 View & Optimize Tree", show_command_tree, "normal")

# Q4: Failure
q4_frame = create_section(control_inner, "Q4: Failure Simulation", "💥")
create_button(q4_frame, "💥 Simulate Network Failure", simulate_failure, "danger")

# Bonus: Coloring
bonus_frame = create_section(control_inner, "Bonus: Graph Coloring", "🎨")
create_button(bonus_frame, "🎨 Assign Frequencies", color_graph_animated, "success")

# Graph Editing
edit_frame = create_section(control_inner, "Graph Operations", "✏️")
create_button(edit_frame, "➕ Add Node", add_node)
create_button(edit_frame, "🔗 Add Edge", add_edge)
create_button(edit_frame, "⚠️ Mark Vulnerable", mark_vulnerable, "warning")
create_button(edit_frame, "🔄 Reset Graph", reset_graph)

# View controls
view_frame = create_section(control_inner, "Views", "👁️")
create_button(view_frame, "📊 Update Statistics", lambda: [draw_statistics(), draw_adjacency_matrix()])
create_button(view_frame, "🔢 Show Matrix", lambda: viz_notebook.select(2))

# Algorithm reference
algo_ref = create_section(control_inner, "Algorithm Reference", "📚")

algorithms_info = [
    ("Kruskal's MST", "O(E log E)", COLORS["success"]),
    ("Dijkstra", "O(V² or E+V log V)", COLORS["accent"]),
    ("Yen's K-Paths", "O(KV(E+V log V))", COLORS["lavender"]),
    ("Tree Traversals", "O(n)", COLORS["teal"]),
    ("Graph Coloring", "O(V + E)", COLORS["peach"])
]

for name, complexity, color in algorithms_info:
    row = tk.Frame(algo_ref, bg=COLORS["card"])
    row.pack(fill=tk.X, padx=8, pady=2)
    
    tk.Label(row, text=f"• {name}", font=("Segoe UI", 9),
             bg=COLORS["card"], fg=color, anchor="w").pack(side=tk.LEFT)
    tk.Label(row, text=complexity, font=("Consolas", 8),
             bg=COLORS["card"], fg=COLORS["subtext"]).pack(side=tk.RIGHT)

# --------------------------------
# Initialize
# --------------------------------
def initialize():
    draw_graph()
    draw_statistics()
    draw_adjacency_matrix()
    log_message("═══ SYSTEM INITIALIZED ═══", "title")
    log_message("Emergency Network Management System v2.0\n", "info")
    log_message("Available operations:", "info")
    log_message("  • Q1: MST visualization with Kruskal's", "step")
    log_message("  • Q2: K-shortest reliable paths", "step")
    log_message("  • Q3: Command hierarchy optimization", "step")
    log_message("  • Q4: Network failure simulation", "step")
    log_message("  • Bonus: Graph coloring for frequency assignment\n", "step")
    log_message("Select an operation from the Control Center.", "success")

root.after(200, initialize)

# --------------------------------
# Run Application
# --------------------------------
root.mainloop()