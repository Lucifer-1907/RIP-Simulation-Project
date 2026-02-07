import tkinter as tk
from network_topology import load_topology
from gui import RIPSimulationGUI
import os

def main():
    topology_file = "data/topology.txt"
    if not os.path.exists(topology_file):
        print(f"Error: {topology_file} not found.")
        return

    print("Loading network topology...")
    routers = load_topology(topology_file)
    print(f"Loaded {len(routers)} routers.")

    print("Starting GUI...")
    root = tk.Tk()
    app = RIPSimulationGUI(root, routers)
    root.mainloop()

if __name__ == "__main__":
    main()
