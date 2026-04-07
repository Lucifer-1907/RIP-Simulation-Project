import os
from router import Router


def load_topology(file_path):
    """
    Reads a network topology file and creates router objects.

    File format:
    Each line represents an undirected link between two routers.
    Example:
        R1 R2
        R2 R3

    Returns:
        A dictionary { router_name : Router_object }
    """
    routers = {}

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Topology file not found: {file_path}")

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()

            # Ignore empty lines or comments
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) != 2:
                raise ValueError(f"Invalid topology line: '{line}'")

            node_a_name, node_b_name = parts

            # Create routers if they do not exist
            if node_a_name not in routers:
                routers[node_a_name] = Router(node_a_name)

            if node_b_name not in routers:
                routers[node_b_name] = Router(node_b_name)

            # Connect routers as neighbors (undirected link)
            routers[node_a_name].add_neighbor(routers[node_b_name])
            routers[node_b_name].add_neighbor(routers[node_a_name])

    return routers
