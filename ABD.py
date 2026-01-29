
"""
Graph Search Algorithms: DFS, BFS, and A* with Real-Time Animation
===================================================================
Problem: Robot parcel delivery between Polish cities
Start: Glogow (Blue node)
Goal: Plock (Red node)

Features:
- Real-time step-by-step animation
- Interactive visualization
- Live open/closed container updates
- Animated robot movement along final path
- Performance metrics and charts
- PDF report generation

"""

from collections import deque
import heapq
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import time
import numpy as np
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════
# 1. STATE SPACE REPRESENTATION (5 Marks)
# ═══════════════════════════════════════════════════════════════════
"""
STATE SPACE DEFINITION:
-----------------------
• States: Each city in Poland represents a state
• Initial State: Glogow
• Goal State: Plock
• Actions: Move from one city to an adjacent connected city
• Transition Model: Moving along a road changes state to neighbor city
• Path Cost: Sum of distances (km) along the path
• State Space Size: 17 cities (nodes), 21 roads (edges)
"""

# GRAPH FROM DIAGRAM - State Space (Adjacency List)
graph = {
    "Glogow": {"Leszno": 45, "Wroclaw": 140},
    "Leszno": {"Glogow": 45, "Poznan": 90, "Kalisz": 130},
    "Poznan": {"Leszno": 90, "Bydgoszcz": 140, "Konin": 120},
    "Bydgoszcz": {"Poznan": 140, "Wloclawek": 110},
    "Wloclawek": {"Bydgoszcz": 110, "Plock": 55},
    "Konin": {"Poznan": 120, "Lodz": 120},
    "Kalisz": {"Leszno": 130, "Lodz": 120, "Czestochowa": 160},
    "Lodz": {"Konin": 120, "Kalisz": 120, "Warsaw": 150, "Radom": 165, "Krakow": 280},
    "Warsaw": {"Lodz": 150, "Plock": 130, "Radom": 105},
    "Radom": {"Warsaw": 105, "Kielce": 82, "Lodz": 165},
    "Kielce": {"Radom": 82, "Krakow": 120},
    "Krakow": {"Kielce": 120, "Katowice": 85, "Lodz": 280},
    "Katowice": {"Krakow": 85, "Czestochowa": 80, "Opole": 118},
    "Czestochowa": {"Kalisz": 160, "Katowice": 80},
    "Opole": {"Wroclaw": 100, "Katowice": 118},
    "Wroclaw": {"Glogow": 140, "Opole": 100},
    "Plock": {"Wloclawek": 55, "Warsaw": 130}
}

# ═══════════════════════════════════════════════════════════════════
# 2. HEURISTIC FUNCTION DESIGN (10 Marks)
# ═══════════════════════════════════════════════════════════════════
"""
HEURISTIC FUNCTION: h(n) = Straight-line distance to Plock
-----------------------------------------------------------
Design Rationale:
1. ADMISSIBILITY: The straight-line distance never overestimates the actual
   road distance because the shortest path between two points is a straight line.
   
2. CONSISTENCY: For any edge (n, n') with cost c(n,n'):
   h(n) ≤ c(n,n') + h(n')
   
3. h(Plock) = 0 (goal state)
"""

heuristic = {
    "Glogow": 280, "Leszno": 250, "Poznan": 200, "Bydgoszcz": 100,
    "Wloclawek": 55, "Konin": 150, "Kalisz": 220, "Lodz": 130,
    "Warsaw": 100, "Radom": 180, "Kielce": 250, "Krakow": 320,
    "Katowice": 350, "Czestochowa": 280, "Opole": 320, "Wroclaw": 300,
    "Plock": 0
}

# Approximate geographical positions for visualization
city_positions = {
    "Glogow": (1.5, 5.5), "Leszno": (2.5, 5.0), "Wroclaw": (2.0, 4.0),
    "Poznan": (3.0, 6.0), "Bydgoszcz": (4.5, 7.0), "Wloclawek": (5.5, 6.5),
    "Plock": (6.0, 6.0), "Konin": (4.0, 5.0), "Kalisz": (3.5, 4.0),
    "Lodz": (5.0, 4.0), "Warsaw": (7.0, 5.0), "Radom": (7.0, 3.5),
    "Kielce": (6.5, 2.5), "Krakow": (5.5, 1.5), "Katowice": (4.5, 1.5),
    "Czestochowa": (4.0, 2.5), "Opole": (3.0, 2.5)
}

start = "Glogow"
goal = "Plock"

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════
def create_networkx_graph(graph):
    """Create NetworkX graph from adjacency list"""
    G = nx.Graph()
    for node in graph:
        for neighbor, weight in graph[node].items():
            G.add_edge(node, neighbor, weight=weight)
    return G

