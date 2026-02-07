import tkinter as tk
import os

from network_topology import load_topology
from gui import RIPSimulationGUI


def main():
    """
    Entry point of the RIP Simulation project.
    Responsible only for:
    - Loading the network topology
    - Initializing routers
    - Launching the GUI
    """

    base_dir = os.path.dirname(os.path.abspath(__file__))
    topology_file = os.path.join(base_dir, "data", "topology.txt")

    if not os.path.exists(topology_file):
        print(f"Error: Topology file not found at {topology_file}")
        return

    print("Loading network topology...")
    routers = load_topology(topology_file)
    print(f"Topology loaded successfully. Routers found: {len(routers)}")

    print("Launching RIP Simulation GUI...")
    root = tk.Tk()
    root.title("RIP Protocol Simulation")
    app = RIPSimulationGUI(root, routers)
    root.mainloop()


if __name__ == "__main__":
    main()
