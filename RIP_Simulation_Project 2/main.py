import tkinter as tk
import os

from network_topology import load_topology
from gui import RIPSimulationGUI, TopologyEditor


def main():
    """
    Entry point for the RIP Simulation.
    1. Try to load topology.txt as the default topology.
    2. Show the Topology Editor so the user can review / modify it.
    3. Launch the main simulation GUI.
    """
    root = tk.Tk()
    root.withdraw()   # hide main window while editor is open

    # ── Load default topology (if present) ────────────────────
    base_dir      = os.path.dirname(os.path.abspath(__file__))
    topology_file = os.path.join(base_dir, "data", "topology.txt")

    default_routers = None
    if os.path.exists(topology_file):
        try:
            default_routers = load_topology(topology_file)
            print(f"Loaded topology: {list(default_routers.keys())}")
        except Exception as e:
            print(f"Could not load topology.txt: {e}")

    # ── Show topology editor ───────────────────────────────────
    editor = TopologyEditor(root, default_routers=default_routers)
    root.wait_window(editor)

    if editor.result is None:
        # User cancelled → exit
        root.destroy()
        return

    routers = editor.result

    # ── Launch simulation ──────────────────────────────────────
    root.deiconify()
    root.title("RIP Protocol Simulation")
    app = RIPSimulationGUI(root, routers)
    root.mainloop()


if __name__ == "__main__":
    main()