# ═══════════════════════════════════════════════════════════════════
# PERFORMANCE METRICS CLASS
# ═══════════════════════════════════════════════════════════════════
class PerformanceMetrics:
    """Track and analyze algorithm performance"""
    
    def __init__(self):
        self.metrics = {}
    
    def record(self, algorithm, path, cost, nodes_expanded, steps, execution_time, trace):
        """Record metrics for an algorithm"""
        self.metrics[algorithm] = {
            'path': path,
            'cost': cost,
            'path_length': len(path),
            'nodes_expanded': nodes_expanded,
            'steps': steps,
            'execution_time': execution_time,
            'trace': trace,
            'max_open_size': max(len(t.get('open', [])) for t in trace),
            'max_closed_size': max(len(t.get('closed', set())) for t in trace)
        }
    
    def get_comparison_data(self):
        """Get data for comparison charts"""
        return self.metrics
    
    def print_summary(self):
        """Print performance summary"""
        print("\n" + "═"*90)
        print("📊 PERFORMANCE METRICS SUMMARY")
        print("═"*90)
        
        headers = ['Metric', 'DFS', 'BFS', 'A*']
        rows = [
            ['Path Cost (km)', 
             self.metrics.get('dfs', {}).get('cost', 'N/A'),
             self.metrics.get('bfs', {}).get('cost', 'N/A'),
             self.metrics.get('astar', {}).get('cost', 'N/A')],
            ['Path Length (nodes)',
             self.metrics.get('dfs', {}).get('path_length', 'N/A'),
             self.metrics.get('bfs', {}).get('path_length', 'N/A'),
             self.metrics.get('astar', {}).get('path_length', 'N/A')],
            ['Nodes Expanded',
             self.metrics.get('dfs', {}).get('nodes_expanded', 'N/A'),
             self.metrics.get('bfs', {}).get('nodes_expanded', 'N/A'),
             self.metrics.get('astar', {}).get('nodes_expanded', 'N/A')],
            ['Total Steps',
             self.metrics.get('dfs', {}).get('steps', 'N/A'),
             self.metrics.get('bfs', {}).get('steps', 'N/A'),
             self.metrics.get('astar', {}).get('steps', 'N/A')],
            ['Max Open Size',
             self.metrics.get('dfs', {}).get('max_open_size', 'N/A'),
             self.metrics.get('bfs', {}).get('max_open_size', 'N/A'),
             self.metrics.get('astar', {}).get('max_open_size', 'N/A')],
            ['Execution Time (ms)',
             f"{self.metrics.get('dfs', {}).get('execution_time', 0)*1000:.2f}",
             f"{self.metrics.get('bfs', {}).get('execution_time', 0)*1000:.2f}",
             f"{self.metrics.get('astar', {}).get('execution_time', 0)*1000:.2f}"],
        ]
        
        # Print table
        col_widths = [25, 15, 15, 15]
        print("┌" + "─"*25 + "┬" + "─"*15 + "┬" + "─"*15 + "┬" + "─"*15 + "┐")
        print(f"│ {headers[0]:<23} │ {headers[1]:<13} │ {headers[2]:<13} │ {headers[3]:<13} │")
        print("├" + "─"*25 + "┼" + "─"*15 + "┼" + "─"*15 + "┼" + "─"*15 + "┤")
        
        for row in rows:
            print(f"│ {str(row[0]):<23} │ {str(row[1]):<13} │ {str(row[2]):<13} │ {str(row[3]):<13} │")
        
        print("└" + "─"*25 + "┴" + "─"*15 + "┴" + "─"*15 + "┴" + "─"*15 + "┘")

# ═══════════════════════════════════════════════════════════════════
# ALGORITHMS WITH TIMING AND METRICS
# ═══════════════════════════════════════════════════════════════════
def dfs_collect_trace(graph, start, goal):
    """DFS with full trace collection for animation"""
    start_time = time.time()
    
    open_list = [(start, [start], 0)]
    closed_set = set()
    trace = []
    nodes_expanded = 0
    
    trace.append({
        'step': 0, 'current': None, 'path': [], 'cost': 0,
        'open': [start], 'closed': set(), 'action': 'Initialize',
        'message': f'Starting DFS from {start} to {goal}'
    })
    
    step = 0
    while open_list:
        step += 1
        current_node, path, cost = open_list.pop()
        
        trace.append({
            'step': step, 'current': current_node, 'path': path.copy(),
            'cost': cost, 'open': [n[0] for n in open_list],
            'closed': closed_set.copy(), 'action': 'Pop from Stack',
            'message': f'Popped {current_node} from OPEN stack'
        })
        
        if current_node == goal:
            execution_time = time.time() - start_time
            trace.append({
                'step': step + 0.5, 'current': current_node, 'path': path.copy(),
                'cost': cost, 'open': [n[0] for n in open_list],
                'closed': closed_set.copy(), 'action': 'GOAL FOUND!',
                'message': f'🎯 Goal {goal} reached! Cost: {cost}km'
            })
            return path, cost, nodes_expanded, step, execution_time, trace
        
        if current_node in closed_set:
            continue
        
        closed_set.add(current_node)
        nodes_expanded += 1
        
        neighbors_added = []
        for neighbor, weight in reversed(list(graph[current_node].items())):
            if neighbor not in closed_set:
                open_list.append((neighbor, path + [neighbor], cost + weight))
                neighbors_added.append(neighbor)
        
        if neighbors_added:
            trace.append({
                'step': step + 0.5, 'current': current_node, 'path': path.copy(),
                'cost': cost, 'open': [n[0] for n in open_list],
                'closed': closed_set.copy(), 'action': 'Expand',
                'message': f'Added {neighbors_added} to OPEN'
            })
    
    execution_time = time.time() - start_time
    return None, None, nodes_expanded, step, execution_time, trace

