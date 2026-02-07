from utils import INFINITY


class Router:
    """
    Represents a router in a RIP (Routing Information Protocol) simulation.
    This is a logical/software representation, not a physical router.
    """

    def __init__(self, name):
        # Router identifier (e.g., R1, R2)
        self.name = name

        # List of directly connected neighbor Router objects
        self.neighbors = []

        # Routing table format:
        # { destination_name : (next_hop_name, hop_count) }
        # Route to itself: hop_count = 0, next_hop = None
        self.routing_table = {self.name: (None, 0)}

    def add_neighbor(self, neighbor):
        """
        Adds a directly connected neighbor router.
        Initializes routing table entry with hop count = 1.
        """
        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)

            # Direct neighbor is reachable in one hop
            if neighbor.name not in self.routing_table:
                self.routing_table[neighbor.name] = (neighbor.name, 1)

    def get_routing_table(self):
        """
        Returns a copy of the routing table to prevent external modification.
        """
        return self.routing_table.copy()

    def receive_update(self, neighbor_name, neighbor_table):
        """
        Processes a routing table received from a neighbor.
        Implements the RIP distance vector update rule.

        Parameters:
        - neighbor_name: name of the router sending the update
        - neighbor_table: routing table of the neighbor

        Returns:
        - True if the routing table was updated
        - False otherwise
        """
        updated = False
        cost_to_neighbor = 1  # RIP hop cost

        for destination, (next_hop, metric) in neighbor_table.items():
            # Calculate new hop count via neighbor
            new_metric = min(metric + cost_to_neighbor, INFINITY)

            current_route = self.routing_table.get(destination)

            # Case 1: New destination learned
            if current_route is None:
                if new_metric < INFINITY:
                    self.routing_table[destination] = (neighbor_name, new_metric)
                    updated = True

            else:
                current_next_hop, current_metric = current_route

                # Case 2: Shorter path found
                if new_metric < current_metric:
                    self.routing_table[destination] = (neighbor_name, new_metric)
                    updated = True

                # Case 3: Update received from the same next hop
                elif current_next_hop == neighbor_name and current_metric != new_metric:
                    self.routing_table[destination] = (neighbor_name, new_metric)
                    updated = True

        return updated

    def print_routing_table(self):
        """
        Prints the routing table in a readable format.
        Useful for debugging and demonstration.
        """
        print(f"\nRouting Table for {self.name}:")
        print("Destination | Next Hop | Hop Count")
        print("----------------------------------")
        for dest, (nh, metric) in self.routing_table.items():
            nh_display = nh if nh is not None else "-"
            print(f"{dest:^11} | {nh_display:^8} | {metric:^9}")

    def __repr__(self):
        return f"Router({self.name})"
