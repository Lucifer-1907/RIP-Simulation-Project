from utils import INFINITY

class Router:
    def __init__(self, name):
        self.name = name
        self.neighbors = []  # List of Router objects
        
        # Routing table: {destination_name: (next_hop_name, hop_count)}
        # next_hop_name is None for self
        self.routing_table = {self.name: (None, 0)}

    def add_neighbor(self, neighbor):
        """Adds a neighbor router."""
        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)
            # Initial distance to neighbor is 1, next hop is neighbor itself
            # We don't overwrite if we already have a better path (unlikely in init, but good practice)
            if neighbor.name not in self.routing_table:
                self.routing_table[neighbor.name] = (neighbor.name, 1)

    def get_routing_table(self):
        """Returns the routing table."""
        return self.routing_table.copy()

    def receive_update(self, neighbor_name, neighbor_table):
        """
        Process a routing table received from a neighbor.
        Returns True if the routing table changed, False otherwise.
        """
        updated = False
        
        # In this simulation, the cost to any neighbor is 1.
        cost_to_neighbor = 1
        
        for dest, (next_hop, metric) in neighbor_table.items():
            new_metric = metric + cost_to_neighbor
            
            # Split Horizon (Basic): Don't accept bad news about a route from the guy we learned it from?
            # Actually, standard Distance Vector rule:
            
            current_route = self.routing_table.get(dest)
            
            if current_route is None:
                # New destination found
                if new_metric < INFINITY:
                    self.routing_table[dest] = (neighbor_name, new_metric)
                    updated = True
            else:
                current_next_hop, current_metric = current_route
                
                # Case 1: Found a shorter path
                if new_metric < current_metric:
                    self.routing_table[dest] = (neighbor_name, new_metric)
                    updated = True
                
                # Case 2: The neighbor we trust for this route has updated information (e.g., cost increased)
                elif current_next_hop == neighbor_name:
                    if current_metric != new_metric:
                       self.routing_table[dest] = (neighbor_name, min(new_metric, INFINITY))
                       updated = True
        
        return updated

    def __repr__(self):
        return f"Router({self.name})"