def bfs_collect_trace(graph, start, goal):
    """BFS with full trace collection for animation"""
    start_time = time.time()
    
    open_queue = deque([(start, [start], 0)])
    closed_set = set()
    trace = []
    nodes_expanded = 0
    
    trace.append({
        'step': 0, 'current': None, 'path': [], 'cost': 0,
        'open': [start], 'closed': set(), 'action': 'Initialize',
        'message': f'Starting BFS from {start} to {goal}'
    })
    
    step = 0
    while open_queue:
        step += 1
        current_node, path, cost = open_queue.popleft()
        
        trace.append({
            'step': step, 'current': current_node, 'path': path.copy(),
            'cost': cost, 'open': [n[0] for n in open_queue],
            'closed': closed_set.copy(), 'action': 'Dequeue',
            'message': f'Dequeued {current_node} from OPEN queue'
        })
        
        if current_node == goal:
            execution_time = time.time() - start_time
            trace.append({
                'step': step + 0.5, 'current': current_node, 'path': path.copy(),
                'cost': cost, 'open': [n[0] for n in open_queue],
                'closed': closed_set.copy(), 'action': 'GOAL FOUND!',
                'message': f'🎯 Goal {goal} reached! Cost: {cost}km'
            })
            return path, cost, nodes_expanded, step, execution_time, trace
        
        if current_node in closed_set:
            continue
        
        closed_set.add(current_node)
        nodes_expanded += 1
        
        neighbors_added = []
        for neighbor, weight in sorted(graph[current_node].items()):
            if neighbor not in closed_set:
                open_queue.append((neighbor, path + [neighbor], cost + weight))
                neighbors_added.append(neighbor)
        
        if neighbors_added:
            trace.append({
                'step': step + 0.5, 'current': current_node, 'path': path.copy(),
                'cost': cost, 'open': [n[0] for n in open_queue],
                'closed': closed_set.copy(), 'action': 'Expand',
                'message': f'Added {neighbors_added} to OPEN'
            })
    
    execution_time = time.time() - start_time
    return None, None, nodes_expanded, step, execution_time, trace

def astar_collect_trace(graph, start, goal, heuristic):
    """A* with full trace collection for animation"""
    start_time = time.time()
    
    open_pq = [(heuristic[start], 0, start, [start])]
    closed_set = set()
    trace = []
    nodes_expanded = 0
    
    trace.append({
        'step': 0, 'current': None, 'path': [], 'cost': 0, 'f': heuristic[start],
        'open': [(heuristic[start], start)], 'closed': set(), 'action': 'Initialize',
        'message': f'Starting A* from {start} to {goal}'
    })
    
    step = 0
    while open_pq:
        step += 1
        f_score, g_score, current_node, path = heapq.heappop(open_pq)
        
        trace.append({
            'step': step, 'current': current_node, 'path': path.copy(),
            'cost': g_score, 'f': f_score,
            'open': [(f, n) for f, g, n, p in open_pq],
            'closed': closed_set.copy(), 'action': 'Pop min f(n)',
            'message': f'Popped {current_node} with f={f_score} (g={g_score}+h={heuristic[current_node]})'
        })
        
        if current_node == goal:
            execution_time = time.time() - start_time
            trace.append({
                'step': step + 0.5, 'current': current_node, 'path': path.copy(),
                'cost': g_score, 'f': f_score,
                'open': [(f, n) for f, g, n, p in open_pq],
                'closed': closed_set.copy(), 'action': 'OPTIMAL GOAL!',
                'message': f'🎯 Optimal path found! Cost: {g_score}km'
            })
            return path, g_score, nodes_expanded, step, execution_time, trace
        
        if current_node in closed_set:
            continue
        
        closed_set.add(current_node)
        nodes_expanded += 1
        
        neighbors_added = []
        for neighbor, weight in sorted(graph[current_node].items()):
            if neighbor not in closed_set:
                new_g = g_score + weight
                new_f = new_g + heuristic[neighbor]
                heapq.heappush(open_pq, (new_f, new_g, neighbor, path + [neighbor]))
                neighbors_added.append(f"{neighbor}(f={new_f})")
        
        if neighbors_added:
            trace.append({
                'step': step + 0.5, 'current': current_node, 'path': path.copy(),
                'cost': g_score, 'f': f_score,
                'open': [(f, n) for f, g, n, p in open_pq],
                'closed': closed_set.copy(), 'action': 'Expand',
                'message': f'Added {len(neighbors_added)} neighbors to OPEN'
            })
    
    execution_time = time.time() - start_time
    return None, None, nodes_expanded, step, execution_time, trace

