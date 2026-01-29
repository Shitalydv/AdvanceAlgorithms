"""
Multithreaded Sorting Visualization — QuickSort + Merge (GUI)
============================================================
Problem: Demonstrate multithreaded sorting (2 sorting threads + merging thread) with live UI

Purpose: Educational GUI showing parallel sorting of array halves and the final merge step

Features:
- Generate random arrays and control animation speed
- Two concurrent sorting threads (left/right halves) with visual quicksort
- Merging thread that waits for sorts and merges with visualization
- Thread-status indicators, progress and final verification/notification
- Interactive controls: generate, start, reset; animated comparisons and merged progress
- Useful for demonstrating synchronization, threads and visual algorithm tracing
"""

import threading
import time
import random
import tkinter as tk
from tkinter import ttk, messagebox
import copy

class MultithreadedSortingGUI:
    """GUI Application for Multithreaded Sorting Visualization"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🧵 Multithreaded Sorting Visualization")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a2e')
        
        # Data
        self.array_size = 20
        self.original_array = []
        self.working_array = []
        self.sorted_array = []
        self.mid_point = 0
        
        # Thread control
        self.is_sorting = False
        self.speed = 0.1  # Animation speed (seconds)
        
        # Thread synchronization
        self.sort_thread1_done = threading.Event()
        self.sort_thread2_done = threading.Event()
        self.sorting_complete = threading.Event()
        
        # Colors
        self.colors = {
            'bg': '#1a1a2e',
            'panel': '#16213e',
            'accent': '#0f3460',
            'highlight': '#e94560',
            'success': '#00ff88',
            'warning': '#ffd700',
            'text': '#ffffff',
            'left_half': '#3498db',
            'right_half': '#e74c3c',
            'merged': '#2ecc71',
            'comparing': '#f39c12',
            'default': '#9b59b6'
        }
        
        self.setup_ui()
        self.generate_array()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ═══════════════════════════════════════════════════════════
        # Title
        # ═══════════════════════════════════════════════════════════
        title_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(
            title_frame,
            text="🧵 MULTITHREADED SORTING VISUALIZATION",
            font=('Helvetica', 24, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['highlight']
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Quick Sort + Merge | 2 Sorting Threads + 1 Merging Thread",
            font=('Helvetica', 12),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        subtitle_label.pack()
        
        # ═══════════════════════════════════════════════════════════
        # Control Panel
        # ═══════════════════════════════════════════════════════════
        control_frame = tk.Frame(main_frame, bg=self.colors['panel'], relief=tk.RAISED, bd=2)
        control_frame.pack(fill=tk.X, pady=10, ipady=10)
        
        # Array Size
        size_frame = tk.Frame(control_frame, bg=self.colors['panel'])
        size_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            size_frame, text="Array Size:",
            font=('Helvetica', 11, 'bold'),
            bg=self.colors['panel'], fg=self.colors['text']
        ).pack(side=tk.LEFT, padx=5)
        
        self.size_var = tk.IntVar(value=20)
        size_spinbox = ttk.Spinbox(
            size_frame, from_=4, to=50, increment=2,
            textvariable=self.size_var, width=5,
            font=('Helvetica', 11)
        )
        size_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Speed Control
        speed_frame = tk.Frame(control_frame, bg=self.colors['panel'])
        speed_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            speed_frame, text="Speed:",
            font=('Helvetica', 11, 'bold'),
            bg=self.colors['panel'], fg=self.colors['text']
        ).pack(side=tk.LEFT, padx=5)
        
        self.speed_var = tk.DoubleVar(value=0.1)
        speed_scale = ttk.Scale(
            speed_frame, from_=0.01, to=0.5,
            variable=self.speed_var, orient=tk.HORIZONTAL,
            length=150
        )
        speed_scale.pack(side=tk.LEFT, padx=5)
        
        self.speed_label = tk.Label(
            speed_frame, text="0.10s",
            font=('Helvetica', 10),
            bg=self.colors['panel'], fg=self.colors['text']
        )
        self.speed_label.pack(side=tk.LEFT, padx=5)
        
        speed_scale.configure(command=self.update_speed_label)
        
        # Buttons
        button_frame = tk.Frame(control_frame, bg=self.colors['panel'])
        button_frame.pack(side=tk.RIGHT, padx=20)
        
        self.generate_btn = tk.Button(
            button_frame, text="🔄 Generate Array",
            font=('Helvetica', 11, 'bold'),
            bg='#3498db', fg='white',
            activebackground='#2980b9',
            command=self.generate_array,
            cursor='hand2'
        )
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        self.start_btn = tk.Button(
            button_frame, text="▶️ Start Sorting",
            font=('Helvetica', 11, 'bold'),
            bg='#2ecc71', fg='white',
            activebackground='#27ae60',
            command=self.start_sorting,
            cursor='hand2'
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = tk.Button(
            button_frame, text="🔃 Reset",
            font=('Helvetica', 11, 'bold'),
            bg='#e74c3c', fg='white',
            activebackground='#c0392b',
            command=self.reset,
            cursor='hand2'
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        # ═══════════════════════════════════════════════════════════
        # Visualization Canvas
        # ═══════════════════════════════════════════════════════════
        canvas_frame = tk.Frame(main_frame, bg=self.colors['panel'], relief=tk.SUNKEN, bd=2)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            bg='#0d1117',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ═══════════════════════════════════════════════════════════
        # Thread Status Panel
        # ═══════════════════════════════════════════════════════════
        status_frame = tk.Frame(main_frame, bg=self.colors['panel'], relief=tk.RAISED, bd=2)
        status_frame.pack(fill=tk.X, pady=10)
        
        # Thread 1 Status
        self.thread1_frame = tk.Frame(status_frame, bg=self.colors['panel'])
        self.thread1_frame.pack(side=tk.LEFT, expand=True, padx=20, pady=10)
        
        self.thread1_indicator = tk.Canvas(
            self.thread1_frame, width=20, height=20,
            bg=self.colors['panel'], highlightthickness=0
        )
        self.thread1_indicator.pack(side=tk.LEFT, padx=5)
        self.thread1_indicator.create_oval(2, 2, 18, 18, fill='gray', outline='white', tags='indicator')
        
        self.thread1_label = tk.Label(
            self.thread1_frame,
            text="🧵 Sorting Thread 1 (Left Half)",
            font=('Helvetica', 11, 'bold'),
            bg=self.colors['panel'], fg=self.colors['left_half']
        )
        self.thread1_label.pack(side=tk.LEFT, padx=5)
        
        self.thread1_status = tk.Label(
            self.thread1_frame, text="⏳ Waiting",
            font=('Helvetica', 10),
            bg=self.colors['panel'], fg='gray'
        )
        self.thread1_status.pack(side=tk.LEFT, padx=10)
        
        # Thread 2 Status
        self.thread2_frame = tk.Frame(status_frame, bg=self.colors['panel'])
        self.thread2_frame.pack(side=tk.LEFT, expand=True, padx=20, pady=10)
        
        self.thread2_indicator = tk.Canvas(
            self.thread2_frame, width=20, height=20,
            bg=self.colors['panel'], highlightthickness=0
        )
        self.thread2_indicator.pack(side=tk.LEFT, padx=5)
        self.thread2_indicator.create_oval(2, 2, 18, 18, fill='gray', outline='white', tags='indicator')
        
        self.thread2_label = tk.Label(
            self.thread2_frame,
            text="🧵 Sorting Thread 2 (Right Half)",
            font=('Helvetica', 11, 'bold'),
            bg=self.colors['panel'], fg=self.colors['right_half']
        )
        self.thread2_label.pack(side=tk.LEFT, padx=5)
        
        self.thread2_status = tk.Label(
            self.thread2_frame, text="⏳ Waiting",
            font=('Helvetica', 10),
            bg=self.colors['panel'], fg='gray'
        )
        self.thread2_status.pack(side=tk.LEFT, padx=10)
        
        # Merge Thread Status
        self.merge_frame = tk.Frame(status_frame, bg=self.colors['panel'])
        self.merge_frame.pack(side=tk.LEFT, expand=True, padx=20, pady=10)
        
        self.merge_indicator = tk.Canvas(
            self.merge_frame, width=20, height=20,
            bg=self.colors['panel'], highlightthickness=0
        )
        self.merge_indicator.pack(side=tk.LEFT, padx=5)
        self.merge_indicator.create_oval(2, 2, 18, 18, fill='gray', outline='white', tags='indicator')
        
        self.merge_label = tk.Label(
            self.merge_frame,
            text="🔀 Merging Thread",
            font=('Helvetica', 11, 'bold'),
            bg=self.colors['panel'], fg=self.colors['merged']
        )
        self.merge_label.pack(side=tk.LEFT, padx=5)
        
        self.merge_status = tk.Label(
            self.merge_frame, text="⏳ Waiting",
            font=('Helvetica', 10),
            bg=self.colors['panel'], fg='gray'
        )
        self.merge_status.pack(side=tk.LEFT, padx=10)
        
        # ═══════════════════════════════════════════════════════════
        # Info Panel
        # ═══════════════════════════════════════════════════════════
        info_frame = tk.Frame(main_frame, bg=self.colors['panel'], relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, pady=5)
        
        self.info_label = tk.Label(
            info_frame,
            text="Click 'Generate Array' to create a new random array, then 'Start Sorting' to begin.",
            font=('Helvetica', 11),
            bg=self.colors['panel'], fg=self.colors['text']
        )
        self.info_label.pack(pady=10)
        
        # Legend
        legend_frame = tk.Frame(info_frame, bg=self.colors['panel'])
        legend_frame.pack(pady=5)
        
        legends = [
            ("Left Half", self.colors['left_half']),
            ("Right Half", self.colors['right_half']),
            ("Comparing", self.colors['comparing']),
            ("Merged", self.colors['merged'])
        ]
        
        for text, color in legends:
            legend_item = tk.Frame(legend_frame, bg=self.colors['panel'])
            legend_item.pack(side=tk.LEFT, padx=15)
            
            color_box = tk.Canvas(legend_item, width=20, height=20, bg=self.colors['panel'], highlightthickness=0)
            color_box.pack(side=tk.LEFT, padx=2)
            color_box.create_rectangle(2, 2, 18, 18, fill=color, outline='white')
            
            tk.Label(
                legend_item, text=text,
                font=('Helvetica', 9),
                bg=self.colors['panel'], fg=self.colors['text']
            ).pack(side=tk.LEFT, padx=2)
    
    def update_speed_label(self, value):
        """Update speed label when slider changes"""
        self.speed = float(value)
        self.speed_label.config(text=f"{self.speed:.2f}s")
    
    def generate_array(self):
        """Generate a new random array"""
        if self.is_sorting:
            messagebox.showwarning("Warning", "Sorting in progress! Please wait or reset.")
            return
        
        self.array_size = self.size_var.get()
        if self.array_size % 2 != 0:
            self.array_size += 1
            self.size_var.set(self.array_size)
        
        self.mid_point = self.array_size // 2
        self.original_array = [random.randint(5, 100) for _ in range(self.array_size)]
        self.working_array = copy.deepcopy(self.original_array)
        self.sorted_array = [0] * self.array_size
        
        self.reset_thread_status()
        self.draw_array(self.working_array)
        
        self.info_label.config(
            text=f"Generated array of {self.array_size} elements. "
                 f"Left half: indices [0-{self.mid_point-1}], Right half: indices [{self.mid_point}-{self.array_size-1}]"
        )
    
    def draw_array(self, array, highlight_indices=None, colors=None):
        """Draw the array as bars on the canvas"""
        self.canvas.delete("all")
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            self.root.after(100, lambda: self.draw_array(array, highlight_indices, colors))
            return
        
        n = len(array)
        if n == 0:
            return
        
        bar_width = (canvas_width - 40) / n
        max_val = max(array) if max(array) > 0 else 1
        
        for i, val in enumerate(array):
            x0 = 20 + i * bar_width
            x1 = x0 + bar_width - 2
            
            bar_height = (val / max_val) * (canvas_height - 80)
            y0 = canvas_height - 40
            y1 = y0 - bar_height
            
            # Determine color
            if colors and i < len(colors):
                color = colors[i]
            elif highlight_indices and i in highlight_indices:
                color = self.colors['comparing']
            elif i < self.mid_point:
                color = self.colors['left_half']
            else:
                color = self.colors['right_half']
            
            # Draw bar
            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                fill=color, outline='white', width=1
            )
            
            # Draw value on top
            if bar_width > 20:
                self.canvas.create_text(
                    (x0 + x1) / 2, y1 - 10,
                    text=str(val), fill='white',
                    font=('Helvetica', 8, 'bold')
                )
            
            # Draw index below
            if bar_width > 15:
                self.canvas.create_text(
                    (x0 + x1) / 2, y0 + 15,
                    text=str(i), fill='gray',
                    font=('Helvetica', 7)
                )
        
        # Draw midpoint line
        mid_x = 20 + self.mid_point * bar_width - 1
        self.canvas.create_line(
            mid_x, 20, mid_x, canvas_height - 20,
            fill='yellow', width=2, dash=(5, 3)
        )
        self.canvas.create_text(
            mid_x, 10, text="↓ Midpoint ↓",
            fill='yellow', font=('Helvetica', 9, 'bold')
        )
        
        self.root.update()
    
    def reset_thread_status(self):
        """Reset all thread status indicators"""
        self.thread1_indicator.itemconfig('indicator', fill='gray')
        self.thread1_status.config(text="⏳ Waiting", fg='gray')
        
        self.thread2_indicator.itemconfig('indicator', fill='gray')
        self.thread2_status.config(text="⏳ Waiting", fg='gray')
        
        self.merge_indicator.itemconfig('indicator', fill='gray')
        self.merge_status.config(text="⏳ Waiting", fg='gray')
    
    def update_thread_status(self, thread_id, status, color):
        """Update thread status indicator"""
        if thread_id == 1:
            self.thread1_indicator.itemconfig('indicator', fill=color)
            self.thread1_status.config(text=status, fg=color)
        elif thread_id == 2:
            self.thread2_indicator.itemconfig('indicator', fill=color)
            self.thread2_status.config(text=status, fg=color)
        elif thread_id == 3:
            self.merge_indicator.itemconfig('indicator', fill=color)
            self.merge_status.config(text=status, fg=color)
        
        self.root.update()
    
    def start_sorting(self):
        """Start the multithreaded sorting process"""
        if self.is_sorting:
            messagebox.showwarning("Warning", "Sorting already in progress!")
            return
        
        if not self.working_array:
            messagebox.showwarning("Warning", "Please generate an array first!")
            return
        
        self.is_sorting = True
        self.start_btn.config(state=tk.DISABLED)
        self.generate_btn.config(state=tk.DISABLED)
        
        # Reset events
        self.sort_thread1_done.clear()
        self.sort_thread2_done.clear()
        self.sorting_complete.clear()
        
        # Reset working array
        self.working_array = copy.deepcopy(self.original_array)
        self.sorted_array = [0] * self.array_size
        
        self.info_label.config(text="🚀 Starting multithreaded sorting...")
        
        # Start sorting in a separate thread to not block GUI
        main_thread = threading.Thread(target=self.run_sorting)
        main_thread.start()
    
    def run_sorting(self):
        """Run the sorting process with threads"""
        # Create threads
        thread1 = threading.Thread(
            target=self.sorting_thread_visual,
            args=(1, 0, self.mid_point)
        )
        thread2 = threading.Thread(
            target=self.sorting_thread_visual,
            args=(2, self.mid_point, self.array_size)
        )
        merge_thread = threading.Thread(target=self.merging_thread_visual)
        
        # Start sorting threads
        thread1.start()
        thread2.start()
        merge_thread.start()
        
        # Wait for completion
        thread1.join()
        thread2.join()
        merge_thread.join()
        
        # Final update
        self.root.after(0, self.sorting_complete_callback)
    
    def sorting_thread_visual(self, thread_id, start_idx, end_idx):
        """Sorting thread with visual updates"""
        self.root.after(0, lambda: self.update_thread_status(
            thread_id, "🔄 Sorting...", self.colors['comparing']
        ))
        
        # Visual quick sort
        self.visual_quick_sort(thread_id, start_idx, end_idx - 1)
        
        self.root.after(0, lambda: self.update_thread_status(
            thread_id, "✅ Complete", self.colors['success']
        ))
        
        if thread_id == 1:
            self.sort_thread1_done.set()
        else:
            self.sort_thread2_done.set()
    
    def visual_quick_sort(self, thread_id, low, high):
        """Quick sort with visualization"""
        if low < high:
            pivot_idx = self.visual_partition(thread_id, low, high)
            self.visual_quick_sort(thread_id, low, pivot_idx - 1)
            self.visual_quick_sort(thread_id, pivot_idx + 1, high)
    
    def visual_partition(self, thread_id, low, high):
        """Partition with visualization"""
        pivot = self.working_array[high]
        i = low - 1
        
        for j in range(low, high):
            # Highlight comparing elements
            self.root.after(0, lambda j=j, high=high: self.draw_array(
                self.working_array, highlight_indices={j, high}
            ))
            time.sleep(self.speed)
            
            if self.working_array[j] <= pivot:
                i += 1
                self.working_array[i], self.working_array[j] = self.working_array[j], self.working_array[i]
                
                self.root.after(0, lambda: self.draw_array(self.working_array))
                time.sleep(self.speed / 2)
        
        self.working_array[i + 1], self.working_array[high] = self.working_array[high], self.working_array[i + 1]
        
        self.root.after(0, lambda: self.draw_array(self.working_array))
        time.sleep(self.speed / 2)
        
        return i + 1
    
    def merging_thread_visual(self):
        """Merging thread with visualization"""
        self.root.after(0, lambda: self.update_thread_status(
            3, "⏳ Waiting for sorts...", 'gray'
        ))
        
        # Wait for both sorting threads
        self.sort_thread1_done.wait()
        self.sort_thread2_done.wait()
        
        self.root.after(0, lambda: self.update_thread_status(
            3, "🔀 Merging...", self.colors['comparing']
        ))
        self.root.after(0, lambda: self.info_label.config(
            text="🔀 Both halves sorted! Now merging..."
        ))
        
        # Merge the two halves
        left_idx = 0
        right_idx = self.mid_point
        merge_idx = 0
        
        while left_idx < self.mid_point and right_idx < self.array_size:
            # Highlight elements being compared
            colors = [self.colors['default']] * self.array_size
            colors[left_idx] = self.colors['comparing']
            colors[right_idx] = self.colors['comparing']
            
            self.root.after(0, lambda c=colors: self.draw_array(self.working_array, colors=c))
            time.sleep(self.speed)
            
            if self.working_array[left_idx] <= self.working_array[right_idx]:
                self.sorted_array[merge_idx] = self.working_array[left_idx]
                left_idx += 1
            else:
                self.sorted_array[merge_idx] = self.working_array[right_idx]
                right_idx += 1
            merge_idx += 1
            
            # Draw merged portion
            self.root.after(0, lambda: self.draw_merged_progress())
            time.sleep(self.speed / 2)
        
        # Copy remaining elements
        while left_idx < self.mid_point:
            self.sorted_array[merge_idx] = self.working_array[left_idx]
            left_idx += 1
            merge_idx += 1
            self.root.after(0, lambda: self.draw_merged_progress())
            time.sleep(self.speed / 2)
        
        while right_idx < self.array_size:
            self.sorted_array[merge_idx] = self.working_array[right_idx]
            right_idx += 1
            merge_idx += 1
            self.root.after(0, lambda: self.draw_merged_progress())
            time.sleep(self.speed / 2)
        
        self.root.after(0, lambda: self.update_thread_status(
            3, "✅ Complete", self.colors['success']
        ))
        
        self.sorting_complete.set()
    
    def draw_merged_progress(self):
        """Draw the merge progress"""
        self.canvas.delete("all")
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        n = len(self.sorted_array)
        bar_width = (canvas_width - 40) / n
        max_val = max(max(self.sorted_array) if any(self.sorted_array) else 1,
                      max(self.working_array) if self.working_array else 1)
        
        # Draw sorted array (bottom half)
        for i, val in enumerate(self.sorted_array):
            if val == 0:
                continue
                
            x0 = 20 + i * bar_width
            x1 = x0 + bar_width - 2
            
            bar_height = (val / max_val) * ((canvas_height - 100) / 2)
            y0 = canvas_height - 40
            y1 = y0 - bar_height
            
            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                fill=self.colors['merged'], outline='white', width=1
            )
            
            if bar_width > 20:
                self.canvas.create_text(
                    (x0 + x1) / 2, y1 - 10,
                    text=str(val), fill='white',
                    font=('Helvetica', 8, 'bold')
                )
        
        # Label
        self.canvas.create_text(
            canvas_width / 2, canvas_height - 20,
            text="Merged Array (Sorted)",
            fill=self.colors['merged'],
            font=('Helvetica', 10, 'bold')
        )
        
        self.root.update()
    
    def sorting_complete_callback(self):
        """Callback when sorting is complete"""
        # Draw final sorted array
        colors = [self.colors['merged']] * self.array_size
        self.draw_array(self.sorted_array, colors=colors)
        
        # Verify
        is_sorted = all(self.sorted_array[i] <= self.sorted_array[i + 1] 
                       for i in range(len(self.sorted_array) - 1))
        
        status = "✅ CORRECTLY" if is_sorted else "❌ NOT"
        self.info_label.config(
            text=f"🎉 Sorting Complete! Array is {status} sorted. "
                 f"Original: {self.original_array[:5]}... → Sorted: {self.sorted_array[:5]}..."
        )
        
        self.is_sorting = False
        self.start_btn.config(state=tk.NORMAL)
        self.generate_btn.config(state=tk.NORMAL)
        
        if is_sorted:
            messagebox.showinfo(
                "Success! 🎉",
                f"Array sorted successfully!\n\n"
                f"Original: {self.original_array}\n\n"
                f"Sorted: {self.sorted_array}"
            )
    
    def reset(self):
        """Reset the application"""
        self.is_sorting = False
        self.sort_thread1_done.set()
        self.sort_thread2_done.set()
        self.sorting_complete.set()
        
        self.working_array = copy.deepcopy(self.original_array)
        self.sorted_array = [0] * self.array_size
        
        self.reset_thread_status()
        self.draw_array(self.working_array)
        
        self.start_btn.config(state=tk.NORMAL)
        self.generate_btn.config(state=tk.NORMAL)
        
        self.info_label.config(text="Reset complete. Ready for new sorting operation.")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    root = tk.Tk()
    
    # Set icon (optional)
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    app = MultithreadedSortingGUI(root)
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()