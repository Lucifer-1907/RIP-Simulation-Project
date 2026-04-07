import tkinter as tk
from tkinter import ttk, messagebox
import math
import os

from rip_algorithm import run_rip_round
from utils import format_routing_table
from router import Router

# ── PIL / Pillow (for image assets) ───────────────────────────
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
#  IMAGE LOADER  (loads + tints router/packet assets)
# ═══════════════════════════════════════════════════════════════

def _tint_image(pil_img, color_hex, alpha=0.55):
    """Blend a PIL RGBA image with a solid colour to show router state."""
    r = int(color_hex[1:3], 16)
    g = int(color_hex[3:5], 16)
    b = int(color_hex[5:7], 16)
    img     = pil_img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (r, g, b, int(255 * alpha)))
    return Image.alpha_composite(img, overlay)


def load_assets(base_dir, node_size=52, packet_size=22):
    """
    Load router.png and packet.png from assets/ folder.
    Returns a dict of ImageTk.PhotoImage objects, or None if unavailable.
    """
    if not PIL_AVAILABLE:
        return None

    assets_dir  = os.path.join(base_dir, "assets")
    router_path = os.path.join(assets_dir, "router.png")
    packet_path = os.path.join(assets_dir, "packet.png")

    if not os.path.exists(router_path) or not os.path.exists(packet_path):
        return None

    try:
        router_base = Image.open(router_path).convert("RGBA").resize(
            (node_size, node_size), Image.LANCZOS)

        assets = {
            "router_default":   ImageTk.PhotoImage(_tint_image(router_base, "#2c3e50", 0.0)),
            "router_updated":   ImageTk.PhotoImage(_tint_image(router_base, "#e67e22", 0.45)),
            "router_converged": ImageTk.PhotoImage(_tint_image(router_base, "#27ae60", 0.45)),
            "packet": ImageTk.PhotoImage(
                Image.open(packet_path).convert("RGBA").resize(
                    (packet_size, packet_size), Image.LANCZOS))
        }
        return assets
    except Exception as e:
        print(f"[WARN] Could not load assets: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
#  TOPOLOGY EDITOR
# ═══════════════════════════════════════════════════════════════

class TopologyEditor(tk.Toplevel):
    """
    Lets the user add/remove routers and links manually.
    self.result is set to a { name: Router } dict on confirm, or None on cancel.
    """

    def __init__(self, parent, default_routers=None):
        super().__init__(parent)
        self.title("Network Topology Editor")
        self.geometry("640x520")
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self.result       = None
        self._routers_raw = []
        self._links_raw   = []

        if default_routers:
            seen = set()
            for name, r in default_routers.items():
                if name not in self._routers_raw:
                    self._routers_raw.append(name)
                for nb in r.neighbors:
                    edge = tuple(sorted((name, nb.name)))
                    if edge not in seen:
                        seen.add(edge)
                        self._links_raw.append(edge)

        self._build_ui()

    def _build_ui(self):
        p = dict(padx=8, pady=4)

        tk.Label(self, text="[NET]  Network Topology Editor",
                 font=("Arial", 14, "bold"), fg="#1a237e").pack(pady=(14, 2))
        tk.Label(self, text="Define routers and connect them with links.",
                 font=("Arial", 9), fg="#555").pack(pady=(0, 6))

        rf = ttk.LabelFrame(self, text="  Routers  ", padding=8)
        rf.pack(fill=tk.X, padx=16, pady=6)

        r1 = ttk.Frame(rf); r1.pack(fill=tk.X)
        tk.Label(r1, text="Name:").pack(side=tk.LEFT, **p)
        self._ent_rname = ttk.Entry(r1, width=10)
        self._ent_rname.pack(side=tk.LEFT, **p)
        self._ent_rname.bind("<Return>", lambda e: self._add_router())
        ttk.Button(r1, text="+ Add",    command=self._add_router).pack(side=tk.LEFT, **p)
        ttk.Button(r1, text="- Remove", command=self._del_router).pack(side=tk.LEFT, **p)

        self._lb_routers = tk.Listbox(rf, height=4, selectmode=tk.SINGLE,
                                      font=("Courier", 10))
        self._lb_routers.pack(fill=tk.X, padx=4, pady=(4, 0))
        for n in self._routers_raw:
            self._lb_routers.insert(tk.END, n)

        lf = ttk.LabelFrame(self, text="  Links  ", padding=8)
        lf.pack(fill=tk.X, padx=16, pady=6)

        r2 = ttk.Frame(lf); r2.pack(fill=tk.X)
        tk.Label(r2, text="From:").pack(side=tk.LEFT, **p)
        self._from_var = tk.StringVar()
        self._to_var   = tk.StringVar()
        self._cb_from  = ttk.Combobox(r2, textvariable=self._from_var,
                                      width=9, state="readonly")
        self._cb_from.pack(side=tk.LEFT, **p)
        tk.Label(r2, text="To:").pack(side=tk.LEFT, **p)
        self._cb_to    = ttk.Combobox(r2, textvariable=self._to_var,
                                      width=9, state="readonly")
        self._cb_to.pack(side=tk.LEFT, **p)
        ttk.Button(r2, text="+ Add Link", command=self._add_link).pack(side=tk.LEFT, **p)
        ttk.Button(r2, text="- Remove",   command=self._del_link).pack(side=tk.LEFT, **p)

        self._lb_links = tk.Listbox(lf, height=4, selectmode=tk.SINGLE,
                                    font=("Courier", 10))
        self._lb_links.pack(fill=tk.X, padx=4, pady=(4, 0))
        for (a, b) in self._links_raw:
            self._lb_links.insert(tk.END, f"{a}  --  {b}")

        self._refresh_combos()

        bf = ttk.Frame(self); bf.pack(pady=16)
        ttk.Button(bf, text="[OK]  Start Simulation",
                   command=self._confirm).pack(side=tk.LEFT, padx=12)
        ttk.Button(bf, text="[X]  Cancel",
                   command=self._cancel).pack(side=tk.LEFT, padx=12)

    def _refresh_combos(self):
        vals = sorted(self._routers_raw)
        self._cb_from["values"] = vals
        self._cb_to["values"]   = vals

    def _add_router(self):
        raw  = self._ent_rname.get().strip()
        name = raw.upper() if raw else ""
        if not name:
            return
        if name in self._routers_raw:
            messagebox.showwarning("Duplicate",
                                   f"Router '{name}' already exists.", parent=self)
            return
        self._routers_raw.append(name)
        self._lb_routers.insert(tk.END, name)
        self._ent_rname.delete(0, tk.END)
        self._refresh_combos()

    def _del_router(self):
        sel = self._lb_routers.curselection()
        if not sel:
            return
        name = self._lb_routers.get(sel[0])
        self._routers_raw.remove(name)
        self._lb_routers.delete(sel[0])
        self._links_raw = [(a, b) for (a, b) in self._links_raw
                           if a != name and b != name]
        self._lb_links.delete(0, tk.END)
        for (a, b) in self._links_raw:
            self._lb_links.insert(tk.END, f"{a}  --  {b}")
        self._refresh_combos()

    def _add_link(self):
        a = self._from_var.get().strip()
        b = self._to_var.get().strip()
        if not a or not b:
            messagebox.showwarning("Select routers",
                                   "Choose both From and To.", parent=self)
            return
        if a == b:
            messagebox.showwarning("Invalid",
                                   "A router cannot link to itself.", parent=self)
            return
        edge = tuple(sorted((a, b)))
        if edge in self._links_raw:
            messagebox.showwarning("Duplicate",
                                   "That link already exists.", parent=self)
            return
        self._links_raw.append(edge)
        self._lb_links.insert(tk.END, f"{edge[0]}  --  {edge[1]}")

    def _del_link(self):
        sel = self._lb_links.curselection()
        if not sel:
            return
        self._links_raw.pop(sel[0])
        self._lb_links.delete(sel[0])

    def _confirm(self):
        if len(self._routers_raw) < 2:
            messagebox.showwarning("Too few routers",
                                   "Add at least 2 routers.", parent=self)
            return
        if not self._links_raw:
            messagebox.showwarning("No links",
                                   "Add at least one link.", parent=self)
            return
        routers = {n: Router(n) for n in self._routers_raw}
        for (a, b) in self._links_raw:
            routers[a].add_neighbor(routers[b])
            routers[b].add_neighbor(routers[a])
        self.result = routers
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


# ═══════════════════════════════════════════════════════════════
#  MAIN SIMULATION GUI
# ═══════════════════════════════════════════════════════════════

class RIPSimulationGUI:

    AUTO_DELAY_MS   = 2400
    PARTICLE_FRAMES = 45
    PARTICLE_MS     = 16
    PARTICLE_R      = 11     # fallback dot radius when no image
    STAGGER_MS      = 10

    NODE_R          = 26     # fallback oval radius when no image
    NODE_IMG_HALF   = 26     # half of node image size (52/2)

    COL_BG          = "#1e272e"
    COL_CANVAS      = "#f5f6fa"
    COL_LINK_IDLE   = "#95a5a6"
    COL_LINK_ACTIVE = "#3498db"
    COL_NODE_DEF    = "#2c3e50"
    COL_NODE_UPD    = "#e67e22"
    COL_NODE_CONV   = "#27ae60"
    COL_PARTICLE    = "#e74c3c"
    COL_GLOW        = "#f39c12"

    def __init__(self, root, routers):
        self.root            = root
        self.routers         = routers
        self.round_number    = 0
        self.converged       = False
        self.selected_router = None
        self._animating      = False

        self.root.title("RIP Protocol Simulation")
        self.root.geometry("1150x760")
        self.root.configure(bg=self.COL_BG)

        base_dir      = os.path.dirname(os.path.abspath(__file__))
        self.assets   = load_assets(base_dir)
        self._use_img = self.assets is not None
        if self._use_img:
            print("[INFO] Image assets loaded successfully.")
        else:
            print("[INFO] Assets not found or PIL unavailable - using shapes.")

        self.node_positions = self._calc_positions()
        self._setup_ui()
        self._draw_network()
        self._log("Topology loaded - click Next Round or Auto Run to begin.")

    # ──────────────────────────────────────────────────────────

    def _calc_positions(self):
        cx, cy, rad = 390, 330, 240
        names = sorted(self.routers.keys())
        pos   = {}
        for i, n in enumerate(names):
            angle = 2 * math.pi * i / max(len(names), 1) - math.pi / 2
            pos[n] = (cx + rad * math.cos(angle),
                      cy + rad * math.sin(angle))
        return pos

    def _setup_ui(self):
        top = tk.Frame(self.root, bg=self.COL_BG, height=56)
        top.pack(side=tk.TOP, fill=tk.X)

        self.lbl_round = tk.Label(
            top, text="Round: 0",
            font=("Arial", 13, "bold"),
            bg=self.COL_BG, fg="white")
        self.lbl_round.pack(side=tk.LEFT, padx=20, pady=12)

        btn_kw = dict(bg="#34495e", fg="white",
                      relief=tk.FLAT, font=("Arial", 10, "bold"),
                      activebackground="#4a6278", activeforeground="white",
                      padx=10, pady=5, cursor="hand2")

        self.btn_next  = tk.Button(top, text=">  Next Round",
                                   command=self._next_round, **btn_kw)
        self.btn_next.pack(side=tk.LEFT, padx=6, pady=10)

        self.btn_auto  = tk.Button(top, text=">>  Auto Run",
                                   command=self._auto_run, **btn_kw)
        self.btn_auto.pack(side=tk.LEFT, padx=6, pady=10)

        self.btn_edit  = tk.Button(top, text="[NET]  Edit Topology",
                                   command=self._edit_topology, **btn_kw)
        self.btn_edit.pack(side=tk.LEFT, padx=6, pady=10)

        self.btn_reset = tk.Button(top, text="<<  Reset",
                                   command=self._reset_simulation, **btn_kw)
        self.btn_reset.pack(side=tk.LEFT, padx=6, pady=10)

        self.lbl_status = tk.Label(
            top, text="* Initialized",
            font=("Arial", 10, "bold"),
            bg=self.COL_BG, fg="#1abc9c")
        self.lbl_status.pack(side=tk.RIGHT, padx=24)

        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        cf = tk.Frame(main_pane, bg=self.COL_CANVAS, relief=tk.FLAT)
        self.canvas = tk.Canvas(cf, bg=self.COL_CANVAS, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        main_pane.add(cf, weight=3)

        rp = ttk.Frame(main_pane)
        main_pane.add(rp, weight=1)

        tk.Label(rp, text="Routing Table",
                 font=("Arial", 10, "bold")).pack(pady=(6, 0))
        tk.Label(rp, text="(click a router)",
                 font=("Arial", 8), fg="gray").pack()

        self.txt_tables = tk.Text(rp, height=17, font=("Courier", 10),
                                  state="disabled", bg="#f9f9f9",
                                  relief=tk.FLAT, bd=0)
        ttk.Scrollbar(rp, command=self.txt_tables.yview)
        self.txt_tables.pack(fill=tk.BOTH, expand=True, padx=4, side=tk.TOP)

        tk.Label(rp, text="Simulation Logs",
                 font=("Arial", 10, "bold")).pack(pady=(8, 0))

        self.txt_logs = tk.Text(rp, height=12, font=("Courier", 9),
                                state="disabled", bg="#f9f9f9",
                                relief=tk.FLAT, bd=0)
        ttk.Scrollbar(rp, command=self.txt_logs.yview)
        self.txt_logs.pack(fill=tk.BOTH, expand=True, padx=4)

    # ──────────────────────────────────────────────────────────
    # Drawing
    # ──────────────────────────────────────────────────────────

    def _draw_network(self, highlight=None, active_links=None):
        self.canvas.delete("static")

        # Links
        drawn = set()
        for name, router in self.routers.items():
            x1, y1 = self.node_positions[name]
            for nb in router.neighbors:
                edge = tuple(sorted((name, nb.name)))
                if edge in drawn:
                    continue
                drawn.add(edge)
                x2, y2 = self.node_positions[nb.name]
                active = active_links and edge in active_links
                lc = self.COL_LINK_ACTIVE if active else self.COL_LINK_IDLE
                lw = 3 if active else 2
                self.canvas.create_line(x1, y1, x2, y2,
                                        fill=lc, width=lw, tags="static")
                mx, my = (x1+x2)/2, (y1+y2)/2
                self.canvas.create_text(mx, my-8, text="1",
                                        fill="#7f8c8d",
                                        font=("Arial", 8), tags="static")

        # Nodes
        for name, (x, y) in self.node_positions.items():
            updated = highlight and name in highlight

            if self._use_img:
                if self.converged:
                    img = self.assets["router_converged"]
                elif updated:
                    img = self.assets["router_updated"]
                else:
                    img = self.assets["router_default"]

                # Glow ring behind image on update
                if updated:
                    nr = self.NODE_IMG_HALF + 8
                    self.canvas.create_oval(x-nr, y-nr, x+nr, y+nr,
                                            fill="", outline=self.COL_GLOW,
                                            width=3, tags=("static", name))

                self.canvas.create_image(x, y, image=img,
                                         tags=("static", name))
                # Label below the router image
                self.canvas.create_text(x, y + self.NODE_IMG_HALF + 10,
                                        text=name, fill="#2c3e50",
                                        font=("Arial", 10, "bold"),
                                        tags=("static", name))
            else:
                # Fallback: coloured ovals
                r = self.NODE_R
                col_fill = (self.COL_NODE_CONV if self.converged
                            else self.COL_NODE_UPD if updated
                            else self.COL_NODE_DEF)
                if updated:
                    self.canvas.create_oval(x-r-6, y-r-6, x+r+6, y+r+6,
                                            fill="", outline=self.COL_GLOW,
                                            width=3, tags=("static", name))
                self.canvas.create_oval(x-r, y-r, x+r, y+r,
                                        fill=col_fill, outline="white",
                                        width=2, tags=("static", name))
                self.canvas.create_text(x, y, text=name, fill="white",
                                        font=("Arial", 10, "bold"),
                                        tags=("static", name))

            self.canvas.tag_bind(name, "<Button-1>",
                                 lambda e, n=name: self._show_table(n))
            self.canvas.tag_bind(name, "<Enter>",
                                 lambda e, n=name: self._on_hover(n))
            self.canvas.tag_bind(name, "<Leave>",
                                 lambda e: self._off_hover())

    # ──────────────────────────────────────────────────────────
    # Packet animation
    # ──────────────────────────────────────────────────────────

    def _animate_packets(self, messages, on_done):
        if not messages:
            on_done()
            return

        total    = len(messages)
        finished = [0]

        def particle_done():
            finished[0] += 1
            if finished[0] >= total:
                on_done()

        for idx, msg in enumerate(messages):
            delay = idx * self.STAGGER_MS
            self.root.after(
                delay,
                lambda s=msg["sender"], rv=msg["receiver"]:
                    self._launch_particle(s, rv, particle_done)
            )

    def _launch_particle(self, sender, receiver, on_done):
        x1, y1 = self.node_positions[sender]
        x2, y2 = self.node_positions[receiver]

        if self._use_img:
            dot = self.canvas.create_image(x1, y1,
                                           image=self.assets["packet"],
                                           tags="particle")
        else:
            pr  = self.PARTICLE_R
            dot = self.canvas.create_oval(
                x1-pr, y1-pr, x1+pr, y1+pr,
                fill=self.COL_PARTICLE, outline="white", width=1,
                tags="particle")

        frame = [0]
        N     = self.PARTICLE_FRAMES

        def step():
            f = frame[0]
            if f >= N:
                self.canvas.delete(dot)
                on_done()
                return
            t  = f / N
            t2 = t * t * (3 - 2 * t)   # smooth-step easing
            nx = x1 + (x2 - x1) * t2
            ny = y1 + (y2 - y1) * t2
            if self._use_img:
                self.canvas.coords(dot, nx, ny)
            else:
                pr = self.PARTICLE_R
                self.canvas.coords(dot, nx-pr, ny-pr, nx+pr, ny+pr)
            frame[0] += 1
            self.root.after(self.PARTICLE_MS, step)

        step()

    # ──────────────────────────────────────────────────────────
    # Hover / log / table
    # ──────────────────────────────────────────────────────────

    def _on_hover(self, name):
        r  = self.routers[name]
        nb = ", ".join(sorted(n.name for n in r.neighbors))
        self.lbl_status.config(
            text=f"  {name} - neighbors: {nb}", fg="#1abc9c")

    def _off_hover(self):
        if not self.converged:
            self.lbl_status.config(text="* Running...", fg="#f39c12")

    def _log(self, msg):
        self.txt_logs.config(state="normal")
        self.txt_logs.insert(tk.END, msg + "\n")
        self.txt_logs.see(tk.END)
        self.txt_logs.config(state="disabled")

    def _show_table(self, name):
        self.selected_router = name
        router  = self.routers[name]
        content = f"=== {name} ===\n\n"
        content += format_routing_table(router.get_routing_table())
        self.txt_tables.config(state="normal")
        self.txt_tables.delete(1.0, tk.END)
        self.txt_tables.insert(tk.END, content)
        self.txt_tables.config(state="disabled")

    # ──────────────────────────────────────────────────────────
    # Simulation steps
    # ──────────────────────────────────────────────────────────

    def _next_round(self):
        if self.converged or self._animating:
            return

        self._animating = True
        self.btn_next.config(state="disabled")
        self.btn_auto.config(state="disabled")

        self.round_number += 1
        self.lbl_round.config(text=f"Round: {self.round_number}")
        self.lbl_status.config(
            text=f"* Round {self.round_number} - transmitting...", fg="#f39c12")

        messages = []
        for rname, router in self.routers.items():
            snap = router.get_routing_table()
            for nb in router.neighbors:
                messages.append({"sender": rname,
                                  "receiver": nb.name,
                                  "table": snap})

        active = {tuple(sorted((m["sender"], m["receiver"])))
                  for m in messages}
        self._draw_network(active_links=active)

        def after_animation():
            converged, updates = run_rip_round(self.routers)

            changed = set()
            for msg in updates:
                self._log(msg)
                parts = msg.split()
                if parts:
                    changed.add(parts[0])

            if not updates:
                self._log(f"[Round {self.round_number}] No changes.")

            self._draw_network(highlight=changed)

            if self.selected_router:
                self._show_table(self.selected_router)

            if converged:
                self.converged = True
                self._draw_network()
                self.lbl_status.config(text="[OK]  CONVERGED", fg="#2ecc71")
                self._log(
                    f">>> Network converged after {self.round_number} round(s) <<<")
                messagebox.showinfo(
                    "RIP Simulation",
                    f"Network converged in {self.round_number} round(s)!")
            else:
                self.lbl_status.config(
                    text=f"* Round {self.round_number} done", fg="#1abc9c")
                self.btn_next.config(state="normal")
                self.btn_auto.config(state="normal")

            self._animating = False

        self._animate_packets(messages, after_animation)

    def _auto_run(self):
        if self.converged or self._animating:
            return

        def step():
            if not self.converged:
                self._next_round()
                self.root.after(self.AUTO_DELAY_MS, step)

        step()

    # ──────────────────────────────────────────────────────────
    # Topology editor / reset
    # ──────────────────────────────────────────────────────────

    def _edit_topology(self):
        ed = TopologyEditor(self.root, default_routers=self.routers)
        self.root.wait_window(ed)
        if ed.result:
            self.routers = ed.result
            self._full_reset()

    def _reset_simulation(self):
        names = list(self.routers.keys())
        edges = set()
        for n, r in self.routers.items():
            for nb in r.neighbors:
                edges.add(tuple(sorted((n, nb.name))))

        new_routers = {n: Router(n) for n in names}
        for (a, b) in edges:
            new_routers[a].add_neighbor(new_routers[b])
            new_routers[b].add_neighbor(new_routers[a])

        self.routers = new_routers
        self._full_reset()

    def _full_reset(self):
        self.round_number    = 0
        self.converged       = False
        self.selected_router = None
        self._animating      = False

        self.node_positions  = self._calc_positions()
        self.canvas.delete("all")
        self._draw_network()

        self.lbl_round.config(text="Round: 0")
        self.lbl_status.config(text="* Initialized", fg="#1abc9c")
        self.btn_next.config(state="normal")
        self.btn_auto.config(state="normal")

        for w in (self.txt_logs, self.txt_tables):
            w.config(state="normal")
            w.delete(1.0, tk.END)
            w.config(state="disabled")

        self._log(f"Topology loaded - "
                  f"{len(self.routers)} routers, ready to simulate.")
