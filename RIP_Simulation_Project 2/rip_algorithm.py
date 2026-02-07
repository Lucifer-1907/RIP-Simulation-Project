from utils import log_event


def run_rip_round(routers):
    """
    Executes ONE RIP update round.

    In one round:
    - Each router sends its current routing table to all neighbors
    - Neighbors update their tables if a shorter path is found

    Returns:
        converged (bool): True if no routing table changed
        updates (list): Human-readable update messages (for GUI/logs)
    """
    updates_log = []
    changes_count = 0

    # STEP 1: Prepare all RIP messages (synchronous round simulation)
    messages = []
    for router_name, router in routers.items():
        routing_table_snapshot = router.get_routing_table()

        for neighbor in router.neighbors:
            messages.append({
                "sender": router_name,
                "receiver": neighbor.name,
                "table": routing_table_snapshot
            })

    # STEP 2: Process all RIP messages
    for msg in messages:
        sender = msg["sender"]
        receiver = msg["receiver"]
        table = msg["table"]

        receiver_router = routers[receiver]
        updated = receiver_router.receive_update(sender, table)

        if updated:
            changes_count += 1
            message = (
                f"{receiver} updated its routing table "
                f"based on information received from {sender}"
            )
            updates_log.append(message)
            log_event(message)

    # STEP 3: Check convergence
    converged = (changes_count == 0)
    return converged, updates_log