# ═══════════════════════════════════════════════════════════════════
# ROBOT PATH ANIMATION CLASS
# ═══════════════════════════════════════════════════════════════════
class RobotPathAnimator:
    """Animate robot moving along the final path"""
    
    def __init__(self, graph, positions, path, algorithm_name):
        self.graph = graph
        self.positions = positions
        self.path = path
        self.algorithm_name = algorithm_name
        self.G = create_networkx_graph(graph)
        
    def animate(self, interval=500):
        """Animate robot moving along path"""
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # Create interpolated positions for smooth movement
        self.interpolated_positions = []
        for i in range(len(self.path) - 1):
            start_pos = np.array(self.positions[self.path[i]])
            end_pos = np.array(self.positions[self.path[i + 1]])
            # Add 10 intermediate positions
            for t in np.linspace(0, 1, 10):
                pos = start_pos + t * (end_pos - start_pos)
                self.interpolated_positions.append({
                    'pos': pos,
                    'from': self.path[i],
                    'to': self.path[i + 1],
                    'progress': t
                })
        
        self.fig = fig
        self.ax = ax
        
        anim = FuncAnimation(
            fig, self._update_robot_frame, 
            frames=len(self.interpolated_positions),
            interval=interval, repeat=True, blit=False
        )
        
        plt.tight_layout()
        plt.show()
        
    def _update_robot_frame(self, frame_idx):
        """Update robot position frame"""
        self.ax.clear()
        pos = self.positions
        
        # Draw base graph
        node_colors = []
        for node in self.G.nodes():
            if node == self.path[0]:
                node_colors.append('#3498db')  # Start
            elif node == self.path[-1]:
                node_colors.append('#e74c3c')  # Goal
            elif node in self.path:
                node_colors.append('#2ecc71')  # Path
            else:
                node_colors.append('#bdc3c7')  # Other
        
        nx.draw_networkx_edges(self.G, pos, edge_color='#bdc3c7', width=2, ax=self.ax)
        
        # Draw path edges
        path_edges = list(zip(self.path, self.path[1:]))
        nx.draw_networkx_edges(self.G, pos, edgelist=path_edges,
                               edge_color='#27ae60', width=4, ax=self.ax)
        
        nx.draw_networkx_nodes(self.G, pos, node_color=node_colors, node_size=1800,
                               edgecolors='#2c3e50', linewidths=2, ax=self.ax)
        nx.draw_networkx_labels(self.G, pos, font_size=7, font_weight='bold', ax=self.ax)
        
        edge_labels = nx.get_edge_attributes(self.G, 'weight')
        nx.draw_networkx_edge_labels(self.G, pos, edge_labels=edge_labels, font_size=6, ax=self.ax)
        
        # Draw robot at current position
        robot_pos = self.interpolated_positions[frame_idx]['pos']
        self.ax.plot(robot_pos[0], robot_pos[1], 'ko', markersize=25, 
                    markerfacecolor='#e67e22', markeredgewidth=3)
        self.ax.plot(robot_pos[0], robot_pos[1], 'w*', markersize=12)
        
        # Draw trail
        if frame_idx > 0:
            trail_x = [self.interpolated_positions[i]['pos'][0] for i in range(frame_idx)]
            trail_y = [self.interpolated_positions[i]['pos'][1] for i in range(frame_idx)]
            self.ax.plot(trail_x, trail_y, 'o-', color='#e67e22', alpha=0.3, 
                        markersize=5, linewidth=2)
        
        current_data = self.interpolated_positions[frame_idx]
        self.ax.set_title(f"🤖 Robot Delivery Animation - {self.algorithm_name}\n"
                         f"Moving: {current_data['from']} → {current_data['to']} "
                         f"({int(current_data['progress']*100)}%)",
                         fontsize=14, fontweight='bold')
        self.ax.axis('off')
        
        # Legend
        legend_elements = [
            mpatches.Patch(color='#3498db', label=f'Start: {self.path[0]}'),
            mpatches.Patch(color='#e74c3c', label=f'Goal: {self.path[-1]}'),
            mpatches.Patch(color='#e67e22', label='Robot'),
        ]
        self.ax.legend(handles=legend_elements, loc='upper left', fontsize=9)

