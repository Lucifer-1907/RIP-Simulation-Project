import tkinter as tk
from tkinter import ttk, messagebox
import math

from rip_algorithm import run_rip_round
from utils import format_routing_table


class RIPSimulationGUI:
    def __init__(self, root, routers):
        self.root = root
        self.routers = routers

        self.round_number = 0
        self.converged = False
        self.selected_router = None

        self.root.title("RIP Protocol Simulation")
        self.root.geometry("1050x720")

        # Pre-calculate node positions
        self.node_positions = self.calculate_positions()

        # Build UI
        self.setup_ui()
        self.draw_network()

    # -------------------- Layout & Geometry --------------------

    def calculate_positions(self):
        """Place routers evenly in a circular layout."""
        positions = {}
        count = len(self.routers)
        center_x, center_y = 380, 320
        radius = 230

        names = sorted(self.routers.keys())
        for i, name in enumerate(names):
            angle = 2 * math.pi * i / count
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[name] = (x, y)

        return positions

    def setup_ui(self):
        # ---------------- Top Control Bar ----------------
        control = ttk.Frame(self.root, padding=10)
        control.pack(side=tk.TOP, fill=tk.X)

        self.lbl_round = ttk.Label(
            control, text="Round: 0", font=("Arial", 14, "bold")
        )
        self.lbl_round.pack(side=tk.LEFT, padx=20)

        self.btn_next = ttk.Button(
            control, text="Next Round", command=self.next_round
        )
        self.btn_next.pack(side=tk.LEFT, padx=8)

        self.btn_auto = ttk.Button(
            control, text="Auto Run", command=self.auto_run
        )
        self.btn_auto.pack(side=tk.LEFT, padx=8)

        self.lbl_status = ttk.Label(
            control, text="Status: Initialized", foreground="blue"
        )
        self.lbl_status.pack(side=tk.LEFT, padx=25)

        # ---------------- Main Split View ----------------
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: Network Canvas
        self.canvas = tk.Canvas(main_pane, bg="white", width=750)
        main_pane.add(self.canvas, weight=2)

        # Right: Tables + Logs
        right_panel = ttk.Frame(main_pane)
        main_pane.add(right_panel, weight=1)

        ttk.Label(
            right_panel,
            text="Routing Table (Click a Router)",
            font=("Arial", 10, "bold"),
        ).pack(pady=5)

        self.txt_tables = tk.Text(
            right_panel, height=20, font=("Consolas", 10)
        )
        self.txt_tables.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(
            right_panel,
            text="Simulation Logs",
            font=("Arial", 10, "bold"),
        ).pack(pady=5)

        self.txt_logs = tk.Text(
            right_panel,
            height=10,
            font=("Consolas", 9),
            state="disabled",
        )
        self.txt_logs.pack(fill=tk.BOTH, expand=True)

    # -------------------- Drawing --------------------

    def draw_network(self, highlight=None):
        self.canvas.delete("all")

        # Draw links
        drawn = set()
        for name, router in self.routers.items():
            x1, y1 = self.node_positions[name]
            for neighbor in router.neighbors:
                edge = tuple(sorted((name, neighbor.name)))
                if edge in drawn:
                    continue
                drawn.add(edge)

                x2, y2 = self.node_positions[neighbor.name]
                self.canvas.create_line(x1, y1, x2, y2, fill="gray", width=2)

        # Draw routers
        for name, (x, y) in self.node_positions.items():
            r = 22
            color = "#4CAF50"

            if highlight and name in highlight:
                color = "#FF9800"  # updated router

            self.canvas.create_oval(
                x - r, y - r, x + r, y + r,
                fill=color, outline="black", width=2, tags=name
            )
            self.canvas.create_text(
                x, y, text=name, fill="white",
                font=("Arial", 10, "bold"), tags=name
            )

            self.canvas.tag_bind(
                name, "<Button-1>",
                lambda e, n=name: self.show_table(n)
            )

    # -------------------- Logging --------------------

    def log(self, message):
        self.txt_logs.config(state="normal")
        self.txt_logs.insert(tk.END, message + "\n")
        self.txt_logs.see(tk.END)
        self.txt_logs.config(state="disabled")

    # -------------------- Routing Tables --------------------

    def show_table(self, router_name):
        self.selected_router = router_name
        router = self.routers[router_name]

        content = f"Routing Table for {router_name}\n"
        content += format_routing_table(router.get_routing_table())

        self.txt_tables.delete(1.0, tk.END)
        self.txt_tables.insert(tk.END, content)

    # -------------------- Simulation Controls --------------------

    def next_round(self):
        if self.converged:
            messagebox.showinfo("RIP Simulation", "Network already converged.")
            return

        self.round_number += 1
        self.lbl_round.config(text=f"Round: {self.round_number}")

        converged, updates = run_rip_round(self.routers)

        changed_routers = set()
        for msg in updates:
            self.log(msg)
            parts = msg.split()
            if parts:
                changed_routers.add(parts[0])

        if not updates:
            self.log("No routing table changes in this round.")

        self.draw_network(highlight=changed_routers)

        if self.selected_router:
            self.show_table(self.selected_router)

        if converged:
            self.converged = True
            self.lbl_status.config(
                text="Status: CONVERGED", foreground="green"
            )
            self.btn_next.config(state="disabled")
            self.btn_auto.config(state="disabled")
            self.log(">>> NETWORK HAS CONVERGED <<<")
            messagebox.showinfo(
                "RIP Simulation",
                f"Network converged in {self.round_number} rounds."
            )
        else:
            self.lbl_status.config(
                text="Status: Running...", foreground="orange"
            )

    def auto_run(self):
        if self.converged:
            return

        def step():
            if not self.converged:
                self.next_round()
                self.root.after(900, step)

        step()
