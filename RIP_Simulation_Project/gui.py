import tkinter as tk
from tkinter import ttk, messagebox
import math
import time
from rip_algorithm import run_rip_round
from utils import format_routing_table

class RIPSimulationGUI:
    def __init__(self, root, routers):
        self.root = root
        self.root.title("RIP Simulation Project")
        self.root.geometry("1000x700")
        
        self.routers = routers
        self.round_number = 0
        self.converged = False
        
        # Calculate node positions (Circle Layout)
        self.node_positions = self.calculate_positions()
        
        # GUI Layout
        self.setup_ui()
        self.draw_network()
        
    def calculate_positions(self):
        """Calculates (x, y) for each router in a circle."""
        positions = {}
        count = len(self.routers)
        center_x, center_y = 350, 300
        radius = 200
        
        router_names = sorted(self.routers.keys())
        for i, name in enumerate(router_names):
            angle = 2 * math.pi * i / count
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[name] = (x, y)
        return positions

    def setup_ui(self):
        # Top Frame: Controls
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.lbl_round = ttk.Label(control_frame, text="Round: 0", font=("Arial", 14, "bold"))
        self.lbl_round.pack(side=tk.LEFT, padx=20)
        
        self.btn_next = ttk.Button(control_frame, text="Next Round", command=self.next_round)
        self.btn_next.pack(side=tk.LEFT, padx=10)
        
        self.btn_auto = ttk.Button(control_frame, text="Auto Run", command=self.auto_run)
        self.btn_auto.pack(side=tk.LEFT, padx=10)

        self.lbl_status = ttk.Label(control_frame, text="Status: Initialized", foreground="blue")
        self.lbl_status.pack(side=tk.LEFT, padx=20)

        # Main Content: Split into Network Graph (Left) and Details (Right)
        paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left: Canvas
        self.canvas = tk.Canvas(paned_window, bg="white", width=700)
        paned_window.add(self.canvas, weight=2)
        
        # Right: Routing Tables & Logs
        right_panel = ttk.Frame(paned_window)
        paned_window.add(right_panel, weight=1)
        
        # Tables area
        lbl_tables = ttk.Label(right_panel, text="Routing Tables (Click Node to View)", font=("Arial", 10, "bold"))
        lbl_tables.pack(pady=5)
        
        self.txt_tables = tk.Text(right_panel, height=20, width=40, font=("Consolas", 10))
        self.txt_tables.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Logs area
        lbl_logs = ttk.Label(right_panel, text="Simulation Logs", font=("Arial", 10, "bold"))
        lbl_logs.pack(pady=5)
        
        self.txt_logs = tk.Text(right_panel, height=10, width=40, font=("Consolas", 9), state='disabled')
        self.txt_logs.pack(fill=tk.BOTH, expand=True, pady=5)

    def draw_network(self):
        self.canvas.delete("all")
        
        # Draw edges
        processed_edges = set()
        for name, router in self.routers.items():
            x1, y1 = self.node_positions[name]
            for neighbor in router.neighbors:
                edge_id = tuple(sorted((name, neighbor.name)))
                if edge_id in processed_edges:
                    continue
                processed_edges.add(edge_id)
                
                x2, y2 = self.node_positions[neighbor.name]
                self.canvas.create_line(x1, y1, x2, y2, fill="gray", width=2)

        # Draw nodes
        for name, (x, y) in self.node_positions.items():
            # Circle
            r = 20
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="#4CAF50", outline="black", tags=name)
            # Label
            self.canvas.create_text(x, y, text=name, font=("Arial", 10, "bold"), fill="white", tags=name)
            
            # Bind click
            self.canvas.tag_bind(name, "<Button-1>", lambda event, n=name: self.show_table(n))

    def log(self, message):
        self.txt_logs.config(state='normal')
        self.txt_logs.insert(tk.END, f"{message}\n")
        self.txt_logs.see(tk.END)
        self.txt_logs.config(state='disabled')

    def show_table(self, router_name):
        router = self.routers[router_name]
        table_str = f"Routing Table for {router_name}:\n"
        table_str += format_routing_table(router.get_routing_table())
        
        self.txt_tables.delete(1.0, tk.END)
        self.txt_tables.insert(tk.END, table_str)

    def next_round(self):
        if self.converged:
            messagebox.showinfo("Simulation", "Network has already converged!")
            return

        self.round_number += 1
        self.lbl_round.config(text=f"Round: {self.round_number}")
        
        converged, updates = run_rip_round(self.routers)
        
        if updates:
            for update in updates:
                self.log(update)
        else:
            self.log("No table updates this round.")

        if converged:
            self.converged = True
            self.lbl_status.config(text="Status: CONVERGED", foreground="green")
            self.log(">>> NETWORK CONVERGED <<<")
            messagebox.showinfo("Simulation", f"Converged in {self.round_number} rounds!")
        else:
            self.lbl_status.config(text="Status: Running...", foreground="orange")
            
        # Refresh current view if a table is showing
        # (Optional: auto-refresh active view)

    def auto_run(self):
        if self.converged:
            return
            
        def step():
            if not self.converged:
                self.next_round()
                self.root.after(1000, step) # 1 second delay
        
        step()

