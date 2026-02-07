# RIP Simulation Project

A Python-based simulation of the Routing Information Protocol (RIP) for educational purposes. This project demonstrates how routers exchange information to build routing tables using the Distance Vector algorithm.

## Features
- **Visual Simulation**: View routers and connections in a GUI.
- **Step-by-Step Mode**: Manually control each round of updates to see how tables evolve.
- **Auto-Run**: Automatically modify the simulation until convergence.
- **Convergence Detection**: Visual and log indicators when the network triggers a steady state.

## Installation
1.  Ensure you have Python installed.
2.  No external dependencies are required (uses standard `tkinter`).

## Usage
1.  Navigate to the project directory:
    ```bash
    cd RIP_Simulation_Project
    ```
2.  Run the simulation:
    ```bash
    python main.py
    ```
3.  **In the GUI**:
    - Click **Next Round** to step through the algorithm.
    - Click **Auto Run** to finish the simulation.
    - **Click on any Router Node** to view its current routing table.

## Concept
- **Distance Vector**: Routers send their routing table to neighbors.
- **Hop Count**: The metric used is the number of hops. Max hops is 15.
- **Convergence**: When no more updates occur, the network is converged.

## Custom Topology
You can modify `data/topology.txt` to create different network graphs.
Format: `Node1 Node2` (one connection per line).