# ═══════════════════════════════════════════════════════════════════
# ENHANCED VISUALIZATION WITH CHARTS
# ═══════════════════════════════════════════════════════════════════
class PerformanceCharts:
    """Generate performance comparison charts"""
    
    def __init__(self, metrics):
        self.metrics = metrics
    
    def plot_all_charts(self):
        """Generate all comparison charts"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle('Algorithm Performance Analysis', fontsize=16, fontweight='bold')
        
        algorithms = ['dfs', 'bfs', 'astar']
        colors = ['#e74c3c', '#3498db', '#2ecc71']
        labels = ['DFS', 'BFS', 'A*']
        
        # 1. Path Cost Comparison
        ax = axes[0, 0]
        costs = [self.metrics.get(a, {}).get('cost', 0) for a in algorithms]
        bars = ax.bar(labels, costs, color=colors, edgecolor='black', linewidth=2)
        ax.set_ylabel('Cost (km)')
        ax.set_title('Path Cost Comparison')
        ax.bar_label(bars, fmt='%d km')
        
        # Highlight optimal
        min_cost = min(costs)
        for bar, cost in zip(bars, costs):
            if cost == min_cost:
                bar.set_edgecolor('gold')
                bar.set_linewidth(4)
        
        # 2. Nodes Expanded
        ax = axes[0, 1]
        expanded = [self.metrics.get(a, {}).get('nodes_expanded', 0) for a in algorithms]
        bars = ax.bar(labels, expanded, color=colors, edgecolor='black', linewidth=2)
        ax.set_ylabel('Nodes Expanded')
        ax.set_title('Nodes Expanded')
        ax.bar_label(bars)
        
        # 3. Path Length
        ax = axes[0, 2]
        lengths = [self.metrics.get(a, {}).get('path_length', 0) for a in algorithms]
        bars = ax.bar(labels, lengths, color=colors, edgecolor='black', linewidth=2)
        ax.set_ylabel('Path Length (nodes)')
        ax.set_title('Path Length')
        ax.bar_label(bars)
        
        # 4. Execution Time
        ax = axes[1, 0]
        times = [self.metrics.get(a, {}).get('execution_time', 0) * 1000 for a in algorithms]
        bars = ax.bar(labels, times, color=colors, edgecolor='black', linewidth=2)
        ax.set_ylabel('Time (ms)')
        ax.set_title('Execution Time')
        ax.bar_label(bars, fmt='%.2f ms')
        
        # 5. Memory Usage (Max Open Size)
        ax = axes[1, 1]
        open_sizes = [self.metrics.get(a, {}).get('max_open_size', 0) for a in algorithms]
        bars = ax.bar(labels, open_sizes, color=colors, edgecolor='black', linewidth=2)
        ax.set_ylabel('Max Open Size')
        ax.set_title('Memory Usage (Max Open)')
        ax.bar_label(bars)
        
        # 6. Radar Chart - Overall Comparison
        ax = axes[1, 2]
        ax.axis('off')
        
        # Create summary table instead
        summary_text = "OVERALL RANKING\n" + "═"*30 + "\n\n"
        
        # Calculate scores
        scores = {}
        for algo in algorithms:
            m = self.metrics.get(algo, {})
            # Lower is better for all metrics
            score = 0
            if m.get('cost') == min(costs): score += 3
            if m.get('nodes_expanded') == min(expanded): score += 2
            if m.get('path_length') == min(lengths): score += 1
            scores[algo] = score
        
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for i, (algo, score) in enumerate(ranked):
            medal = ['🥇', '🥈', '🥉'][i]
            summary_text += f"{medal} {algo.upper()}: {score} points\n"
        
        summary_text += "\n" + "═"*30 + "\n"
        summary_text += "✅ A* is OPTIMAL for weighted graphs"
        
        ax.text(0.5, 0.5, summary_text, transform=ax.transAxes,
               fontsize=12, ha='center', va='center', fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig('performance_charts.png', dpi=150, bbox_inches='tight')
        plt.show()

# ═══════════════════════════════════════════════════════════════════
# REAL-TIME ANIMATED VISUALIZATION CLASS
# ═══════════════════════════════════════════════════════════════════
class RealTimeSearchVisualizer:
    """Real-time animated visualization of search algorithms"""
    
    def __init__(self, graph, start, goal, heuristic, positions):
        self.graph = graph
        self.start = start
        self.goal = goal
        self.heuristic = heuristic
        self.positions = positions
        self.G = create_networkx_graph(graph)
        
    def animate_search(self, algorithm='astar', interval=800, save_gif=False):
        """Animate the search algorithm in real-time"""
        # Collect trace
        if algorithm == 'dfs':
            path, cost, nodes_exp, steps, exec_time, trace = dfs_collect_trace(
                self.graph, self.start, self.goal)
            title = "Depth-First Search (DFS) - Real-Time"
            container_name = "OPEN (Stack - LIFO)"
        elif algorithm == 'bfs':
            path, cost, nodes_exp, steps, exec_time, trace = bfs_collect_trace(
                self.graph, self.start, self.goal)
            title = "Breadth-First Search (BFS) - Real-Time"
            container_name = "OPEN (Queue - FIFO)"
        else:
            path, cost, nodes_exp, steps, exec_time, trace = astar_collect_trace(
                self.graph, self.start, self.goal, self.heuristic)
            title = "A* Search - Real-Time"
            container_name = "OPEN (Priority Queue)"
        
        # Setup figure
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 4, height_ratios=[4, 1, 1], hspace=0.3, wspace=0.3)
        
        ax_graph = fig.add_subplot(gs[0, :3])
        ax_info = fig.add_subplot(gs[0, 3])
        ax_info.axis('off')
        ax_open = fig.add_subplot(gs[1, :2])
        ax_closed = fig.add_subplot(gs[1, 2:])
        ax_path = fig.add_subplot(gs[2, :])
        
        self.fig = fig
        self.ax_graph = ax_graph
        self.ax_info = ax_info
        self.ax_open = ax_open
        self.ax_closed = ax_closed
        self.ax_path = ax_path
        self.trace = trace
        self.final_path = path
        self.final_cost = cost
        self.title = title
        self.container_name = container_name
        self.algorithm = algorithm
        
        anim = FuncAnimation(
            fig, self._update_frame, frames=len(trace),
            interval=interval, repeat=False, blit=False
        )
        
        plt.tight_layout()
        
        if save_gif:
            print(f"Saving {algorithm}_animation.gif...")
            anim.save(f'{algorithm}_animation.gif', writer='pillow', fps=1000//interval)
            print("Saved!")
        
        plt.show()
        
        return path, cost, nodes_exp, steps, exec_time, trace
    
    def _update_frame(self, frame_idx):
        """Update a single frame of animation"""
        state = self.trace[frame_idx]
        
        self.ax_graph.clear()
        self.ax_info.clear()
        self.ax_open.clear()
        self.ax_closed.clear()
        self.ax_path.clear()
        
        pos = self.positions
        
        # Node colors
        node_colors = []
        node_sizes = []
        for node in self.G.nodes():
            if node == state.get('current'):
                node_colors.append('#f39c12')
                node_sizes.append(2500)
            elif node == self.start:
                node_colors.append('#3498db')
                node_sizes.append(2200)
            elif node == self.goal:
                node_colors.append('#e74c3c')
                node_sizes.append(2200)
            elif node in state.get('closed', set()):
                node_colors.append('#9b59b6')
                node_sizes.append(1800)
            elif node in state.get('path', []):
                node_colors.append('#2ecc71')
                node_sizes.append(2000)
            elif node in [n if isinstance(n, str) else n[1] for n in state.get('open', [])]:
                node_colors.append('#f1c40f')
                node_sizes.append(1800)
            else:
                node_colors.append('#bdc3c7')
                node_sizes.append(1500)
        
        nx.draw_networkx_edges(self.G, pos, edge_color='#bdc3c7', width=2, 
                               alpha=0.5, ax=self.ax_graph)
        
        if len(state.get('path', [])) > 1:
            path_edges = list(zip(state['path'], state['path'][1:]))
            nx.draw_networkx_edges(self.G, pos, edgelist=path_edges,
                                   edge_color='#27ae60', width=4, ax=self.ax_graph)
        
        nx.draw_networkx_nodes(self.G, pos, node_color=node_colors, 
                               node_size=node_sizes, edgecolors='#2c3e50',
                               linewidths=2, ax=self.ax_graph)
        
        nx.draw_networkx_labels(self.G, pos, font_size=7, font_weight='bold',
                                ax=self.ax_graph)
        
        edge_labels = nx.get_edge_attributes(self.G, 'weight')
        nx.draw_networkx_edge_labels(self.G, pos, edge_labels=edge_labels,
                                     font_size=6, ax=self.ax_graph)
        
        # Robot icon
        if state.get('current'):
            curr_pos = pos[state['current']]
            self.ax_graph.plot(curr_pos[0], curr_pos[1], 'k*', markersize=20, 
                              markeredgecolor='white', markeredgewidth=2)
        
        self.ax_graph.set_title(f"{self.title}\nStep {int(state['step'])}: {state.get('action', '')}",
                                fontsize=14, fontweight='bold')
        self.ax_graph.axis('off')
        
        # Info Panel
        self.ax_info.axis('off')
        info_text = f"""
