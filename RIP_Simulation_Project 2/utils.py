# RIP constants
INFINITY = 16  # Hop count >= 16 means unreachable


def format_routing_table(routing_table):
    """
    Formats a routing table dictionary into a readable table.

    Input format:
    { destination : (next_hop, hop_count) }
    """
    lines = []
    header = f"{'Destination':<12} | {'Next Hop':<10} | {'Hop Count':<9}"
    divider = "-" * len(header)

    lines.append(header)
    lines.append(divider)

    for dest, (next_hop, metric) in sorted(routing_table.items()):
        nh = next_hop if next_hop is not None else "-"
        lines.append(f"{dest:<12} | {nh:<10} | {metric:<9}")

    return "\n".join(lines)


def log_event(message):
    """
    Simple logging utility for RIP simulation events.
    """
    print(f"[LOG] {message}")
