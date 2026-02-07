import os
from router import Router

def load_topology(file_path):
    """
    Reads a topology file and returns a dictionary of Router objects.
    Format: "NodeA NodeB" per line (undirected link).
    """
    routers = {}
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Topology file not found: {file_path}")

    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            
            node_a_name, node_b_name = parts[0], parts[1]
            
            # Create routers if they don't exist
            if node_a_name not in routers:
                routers[node_a_name] = Router(node_a_name)
            if node_b_name not in routers:
                routers[node_b_name] = Router(node_b_name)
            
            # Connect them (undirected)
            routers[node_a_name].add_neighbor(routers[node_b_name])
            routers[node_b_name].add_neighbor(routers[node_a_name])
            
    return routers