ALGORITHM INFO
══════════════════
Algorithm: {self.algorithm.upper()}
Start: {self.start}
Goal: {self.goal}

CURRENT STATE
══════════════════
Step: {int(state['step'])}
Current: {state.get('current', 'N/A')}
Cost: {state.get('cost', 0)} km
Path Len: {len(state.get('path', []))}

ACTION
══════════════════
{state.get('action', '')}

{state.get('message', '')}
"""
        self.ax_info.text(0.05, 0.95, info_text, transform=self.ax_info.transAxes,
                         fontsize=9, verticalalignment='top', fontfamily='monospace',
                         bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.8))
        
        # Open Container
        self.ax_open.axis('off')
        open_list = state.get('open', [])
        if self.algorithm == 'astar':
            open_display = [f"{n[1]}(f={n[0]})" if isinstance(n, tuple) else str(n) 
                           for n in open_list[:8]]
        else:
            open_display = open_list[:10]
        
        open_text = f"{self.container_name}\n" + "─"*40 + "\n"
        open_text += " → ".join(map(str, open_display)) if open_display else "(empty)"
        if len(open_list) > 8:
            open_text += f" ... (+{len(open_list)-8})"
        
        self.ax_open.text(0.5, 0.5, open_text, transform=self.ax_open.transAxes,
                         fontsize=10, ha='center', va='center', fontfamily='monospace',
                         bbox=dict(boxstyle='round', facecolor='#f1c40f', alpha=0.3))
        self.ax_open.set_title("OPEN Container", fontsize=10, fontweight='bold')
        
        # Closed Container
        self.ax_closed.axis('off')
        closed_set = state.get('closed', set())
        closed_text = "CLOSED (Set)\n" + "─"*40 + "\n"
        closed_text += ", ".join(sorted(list(closed_set)[:12])) if closed_set else "(empty)"
        if len(closed_set) > 12:
            closed_text += f" ... (+{len(closed_set)-12})"
        
        self.ax_closed.text(0.5, 0.5, closed_text, transform=self.ax_closed.transAxes,
                           fontsize=10, ha='center', va='center', fontfamily='monospace',
                           bbox=dict(boxstyle='round', facecolor='#9b59b6', alpha=0.3))
        self.ax_closed.set_title("CLOSED Container", fontsize=10, fontweight='bold')
        
        # Path
        self.ax_path.axis('off')
        current_path = state.get('path', [])
        path_text = "PATH: " + (" → ".join(current_path) if current_path else "(empty)")
        path_text += f"  |  Cost: {state.get('cost', 0)} km"
        
        color = '#27ae60' if 'GOAL' in state.get('action', '') else '#3498db'
        self.ax_path.text(0.5, 0.5, path_text, transform=self.ax_path.transAxes,
                         fontsize=12, ha='center', va='center', fontweight='bold',
                         bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))
        
        # Legend
        legend_elements = [
            mpatches.Patch(color='#3498db', label='Start'),
            mpatches.Patch(color='#e74c3c', label='Goal'),
            mpatches.Patch(color='#f39c12', label='Current'),
            mpatches.Patch(color='#f1c40f', label='Open'),
            mpatches.Patch(color='#9b59b6', label='Closed'),
            mpatches.Patch(color='#2ecc71', label='Path'),
        ]
        self.ax_graph.legend(handles=legend_elements, loc='upper left', fontsize=8, ncol=3)

# ═══════════════════════════════════════════════════════════════════
# STATIC COMPARISON
# ═══════════════════════════════════════════════════════════════════
def draw_comparison_static(graph, positions, start, goal, heuristic):
    """Draw static comparison"""
    dfs_result = dfs_collect_trace(graph, start, goal)
    bfs_result = bfs_collect_trace(graph, start, goal)
    astar_result = astar_collect_trace(graph, start, goal, heuristic)
    
    fig, axes = plt.subplots(1, 3, figsize=(20, 7))
    fig.suptitle('Algorithm Comparison: Glogow → Plock', fontsize=16, fontweight='bold')
    
    G = create_networkx_graph(graph)
    
    results = [
        (dfs_result[0], dfs_result[1], "DFS", axes[0]),
        (bfs_result[0], bfs_result[1], "BFS", axes[1]),
        (astar_result[0], astar_result[1], "A* (Optimal)", axes[2])
    ]
    
    for path, cost, name, ax in results:
        node_colors = []
        for node in G.nodes():
            if node == start:
                node_colors.append('#3498db')
            elif node == goal:
                node_colors.append('#e74c3c')
            elif node in path:
                node_colors.append('#2ecc71')
            else:
                node_colors.append('#bdc3c7')
        
        nx.draw_networkx_edges(G, positions, edge_color='#bdc3c7', width=1.5, ax=ax)
        path_edges = list(zip(path, path[1:]))
        nx.draw_networkx_edges(G, positions, edgelist=path_edges,
                               edge_color='#27ae60', width=4, ax=ax)
        nx.draw_networkx_nodes(G, positions, node_color=node_colors,
                               node_size=1500, edgecolors='#2c3e50', linewidths=2, ax=ax)
        nx.draw_networkx_labels(G, positions, font_size=7, font_weight='bold', ax=ax)
        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, positions, edge_labels=edge_labels, font_size=6, ax=ax)
        ax.set_title(f"{name}\nPath: {len(path)} nodes | Cost: {cost} km", 
                    fontsize=11, fontweight='bold')
        ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('algorithm_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    return {
        'dfs': {'path': dfs_result[0], 'cost': dfs_result[1], 
                'nodes_expanded': dfs_result[2], 'steps': dfs_result[3],
                'execution_time': dfs_result[4], 'trace': dfs_result[5]},
        'bfs': {'path': bfs_result[0], 'cost': bfs_result[1],
                'nodes_expanded': bfs_result[2], 'steps': bfs_result[3],
                'execution_time': bfs_result[4], 'trace': bfs_result[5]},
        'astar': {'path': astar_result[0], 'cost': astar_result[1],
                  'nodes_expanded': astar_result[2], 'steps': astar_result[3],
                  'execution_time': astar_result[4], 'trace': astar_result[5]}
    }

# ═══════════════════════════════════════════════════════════════════
# PRINT DISCUSSION
# ═══════════════════════════════════════════════════════════════════
def print_discussion(results):
    """Print advantages/disadvantages discussion"""
    dfs = results['dfs']
    bfs = results['bfs']
    astar = results['astar']
    
    print("\n" + "═"*80)
    print("3. ALGORITHM COMPARISON AND DISCUSSION (5 Marks)")
    print("═"*80)
    
    print(f"""
