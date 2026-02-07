HOPS_LIMIT = 15
INFINITY = 16

def format_routing_table(routing_table):
    """Formats the routing table for string display."""
    output = []
    output.append(f"{'Dest':<10} | {'Next Hop':<10} | {'Cost':<5}")
    output.append("-" * 30)
    for dest, (next_hop, metric) in routing_table.items():
        output.append(f"{dest:<10} | {next_hop if next_hop else '-':<10} | {metric:<5}")
    return "\n".join(output)

def log_event(message):
    """Simple logger wrapper."""
    print(f"[LOG] {message}")