┌────────────────────────────────────────────────────────────────────────────┐
│                           RESULTS SUMMARY                                  │
├────────────────────────────────────────────────────────────────────────────┤
│  Algorithm  │  Path Length  │  Cost (km)  │  Optimal?                     │
├────────────────────────────────────────────────────────────────────────────┤
│  DFS        │  {len(dfs['path']):<11}  │  {dfs['cost']:<10}  │  No                           │
│  BFS        │  {len(bfs['path']):<11}  │  {bfs['cost']:<10}  │  No (weighted graphs)         │
│  A*         │  {len(astar['path']):<11}  │  {astar['cost']:<10}  │  Yes ✓                        │
└────────────────────────────────────────────────────────────────────────────┘

PATHS:
  DFS:  {' → '.join(dfs['path'])}
  BFS:  {' → '.join(bfs['path'])}
  A*:   {' → '.join(astar['path'])}

═══════════════════════════════════════════════════════════════════════════════
                        ADVANTAGES & DISADVANTAGES
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                        DEPTH-FIRST SEARCH (DFS)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ ✅ ADVANTAGES:                                                              │
│    • Memory efficient: O(bm) - only stores current path                     │
│    • Simple to implement using stack/recursion                              │
│    • Good when any solution is acceptable                                   │
│                                                                             │
│ ❌ DISADVANTAGES:                                                           │
│    • NOT optimal: Found {dfs['cost']}km vs optimal {astar['cost']}km                         │
│    • Can get stuck in infinite branches                                     │
│    • Solution depends on edge ordering                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                       BREADTH-FIRST SEARCH (BFS)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ ✅ ADVANTAGES:                                                              │
│    • Complete: Always finds solution if one exists                          │
│    • Optimal for UNWEIGHTED graphs (fewest edges)                           │
│    • Systematic level-by-level exploration                                  │
│                                                                             │
│ ❌ DISADVANTAGES:                                                           │
│    • Memory intensive: O(b^d) - stores entire frontier                      │
│    • NOT optimal for weighted: {bfs['cost']}km vs {astar['cost']}km                        │
│    • Slow for deep solutions                                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              A* SEARCH                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ ✅ ADVANTAGES:                                                              │
│    • OPTIMAL: Guaranteed shortest path with admissible heuristic            │
│    • Complete: Will find solution if one exists                             │
│    • Efficient: Heuristic guides search toward goal                         │
│    • Best for weighted graphs like road networks                            │
│                                                                             │
│ ❌ DISADVANTAGES:                                                           │
│    • Requires good heuristic design                                         │
│    • Memory intensive: O(b^d) worst case                                    │
│    • Computational overhead for f(n) = g(n) + h(n)                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           KEY CONCLUSIONS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. For robot delivery (weighted graphs): A* is the BEST choice              │
│ 2. DFS: Use when memory is limited or any solution is acceptable            │
│ 3. BFS: Use for unweighted graphs or when hop count matters                 │
│ 4. Heuristic quality directly impacts A* efficiency                         │
│ 5. A* optimal path: {' → '.join(astar['path'])}    │
└─────────────────────────────────────────────────────────────────────────────┘
""")

# ═══════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "╔" + "═"*68 + "╗")
    print("║" + " GRAPH SEARCH ALGORITHMS - ENHANCED VISUALIZATION ".center(68) + "║")
    print("║" + " Robot Parcel Delivery: Glogow → Plock ".center(68) + "║")
    print("╚" + "═"*68 + "╝")
    
    # State Space Info
    print("\n" + "═"*70)
    print("1. STATE SPACE REPRESENTATION")
    print("═"*70)
    print(f"• Total Cities: {len(graph)}")
    print(f"• Total Roads: {sum(len(v) for v in graph.values()) // 2}")
    print(f"• Start: {start} | Goal: {goal}")
    
    visualizer = RealTimeSearchVisualizer(graph, start, goal, heuristic, city_positions)
    metrics = PerformanceMetrics()
    
    # Menu
    print("\n" + "═"*70)
    print("SELECT VISUALIZATION MODE")
    print("═"*70)
    print("1. Real-time DFS Animation")
    print("2. Real-time BFS Animation")
    print("3. Real-time A* Animation")
    print("4. Run All Algorithms (Animated)")
    print("5. Static Comparison")
    print("6. Performance Charts")
    print("7. Robot Path Animation (A*)")
    print("8. Complete Analysis (All Features)")
    print("═"*70)
    
    try:
        choice = input("\nEnter choice (1-8) [default=8]: ").strip() or "8"
        choice = int(choice)
    except:
        choice = 8
    
    if choice == 1:
        result = visualizer.animate_search('dfs', interval=800)
    elif choice == 2:
        result = visualizer.animate_search('bfs', interval=800)
    elif choice == 3:
        result = visualizer.animate_search('astar', interval=800)
    elif choice == 4:
        for algo in ['dfs', 'bfs', 'astar']:
            print(f"\n▶️  {algo.upper()} Animation...")
            result = visualizer.animate_search(algo, interval=700)
            metrics.record(algo, result[0], result[1], result[2], result[3], result[4], result[5])
    elif choice == 5:
        results = draw_comparison_static(graph, city_positions, start, goal, heuristic)
        print_discussion(results)
    elif choice == 6:
        results = draw_comparison_static(graph, city_positions, start, goal, heuristic)
        for algo in ['dfs', 'bfs', 'astar']:
            r = results[algo]
            metrics.record(algo, r['path'], r['cost'], r['nodes_expanded'], 
                          r['steps'], r['execution_time'], r['trace'])
        metrics.print_summary()
        charts = PerformanceCharts(metrics.metrics)
        charts.plot_all_charts()
    elif choice == 7:
        _, _, _, _, _, trace = astar_collect_trace(graph, start, goal, heuristic)
        path = trace[-1]['path']
        animator = RobotPathAnimator(graph, city_positions, path, "A* Optimal Path")
        animator.animate(interval=100)
    else:
        # Complete analysis
        print("\n🎬 Running complete analysis...\n")
        
        # 1. Static comparison
        print("📊 1. Generating static comparison...")
        results = draw_comparison_static(graph, city_positions, start, goal, heuristic)
        
        # 2. Record metrics
        for algo in ['dfs', 'bfs', 'astar']:
            r = results[algo]
            metrics.record(algo, r['path'], r['cost'], r['nodes_expanded'],
                          r['steps'], r['execution_time'], r['trace'])
        
        # 3. Print metrics
        metrics.print_summary()
        
        # 4. Performance charts
        print("\n📊 2. Generating performance charts...")
        charts = PerformanceCharts(metrics.metrics)
        charts.plot_all_charts()
        
        # 5. Animated algorithms
        print("\n🎬 3. Running animated visualizations...")
        for algo in ['dfs', 'bfs', 'astar']:
            print(f"\n▶️  {algo.upper()} Animation...")
            visualizer.animate_search(algo, interval=600)
        
        # 6. Robot animation
        print("\n🤖 4. Robot path animation...")
        path = results['astar']['path']
        animator = RobotPathAnimator(graph, city_positions, path, "A* Optimal Path")
        animator.animate(interval=80)
        
        # 7. Print discussion
        print_discussion(results)
    
    print("\n" + "═"*70)
    print("✅ VISUALIZATION COMPLETE!")
    print("   Generated files: algorithm_comparison.png, performance_charts.png")
    print("═"*70)